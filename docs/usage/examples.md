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
```py
def run_plan(plan):
    optimizer = plan.add_optimizer()       # Add an optimizer step
    tracker = plan.add_tracker(optimizer)  # Add a tracker
    plan.add_table(optimizer)              # Add a table handler
    exit_code = optimizer.run()            # Run the optimizer
    return tracker, exit_code              # Return the results
```

## Running two optimizers
```py
def run_plan(plan):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)

    print("Running first optimizer...")
    optimizer.run()

    config = plan.config_copy()
    config["optimization"]["max_function_evaluations"] = 2

    print("Running second optimizer...")
    exit_code = optimizer.run(
        config=config, variables=tracker.variables
    )
    return tracker, exit_code
```

## Running optimizers in a loop
```py
def run_plan(plan):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer, what="last")
    plan.add_table(optimizer)

    config = plan.config_copy()
    config["optimization"]["max_function_evaluations"] = 2
    for idx in range(3):
        exit_code = optimizer.run(
            config=config,
            variables=tracker.variables,
            metadata={"iteration": idx},
        )
        print(tracker.dataframe("results"))
    return tracker, exit_code
```

## Running an evaluation
```py
def run_plan(plan):
    evaluator = plan.add_evaluator()
    tracker = plan.add_tracker(evaluator, what="all")
    exit_code = evaluator.run(variables=[[0, 0, 0], [1, 1, 1]])
    print(tracker.dataframe("results"))
    return tracker, exit_code
```