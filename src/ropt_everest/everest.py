"""This module implements the ropt-everest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ropt.plugins.compute_step.base import ComputeStepPlugin
from ropt.plugins.evaluator.base import EvaluatorPlugin
from ropt.plugins.event_handler.base import EventHandlerPlugin

from ._cached_evaluator import EverestDefaultCachedEvaluator
from ._evaluator import EverestEvaluatorStep
from ._optimizer import EverestOptimizerStep
from ._run_script import EverestRunScriptComputeStep
from ._store import EverestStoreHandler
from ._tracker import EverestTrackerHandler

if TYPE_CHECKING:
    from ropt.plugins.compute_step.base import ComputeStep
    from ropt.plugins.evaluator.base import Evaluator
    from ropt.plugins.event_handler.base import EventHandler

_STEP_OBJECTS: Final[dict[str, type[ComputeStep]]] = {
    "run_script": EverestRunScriptComputeStep,
    "optimizer": EverestOptimizerStep,
    "evaluator": EverestEvaluatorStep,
}

_EVALUATOR_OBJECTS: Final[dict[str, type[Evaluator]]] = {
    "cached_evaluator": EverestDefaultCachedEvaluator,
}
_EVENT_HANDLER_OBJECTS: Final[dict[str, type[EventHandler]]] = {
    "store": EverestStoreHandler,
    "tracker": EverestTrackerHandler,
}


class EverestComputeStepPlugin(ComputeStepPlugin):
    """The everest compute step plugin class."""

    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> ComputeStep:
        """Create a step.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        step_obj = _STEP_OBJECTS.get(name)
        if step_obj is not None:
            return step_obj(**kwargs)

        msg = f"Unknown step type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        # noqa
        """
        return method.lower() in _STEP_OBJECTS


class EverestEvaluatorPlugin(EvaluatorPlugin):
    """The everest evaluator plugin."""

    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> Evaluator:
        """Create a step.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        evaluator_obj = _EVALUATOR_OBJECTS.get(name)
        if evaluator_obj is not None:
            return evaluator_obj(**kwargs)

        msg = f"Unknown evaluator type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        # noqa
        """
        return method.lower() in _EVALUATOR_OBJECTS


class EverestEventHandlerPlugin(EventHandlerPlugin):
    """The everest evaluator plugin."""

    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> EventHandler:
        """Create a step.

        # noqa
        """
        _, _, name = name.lower().rpartition("/")
        event_handler_obj = _EVENT_HANDLER_OBJECTS.get(name)
        if event_handler_obj is not None:
            return event_handler_obj(**kwargs)

        msg = f"Unknown event handler type: {name}"
        raise TypeError(msg)

    @classmethod
    def is_supported(cls, method: str) -> bool:
        """Check if a method is supported.

        # noqa
        """
        return method.lower() in _EVENT_HANDLER_OBJECTS
