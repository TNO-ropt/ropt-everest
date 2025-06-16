# type: ignore
# ruff: noqa

from ropt_everest import load_config, run_everest


def run_plan(plan):
    config = load_config("config_example.yml")
    evaluator = plan.add_ensemble_evaluator()
    store = plan.add_store(evaluator)
    evaluator.run(config, controls=[[0, 0, 0], [0.25, 0.25, 0.25], [1, 1, 1]])
    print(store.dataframe("results"))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
