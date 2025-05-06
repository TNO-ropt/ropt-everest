"""A handler for creating report tables."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal

from ropt.enums import ResultAxis

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd
    from everest.config import EverestConfig

TABLE_COLUMNS: Final[dict[str, dict[str, str]]] = {
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
        "evaluations.evaluation_info.sim_ids": "Simulation",
    },
    "perturbations": {
        "batch_id": "Batch",
        "realization": "Realization",
        "perturbation": "Perturbation",
        "evaluations.perturbed_variables": "Control",
        "evaluations.perturbed_objectives": "Objective",
        "evaluations.perturbed_constraints": "Constraint",
        "evaluations.evaluation_info.sim_ids": "Simulation",
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

TABLE_TYPE_MAP: Final[dict[str, Literal["functions", "gradients"]]] = {
    "results": "functions",
    "gradients": "gradients",
    "simulations": "functions",
    "perturbations": "gradients",
    "constraints": "functions",
}


def get_names(
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


def reorder_columns(
    data: pd.DataFrame, columns: list[str] | dict[str, str]
) -> pd.DataFrame:
    reordered_columns = [
        name
        for key in columns
        for name in data.columns.to_numpy()
        if name == key or (isinstance(name, tuple) and name[0] == key)
    ]
    return data.reindex(columns=reordered_columns)


def rename_columns(data: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    renamed_columns = [
        "\n".join([columns[name[0]]] + [str(item) for item in name[1:]])
        if isinstance(name, tuple)
        else columns[name]
        for name in data.columns.to_numpy()
    ]
    return data.set_axis(renamed_columns, axis="columns")


def fix_columns(data: pd.DataFrame) -> pd.DataFrame:
    def _strip(value: str) -> str:
        _, _, new_value = value.partition(".")
        return new_value.replace("variables", "controls")

    renamed_columns = [
        (_strip(name[0]), *(str(item) for item in name[1:]))
        if isinstance(name, tuple)
        else _strip(name)
        for name in data.columns.to_numpy()
    ]
    return data.set_axis(renamed_columns, axis="columns")
