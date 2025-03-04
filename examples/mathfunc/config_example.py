# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)
    exit_code = optimizer.run()
    return tracker, exit_code


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
