from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.run_models.everest_run_model import EverestExitCode, EverestRunModel
from everest.config import EverestConfig
from everest.optimizer.everest2ropt import everest2ropt
from everest.optimizer.opt_model_transforms import get_optimization_domain_transforms
from ropt.config import EnOptConfig
from ropt.results import FunctionResults, GradientResults, Results, results_to_dataframe
from ropt.transforms import OptModelTransforms

from ._utils import TABLE_COLUMNS, TABLE_TYPE_MAP, fix_columns, reorder_columns

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy as np
    import pandas as pd
    from numpy.typing import ArrayLike, NDArray
    from ropt.evaluator import EvaluatorCallback
    from ropt.plan import Plan
    from ropt.plugins.plan.base import Evaluator, EventHandler, PlanStep


class EverestPlan:
    """Represents an execution plan for an Everest optimization workflow.

    The `EverestPlan` class provides a high-level interface for defining and
    managing optimization workflows in Everest. It allows you to add various
    steps to the plan, such as optimizers and evaluators, that are then executed
    to achieve the desired optimization goal.
    """

    def __init__(self, plan: Plan, evaluator: EvaluatorCallback) -> None:
        self._plan = plan
        self._evaluator = plan.add_evaluator("function_evaluator", evaluator=evaluator)

    def add_optimizer(self) -> EverestOptimizerStep:
        """Adds an optimizer to the execution plan.

        This method integrates an optimization step into your Everest workflow.
        Invoking this method returns an
        [`EverestOptimizerStep`][ropt_everest.EverestOptimizerStep] object,
        which you can execute using its
        [`run`][ropt_everest.EverestOptimizerStep.run] method.

        Returns:
            An `EverestOptimizerStep` object, representing the added optimizer.
        """
        step = self._plan.add_step("optimizer")
        self._evaluator.add_clients(step)
        return EverestOptimizerStep(self._plan, step)

    def add_ensemble_evaluator(self) -> EverestEnsembleEvaluatorStep:
        """Adds an evaluator to the execution plan.

        This method integrates an ensemble evaluator step into your Everest
        workflow. Invoking this method returns an
        [`EverestEnsembleEvaluatorStep`][ropt_everest.EverestEnsembleEvaluatorStep]
        object, which you can execute using its
        [`run`][ropt_everest.EverestEnsembleEvaluatorStep.run] method.

        Returns:
            An `EverestEnsembleEvaluatorStep` object, representing the added evaluator.
        """
        step = self._plan.add_step("ensemble_evaluator")
        self._evaluator.add_clients(step)
        return EverestEnsembleEvaluatorStep(self._plan, step)

    def add_cache(
        self,
        steps: EverestStepBase | Sequence[EverestStepBase] | set[EverestStepBase],
        sources: EverestEventHandlerBase
        | Sequence[EverestEventHandlerBase]
        | set[EverestEventHandlerBase],
    ) -> EverestCachedEvaluator:
        """Adds an cache to the execution plan.

        This method integrates a caching mechanism into your Everest workflow.
        Invoking this method returns an
        [`EverestCachedEvaluator`][ropt_everest.EverestCachedEvaluator] object,
        which will act as a cache.

        The cache is only serving the steps specified in the `steps` argument.
        Cached values are retrieved from the specified source(s) and used to
        avoid redundant evaluations. The sources must be an event handler that
        stores the results produced by the optimization or evaluation steps.

        Args:
            steps:   The steps that will use the cache.
            sources: The source(s) of cached values.

        Returns:
            A cache object.
        """
        steps = {steps} if isinstance(steps, EverestStepBase) else set(steps)
        sources = (
            {sources} if isinstance(sources, EverestEventHandlerBase) else set(sources)
        )
        cache = self._plan.add_evaluator(
            "everest/cached_evaluator",
            clients={step.step for step in steps},
            sources={source.handler for source in sources},
        )
        self._evaluator.remove_clients({step.step for step in steps})
        self._evaluator.add_clients(cache)
        return EverestCachedEvaluator(self._plan, cache)

    def add_store(
        self,
        steps: EverestStepBase | Sequence[EverestStepBase],
    ) -> EverestStore:
        """Adds a results store to the execution plan.

        Stores the results of specified optimization or evaluation steps.

        Invoking this method returns an
        [`EverestStore`][ropt_everest.EverestStore] object, which provides
        various methods to access the stored results.

        **steps:** This argument specifies which steps in the execution plan the
        store should monitor. You can provide either a single step object
        (such as an optimizer or evaluator) or a sequence of steps. The store object
        will record all the results generated by these steps.

        Args:
            steps: The EverestStep(s) to monitor.

        Returns:
            An `EverestStore` object, which can be used to access the stored results.
        """
        step_set = {steps} if isinstance(steps, EverestBase) else set(steps)
        handler = self._plan.add_event_handler(
            "store", sources={obj.step for obj in step_set}
        )
        return EverestStore(self._plan, handler)

    def add_tracker(
        self,
        steps: EverestStepBase | Sequence[EverestStepBase],
        *,
        what: Literal["best", "last"] = "best",
        constraint_tolerance: float | None = None,
    ) -> EverestTracker:
        """Adds a tracker to the execution plan.

        Trackers monitor the progress of specified optimization or evaluation
        steps and record relevant results. They provide a way to capture and
        analyze the outcomes of these steps during the execution of the plan.
        You can configure a tracker to save the best or the last results
        generated by the tracked steps.

        Invoking this method returns an
        [`EverestTracker`][ropt_everest.EverestTracker] object, which provides
        various methods to access the tracked results.

        A tracker is configured by three arguments:

        **steps:** This argument specifies which steps in the execution plan the
        tracker should monitor. You can provide either a single step object
        (such as an optimizer or evaluator) or a sequence of steps. The tracker
        will record the results generated by these steps.

        **what:** This argument determines which results the tracker should
        record. You can choose from the following options:

        - `"best"`: Only the best result found so far is tracked.
        - `"last"`: Only the most recently generated result is tracked.

        The default value is `"best"`.

        **constraint_tolerance:** This optional argument specifies the tolerance
        for constraint satisfaction. It is used to determine whether a result is
        considered feasible, meaning it satisfies the defined constraints within
        the specified tolerance. Only feasible results will be recorded. If it
        is not set, constraints are not tested.

        Args:
            steps:                The EverestStep(s) to monitor.
            what:                 Which results to track ("best" or "last").
            constraint_tolerance: Tolerance for constraint satisfaction.

        Returns:
            An `EverestTracker` object, which can be used to access the tracked results.
        """
        step_set = {steps} if isinstance(steps, EverestBase) else set(steps)
        handler = self._plan.add_event_handler(
            "tracker",
            what=what,
            constraint_tolerance=constraint_tolerance,
            sources={obj.step for obj in step_set},
        )
        return EverestTracker(self._plan, handler)

    def add_table(
        self,
        steps: EverestStepBase | Sequence[EverestStepBase],
    ) -> EverestTableHandler:
        """Adds an event handler that create a table to the execution plan.

        This event handler will monitor the progress of specified optimization
        or evaluation steps and record relevant results. A set of tables will
        then be generated and saved in the output directory.

        Args:
            steps: The EverestStep(s) to monitor.

        Returns:
            An `EverestTableHandler` object.
        """
        step_set = {steps} if isinstance(steps, EverestBase) else set(steps)
        handler = self._plan.add_event_handler(
            "everest/table", sources={obj.step for obj in step_set}
        )
        return EverestTableHandler(self._plan, handler)


