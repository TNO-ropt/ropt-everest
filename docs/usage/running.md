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
[`everest`][ropt_everest.EverestPlan.everest] class method. This method allows
you to execute an Everest optimization directly, bypassing the Everest CLI.
Instead of launching a separate server process in the background or on a
cluster, as the Everest CLI typically does, the `everest` method runs the
optimization directly within your current process. A key benefit of this is that
anything written to `stdout` or `stderr` is sent directly to your console.

**Example: Custom `run_plan` and Direct Execution**

Here's an example of a Python module that customizes the optimization process.
When placed in the same directory as an Everest configuration file (YAML) and
given the same base name, this module will be used by Everest. It can also be
directly executed as a Python script to run the workflow without the Everest
CLI:

```py
from ropt_everest import EverestPlan
from pathlib import Path


def run_plan(plan):
    optimizer = plan.add_optimizer()
    tracker = plan.add_tracker(optimizer)
    plan.add_table(optimizer)
    exit_code = optimizer.run()
    return tracker, exit_code


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    EverestPlan.everest(Path(__file__).with_suffix(".yml"))
```

Here, within the `if __name__ == "__main__":` block, we first suppress warnings
that Everest might produce. These warnings are generally intended for end-users
and are typically not relevant during the development of a custom `run_plan`
function. We then execute the `everest` class method, passing the path to the
corresponding configuration file, which we construct dynamically by replacing
the `.py` suffix of the current file (`__file__`) with `.yml`.
