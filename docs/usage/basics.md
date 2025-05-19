## Running custom optimization workflows

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
def run_plan(plan: EverestPlan, config: dict[str, Any]) -> None:
    ...
```

The first argument is an [`EverestPlan`][ropt_everest.EverestPlan] object, which
is used to define and execute the optimization workflow. This object is created
by Everest and provided to `run_plan` via the `plan` parameter. The second
argument is a dictionary that contains the parsed configuration that was
provided to Everest. It can be modified and passed to optimization and
evaluation steps in the workflow to modify their behavior.

Developing and executing a custom workflow involves two key aspects:

1.  **Defining the Workflow:** This entails adding the individual steps and
    their associated event handlers to the `EverestPlan`. These steps can
    include optimizers, evaluators, and other custom operations. Result
    handlers, such as trackers and table outputs, capture the outcomes of each
    step.

2.  **Executing and Inspecting:** This process involves arranging the defined
    steps in the desired order of execution and leveraging the event handlers
    to analyze the output data. The `EverestPlan` automatically manages the
    execution of these steps, guaranteeing their correct operation and ensuring
    that results are consistently captured and made accessible. Because the
    `run_plan` function is implemented in standard Python, you can use the full
    power of Python programming (e.g., loops, conditional statements, and custom
    functions) to create sophisticated and adaptable optimization workflows.

A `run_plan` function constructs a workflow by creating _step_ objects and
_handler_ objects. You create these objects by calling methods on the `plan`
object, typically using the pattern `plan.add_*()`. For example,
`plan.add_optimizer()` creates an optimizer step and registers it with the plan.
When added to the plan, step objects generally don't require arguments. Instead,
you configure and execute them later by calling their `run` method (e.g., to
start an optimization).

The `run` method may accept additional arguments to customize the step's
behavior. As steps execute, they may generate results. The plan receives these
results and forwards them to any event handler objects that have expressed
interest. When creating event handler objects, you specify one or more step
objects they should monitor, indicating their interest in receiving results from
those steps. Handlers may also accept additional configuration arguments during
creation to refine how they process these results.

In summary, building an optimization workflow involves: 1) defining one or more
steps, 2) adding event handlers to process the results of those steps, and 3)
finally, executing the steps by calling their `run` methods, potentially
multiple times.

For example, this `run_plan` function reproduces the default Everest optimization:

```py
def run_plan(plan, config):
    optimizer = plan.add_optimizer()  # Add an optimizer step
    plan.add_table(optimizer)         # Add a table event handler
    optimizer.run()                   # Run the optimizer
