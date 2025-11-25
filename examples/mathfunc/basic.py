# type: ignore
# ruff: noqa

from ropt_everest import create_optimizer, load_config, run_everest


def run(evaluator):
    config = load_config("config_example.yml")
    optimizer = create_optimizer(evaluator)
    optimizer.add_table()
    optimizer.run(config)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