class EverestBase:
    def __init__(self, plan: Plan) -> None:
        self._plan = plan

    @property
    def plan(self) -> Plan:
        return self._plan


class EverestStepBase(EverestBase):
    def __init__(self, plan: Plan, step: PlanStep) -> None:
        super().__init__(plan)
        self._step = step

    @property
    def step(self) -> PlanStep:
        return self._step


class EverestEventHandlerBase(EverestBase):
    def __init__(self, plan: Plan, handler: EventHandler) -> None:
        super().__init__(plan)
        self._handler = handler

    @property
    def handler(self) -> EventHandler:
        return self._handler


class EverestEvaluatorBase(EverestBase):
    def __init__(self, plan: Plan, evaluator: Evaluator) -> None:
        super().__init__(plan)
        self._evaluator = evaluator

    @property
    def evaluator(self) -> Evaluator:
        return self._evaluator


class EverestCachedEvaluator(EverestEvaluatorBase):
    def __init__(self, plan: Plan, cache: Evaluator) -> None:
        super().__init__(plan, cache)


class EverestOptimizerStep(EverestStepBase):
    """Represents an optimizer step in an Everest execution plan.

    This class encapsulates an optimization step within an Everest workflow. It
    provides a method to execute the optimizer.
    """

    def __init__(self, plan: Plan, optimizer: PlanStep) -> None:
        super().__init__(plan, optimizer)

    def run(
        self,
        config: dict[str, Any],
        controls: ArrayLike | None = None,
        metadata: dict[str, Any] | None = None,
        output_dir: str | None = None,
    ) -> None:
        """Runs the optimizer.

        This method executes the underlying optimizer with the given parameters.

        **Configuration**:

        - The `config` dictionary should be a dictionary that can be validated
          as an `EverestConfig` object.

        **Controls**:

        If no controls are provided, the optimizer will use the initial values
        from the configuration.

        **Metadata**:

        - The `metadata` parameter allows you to associate arbitrary data with
          each result generated by the optimizer or ensemble evaluators.
        - This metadata is included in generated tables and data frames.
        - The keys in the `metadata` dictionary are used as column names in
          the output tables.

        **Optimizer output**:

        Normally, the optimizer's output is directed to the `optimization_output`
        subdirectory within the main output directory specified in the Everest
        configuration. When multiple optimization steps are executed, there's a
        risk of output files being overwritten. The `output_dir` argument
        provides a way to override the default output location for the optimizer.
        You can specify an absolute path, or a relative path, which will be
        interpreted as relative to the `optimization_output` directory.

        Args:
            config:     An optional dictionary containing the Everest configuration
                        for the optimizer. If omitted, the default configuration is
                        used.
            controls:   An array-like object containing the controls for the optimization.
            metadata:   An optional dictionary of metadata to associate with the
                        results of the optimizer's results.
            output_dir: An optional output directory for the optimizer.
        """
        everest_config = EverestConfig.with_plugins(config)
        config_dict, initial_values = everest2ropt(
            everest_config.controls,
            everest_config.objective_functions,
            everest_config.input_constraints,
            everest_config.output_constraints,
            everest_config.optimization,
            everest_config.model,
            everest_config.environment.random_seed,
            everest_config.optimization_output_dir,
        )
        everest_transforms = get_optimization_domain_transforms(
            everest_config.controls,
            everest_config.objective_functions,
            everest_config.output_constraints,
            everest_config.model,
        )
        transforms = (
            OptModelTransforms(
                variables=everest_transforms["control_scaler"],
                objectives=everest_transforms["objective_scaler"],
                nonlinear_constraints=everest_transforms["constraint_scaler"],
            )
            if everest_transforms
            else None
        )

        if output_dir is not None:
            output_path = Path(output_dir)
            if not output_path.is_absolute():
                output_path = config_dict["optimizer"]["output_dir"] / output_path
            config_dict["optimizer"]["output_dir"] = output_path
            output_path.mkdir(parents=True, exist_ok=True)

            self.step.run(
                config=EnOptConfig.model_validate(config_dict),
                transforms=transforms,
                metadata=metadata,
                variables=initial_values if controls is None else controls,
            )


