from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
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


def test_workflow_job(copy_data: Any) -> None:
    copy_data("math_func")
    shutil.move("workflow_job.py", "config_minimal.py")
    config = EverestConfig.load_file("config_minimal.yml")
    run_model = EverestRunModel.create(config)
    evaluator_server_config = EvaluatorServerConfig()
    run_model.run_experiment(evaluator_server_config)
    first = Path("first.txt")
    assert first.exists()
    with first.open() as fp:
        content = fp.read()
        assert "one" in content
    second = Path("second.txt")
    assert second.exists()
    with second.open() as fp:
        content = fp.read()
        assert "one two three" in content
    assert run_model.exit_code.value == EverestExitCode.MAX_FUNCTIONS_REACHED


def test_workflow_fail(copy_data: Any) -> None:
    copy_data("math_func")
    shutil.move("workflow_fail.py", "config_minimal.py")
    config = EverestConfig.load_file("config_minimal.yml")
    run_model = EverestRunModel.create(config)
    evaluator_server_config = EvaluatorServerConfig()
    with pytest.raises(RuntimeError, match="workflow job failed"):
        run_model.run_experiment(evaluator_server_config)
