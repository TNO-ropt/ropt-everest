from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Literal, Sequence

from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.run_models.everest_run_model import EverestRunModel
from everest.config import EverestConfig
from everest.optimizer.everest2ropt import everest2ropt
from ropt.results import Results, results_to_dataframe

from ._utils import (
    TABLE_COLUMNS,
    TABLE_TYPE_MAP,
    get_names,
    reorder_columns,
    strip_prefix_from_columns,
)

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd
    from numpy.typing import ArrayLike, NDArray
    from ropt.enums import OptimizerExitCode
    from ropt.plan import Plan
    from ropt.plugins.plan.base import PlanStep, ResultHandler
    from ropt.results import FunctionResults
    from ropt.transforms import OptModelTransforms


class EverestPlan:
    """Represents an execution plan for an Everest optimization workflow.

    The `EverestPlan` class provides a high-level interface for defining and
    managing optimization workflows in Everest. It allows you to add various
    steps to the plan, such as optimizers, evaluators, and workflow jobs, that
    are then executed to achieve the desired optimization goal.

    **Key Features:**

    -   **Step Management:** Add and manage different types of optimization
        steps, including optimizers, evaluators, and workflow jobs.
    -   **Tracking and Monitoring:** Incorporate trackers to monitor the
        progress of specific steps and collect relevant results.
    -   **Table Generation:** Generate tables to summarize the results of the
        optimization process.
    -   **Configuration Handling:** Manage Everest configurations, including the
        ability to override default settings.
    -   **Metadata Association:** Associate arbitrary metadata with steps and
        results, facilitating the tracking of additional information.
    -   **Direct Execution:** Execute the plan directly, providing more control
        over stdout and error traces.
    """

    def __init__(self, plan: Plan, transforms: OptModelTransforms) -> None:
        self._plan = plan
        self._config: EverestConfig = plan["everest_config"]
        self._config_dict: dict[str, Any] = self._config.model_dump(exclude_none=True)
        self._transforms = transforms
        self._tag_id = 0

    def config_copy(self) -> dict[str, Any]:
        """Retrieves a copy of the default Everest configuration.

        This method returns a copy of the Everest configuration used during
        startup. Modifications to the returned dictionary will not affect the
        original configuration.

        Returns:
            A dictionary representing the Everest configuration.
        """
        return deepcopy(self._config_dict)

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
        tag = f"tag{self._tag_id}"
        self._tag_id += 1
        step = self._plan.add_step("optimizer", tag=tag)
        return EverestOptimizerStep(
            step, self._plan, self._config, self._transforms, tag
        )

    def add_evaluator(self) -> EverestEvaluatorStep:
        """Adds an evaluator to the execution plan.

        This method integrates an evaluation step into your Everest workflow.
        Invoking this method returns an
        [`EverestEvaluatorStep`][ropt_everest.EverestEvaluatorStep] object,
        which you can execute using its
        [`run`][ropt_everest.EverestEvaluatorStep.run] method.

        Returns:
            An `EverestEvaluatorStep` object, representing the added evaluator.
        """
        tag = f"tag{self._tag_id}"
        self._tag_id += 1
        step = self._plan.add_step("evaluator", tag=tag)
        return EverestEvaluatorStep(
            step, self._plan, self._config, self._transforms, tag
        )

    def add_workflow_job(self) -> EverestWorkflowJobStep:
        """Adds a workflow job step to the execution plan.

        This method incorporates a workflow job into the execution plan.
        Workflow jobs are used to run external operations. Invoking this method
        returns an
        [`EverestWorkflowJobStep`][ropt_everest.EverestWorkflowJobStep] object,
        which you can execute using its
        [`run`][ropt_everest.EverestWorkflowJobStep.run] method.

        This step can be used to incorporate different external programs or
        scripts into the current optimization process.

        Returns:
            An `EverestWorkflowJobStep` object, representing the added workflow job step.
        """
        step = self._plan.add_step("workflow_job")
        return EverestWorkflowJobStep(step, self._plan)

    def add_tracker(
        self,
        track: EverestStep | Sequence[EverestStep],
        *,
        what: Literal["best", "last", "all"] = "best",
        constraint_tolerance: float | None = None,
    ) -> EverestTracker:
        """Adds a tracker to the execution plan.

        Trackers monitor the progress of specified optimization or evaluation
        steps and record relevant results. They provide a way to capture and
        analyze the outcomes of these steps during the execution of the plan.
        You can configure a tracker to save the best, last, or all results
        generated by the tracked steps.

        Invoking this method returns an
        [`EverestTracker`][ropt_everest.EverestTracker] object, which provides
        various methods to access the tracked results.

        A tracker is configured by three arguments:

        **track:** This argument specifies which steps in the execution plan the
        tracker should monitor. You can provide either a single step object
        (such as an optimizer or evaluator) or a sequence of steps. The tracker
        will record the results generated by these steps.

        **what:** This argument determines which results the tracker should
        record. You can choose from the following options:

        - `"best"`: Only the best result found so far is tracked.
        - `"last"`: Only the most recently generated result is tracked.
        - `"all"`: All results are tracked.

        The default value is `"best"`.

        **constraint_tolerance:** This optional argument specifies the tolerance
        for constraint satisfaction. It is used to determine whether a result is
        considered feasible, meaning it satisfies the defined constraints within
        the specified tolerance. Only feasible results will be recorded. If it
        is not set, constraints are not tested.

        Args:
            track:                The EverestStep(s) to track.
            what:                 Which results to track ("best", "last", or "all").
            constraint_tolerance: Tolerance for constraint satisfaction.

        Returns:
            An `EverestTracker` object, which can be used to access the tracked results.
        """
        if isinstance(track, EverestStep):
            track = [track]
        step = self._plan.add_handler(
            "tracker",
            what=what,
            constraint_tolerance=constraint_tolerance,
            tags={step.tag for step in track},
        )
        return EverestTracker(step, self._plan, get_names(self._config))

    def add_table(
        self,
        track: EverestStep | Sequence[EverestStep],
    ) -> EverestTableHandler:
        """Adds a handler that create a table to the execution plan.

        This handler will monitor the progress of specified optimization or
        evaluation steps and record relevant results. A set of tables will then
        be generated and saved in the output dir.

        Args:
            track: The EverestStep(s) to track.

        Returns:
            An `EverestTableHandler` object.
        """
        if isinstance(track, EverestStep):
            track = [track]
        step = self._plan.add_handler(
            "table",
            everest_config=self._config,
            tags={step.tag for step in track},
        )
        return EverestTableHandler(step, self._plan)

    @classmethod
    def everest(cls, config_file: str) -> None:
        """Runs an Everest optimization directly from a configuration file.

        This class method provides a convenient way to execute an Everest
        optimization plan  without having to use the `everest` command. This
        method will run a full optimization, but it will not produce the usual
        monitoring output of Everest.

        Using this method instead of the `everest` command-line tool offers
        several advantages, including:

        - Direct access to standard output (stdout): Unlike the `everest`
          command, this does not redirect standard output.
        - Error traces: If errors occur during the optimization, you'll get a
          full Python stack trace, making debugging easier.

        Args:
            config_file: The path to the Everest configuration file (YAML).
        """
        EverestRunModel.create(EverestConfig.load_file(config_file)).run_experiment(
            EvaluatorServerConfig()
        )

    def __getitem__(self, name: str) -> Any:  # noqa: ANN401
        return self._plan[name]

    def __setitem__(self, name: str, value: Any) -> None:  # noqa: ANN401
        self._plan[name] = value

    def __contains__(self, name: str) -> bool:
        return name in self._plan


