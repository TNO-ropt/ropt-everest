# type: ignore
# ruff: noqa

from ropt_everest import create_optimizer, load_config, run_everest


def run(evaluator):
    config = load_config("config_example.yml")
    optimizer = create_optimizer(evaluator)
    tracker = optimizer.add_tracker()
    optimizer.run(config)
    print(tracker.controls)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
