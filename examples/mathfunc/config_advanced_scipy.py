# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan):
    optimizer = plan.add_evaluator()
    tracker = plan.add_tracker(optimizer, constraint_tolerance=1e-6)
    plan["bar"] = 1
    plan.add_table(optimizer, metadata={"Foo": "$bar"})
    exit_code = optimizer.run(variables=[[0, 0, 0], [1, 2, 3]])
    return tracker, exit_code


if __name__ == "__main__":
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