```

This function executes a basic optimization workflow by performing these steps:

1.  **Plan Creation**: Everest creates an
    [`EverestPlan`][ropt_everest.EverestPlan] object and passes it to `run_plan`
    via the `plan` parameter. In addition it passes the Everest configuration
    dictionary, although it is not used in this example.
2.  **Optimizer Addition**: An optimizer step is added to the plan using the
    [`add_optimizer`][ropt_everest.EverestPlan.add_optimizer] method.
3.  **Table Handler Addition**: A table event handler is added to the plan using
    the [`add_table`][ropt_everest.EverestPlan.add_table] method. This will save
    the optimization results in a set of tables.
4.  **Optimizer Execution**: The optimization process is started by calling the
    [`run`][ropt_everest.EverestOptimizerStep.run] method of the optimizer step. It
    uses the configuration that was passed to Everest without modification.


## EverestPlan Methods

The `EverestPlan` class provides a high-level interface for defining and
managing optimization workflows in Everest. It allows you to add various steps
to the plan, such as optimizers, and evaluators, that are then executed to
achieve the desired optimization goal.

**Key Features:**


- **Step Management:** Add and manage different types of optimization steps,
    including optimizers, and evaluators.
- **Tracking and Monitoring:** Incorporate trackers to monitor the progress of
    specific steps and collect relevant results.
- **Table Generation:** Generate tables to summarize the results of the
    optimization process.
- **Configuration Handling:** Manage Everest configurations, including the
    ability to override default settings.
- **Metadata Association:** Associate arbitrary metadata with steps and results,
   facilitating the tracking of additional information.
- **Direct Execution:** Execute the plan directly, providing more control over
    stdout and error traces.
- **Caching Results:** Add event handlers to the caching mechanism of the plan.
    Any results stored by those handlers can be re-used by the optimizer and
    evaluation steps.

The [`EverestPlan`][ropt_everest.EverestPlan] object provides several methods
for building and managing optimization workflows:

### [`add_optimizer`][ropt_everest.EverestPlan.add_optimizer]
Adds an optimizer step to the workflow plan. The resulting
[`EverestOptimizerStep`][ropt_everest.EverestOptimizerStep] object can be
executed using its [`run`][ropt_everest.EverestOptimizerStep.run] method. The
`run` method supports the following parameters to customize its behavior:

- **config** (`dict`, optional): A dictionary to override the default Everest
    configuration. If not specified, the original Everest configuration is used.
    You can copy and modify the configuration passed to the `run_plan` function
    to create a suitable configuration.
- **controls** (`array-like`, optional): Initial control values for the
    optimizer. If not specified, the initial values from the Everest
    configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the optimizer.
- **output_dir** (`string`, optional): A directory (absolute or relative) where
    the optimizer stores output.
    
### [`add_ensemble_evaluator`][ropt_everest.EverestPlan.add_ensemble_evaluator]
Adds an ensemble evaluator step to the workflow plan. The resulting
[`EverestEnsembleEvaluatorStep`][ropt_everest.EverestEnsembleEvaluatorStep]
object can be executed using its
[`run`][ropt_everest.EverestEnsembleEvaluatorStep.run] method. The `run` method
supports the following parameters to customize its behavior:

- **config** (`dict`, optional): A dictionary to override the default Everest
    configuration. If not specified, the original Everest configuration is used.
    You can copy and modify the configuration passed to the `run_plan` function
    to create a suitable configuration.
- **controls** (`array-like`, optional): The controls that will be evaluated.
    This can be a single vector, a sequence of multiple vectors, or a 2D matrix
    where the control vectors are the rows. If multiple vectors or a 2D matrix
    is supplied, an evaluation is performed for each control vector. If not
    specified, the initial values from the Everest configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the evaluator.

### [`add_store`][ropt_everest.EverestPlan.add_tracker]
Adds a result store to the plan to record the progress of a step. The resulting
[`EverestStore`][ropt_everest.EverestStore] object stores results emitted by
optimizers and evaluators that it is monitoring. It accepts the following
arguments:

- **steps**: A single step object or a list of step objects to track. The
    tracker will only record results generated by the specified steps.

The tracker object returned by [`add_store`][ropt_everest.EverestPlan.add_store]
supports the following properties to inspect the results that it stores:

- **results**:  The list of results that is stored.
- **controls**: The controls in the stored results.

In addition, the following methods are available:

- **[`reset`][ropt_everest.EverestStore.reset]**: Reset the tracker to contain
    no results.
- **[`dataframe`][ropt_everest.EverestStore.dataframe]**: Export the results
    as Pandas data frames.


### [`add_tracker`][ropt_everest.EverestPlan.add_tracker]
Adds a result tracker to the plan to monitor the progress of a step. The
resulting [`EverestTracker`][ropt_everest.EverestTracker] object tracks and
stores results emitted by optimizers and evaluators that it is monitoring.
It accepts the following arguments:

- **steps**: A single step object or a list of step objects to track. The
    tracker will only record results generated by the specified steps.
- **what**: This argument determines which results the tracker should
    record. Possible values:
    - `"best"`: Only the best result found so far is tracked. This is the default.
    - `"last"`: Only the most recently generated result is tracked.
- **constraint_tolerance**: A tolerance for detecting constraint violations.

The tracker object returned by [`add_tracker`][ropt_everest.EverestPlan.add_tracker]
supports the following properties to inspect the results that it stores:

- **results**:  The results object that is stored.
- **controls**: The controls in the stored results.

In addition, the following methods are available:

- **[`reset`][ropt_everest.EverestTracker.reset]**: Reset the tracker to contain
    no results.
- **[`dataframe`][ropt_everest.EverestTracker.dataframe]**: Export the results
    as Pandas data frames.

### [`add_table`][ropt_everest.EverestPlan.add_table]
Adds a table event handler to the plan. The resulting
[`EverestTableHandler`][ropt_everest.EverestTableHandler] object tracks and
stores results emitted by optimizers and evaluators in tables on file. It
accepts a single argument:

- **steps**: A single step object or a list of step objects to track. The
    tracker will only record results generated by the specified steps.


### [`add_to_cache`][ropt_everest.EverestPlan.add_to_cache] and [`remove_from_cache`][ropt_everest.EverestPlan.remove_from_cache]
These add and remove event handlers to the caching mechanism of the plan. Any
results stored in the event handlers can be re-used by the optimizer and
evaluation steps. Both methods accept a single argument:

- **source:** The event handlers to add or to remove.
