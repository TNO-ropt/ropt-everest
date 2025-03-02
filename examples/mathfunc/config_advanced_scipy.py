# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan):
    plan["bar"] = 1
    optimizer = plan.add_optimizer(metadata={"foo": "$bar"})
    tracker = plan.add_tracker(optimizer, constraint_tolerance=1e-6)
    plan.add_table(optimizer, metadata={"foo": "Foo"})
    exit_code = optimizer.run()
    return tracker, exit_code


if __name__ == "__main__":
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
