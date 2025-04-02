"""This module implements the ropt-everest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Type

from ropt.plugins.plan.base import PlanHandlerPlugin, PlanStepPlugin

from ._everest_config import EverestConfigStep
from ._results_table import EverestDefaultTableHandler
from ._workflow_job import EverestWorkflowJob

if TYPE_CHECKING:
    from ropt.plan import Plan
    from ropt.plugins.plan.base import PlanStep, ResultHandler

_STEP_OBJECTS: Final[dict[str, Type[PlanStep]]] = {
    "everest_config": EverestConfigStep,
    "workflow_job": EverestWorkflowJob,
}

_RESULT_HANDLER_OBJECTS: Final[dict[str, Type[ResultHandler]]] = {
    "table": EverestDefaultTableHandler,
}


class EverestPlanHandlerPlugin(PlanHandlerPlugin):
    """The everest plan handler class."""

    @classmethod
    def create(cls, name: str, plan: Plan, **kwargs: dict[str, Any]) -> ResultHandler:
        """Create a result  handler.

        See the [ropt.plugins.plan.base.PlanPlugin][] abstract base class.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        obj = _RESULT_HANDLER_OBJECTS.get(name)
        if obj is not None:
            return obj(plan, **kwargs)

        msg = f"Unknown results handler object type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        See the [ropt.plugins.base.Plugin][] abstract base class.

        # noqa
        """
        return method.lower() in _RESULT_HANDLER_OBJECTS


class EverestPlanStepPlugin(PlanStepPlugin):
    """The everest plan step class."""

    @classmethod
    def create(cls, name: str, plan: Plan, **kwargs: Any) -> PlanStep:  # noqa: ANN401
        """Create a step.

        See the [ropt.plugins.plan.base.PlanPlugin][] abstract base class.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        step_obj = _STEP_OBJECTS.get(name)
        if step_obj is not None:
            return step_obj(plan, **kwargs)

        msg = f"Unknown step type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        See the [ropt.plugins.base.Plugin][] abstract base class.

        # noqa
        """
        return method.lower() in _STEP_OBJECTS
