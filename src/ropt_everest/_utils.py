from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal

from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.plugins import get_site_plugins
from ert.run_models.everest_run_model import EverestExitCode, EverestRunModel
from everest.config import EverestConfig

if TYPE_CHECKING:
    import pandas as pd

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
        "evaluations.evaluation_info.batch_ids": "Source-batch",
        "evaluations.evaluation_info.sim_ids": "Simulation",
    },
    "perturbations": {
        "batch_id": "Batch",
        "realization": "Realization",
        "perturbation": "Perturbation",
        "evaluations.perturbed_variables": "Control",
        "evaluations.perturbed_objectives": "Objective",
        "evaluations.perturbed_constraints": "Constraint",
        "evaluations.evaluation_info.batch_ids": "Source-batch",
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


def load_config(config_file: str) -> dict[str, Any]:
    """Loads an Everest configuration from a YAML file.

    This function reads an Everest configuration specified by the `config_file`
    path, parses it, and returns it as a Python dictionary.

    Args:
        config_file: The path to the Everest configuration YAML file.

    Returns:
        A dictionary representing the Everest configuration.
    """
    config: dict[str, Any] = EverestConfig.load_file(config_file).model_dump(
        exclude_none=True
    )
    return config


def run_everest(
    config_file: str,
    *,
    script: Path | str | None = None,
    report_exit_code: bool = True,
) -> EverestExitCode:
    """Runs an Everest optimization directly from a configuration file.

    This function provides a convenient way to execute an Everest optimization
    workflow without having to use the `everest` command. This method will run a
    full optimization, but it will not produce the usual monitoring output of
    Everest.

    Using this method instead of the `everest` command-line tool offers
    several advantages, including:

    - Direct access to standard output (stdout): Unlike the `everest`
        command, this does not redirect standard output.
    - Error traces: If errors occur during the optimization, you'll get a
        full Python stack trace, making debugging easier.
    - Exceptional exit conditions, such as maximum number batch reached, or
        a user abort are reported, if `report_exit_code` is set (the default).

    The optional `script` argument is used to define a custom script that runs
    the optimization. If the file named by `script` does not exists, the
    argument is ignored and the default optimization workflow is run.

    Args:
        config_file:      The path to the Everest configuration file (YAML).
        script:           Optional script to replace the default optimization.
        report_exit_code: If `True`, report the exit code.

    Returns:
        The Everest exit code.
    """
    run_model = EverestRunModel.create(
        EverestConfig.load_file(config_file), runtime_plugins=get_site_plugins()
    )
    if script is not None and Path(script).exists():
        env_var = os.environ.get("ROPT_SCRIPT", None)
        try:
            os.environ["ROPT_SCRIPT"] = str(script)
            run_model.run_experiment(EvaluatorServerConfig())
        finally:
            if env_var is not None:
                os.environ["ROPT_SCRIPT"] = env_var
            else:
                del os.environ["ROPT_SCRIPT"]
    else:
        run_model.run_experiment(EvaluatorServerConfig())
    if report_exit_code:
        match run_model.exit_code:
            case EverestExitCode.MAX_BATCH_NUM_REACHED:
                msg = "Optimization aborted: maximum number of batches reached."
            case EverestExitCode.USER_ABORT:
                msg = "Optimization aborted: user abort."
            case _:
                msg = "Optimization completed."
        print(msg)  # noqa: T201
    return run_model.exit_code
