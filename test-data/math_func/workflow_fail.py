# type: ignore
# ruff: noqa

from ropt.enums import OptimizerExitCode


def run_plan(plan):
    workflow_job = plan.add_workflow_job()
    info = workflow_job.run(["fail"])
    if not all(v["completed"] for v in info.values()):
        msg = "workflow job failed"
        raise RuntimeError(msg)
    return None, OptimizerExitCode.MAX_FUNCTIONS_REACHED