class EverestStep:
    def __init__(self, plan: Plan, tag: str | None = None) -> None:
        self._plan = plan
        self._tag = "" if tag is None else tag

    @property
    def tag(self) -> str:
        return self._tag


class EverestOptimizerStep(EverestStep):
    """Represents an optimizer step in an Everest execution plan.

    This class encapsulates an optimization step within an Everest workflow. It
    provides a method to execute the optimizer .
    """

    def __init__(
        self,
        optimizer: PlanStep,
        plan: Plan,
        config: EverestConfig,
        transforms: OptModelTransforms,
        tag: str,
    ) -> None:
        super().__init__(plan, tag)
        self._optimizer = optimizer
        self._config = config
        self._transforms = transforms

    def run(
        self,
        config: dict[str, Any] | None = None,
        variables: ArrayLike | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OptimizerExitCode:
        """Runs the optimizer.

        This method executes the underlying optimizer with the given parameters.
        You can tailor the optimizer's behavior by providing an optional
        configuration dictionary.

        **Configuration**:

        - If no `config` is provided, the optimizer will use the default
          Everest configuration loaded during startup.
        - If a `config` dictionary is provided, it will override the default
          configuration. It should be a dictionary that can be validated as an
          `EverestConfig` object.

        **Variables**:

        If no variables are provided, the optimizer will use the initial values
        from the configuration.

        **Metadata**:

        - The `metadata` parameter allows you to associate arbitrary data with
          each result generated by the optimizer or evaluators.
        - This metadata is included in generated tables and data frames.
        - The keys in the `metadata` dictionary are used as column names in
          the output tables.

        Args:
            config:    An optional dictionary containing the Everest configuration
                       for the optimizer. If omitted, the default configuration is
                       used.
            variables: An array-like object containing the variables for the optimization.
            metadata:  An optional dictionary of metadata to associate with the
                       results of the optimizer's results.

        Returns:
            The exit code indicating the result of the optimization run.
        """
        return self._plan.run_step(  # type: ignore[no-any-return]
            self._optimizer,
            config=(
                everest2ropt(self._config, transforms=self._transforms)
                if config is None
                else everest2ropt(
                    EverestConfig.model_validate(config), transforms=self._transforms
                )
            ),
            transforms=self._transforms,
            metadata=metadata,
            variables=variables,
        )


class EverestEvaluatorStep(EverestStep):
    """Represents an evaluator step in an Everest execution plan.

    This class encapsulates an evaluation step within an Everest workflow. It
    provides a method to execute the evaluator .
    """

    def __init__(
        self,
        evaluator: PlanStep,
        plan: Plan,
        config: EverestConfig,
        transforms: OptModelTransforms,
        tag: str,
    ) -> None:
        super().__init__(plan, tag)
        self._evaluator = evaluator
        self._config = config
        self._transforms = transforms

    def run(
        self,
        config: dict[str, Any] | None = None,
        variables: ArrayLike | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OptimizerExitCode:
        """Runs the evaluator.

        This method executes the underlying evaluator with the given parameters.
        You can tailor the evaluators's behavior by providing an optional
        configuration dictionary.

        **Configuration**:

        - If no `config` is provided, the evaluator will use the default
          Everest configuration loaded during startup.
        - If a `config` dictionary is provided, it will override the default
          configuration. It should be a dictionary that can be validated as an
          `EverestConfig` object.

        **Variables**:

        The `variables` parameter can be a single vector, a sequence of multiple
        vectors, or a 2D matrix where the variable vectors are the rows. If no
        variables are provided, the evaluator will use its default
        the initial values from the configuration.

        **Metadata**:

        - The `metadata` parameter allows you to associate arbitrary data with
          each result generated by the optimizer or evaluators.
        - This metadata is included in generated tables and data frames.
        - The keys in the `metadata` dictionary are used as column names in
          the output tables.

        Args:
            config:    An optional dictionary containing the Everest configuration
                       for the optimizer. If omitted, the default configuration is
                       used.
            variables: An array-like object containing the variables for the optimization.
            metadata:  An optional dictionary of metadata to associate with the
                       results of the optimizer's results.

        Returns:
            The exit code indicating the result of the optimization run.
        """
        return self._plan.run_step(  # type: ignore[no-any-return]
            self._evaluator,
            config=(
                everest2ropt(self._config, transforms=self._transforms)
                if config is None
                else everest2ropt(
                    EverestConfig.model_validate(config), transforms=self._transforms
                )
            ),
            transforms=self._transforms,
            metadata=metadata,
            variables=variables,
        )


class EverestWorkflowJobStep(EverestStep):
    """Represents a workflow job step in an Everest execution plan.

    This class encapsulates a workflow job step within an Everest workflow. It
    provides a method to execute the workflow job.
    """

    def __init__(self, workflow_job: PlanStep, plan: Plan) -> None:
        super().__init__(plan)
        self._workflow_job = workflow_job

    def run(self, jobs: list[str]) -> dict[str, Any]:
        """Runs the workflow job.

        This method executes the workflow jobs as defined by the provided job
        names. The jobs must have been defined in the Everest configuration
        file in the `install_workflow_jobs` section.

        Args:
            jobs: A list of commands to run.

        Returns:
            A dictionary containing the workflow report.
        """
        return self._plan.run_step(self._workflow_job, jobs=jobs)  # type: ignore[no-any-return]


class EverestHandler:
    def __init__(self, plan: Plan) -> None:
        self._plan = plan


class EverestTracker(EverestHandler):
    """Provides access to the results tracked by an Everest execution plan.

    This class provides methods to retrieve and analyze the results tracked by a
    tracker within an Everest execution plan. It allows you to access the
    results. You can also convert the tracked results into a Pandas DataFrame
    for easier analysis.

    The tracker can keep track of the best, the last, or all the results. The
    tracker can also be set to only keep track of the feasible results.
    """

    def __init__(
        self,
        tracker: ResultHandler,
        plan: Plan,
        names: dict[str, Sequence[str | int] | None] | None,
    ) -> None:
        super().__init__(plan)
        self._tracker = tracker
        self._names = names

    @property
    def results(self) -> FunctionResults | tuple[FunctionResults, ...] | None:
        """Retrieves the tracked results.

        The tracked results can be a single `FunctionResults` object, a tuple of
        `FunctionResults` objects, or `None` if no results have been tracked.

        Returns:
            The tracked results.
        """
        results: FunctionResults | tuple[FunctionResults, ...] | None
        results = self._tracker["results"]
        return results

    @property
    def variables(self) -> NDArray[np.float64] | tuple[NDArray[np.float64], ...] | None:
        """Retrieves the tracked variables.

        The tracked variables can be a single NumPy array, a tuple of NumPy
        arrays, or None if no variables have been tracked.

        Returns:
            The tracked variables.
        """
        variables: NDArray[np.float64] | tuple[NDArray[np.float64], ...] | None
        variables = self._tracker["variables"]
        return variables

    @property
    def ropt_tracker(self) -> ResultHandler:
        return self._tracker

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
            if isinstance(results, Results):
                results = (results,)
            columns = deepcopy(TABLE_COLUMNS[kind])
            if results[0].metadata is not None:
                for item in results[0].metadata:
                    columns[f"metadata.{item}"] = item
            fields = set(columns)
            return strip_prefix_from_columns(
                reorder_columns(
                    results_to_dataframe(
                        results,
                        fields=fields,
                        result_type=TABLE_TYPE_MAP[kind],
                        names=self._names,
                    ),
                    columns,
                )
            )
        return None


class EverestTableHandler(EverestHandler):
    """Represents a table handler in an Everest execution plan."""

    def __init__(self, table_handler: ResultHandler, plan: Plan) -> None:
        super().__init__(plan)
        self._table_handler = table_handler
