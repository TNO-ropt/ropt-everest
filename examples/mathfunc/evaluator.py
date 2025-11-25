# type: ignore
# ruff: noqa

from ropt_everest import create_ensemble_evaluator, load_config, run_everest


def run(evaluator):
    config = load_config("config_example.yml")
    evaluator = create_ensemble_evaluator(evaluator)
    store = evaluator.add_store()
    evaluator.run(config, controls=[[0, 0, 0], [0.25, 0.25, 0.25], [1, 1, 1]])
    print(store.dataframe("results"))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
