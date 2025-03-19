It is recommended to run these examples directly using this script template, so
that output is printed to the console:

```py
from ropt_everest import EverestPlan
from pathlib import Path

def run_plan(plan):
    ...

if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
```

## Basic plan
A basic plan that corresponds to the default Everest optimization:

```py
def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run()
```

## Running two optimizers
Running two optimizers with different configurations, sending optimizer output
to different directories:

```py
def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    config["optimization"]["max_function_evaluations"] = 2

    print("Running first optimizer...")
    optimizer.run(config=config, output_dir="output1")

    print("Running second optimizer...")
    optimizer.run(config=config, controls=tracker.controls, output_dir="output2")
```

## Running optimizers in a loop
Run an optimizer in a loop, each time starting from the last result of the
previous. Store all results in memory and export the gradients of all results to
a Pandas data frame. In addition, add the index of the loop to the metadata,
which an additional `iteration` column to the data frame:

```py
def run_plan(plan, config):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    store = plan.add_store(optimizer)

    config["optimization"]["max_function_evaluations"] = 2
    for idx in range(3):
        optimizer.run(
            config=config,
            controls=tracker.controls,
            metadata={"iteration": idx},
            output_dir=f"output{idx}",
        )
    print(store.dataframe("gradients"))
```

## Running an evaluation
Run an evaluation of the function for two control vectors and export the results
to a Pandas data frame:

```py
def run_plan(plan, config):
    evaluator = plan.add_evaluator()
    store = plan.add_store(evaluator)
    evaluator.run(controls=[[0, 0, 0], [1, 1, 1]])
    print(store.dataframe("results"))
```