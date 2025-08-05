"""This module implements the ropt-everest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ropt.plugins.plan.base import EvaluatorPlugin, PlanStepPlugin

from ._cached_evaluator import EverestDefaultCachedEvaluator
from ._everest_run_plan import EverestRunPlanStep

if TYPE_CHECKING:
    from ropt.plan import Plan
    from ropt.plugins.plan.base import Evaluator, PlanComponent, PlanStep

_STEP_OBJECTS: Final[dict[str, type[PlanStep]]] = {
    "run_plan": EverestRunPlanStep,
}

_EVALUATOR_OBJECTS: Final[dict[str, type[Evaluator]]] = {
    "cached_evaluator": EverestDefaultCachedEvaluator,
}


class EverestPlanStepPlugin(PlanStepPlugin):
    """The everest plan step class."""

    @classmethod
    def create(
        cls,
        name: str,
        plan: Plan,
        tags: set[str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> PlanStep:
        """Create a step.

        See the [ropt.plugins.plan.base.PlanPlugin][] abstract base class.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        step_obj = _STEP_OBJECTS.get(name)
        if step_obj is not None:
            return step_obj(plan, tags, **kwargs)

        msg = f"Unknown step type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        See the [ropt.plugins.base.Plugin][] abstract base class.

        # noqa
        """
        return method.lower() in _STEP_OBJECTS


class EverestEvaluatorPlugin(EvaluatorPlugin):
    """The everest evaluator plugin."""

    @classmethod
    def create(
        cls,
        name: str,
        plan: Plan,
        tags: set[str] | None = None,
        clients: set[PlanComponent | str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Evaluator:
        """Create a step.

        See the [ropt.plugins.plan.base.PlanPlugin][] abstract base class.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        evaluator_obj = _EVALUATOR_OBJECTS.get(name)
        if evaluator_obj is not None:
            return evaluator_obj(plan, tags, clients, **kwargs)

        msg = f"Unknown evaluator type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        See the [ropt.plugins.base.Plugin][] abstract base class.

        # noqa
        """
        return method.lower() in _EVALUATOR_OBJECTS
