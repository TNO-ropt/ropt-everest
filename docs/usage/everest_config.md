## Modifying Everest Configuration Settings

The `run_plan` function accepts the Everest configuration as an argument when it
starts. This configuration can be modified before running any optimization or
evaluation steps. However, it's important to note that not all modifications
will necessarily take effect, and some may lead to unexpected behavior.
Currently, it's considered safe to modify most settings within the
`optimization` section, as well as the `realization_weights` in the `model`
section.

## Handling `max_batch_num`

Modifying the `max_batch_num` setting within the `optimization` section after
the plan has started will have no effect. It's crucial to understand that
`max_batch_num` determines the total number of batches allowed across the
*entire* optimization process. Consequently, if your `run_plan` function
includes multiple optimization runs, and the first run reaches the
`max_batch_num` limit, subsequent optimization steps will not be executed.
