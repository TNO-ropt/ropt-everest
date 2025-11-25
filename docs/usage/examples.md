It is recommended to run these examples directly using this script template, so
that output is printed to the console:

```py
def run(evaluator):
    ...

if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config_example.yml", script=__file__)
```

## Basic plan
A basic plan that corresponds to the default Everest optimization, while writing results to disk:

```py
from ropt_everest import create_optimizer, load_config, run_everest

def run(evaluator):
    config = load_config("config_example.yml")
    optimizer = create_optimizer(evaluator)
    optimizer.add_table()
    optimizer.run(config)
```

## Running two optimizers
Running two optimizers, sending optimizer output to different directories:

```py
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
```

## Running optimizers in a loop
Run an optimizer in a loop, each time starting from the last result of the
previous. Store all results in memory and export the simulations of all to a
Pandas data frame. In addition, add the index of the loop to the metadata, which
an additional `iteration` column to the data frame:

```py
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
```

## Running an evaluation
Run an evaluation of the function for two control vectors and export the results
to a Pandas data frame:

```py
from ropt_everest import create_ensemble_evaluator, load_config, run_everest

def run(evaluator):
    config = load_config("config_example.yml")
    evaluator = create_ensemble_evaluator(evaluator)
    store = evaluator.add_store()
    evaluator.run(config, controls=[[0, 0, 0], [0.25, 0.25, 0.25], [1, 1, 1]])
    print(store.dataframe("results"))
```
