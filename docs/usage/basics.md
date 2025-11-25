## Running custom optimization workflows

The ropt-everest plugin allows you to customize and extend the default
optimization workflow in Everest. Normally, Everest performs a single
optimization run based on the parameters in a YAML configuration file. However,
with ropt-everest, you can override this behavior.

To customize the workflow, create a Python file that contains a function named
`run` with the following signature:

```py
def run(evaluator: Evaluator) -> None:
    ...
```

The only argument is an [`Evaluator`][ropt.plugins.evaluator.base.Evaluator]
object. This object is created by Everest and provided to `run` via the
`evaluator` parameter. This object will be passed to optimizers and ensemble
evaluators to perform the black-box functions that they require. 

Everest can now directed to use the `run` function to run the workflow by
setting the `ROPT_SCRIPT` environment variable. For instance:

```sh
ROPT_SCRIPT=run.py everest run config.yml
```

Developing and executing a custom workflow involves two key aspects:

1.  **Defining the workflow:** This entails adding the individual steps and
    their associated event handlers to the workflow. These steps can include
    optimizers, evaluators, and other custom operations. Result handlers, such
    as trackers and table outputs, capture the outcomes of each step.

2.  **Executing and inspecting:** This process involves arranging the defined
    steps in the desired order of execution and leveraging the event handlers to
    analyze the output data. Because the `run` function is implemented in
    standard Python, you can use the full power of Python programming (e.g.,
    loops, conditional statements, and custom functions) to create sophisticated
    and adaptable optimization workflows.

A `run` function constructs a workflow by creating objects that execute the
computations, such as optimizers and ensemble evaluators, with associated
_handler_ objects. You create these objects by calling factory functions such as
[`create_optimizer`][ropt_everest.create_optimizer]. You then add event handlers
to the new object using methods, such as for instance
[`add_tracker`][ropt_everest.HandlerMixin.add_tracker]. The created objects can
then be executed by calling their `run` method.

The `run` method may accept additional arguments to customize behavior. While
executing, these objects may generate results. These are forwarded to any event
handler objects that have been added to the object doing the computation.
Handlers may also accept additional configuration arguments during creation to
refine how they process these results.

In summary, building an optimization workflow involves: 1) defining one or more
objects that implement the computation, such as an optimization, 2) adding event
handlers to these objects to process the results of those steps, and 3) finally,
executing the steps by calling their `run` methods, potentially multiple times.

For example, given athe Everest configuration file called `config.yml`, this
script runs a single optimization and prints the best result it finds:

```py
from ropt_everest import create_optimizer, load_config, run_everest

def run(evaluator):
    config = load_config("config_example.yml") # Load the configuration
    optimizer = create_optimizer(evaluator)    # Create an optimizer
    tracker = optimizer.add_tracker()          # Add a tracker
    optimizer.run(config)                      # Run the optimizer
    print(tracker.controls)                    # Print the best results
```

This function executes a basic optimization workflow by performing these steps:

1.  **Load the configuration**: Load an Everest configuration using the
    [`load_config`][ropt_everest.load_config] function.
2.  **Create an optimizer**: An optimizer step is added to the plan using the
    [`create_optimizer`][ropt_everest.create_optimizer] function.
3.  **Add a tracker**: A tracker event handler is added to the optimizer using
    the [`add_tracker`][ropt_everest.HandlerMixin.add_tracker] method. This will
    save the best results encountered during optimization.
4.  **Execute the optimizer**: The optimization process is started by calling
    the [`run`][ropt_everest.EverestOptimizer.run] method of the optimizer. It
    uses the configuration that was passed to Everest without modification.
5.  **Print the result**: The tracker has inspected all results and kept the best.
    The best control values are displayed by printing the `controls` property of
    the 

## Classes and functions

The classes and functions of `ropt-everest` provide a high-level interface for
defining and managing optimization workflows in Everest. It allows you to add
various steps to the plan, such as optimizers, and evaluators, that are then
executed to achieve the desired optimization goal.


The `ropt-everest` package provides the following helper functions that create
the objects for optimizers and ensemble evaluators:

