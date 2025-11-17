"""This module implements the ropt-everest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from ropt.plugins.compute_step.base import ComputeStepPlugin
from ropt.plugins.evaluator.base import EvaluatorPlugin

from ._cached_evaluator import EverestDefaultCachedEvaluator
from ._everest_run_plan import EverestRunScriptComputeStep

if TYPE_CHECKING:
    from ropt.plugins.compute_step.base import ComputeStep
    from ropt.plugins.evaluator.base import Evaluator

_STEP_OBJECTS: Final[dict[str, type[ComputeStep]]] = {
    "run_script": EverestRunScriptComputeStep,
}

_EVALUATOR_OBJECTS: Final[dict[str, type[Evaluator]]] = {
    "cached_evaluator": EverestDefaultCachedEvaluator,
}


class EverestComputeStepPlugin(ComputeStepPlugin):
    """The everest plan step class."""

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
