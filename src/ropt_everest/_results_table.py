"""A handler for creating report tables."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, Sequence

from ropt.enums import EventType, ResultAxis
from ropt.plugins.plan.base import ResultHandler
from ropt.report import ResultsDataFrame
from tabulate import tabulate

if TYPE_CHECKING:
    from everest.config import EverestConfig
    from ropt.plan import Event, Plan

_COLUMNS: Final[dict[str, dict[str, str]]] = {
    "results": {
        "batch_id": "Batch",
        "functions.weighted_objective": "Total-Objective",
        "functions.objectives": "Objective",
        "functions.constraints": "Constraint",
        "evaluations.variables": "Control",
    },
    "gradients": {
        "batch_id": "Batch",
        "gradients.weighted_objective": "Total-Gradient",
        "gradients.objectives": "Grad-objective",
        "gradients.constraints": "Grad-constraint",
    },
    "simulations": {
        "batch_id": "Batch",
        "realization": "Realization",
        "variable": "Control-name",
        "evaluations.variables": "Control",
        "evaluations.objectives": "Objective",
        "evaluations.constraints": "Constraint",
        "evaluations.evaluation_ids": "Simulation",
    },
    "perturbations": {
        "batch_id": "Batch",
        "realization": "Realization",
        "perturbation": "Perturbation",
        "evaluations.perturbed_variables": "Control",
        "evaluations.perturbed_objectives": "Objective",
        "evaluations.perturbed_constraints": "Constraint",
        "evaluations.perturbed_evaluation_ids": "Simulation",
    },
    "constraints": {
        "batch_id": "Batch",
        "constraint_info.bound_lower": "BCD-lower",
        "constraint_info.bound_upper": "BCD-upper",
        "constraint_info.linear_lower": "ICD-lower",
        "constraint_info.linear_upper": "ICD-upper",
        "constraint_info.nonlinear_lower": "OCD-lower",
        "constraint_info.nonlinear_upper": "OCD-upper",
        "constraint_info.bound_violation": "BCD-violation",
        "constraint_info.linear_violation": "ICD-violation",
        "constraint_info.nonlinear_violation": "OCD-violation",
    },
}

_TABLE_TYPE_MAP: Final[dict[str, Literal["functions", "gradients"]]] = {
    "results": "functions",
    "gradients": "gradients",
    "simulations": "functions",
    "perturbations": "gradients",
    "constraints": "functions",
}


class EverestDefaultTableHandler(ResultHandler):
    def __init__(
        self,
        plan: Plan,
        *,
        everest_config: EverestConfig,
        tags: str | set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(plan)
        self._tags = _get_set(tags)
        self._everest_config = everest_config
        self._metadata = metadata
        self._tables = []
        for type_, table_type in _TABLE_TYPE_MAP.items():
            columns = deepcopy(_COLUMNS[type_])
            if self._metadata is not None:
                for key in self._metadata:
                    columns[f"metadata.{key}"] = key
            self._tables.append(
                ResultsTable(
                    columns,
                    Path(everest_config.optimization_output_dir) / f"{type_}.txt",
                    table_type=table_type,
                    min_header_len=3,
                )
            )

    def handle_event(self, event: Event) -> Event:
        """Handle an event."""
        if (
            event.event_type == EventType.FINISHED_EVALUATION
            and "results" in event.data
            and (event.tags & self._tags)
        ):
            if self._metadata is not None:
                metadata = {
                    key: self.plan[value[1:]]
                    if (
                        isinstance(value, str)
                        and value.startswith("$")
                        and not value[1:].startswith("$")
                    )
                    else value
                    for key, value in self._metadata.items()
                }
                for item in event.data["results"]:
                    item.metadata = metadata

            names = _get_names(self._everest_config)
            for table in self._tables:
                added = False
                for item in event.data["results"]:
                    if table.add_results(item, names):
                        added = True
                if added:
                    table.save()
        return event


class ResultsTable(ResultsDataFrame):
    def __init__(
        self,
        columns: dict[str, str],
        path: Path,
        *,
        table_type: Literal["functions", "gradients"] = "functions",
        min_header_len: int | None = None,
    ) -> None:
        super().__init__(set(columns), table_type=table_type)

        if path.parent.exists():
            if not path.parent.is_dir():
                msg = f"Cannot write table to: {path}"
                raise RuntimeError(msg)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)

        self._columns = columns
        self._path = path
        self._min_header_len = min_header_len

    def save(self) -> None:
        data = self.frame
        if not data.empty:
            # Turn the multi-index into columns:
            data = data.reset_index()

            # Reorder the columns to match the order of the headers:
            reordered_columns = [
                name
                for key in self._columns
                for name in data.columns.to_numpy()
                if name == key or (isinstance(name, tuple) and name[0] == key)
            ]
            data = data.reindex(columns=reordered_columns)

            # Rename the columns:
            renamed_columns = [
                "\n".join([self._columns[name[0]]] + [str(item) for item in name[1:]])
                if isinstance(name, tuple)
                else self._columns[name]
                for name in reordered_columns
            ]
            data = data.set_axis(renamed_columns, axis="columns")

            # Add newlines to the headers to make them all the same length:
            max_lines = max(len(str(column).split("\n")) for column in data.columns)
            if self._min_header_len is not None and max_lines < self._min_header_len:
                max_lines = self._min_header_len
            data = data.rename(
                columns={
                    column: str(column)
                    + (max_lines - len(str(column).split("\n"))) * "\n"
                    for column in data.columns
                },
            )

            # Write the table to a file:
            table_data = {str(column): data[column] for column in data}
            self._path.write_text(
                tabulate(
                    table_data, headers="keys", tablefmt="simple", showindex=False
                ),
            )


def _get_set(values: str | set[str] | list[str] | tuple[str, ...] | None) -> set[str]:
    match values:
        case str():
            return {values}
        case set() | list() | tuple():
            return set(values)
        case None:
            return set()
    msg = f"Invalid type for values: {type(values)}"
    raise TypeError(msg)


def _get_names(
    everest_config: EverestConfig | None,
) -> dict[str, Sequence[str | int] | None] | None:
    if everest_config is None:
        return None

    return {
        ResultAxis.VARIABLE: everest_config.formatted_control_names,
        ResultAxis.OBJECTIVE: everest_config.objective_names,
        ResultAxis.NONLINEAR_CONSTRAINT: everest_config.constraint_names,
        ResultAxis.REALIZATION: everest_config.model.realizations,
    }
