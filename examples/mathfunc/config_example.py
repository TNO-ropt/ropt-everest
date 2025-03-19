# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


example = "basic"


def run_plan_basic(plan):
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run()


def run_plan_two_optimizers(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    config["optimization"]["max_function_evaluations"] = 2

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")


def run_plan_loop(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    store = plan.add_store(optimizer)

    config["optimization"]["max_function_evaluations"] = 2
    for idx in range(3):
        optimizer.run(
            config=config,
            controls=tracker.controls,
            metadata={"iteration": idx},
            output_dir=f"output{idx}",
        )
    print(store.dataframe("gradients"))


def run_plan_evaluation(plan):
    evaluator = plan.add_evaluator()
    store = plan.add_store(evaluator)
    evaluator.run(controls=[[0, 0, 0], [1, 1, 1]])
    print(store.dataframe("results"))


def run_plan(plan, config):
    match example:
        case "basic":
            return run_plan_basic(plan)
        case "two_optimizers":
            return run_plan_two_optimizers(plan, config)
        case "loop":
            return run_plan_loop(plan, config)
        case "evaluation":
            return run_plan_evaluation(plan)
        case _:
            raise ValueError(f"Unknown example: {example}")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
