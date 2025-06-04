from __future__ import annotations

import importlib
import sys
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from everest.config import EverestConfig
from ropt.enums import ExitCode
from ropt.exceptions import PlanAborted
from ropt.plugins.plan.base import PlanStep

from ._everest_plan import EverestPlan
from ._utils import get_names

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np
    from numpy.typing import NDArray
    from ropt.evaluator import EvaluatorContext, EvaluatorResult
    from ropt.plan import Plan

    from ._everest_plan import EverestTracker


class EverestConfigStep(PlanStep):
    def run_step_from_plan(
        self,
        *,
        everest_config: Path,
        evaluator: Callable[[NDArray[np.float64], EvaluatorContext], EvaluatorResult],
    ) -> Callable[[Plan], ExitCode] | None:
        try:
            config = EverestConfig.load_file(everest_config)
        except:  # noqa: E722
            return None

        if (
            everest_config.suffix == ".yml"
            and (path := everest_config.with_suffix(".py")).exists()
        ):
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
                    config=config,
                    evaluator=evaluator,
                )

            msg = f"Function `run_plan` not found in module {module_name}"
            raise ImportError(msg)

        if Path(sys.argv[0]).name != "pytest":
            self.plan.add_event_handler(
                "everest/table",
                sources={"__basic_optimizer__"},
                names=get_names(config),
            )

        return None


def _run_plan(
    plan: Plan,
    func: Callable[
        [EverestPlan, dict[str, Any]], tuple[EverestTracker | None, ExitCode]
    ],
    config: EverestConfig,
    evaluator: Callable[[NDArray[np.float64], EvaluatorContext], EvaluatorResult],
) -> ExitCode:
    ever_plan = EverestPlan(plan, evaluator)
    try:
        func(ever_plan, config.model_dump(exclude_none=True))
    except PlanAborted:
        return ExitCode.USER_ABORT
    return ExitCode.UNKNOWN
