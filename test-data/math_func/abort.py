from ropt.enums import OptimizerExitCode
from ropt.plan import Plan
from ropt.plugins.plan.base import ResultHandler


def run_plan(plan: Plan) -> tuple[ResultHandler | None, OptimizerExitCode | None]:
    return None, OptimizerExitCode.USER_ABORT
