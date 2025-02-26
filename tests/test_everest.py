from __future__ import annotations

import shutil
from typing import Any

from ert.ensemble_evaluator.config import EvaluatorServerConfig
from ert.run_models.everest_run_model import EverestExitCode, EverestRunModel
from everest.config import EverestConfig


def test_override_plan_abort(copy_data: Any) -> None:
    copy_data("math_func")
    shutil.move("abort.py", "config_minimal.py")
    config = EverestConfig.load_file("config_minimal.yml")
    run_model = EverestRunModel.create(config)
    evaluator_server_config = EvaluatorServerConfig()
    run_model.run_experiment(evaluator_server_config)
    assert run_model.exit_code.value == EverestExitCode.USER_ABORT
