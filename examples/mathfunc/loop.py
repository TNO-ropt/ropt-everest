# type: ignore
# ruff: noqa

from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    store = plan.add_store(optimizer)

    for idx in range(3):
        optimizer.run(
            config=config,
            controls=tracker.controls,
            metadata={"iteration": idx},
            output_dir=f"output{idx}",
        )
    print(store.dataframe("results"))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
