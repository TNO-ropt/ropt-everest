# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan, config):
    evaluator = plan.add_ensemble_evaluator()
    store = plan.add_store(evaluator)
    evaluator.run(config, controls=[[0, 0, 0], [0.25, 0.25, 0.25], [1, 1, 1]])
    print(store.dataframe("results"))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
