# type: ignore
# ruff: noqa

from ropt_everest import load_config, run_everest


def run_plan(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run(config)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
