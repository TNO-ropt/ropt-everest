# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path

test_to_run = "basic"


def run_plan_basic(plan, constraint_tolerance=1e-10):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, constraint_tolerance=constraint_tolerance)
    plan.add_table(optimizer)
    exit_code = optimizer.run()
    return tracker, exit_code


def run_plan(plan):
    match test_to_run:
        case "basic":
            # Reproduces the default Everest optimization:
            return run_plan_basic(plan)


if __name__ == "__main__":
    # Run this script directly:
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
