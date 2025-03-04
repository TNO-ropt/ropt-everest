The ropt-everest plugin allows you to customize and extend the default
optimization workflow in Everest. Normally, Everest performs a single
optimization run based on the parameters in a YAML configuration file. However,
with ropt-everest, you can override this behavior.

To customize the workflow, create a Python file with the same base name as your
Everest configuration file (YAML) and place it in the same directory. If this
Python file contains a function named `run_plan`, this function will be executed
instead of the standard Everest optimization process. This allows you to define
complex, multi-step optimization strategies, incorporate custom logic, and gain
fine-grained control over the optimization process.

The `run_plan` function must have the following signature:

```py
def run_plan_basic(
    plan: EverestPlan,
) -> tuple[EverestTracker | None, OptimizerExitCode]:
    ...
```

- The function must accept an [`EverestPlan`][ropt_everest.EverestPlan] object,
   which is used to define and execute the optimization workflow. This object is
   created by Everest and provided to `run_plan` via the `plan` parameter.
- The function must return a tuple containing:
    - An [`EverestTracker`][ropt_everest.EverestTracker] object (or `None`).
    - An exit code indicating the outcome of the optimization. This exit code is
      typically returned by an optimizer or evaluation step.

For example, this `run_plan` function reproduces the default Everest optimization:

```py
def run_plan(plan):
    optimizer = plan.add_optimizer()       # Add an optimizer step
    tracker = plan.add_tracker(optimizer)  # Add a tracker
    plan.add_table(optimizer)              # Add a table handler
    exit_code = optimizer.run()            # Run the optimizer
    return tracker, exit_code              # Return the results
```

This function executes a basic optimization workflow by performing these steps:

1.  **Plan Creation**: Everest creates an `EverestPlan` object and passes it to
    `run_plan` via the `plan` parameter.
2.  **Optimizer Addition**: An optimizer step is added to the plan using the
    [`add_optimizer`][ropt_everest.EverestPlan.add_optimizer] method.
3.  **Tracker Addition**: A tracker is attached to the optimizer step using the
    [`add_tracker`][ropt_everest.EverestPlan.add_tracker] method to monitor its
    progress.
4.  **Table Handler Addition**: A table handler is added to the plan using the
    [`add_table`][ropt_everest.EverestPlan.add_table] method. This will save the
    optimization results in a set of tables.
5.  **Optimizer Execution**: The optimization process is started by calling the
    [`run`][ropt_everest.EverestOptimizerStep.run] method of the optimizer step.
6.  **Result Return**: The `run_plan` function returns the tracker object (which
    contains the tracked results) and the exit code returned by the optimizer's
    `run` method.