### [`create_optimizer`][ropt_everest.create_optimizer]
Creates an optimizer [`EverestOptimizer`][ropt_everest.EverestOptimizer] object
that can be executed using its [`run`][ropt_everest.EverestOptimizer.run]
method. The `run` method supports the following parameters to customize its
behavior:

- **config** (`dict`, optional): An Everest configuration dictionary. You can
    use the [`load_config`][ropt_everest.load_config] function to load an Everest YAML
    configuration file and parse it into a suitable dictionary.
- **controls** (`array-like`, optional): Initial control values for the
    optimizer. If not specified, the initial values from the Everest
    configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the optimizer.
- **output_dir** (`string`, optional): A directory (absolute or relative) where
    the optimizer stores output. This is  useful when multiple optimization
    runs are performed to prevent output from being overwritten.
    
### [`create_ensemble_evaluator`][ropt_everest.create_ensemble_evaluator]
Adds an ensemble evaluator step to the workflow plan. The resulting
[`EverestEnsembleEvaluator`][ropt_everest.EverestEnsembleEvaluator]
object can be executed using its
[`run`][ropt_everest.EverestEnsembleEvaluator.run] method. The `run` method
supports the following parameters to customize its behavior:

- **config** (`dict`, optional): An Everest configuration dictionary. You can
    use the [`load_config`][ropt_everest.load_config] function to load an Everest YAML
    configuration file and parse it into a suitable dictionary.
- **controls** (`array-like`, optional): The controls that will be evaluated.
    This can be a single vector, a sequence of multiple vectors, or a 2D matrix
    where the control vectors are the rows. If multiple vectors or a 2D matrix
    is supplied, an evaluation is performed for each control vector. If not
    specified, the initial values from the Everest configuration are used.
- **metadata** (`dict`, optional): A dictionary of metadata to be associated
    with each result generated by the evaluator.
- **output_dir** (`string`, optional): A directory (absolute or relative) where
    the ensemble evaluator stores output. This is  useful when multiple
    runs are performed to prevent output from bing overwritten.

The optimizers end ensemble evaluators created by these function are executed by
their `run` methods. While executing they emit events that can be handled by
event handler objects that are added by the following methods:


### [`add_tracker`][ropt_everest.HandlerMixin.add_tracker]
Adds a result tracker to the optimizer or ensemble evaluator to monitor the
progress. The resulting [`EverestTracker`][ropt_everest.EverestTracker] object
tracks and stores emitted results. It accepts the following arguments:

- **what**: This argument determines which results the tracker should
    record. Possible values:
    - `"best"`: Only the best result found so far is tracked. This is the default.
    - `"last"`: Only the most recently generated result is tracked.
- **constraint_tolerance**: A tolerance for detecting constraint violations.

The tracker object returned by
[`add_tracker`][ropt_everest.HandlerMixin.add_tracker] method supports the
following properties to inspect the results that it stores:

- **[`results`][ropt_everest.EverestTracker.results]**:  The results object that
  is stored.
- **[`controls`][ropt_everest.EverestTracker.controls]**: The controls in the
  stored results.

In addition, the following methods are available:

- **[`reset`][ropt_everest.EverestTracker.reset]**: Reset the tracker to contain
    no results.
- **[`dataframe`][ropt_everest.EverestTracker.dataframe]**: Export the results
    as Pandas data frames.


### [`add_store`][ropt_everest.HandlerMixin.add_store]
Adds a result store to the optimizer or ensemble evaluator to record the
progress of a step. The resulting [`EverestStore`][ropt_everest.EverestStore]
object stores results emitted by optimizers and evaluators that it is
monitoring.

The store object returned by [`add_store`][ropt_everest.HandlerMixin.add_store]
supports the following properties to inspect the results that it stores:

- **[`results`][ropt_everest.EverestStore.results]**:  The list of results that
  is stored.
- **[`controls`][ropt_everest.EverestStore.controls]**: The controls in the
  stored results.

In addition, the following methods are available:

- **[`reset`][ropt_everest.EverestStore.reset]**: Reset the tracker to contain
    no results.
- **[`dataframe`][ropt_everest.EverestStore.dataframe]**: Export the results
    as Pandas data frames.


### [`add_table`][ropt_everest.HandlerMixin.add_table]
Adds a table event handler to the plan. This handler writes text files
summarizing the results to the output directory.
