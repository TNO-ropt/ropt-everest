import shutil
from pathlib import Path
from typing import Any

import pytest

from ropt_everest import run_everest


def test_example_without_script(tmp_path: Path, monkeypatch: Any) -> None:
    path = Path(__file__).parent.parent / "examples" / "mathfunc"
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    run_everest("config_example.yml")


@pytest.mark.parametrize("filename", ["basic", "two", "loop", "evaluator"])
def test_example(filename: str, tmp_path: Path, monkeypatch: Any) -> None:
    path = Path(__file__).parent.parent / "examples" / "mathfunc"
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    run_everest("config_example.yml", script=f"{filename}.py")
