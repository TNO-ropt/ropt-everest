# type: ignore
# ruff: noqa


from ropt_everest import EverestPlan
from pathlib import Path

test_to_run = "basic"


def run_plan_basic(plan):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)
    exit_code = optimizer.run()
    print(tracker.variables)
    return tracker, exit_code


def run_plan(plan):
    match test_to_run:
        case "basic":
            # Reproduces the default Everest optimization:
            return run_plan_basic(plan)


if __name__ == "__main__":
    # Run this script directly:
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
