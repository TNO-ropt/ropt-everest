# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run(config)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
