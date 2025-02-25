"""This module implements the K2 optimizer step."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ropt.plugins.plan.base import PlanStep

if TYPE_CHECKING:
    from everest.config import EverestConfig


class EverestConfigStep(PlanStep):
    def run(self, *, everest_config: EverestConfig) -> None:  # type: ignore[override]
        self.plan["everest_config"] = everest_config
