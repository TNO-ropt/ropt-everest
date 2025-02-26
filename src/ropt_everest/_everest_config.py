"""This module implements the K2 optimizer step."""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

from ropt.plugins.plan.base import PlanStep

if TYPE_CHECKING:
    from everest.config import EverestConfig


class EverestConfigStep(PlanStep):
    def run(self, *, everest_config: EverestConfig) -> None:  # type: ignore[override]
        self.plan["everest_config"] = everest_config

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
                self.plan.add_function(module.run_plan)
            else:
                msg = f"Function `run_plan` not found in module {module_name}"
                raise ImportError(msg)