class EverestEnsembleEvaluatorStep(EverestStepBase):
    """Represents an evaluator step in an Everest execution plan.

    This class encapsulates an evaluation step within an Everest workflow. It
    provides a method to execute the evaluator .
    """

    def __init__(self, plan: Plan, ensemble_evaluator: PlanStep) -> None:
        super().__init__(plan, ensemble_evaluator)

    def run(
        self,
        config: dict[str, Any],
        controls: ArrayLike | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Runs the ensemble evaluator.

        This method executes the underlying ensemble evaluator with the given
        parameters.

        **Configuration**:

        - The `config` dictionary should be a dictionary that can be validated
          as an `EverestConfig` object.

        **Controls**:

        The `controls` parameter can be a single vector, a sequence of multiple
        vectors, or a 2D matrix where the control vectors are the rows. If no
        controls are provided, the evaluator will use its default
        the initial values from the configuration.

        **Metadata**:

        - The `metadata` parameter allows you to associate arbitrary data with
          each result generated by the optimizer or evaluators.
        - This metadata is included in generated tables and data frames.
        - The keys in the `metadata` dictionary are used as column names in
          the output tables.

        Args:
            config:   An optional dictionary containing the Everest configuration
                      for the optimizer. If omitted, the default configuration is
                      used.
            controls: An array-like object containing the controls for the optimization.
            metadata: An optional dictionary of metadata to associate with the
                      results of the optimizer's results.
        """
        everest_config = EverestConfig.with_plugins(config)
        config_dict, initial_values = everest2ropt(
            everest_config.controls,
            everest_config.objective_functions,
            everest_config.input_constraints,
            everest_config.output_constraints,
            everest_config.optimization,
            everest_config.model,
            everest_config.environment.random_seed,
            everest_config.optimization_output_dir,
        )
        everest_transforms = get_optimization_domain_transforms(
            everest_config.controls,
            everest_config.objective_functions,
            everest_config.output_constraints,
            everest_config.model,
        )
        transforms = (
            OptModelTransforms(
                variables=everest_transforms["control_scaler"],
                objectives=everest_transforms["objective_scaler"],
                nonlinear_constraints=everest_transforms["constraint_scaler"],
            )
            if everest_transforms
            else None
        )
        self.step.run(
            config=EnOptConfig.model_validate(config_dict),
            transforms=transforms,
            metadata=metadata,
            variables=initial_values if controls is None else controls,
        )


class EverestStore(EverestEventHandlerBase):
    """Provides access to the results stored by an Everest execution plan.

    This class provides methods to retrieve and analyze the results produces
    within an Everest execution plan. It allows you to access the results. You
    can also convert the stored results into a Pandas DataFrame for easier
    analysis.
    """

    def __init__(self, plan: Plan, store: EventHandler) -> None:
        super().__init__(plan, store)

    @property
    def results(self) -> list[Results] | None:
        """Retrieves the stored results.

        Returns:
            The stored results.
        """
        results: tuple[Results] | None = self.handler["results"]
        return None if results is None else list(results)

    @property
    def controls(self) -> NDArray[np.float64] | list[NDArray[np.float64]] | None:
        """Retrieves the stored controls.

        Returns:
            The stored controls.
        """
        results = self.results
        if results is None:
            return None
        return [
            item.evaluations.variables
            for item in results
            if isinstance(item, (FunctionResults, GradientResults))
        ]

    def reset(self) -> None:
        """Reset the store.

        Clears any results accumulated so far.
        """
        self.handler["results"] = None

    def dataframe(self, kind: str) -> pd.DataFrame | None:
        """Converts the stored results to a Pandas DataFrame.

        This method converts the tracked results into a Pandas DataFrame, making
        it easier to analyze and visualize the data.

        The `kind` argument supports the following options:

        - `"results"`:       For function results.
        - `"gradients"`:     For gradient results.
        - `"simulations"`:   For simulation results.
        - `"perturbations"`: For perturbation results.
        - `"constraints"`:   For constraint information.

        Note:
            The column names of the dataframe may be strings or tuples of
            strings. In the tuple form, the name is usually composed of a string
            indicating the type of column and one or more objective, constraint
            or control names. For instance, a column containing values of the
            control `point.x` may have the name: `(controls, point.x)`. The
            gradient of an objective `distance` with respect to a control
            `point.x` may have the column name `(objectives, distance, point.x.0)`.

        Args:
            kind: The type of table to create.

        Returns:
            A Pandas DataFrame containing the store results, or None.
        """
        if kind not in TABLE_COLUMNS:
            msg = f"Cannot make frame for `{kind}`"
            raise RuntimeError(msg)
        results = self.results
        if results is not None:
            columns = deepcopy(TABLE_COLUMNS[kind])
            if results[0].metadata is not None:
                for item in results[0].metadata:
                    columns[f"metadata.{item}"] = item
            return fix_columns(
                reorder_columns(
                    results_to_dataframe(
                        results,
                        fields=set(columns),
                        result_type=TABLE_TYPE_MAP[kind],
                    ),
                    columns,
                )
            )
        return None


class EverestTracker(EverestEventHandlerBase):
    """Provides access to the results generated by an Everest execution plan.

    This class provides methods to retrieve and analyze the results tracked by a
    tracker within an Everest execution plan. It allows you to access the
    results. You can also convert the tracked results into a Pandas DataFrame
    for easier analysis.

    The tracker can keep track of the best, the last, or all the results. The
    tracker can also be set to only keep track of the feasible results.
    """

    def __init__(
        self,
        plan: Plan,
        tracker: EventHandler,
    ) -> None:
        super().__init__(plan, tracker)

    @property
    def results(self) -> FunctionResults | None:
        """Retrieves the tracked results.

        Returns:
            The tracked results.
        """
        results: FunctionResults | None = self.handler["results"]
        return results

    @property
    def controls(self) -> NDArray[np.float64] | None:
        """Retrieves the tracked controls.

        Returns:
            The tracked controls.
        """
        results = self.results
        return None if results is None else results.evaluations.variables

    def reset(self) -> None:
        """Reset the tracker.

        Clears any results accumulated so far.
        """
        self.handler["results"] = None

    def dataframe(self, kind: str) -> pd.DataFrame | None:
        """Converts the tracked results to a Pandas DataFrame.

        This method converts the tracked results into a Pandas DataFrame, making
        it easier to analyze and visualize the data.

        The `kind` argument supports the following options:

        - `"results"`:       For function results.
        - `"gradients"`:     For gradient results.
        - `"simulations"`:   For simulation results.
        - `"perturbations"`: For perturbation results.
        - `"constraints"`:   For constraint information.

        Note:
            The column names of the dataframe may be strings or tuples of
            strings. In the tuple form, the name is usually composed of a string
            indicating the type of column and one or more objective, constraint
            or control names. For instance, a column containing values of the
            control `point.x` may have the name: `(controls, point.x)`. The
            gradient of an objective `distance` with respect to a control
            `point.x` may have the column name `(objectives, distance, point.x.0)`.

        Args:
            kind: The type of table to create.

        Returns:
            A Pandas DataFrame containing the tracked results, or None.
        """
        if kind not in TABLE_COLUMNS:
            msg = f"Cannot make frame for `{kind}`"
            raise RuntimeError(msg)
        results = self.results
        if results is not None:
            columns = deepcopy(TABLE_COLUMNS[kind])
            if results.metadata is not None:
                for item in results.metadata:
                    columns[f"metadata.{item}"] = item
            return fix_columns(
                reorder_columns(
                    results_to_dataframe(
                        [results],
                        fields=set(columns),
                        result_type=TABLE_TYPE_MAP[kind],
                    ),
                    columns,
                )
            )
        return None


class EverestTableHandler(EverestEventHandlerBase):
    """Represents a table event handler in an Everest execution plan."""

    def __init__(self, plan: Plan, table_handler: EventHandler) -> None:
        super().__init__(plan, table_handler)


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
    plan  without having to use the `everest` command. This method will run a
    full optimization, but it will not produce the usual monitoring output of
    Everest.

    Using this method instead of the `everest` command-line tool offers
    several advantages, including:

    - Direct access to standard output (stdout): Unlike the `everest`
        command, this does not redirect standard output.
    - Error traces: If errors occur during the optimization, you'll get a
        full Python stack trace, making debugging easier.
    - Exceptional exit conditions, such as maximum number batch reached, or
        a user abort are reported, if `report_exit_code` is set.

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
    run_model = EverestRunModel.create(EverestConfig.load_file(config_file))
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
