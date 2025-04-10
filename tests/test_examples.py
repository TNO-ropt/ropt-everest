import shutil
from pathlib import Path
from typing import Any

import pytest

from ropt_everest import EverestPlan


@pytest.mark.parametrize("filename", ["basic", "two", "loop", "evaluator"])
def test_example(filename: str, tmp_path: Path, monkeypatch: Any) -> None:
    path = Path(__file__).parent.parent / "examples" / "mathfunc"
    shutil.copytree(path, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    Path(f"{filename}.py").rename("config_example.py")
    EverestPlan.everest("config_example.yml")
