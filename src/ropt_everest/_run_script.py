from __future__ import annotations

import sys
from functools import partial
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING

from ropt.plugins.compute_step.base import ComputeStep
from ropt.plugins.evaluator.base import Evaluator
from ropt.workflow import create_evaluator

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np
    from numpy.typing import NDArray
    from ropt.enums import ExitCode
    from ropt.evaluator import EvaluatorCallback, EvaluatorContext, EvaluatorResult


class EverestRunScriptComputeStep(ComputeStep):
    def run(  # noqa: PLR6301
        self, *, evaluator: EvaluatorCallback, script: Path | str
    ) -> Callable[..., ExitCode | None] | None:
        path = Path(script)
        if path.exists():
            module_name = path.stem
            spec = spec_from_file_location(module_name, path)
            if spec is None:
                msg = f"Could not load {module_name}.py"
                raise ImportError(msg)
            module = module_from_spec(spec)
            sys.modules[module_name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                return partial(_run_script, func=module.run, evaluator=evaluator)

            msg = f"Function `run` not found in module {module_name}"
            raise ImportError(msg)

        return None


class _Evaluator(Evaluator):
    def __init__(self, *, callback: EvaluatorCallback) -> None:
        super().__init__()
        self._evaluator_callback = callback

    def eval(
        self, variables: NDArray[np.float64], context: EvaluatorContext
    ) -> EvaluatorResult:
        return self._evaluator_callback(variables, context)


def _run_script(
    func: Callable[[Evaluator], ExitCode | None], evaluator: EvaluatorCallback
) -> ExitCode | None:
    function_evaluator = _Evaluator(callback=evaluator)
    return func(
        create_evaluator("everest/cached_evaluator", evaluator=function_evaluator)
    )
