from __future__ import annotations

import importlib
import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ropt.enums import ExitCode
from ropt.exceptions import PlanAborted
from ropt.plugins.plan.base import PlanStep

from ._everest_plan import EverestPlan

if TYPE_CHECKING:
    from ropt.evaluator import EvaluatorCallback
    from ropt.plan import Plan


class EverestRunPlanStep(PlanStep):
    def run(
        self, *, evaluator: EvaluatorCallback, script: Path | str
    ) -> Callable[[Plan], ExitCode] | None:
        path = Path(script)
        if path.exists():
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
                return partial(
                    _run_plan,
                    func=module.run_plan,
                    evaluator=evaluator,
                )

            msg = f"Function `run_plan` not found in module {module_name}"
            raise ImportError(msg)

        return None


def _run_plan(
    plan: Plan, func: Callable[[EverestPlan], None], evaluator: EvaluatorCallback
) -> ExitCode:
    ever_plan = EverestPlan(plan, evaluator)
    try:
        func(ever_plan)
    except PlanAborted:
        return ExitCode.USER_ABORT
    return ExitCode.UNKNOWN
