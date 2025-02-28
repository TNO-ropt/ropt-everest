# type: ignore
# ruff: noqa

from pathlib import Path
from ropt_everest import EverestPlan


def run_plan(plan):
    optimizer = plan.add_optimizer(plan.config)
    tracker = plan.add_tracker(optimizer, constraint_tolerance=1e-6)
    exit_code = optimizer.run()
    return tracker, exit_code


if __name__ == "__main__":
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
