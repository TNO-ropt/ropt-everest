# type: ignore
# ruff: noqa

from ropt_everest import load_config, run_everest


def run_plan(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    store = plan.add_store(optimizer)
    # plan.add_cache(steps=optimizer, sources=tracker)

    for idx in range(3):
        optimizer.run(
            config,
            controls=tracker.controls,
            metadata={"iteration": idx},
            output_dir=f"output{idx}",
        )
    print(store.dataframe("simulations"))


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
