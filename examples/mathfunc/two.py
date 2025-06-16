# type: ignore
# ruff: noqa

from ropt_everest import load_config, run_everest


def run_plan(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
