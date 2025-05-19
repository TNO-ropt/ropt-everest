from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from ropt.plugins.plan.cached_evaluator import DefaultCachedEvaluator

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from ropt.evaluator import EvaluatorContext, EvaluatorResult
    from ropt.plan import Plan
    from ropt.plugins.plan.base import EventHandler, PlanComponent


class EverestDefaultCachedEvaluator(DefaultCachedEvaluator):
    def __init__(
        self,
        plan: Plan,
        tags: set[str] | None = None,
        clients: set[PlanComponent | str] | None = None,
        *,
        sources: list[EventHandler] | None = None,
    ) -> None:
        super().__init__(plan, tags, clients, sources=sources)

    def eval(
        self, variables: NDArray[np.float64], context: EvaluatorContext
    ) -> EvaluatorResult:
        results, cached = self.eval_cached(variables, context)
        sim_ids = results.evaluation_info.get("sim_ids")
        if sim_ids is not None:
            batch_ids = np.full_like(sim_ids, results.batch_id)
            for idx, (cached_realization_index, item) in cached.items():
                evaluation_info = item.evaluations.evaluation_info
                sim_ids[idx] = evaluation_info["sim_ids"][cached_realization_index]
                batch_ids[idx] = item.batch_id
            results.evaluation_info["sim_ids"] = sim_ids
            results.evaluation_info["batch_ids"] = batch_ids
        return results
