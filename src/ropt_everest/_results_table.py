"""A handler for creating report tables."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, Sequence

import pandas as pd
from ropt.enums import EventType, ResultAxis
from ropt.plugins.plan.base import ResultHandler
from ropt.results import Results, results_to_dataframe
from tabulate import tabulate

if TYPE_CHECKING:
    from everest.config import EverestConfig
    from ropt.plan import Event, Plan

_COLUMNS: Final[dict[str, dict[str, str]]] = {
    "results": {
        "eval_id": "Eval-ID",
        "batch_id": "Batch",
        "functions.weighted_objective": "Total-Objective",
        "functions.objectives": "Objective",
        "functions.constraints": "Constraint",
        "evaluations.variables": "Control",
    },
    "gradients": {
        "eval_id": "Eval-ID",
        "batch_id": "Batch",
        "gradients.weighted_objective": "Total-Gradient",
        "gradients.objectives": "Grad-objective",
        "gradients.constraints": "Grad-constraint",
    },
    "simulations": {
        "eval_id": "Eval-ID",
        "batch_id": "Batch",
        "realization": "Realization",
        "variable": "Control-name",
        "evaluations.variables": "Control",
        "evaluations.objectives": "Objective",
        "evaluations.constraints": "Constraint",
        "evaluations.evaluation_ids": "Simulation",
    },
    "perturbations": {
        "eval_id": "Eval-ID",
        "batch_id": "Batch",
        "realization": "Realization",
        "perturbation": "Perturbation",
        "evaluations.perturbed_variables": "Control",
        "evaluations.perturbed_objectives": "Objective",
        "evaluations.perturbed_constraints": "Constraint",
        "evaluations.perturbed_evaluation_ids": "Simulation",
    },
    "constraints": {
        "eval_id": "Eval-ID",
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
        self._tables = []
        names = _get_names(everest_config)
        for type_, table_type in _TABLE_TYPE_MAP.items():
            self._tables.append(
                ResultsTable(
                    _COLUMNS[type_],
                    Path(everest_config.optimization_output_dir) / f"{type_}.txt",
                    table_type=table_type,
                    metadata=metadata,
                    names=names,
                    min_header_len=3,
                )
            )

    def handle_event(self, event: Event) -> None:
        """Handle an event."""
        if (
            event.event_type == EventType.FINISHED_EVALUATION
            and "results" in event.data
            and (event.tags & self._tags)
        ):
            for table in self._tables:
                table.add_results(event.data["results"])


class ResultsTable:
    def __init__(  # noqa: PLR0913
        self,
        columns: dict[str, str],
        path: Path,
        *,
        table_type: Literal["functions", "gradients"] = "functions",
        metadata: dict[str, Any] | None = None,
        names: dict[str, Sequence[str | int] | None] | None = None,
        min_header_len: int | None = None,
    ) -> None:
        columns = deepcopy(columns)
        if metadata is not None:
            for key, value in metadata.items():
                columns[f"metadata.{key}"] = value

        if path.parent.exists():
            if not path.parent.is_dir():
                msg = f"Cannot write table to: {path}"
                raise RuntimeError(msg)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)

        self._columns = columns
        self._path = path
        self._names = names
        self._results_type = table_type
        self._min_header_len = min_header_len
        self._frames: list[pd.DataFrame] = []

    def add_results(self, results: Sequence[Results]) -> None:
        frame = results_to_dataframe(
            results,
            set(self._columns.keys()),
            result_type=self._results_type,
            names=self._names,
        )
        if not frame.empty:
            self._frames.append(frame)
            self.save()

    def save(self) -> None:
        data = pd.concat(self._frames)
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
