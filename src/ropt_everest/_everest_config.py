"""This module implements the K2 optimizer step."""

from __future__ import annotations

import importlib
import sys
from functools import partial
from typing import TYPE_CHECKING, Any, Callable

from ropt.enums import OptimizerExitCode
from ropt.plugins.plan.base import PlanStep

from ._everest_plan import EverestPlan

if TYPE_CHECKING:
    from everest.config import EverestConfig
    from ropt.plan import Plan
    from ropt.plugins.plan.base import ResultHandler
    from ropt.transforms import OptModelTransforms

    from ._everest_plan import EverestTracker


class EverestConfigStep(PlanStep):
    def run(self, *, everest_config: EverestConfig) -> None:
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
                self.plan.clear_handlers()
                self.plan.add_function(
                    partial(_run_plan, func=module.run_plan, config=everest_config)
                )
            else:
                msg = f"Function `run_plan` not found in module {module_name}"
                raise ImportError(msg)


def _run_plan(
    plan: Plan,
    transforms: OptModelTransforms,
    func: Callable[
        [EverestPlan, dict[str, Any]], tuple[EverestTracker | None, OptimizerExitCode]
    ],
    config: EverestConfig,
) -> tuple[ResultHandler | None, OptimizerExitCode]:
    ever_plan = EverestPlan(plan, config, transforms)
    func(ever_plan, config.model_dump(exclude_none=True))
    return None, OptimizerExitCode.UNKNOWN
