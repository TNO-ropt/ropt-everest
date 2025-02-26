from ropt.enums import OptimizerExitCode
from ropt.plan import Plan
from ropt.plugins.plan.base import ResultHandler
from ropt.transforms import OptModelTransforms


def run_plan(
    plan: Plan, _: OptModelTransforms | None
) -> tuple[ResultHandler | None, OptimizerExitCode | None]:
    step = plan.add_step("workflow_job")
    plan.run_step(
        step, jobs=["report first.txt one", "report second.txt one two three"]
    )
    return None, OptimizerExitCode.MAX_FUNCTIONS_REACHED
