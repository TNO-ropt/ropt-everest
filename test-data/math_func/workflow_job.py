# type: ignore
# ruff: noqa

from ropt.enums import OptimizerExitCode


def run_plan(plan):
    workflow_job = plan.add_workflow_job()
    workflow_job.run(["report first.txt one", "report second.txt one two three"])
    return None, OptimizerExitCode.MAX_FUNCTIONS_REACHED
