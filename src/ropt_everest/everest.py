"""This module implements the ropt-everest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ropt.plugins.plan.base import EventHandlerPlugin, PlanStepPlugin

from ._everest_config import EverestConfigStep
from ._results_table import EverestDefaultTableHandler

if TYPE_CHECKING:
    from ropt.plan import Plan
    from ropt.plugins.plan.base import EventHandler, PlanStep

_STEP_OBJECTS: Final[dict[str, type[PlanStep]]] = {
    "everest_config": EverestConfigStep,
}

_EVENT_HANDLER_OBJECTS: Final[dict[str, type[EventHandler]]] = {
    "table": EverestDefaultTableHandler,
}


class EverestEventHandlerPlugin(EventHandlerPlugin):
    """The everest event handler class."""

    @classmethod
    def create(
        cls,
        name: str,
        plan: Plan,
        sources: set[PlanStep] | None = None,
        **kwargs: dict[str, Any],
    ) -> EventHandler:
        """Create a event event handler.

        See the [ropt.plugins.plan.base.PlanPlugin][] abstract base class.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        obj = _EVENT_HANDLER_OBJECTS.get(name)
        if obj is not None:
            return obj(plan, sources=sources, **kwargs)

        msg = f"Unknown event handler object type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        See the [ropt.plugins.base.Plugin][] abstract base class.

        # noqa
        """
        return method.lower() in _EVENT_HANDLER_OBJECTS


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
