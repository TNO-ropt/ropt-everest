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
def run_plan_basic(plan: EverestPlan) -> None:
    ...
```

The function must accept an [`EverestPlan`][ropt_everest.EverestPlan] object,
which is used to define and execute the optimization workflow. This object is
created by Everest and provided to `run_plan` via the `plan` parameter.

Developing and executing a custom workflow involves two key aspects:

1.  **Defining the Workflow:** This entails adding the individual steps and
    their associated result handlers to the `EverestPlan`. These steps can
    include optimizers, evaluators, and other custom operations. Result
    handlers, such as trackers and table outputs, capture the outcomes of each
    step.

2.  **Executing and Inspecting:** This process involves arranging the defined
    steps in the desired order of execution and leveraging the result handlers
    to analyze the output data. The `EverestPlan` automatically manages the
    execution of these steps, guaranteeing their correct operation and ensuring
    that results are consistently captured and made accessible. Because the
    `run_plan` function is implemented in standard Python, you can use the full
    power of Python programming (e.g., loops, conditional statements, and custom
    functions) to create sophisticated and adaptable optimization workflows.

For example, this `run_plan` function reproduces the default Everest optimization:

```py
def run_plan(plan):
    optimizer = plan.add_optimizer()  # Add an optimizer step
    plan.add_table(optimizer)         # Add a table handler
    optimizer.run()                   # Run the optimizer
```

This function executes a basic optimization workflow by performing these steps:

1.  **Plan Creation**: Everest creates an
    [`EverestPlan`][ropt_everest.EverestPlan] object and passes it to `run_plan`
    via the `plan` parameter.
2.  **Optimizer Addition**: An optimizer step is added to the plan using the
    [`add_optimizer`][ropt_everest.EverestPlan.add_optimizer] method.
3.  **Table Handler Addition**: A table handler is added to the plan using the
    [`add_table`][ropt_everest.EverestPlan.add_table] method. This will save the
    optimization results in a set of tables.
4.  **Optimizer Execution**: The optimization process is started by calling the
    [`run`][ropt_everest.EverestOptimizerStep.run] method of the optimizer step.


## EverestPlan Methods

The `EverestPlan` class provides a high-level interface for defining and
managing optimization workflows in Everest. It allows you to add various
steps to the plan, such as optimizers, evaluators, and workflow jobs, that
are then executed to achieve the desired optimization goal.

**Key Features:**


- **Step Management:** Add and manage different types of optimization steps,
    including optimizers, evaluators, and workflow jobs.
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

The [`EverestPlan`][ropt_everest.EverestPlan] object provides several methods
for building and managing optimization workflows:

### [`config_copy`][ropt_everest.EverestPlan.config_copy]
Creates a modifiable copy of the Everest configuration dictionary. This copy
allows you to override specific configuration settings to use with optimizer
steps.

### [`add_optimizer`][ropt_everest.EverestPlan.add_optimizer]
Adds an optimizer step to the workflow plan. The resulting
[`EverestOptimizerStep`][ropt_everest.EverestOptimizerStep] object can be
executed using its [`run`][ropt_everest.EverestOptimizerStep.run] method. The
`run` method supports the following parameters to customize its behavior:

- **config** (`dict`, optional): A dictionary to override the default Everest
    configuration. If not specified, the original Everest configuration is used.
    You can modify the result of
    [`plan.config_copy()`][ropt_everest.EverestPlan.config_copy] to create a
    suitable configuration.
- **controls** (`array-like`, optional): Initial control values for the
    optimizer. If not specified, the initial values from the Everest
    configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the optimizer.
    
### [`add_evaluator`][ropt_everest.EverestPlan.add_evaluator]
Adds an evaluator step to the workflow plan. The resulting
[`EverestEvaluatorStep`][ropt_everest.EverestEvaluatorStep] object can be
executed using its [`run`][ropt_everest.EverestEvaluatorStep.run] method. The
`run` method supports the following parameters to customize its behavior:

- **config** (`dict`, optional): A dictionary to override the default Everest
    configuration. If not specified, the original Everest configuration is used.
    You can modify the result of
    [`plan.config_copy()`][ropt_everest.EverestPlan.config_copy] to create a
    suitable configuration.
- **controls** (`array-like`, optional): The controls that will be evaluated.
    This can be a single vector, a sequence of multiple vectors, or a 2D matrix
    where the control vectors are the rows. If multiple vectors or a 2D matrix
    is supplied, an evaluation is performed for each control vector. If not
    specified, the initial values from the Everest configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the evaluator.

### [`add_workflow_job`][ropt_everest.EverestPlan.add_workflow_job]
Adds a workflow job step to the plan. The resulting
[`EverestWorkflowJobStep`][ropt_everest.EverestWorkflowJobStep] object can be
executed using its [`run`][ropt_everest.EverestWorkflowJobStep.run] method. The
`run` method accepts a list of job names to execute. These jobs must be defined
in the `install_workflow_jobs` section of the Everest configuration file.

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
Adds a table result handler to the plan. The resulting
[`EverestTableHandler`][ropt_everest.EverestTableHandler] object tracks and
stores results emitted by optimizers and evaluators in tables on file. It
accepts a single argument:

- **steps**: A single step object or a list of step objects to track. The
    tracker will only record results generated by the specified steps.
