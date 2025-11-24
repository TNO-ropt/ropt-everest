# type: ignore
# ruff: noqa

from ropt_everest import create_optimizer, load_config, run_everest


def run(evaluator):
    config = load_config("config_example.yml")
    optimizer = create_optimizer(evaluator)
    tracker = optimizer.add_tracker(what="last")
    store = optimizer.add_store()
    optimizer.add_table()

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
