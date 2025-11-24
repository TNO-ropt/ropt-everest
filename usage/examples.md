It is recommended to run these examples directly using this script template, so
that output is printed to the console:

```py
from ropt_everest import load_config, run_everest

def run(plan):
    ...

if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
```

## Basic plan
A basic plan that corresponds to the default Everest optimization:

```py
def run(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run(config)
```

## Running two optimizers
Running two optimizers, sending optimizer output to different directories:

```py
def run(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")
```

## Running optimizers in a loop
Run an optimizer in a loop, each time starting from the last result of the
previous. Add the tracker that stores the last value to the plan as a cache.
Store all results in memory and export the simulations of all to a Pandas data
frame. In addition, add the index of the loop to the metadata, which an
additional `iteration` column to the data frame:

```py
def run(plan):
    config = load_config("config_example.yml")
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    store = plan.add_store(optimizer)
    plan.add_cache(steps=optimizer, sources=tracker)

    for idx in range(3):
        optimizer.run(
            config,
            controls=tracker.controls,
            metadata={"iteration": idx},
            output_dir=f"output{idx}",
        )
    print(store.dataframe("simulations"))
```

## Running an evaluation
Run an evaluation of the function for two control vectors and export the results
to a Pandas data frame:

```py
def run(plan):
    config = load_config("config_example.yml")
    evaluator = plan.add_ensemble_evaluator()
    store = plan.add_store(evaluator)
    evaluator.run(config, controls=[[0, 0, 0], [0.25, 0.25, 0.25], [1, 1, 1]])
    print(store.dataframe("results"))
```
