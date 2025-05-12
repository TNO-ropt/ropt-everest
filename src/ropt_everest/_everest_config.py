"""This module implements the K2 optimizer step."""

from __future__ import annotations

import importlib
import sys
from functools import partial
from typing import TYPE_CHECKING, Any

from ropt.enums import OptimizerExitCode
from ropt.exceptions import PlanAborted
from ropt.plugins.plan.base import PlanStep

from ._everest_plan import EverestPlan

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np
    from everest.config import EverestConfig
    from numpy.typing import NDArray
    from ropt.evaluator import EvaluatorContext, EvaluatorResult
    from ropt.plan import Plan
    from ropt.plugins.plan.base import EventHandler

    from ._everest_plan import EverestTracker


class EverestConfigStep(PlanStep):
    def run_step_from_plan(
        self,
        *,
        everest_config: EverestConfig,
        evaluator: Callable[[NDArray[np.float64], EvaluatorContext], EvaluatorResult],
    ) -> None:
        path = everest_config.config_path
        if path.suffix == ".yml" and (path := path.with_suffix(".py")).exists():
            module_name = path.stem
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None:
                msg = f"Could not load {module_name}.py"
                raise ImportError(msg)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)

            if hasattr(module, "run_plan"):
                self.plan.set_run_function(
                    partial(
                        _run_plan,
                        func=module.run_plan,
                        config=everest_config,
                        evaluator=evaluator,
                    )
                )
            else:
                msg = f"Function `run_plan` not found in module {module_name}"
                raise ImportError(msg)
        else:
            self.plan.add_event_handler("everest/table", everest_config=everest_config)


def _run_plan(
    plan: Plan,
    func: Callable[
        [EverestPlan, dict[str, Any]], tuple[EverestTracker | None, OptimizerExitCode]
    ],
    config: EverestConfig,
    evaluator: Callable[[NDArray[np.float64], EvaluatorContext], EvaluatorResult],
) -> tuple[EventHandler | None, OptimizerExitCode]:
    ever_plan = EverestPlan(plan, config, evaluator)
    try:
        func(ever_plan, config.model_dump(exclude_none=True))
    except PlanAborted:
        return None, OptimizerExitCode.USER_ABORT
    return None, OptimizerExitCode.UNKNOWN
