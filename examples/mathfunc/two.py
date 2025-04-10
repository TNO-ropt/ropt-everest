# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    config["optimization"]["max_function_evaluations"] = 2

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
