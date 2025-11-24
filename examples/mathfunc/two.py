# type: ignore
# ruff: noqa

from ropt_everest import create_optimizer, load_config, run_everest


def run(evaluator):
    config = load_config("config_example.yml")
    optimizer = create_optimizer(evaluator)
    tracker = optimizer.add_tracker()
    optimizer.add_table()

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
