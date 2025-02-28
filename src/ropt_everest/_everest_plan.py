from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.run_models.everest_run_model import EverestRunModel
from everest.config import EverestConfig
from everest.optimizer.everest2ropt import everest2ropt

if TYPE_CHECKING:
    from numpy.typing import ArrayLike
    from ropt.enums import OptimizerExitCode
    from ropt.plan import Plan
    from ropt.plugins.plan.base import PlanStep, ResultHandler
    from ropt.transforms import OptModelTransforms


class EverestPlan:
    def __init__(self, plan: Plan, transforms: OptModelTransforms) -> None:
        self._plan = plan
        self._config: EverestConfig = plan["everest_config"]
        self._config_dict: dict[str, Any] = self._config.model_dump(exclude_none=True)
        self._transforms = transforms
        self._tag_id = 0

    @property
    def config(self) -> dict[str, Any]:
        return self._config_dict

    def add_optimizer(
        self, config: dict[str, Any] | None = None
    ) -> EverestOptimizerStep:
        tag = f"tag{self._tag_id}"
        self._tag_id += 1
        step = self._plan.add_step(
            "optimizer",
            config=(
                everest2ropt(self._config)
                if config is None
                else everest2ropt(EverestConfig.model_validate(config))
            ),
            transforms=self._transforms,
            tags=tag,
        )
        return EverestOptimizerStep(step, self._plan, tag)

    def add_evaluator(
        self, config: dict[str, Any] | None = None
    ) -> EverestEvaluatorStep:
        tag = f"tag{self._tag_id}"
        self._tag_id += 1
        step = self._plan.add_step(
            "evaluator",
            config=(
                everest2ropt(self._config)
                if config is None
                else everest2ropt(EverestConfig.model_validate(config))
            ),
            transforms=self._transforms,
            tags=tag,
        )
        return EverestEvaluatorStep(step, self._plan, tag)

    def add_workflow_job(self) -> EverestWorkflowJobStep:
        step = self._plan.add_step("workflow_job")
        return EverestWorkflowJobStep(step, self._plan)

    def add_tracker(
        self,
        track: EverestStep | Sequence[EverestStep],
        *,
        constraint_tolerance: float | None = None,
    ) -> EverestTracker:
        if isinstance(track, EverestStep):
            track = [track]
        step = self._plan.add_handler(
            "tracker",
            constraint_tolerance=constraint_tolerance,
            tags={step.tag for step in track},
        )
        return EverestTracker(step, self._plan)

    def add_table(
        self,
        track: EverestStep | Sequence[EverestStep],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> EverestTableHandler:
        if isinstance(track, EverestStep):
            track = [track]
        step = self._plan.add_handler(
            "table",
            everest_config=self._config,
            tags={step.tag for step in track},
            metadata=metadata,
        )
        return EverestTableHandler(step, self._plan)

    @classmethod
    def everest(cls, config_file: str) -> None:
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
    def __init__(self, optimizer: PlanStep, plan: Plan, tag: str) -> None:
        super().__init__(plan, tag)
        self._optimizer = optimizer

    def run(self, variables: ArrayLike | None = None) -> OptimizerExitCode:
        return self._plan.run_step(self._optimizer, variables=variables)  # type: ignore[no-any-return]


class EverestEvaluatorStep(EverestStep):
    def __init__(self, evaluator: PlanStep, plan: Plan, tag: str) -> None:
        super().__init__(plan, tag)
        self._evaluator = evaluator

    def run(self, variables: ArrayLike | None = None) -> OptimizerExitCode:
        return self._plan.run_step(self._evaluator, variables=variables)  # type: ignore[no-any-return]


class EverestWorkflowJobStep(EverestStep):
    def __init__(self, workflow_job: PlanStep, plan: Plan) -> None:
        super().__init__(plan)
        self._workflow_job = workflow_job

    def run(self, jobs: list[str]) -> dict[str, Any]:
        return self._plan.run_step(self._workflow_job, jobs=jobs)  # type: ignore[no-any-return]


class EverestHandler:
    def __init__(self, plan: Plan) -> None:
        self._plan = plan


class EverestTracker(EverestHandler):
    def __init__(self, tracker: ResultHandler, plan: Plan) -> None:
        super().__init__(plan)
        self._tracker = tracker

    @property
    def ropt_tracker(self) -> ResultHandler:
        return self._tracker


class EverestTableHandler(EverestHandler):
    def __init__(self, table_handler: ResultHandler, plan: Plan) -> None:
        super().__init__(plan)
        self._table_handler = table_handler
