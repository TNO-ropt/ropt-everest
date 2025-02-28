# type: ignore
# ruff: noqa

from ropt.enums import OptimizerExitCode


def run_plan(_):
    return None, OptimizerExitCode.USER_ABORT
