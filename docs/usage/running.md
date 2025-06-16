Typically, Everest optimization workflows are executed using the standard
Everest command-line interface (CLI). This approach works seamlessly even when
you've implemented a custom `run_plan` function using `ropt-everest`. However,
the Everest CLI often obscures exceptions and errors, providing limited feedback
or relegating detailed information to log files. This can be cumbersome during
the development of a custom `run_plan` function, as not all exceptions are
immediately visible. Moreover, the standard Everest CLI redirects standard
output (stdout) and standard error (stderr) to files, which can further
complicate debugging.

To address these challenges, `ropt-everest` offers the
[`run_everest`][ropt_everest.run_everest] function. This function allows you to
execute an Everest optimization directly, bypassing the Everest CLI. Instead of
launching a separate server process in the background or on a cluster, as the
Everest CLI typically does, the `run_everest` method runs the optimization
directly within your current process. A key benefit of this is that anything
written to `stdout` or `stderr` is sent directly to your console.

In the simplest case, `run_everest` takes only the name of the Everest
configuration file, and runs the default optimization workflow. To run a custom
workflow, the `script` keyword argument can be set to the name of Python script
that provides a `run_plan` function that executes the custom plan.

**Example: Custom `run_plan` and Direct Execution**

Here's an example of a Python script that customizes the optimization process.
It can be run using Everest by setting the `ROPT_SCRIPT` variable to the name of
this script. However, it can also be directly executed as a Python script, using
the `run_everest` function:

```py
from ropt_everest import load_config, run_everest


def run_plan(plan):
    config = load_config("config.yml")
    optimizer = plan.add_optimizer()
    plan.add_table(optimizer)
    optimizer.run(config)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    run_everest("config.yml", __file__)
```

Here, within the `if __name__ == "__main__":` block, we first suppress warnings
that Everest might produce. These warnings are generally intended for end-users
and are typically not relevant during the development of a custom `run_plan`
function. We then execute the `run_everest` function, passing the path to the
configuration file and to the script file.


**Note: Running on a HPC cluster**

The standard Everest command interface runs the optimization as a separate
server process. If Everest is configured for an HPC cluster, this server
process, which manages the optimization, is submitted to and executes on the
cluster.

In contrast, the direct execution method (`run_everest`) runs the optimization
within the current Python process. Consequently, the optimization executes on
the machine where your script is run (e.g., a login node or your local machine),
*not* automatically on an HPC cluster compute node. This is true even if Everest
is configured to use the cluster for other tasks, such as forward model
evaluations.

Importantly, regardless of how the optimization process itself is launched
(standard CLI or direct execution), forward model evaluations managed by Everest
will still be submitted to the HPC cluster if Everest is configured to do so.

If you intend for the main optimization process (when using direct execution via
`run_everest`) to also run on an HPC cluster, you must explicitly submit your
Python script to the cluster. This is done using standard cluster job submission
procedures, such as creating a batch script for schedulers like SLURM or PBS.
