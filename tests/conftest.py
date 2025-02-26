import shutil
import warnings
from pathlib import Path
from typing import Any, Callable

import pytest
from ert.config import ConfigWarning


@pytest.fixture(autouse=True)
def filter_warnings() -> None:
    warnings.filterwarnings(
        "ignore",
        message=".*Forward model might not write the required output.*",
        category=ConfigWarning,
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
    )


@pytest.fixture
def copy_data(tmp_path: Any, monkeypatch: Any) -> Callable[[str | Path], None]:
    def _copy_data(path: str | Path) -> None:
        shutil.copytree(
            Path(__file__).parent.parent / "test-data" / path,
            tmp_path,
            dirs_exist_ok=True,
        )
        monkeypatch.chdir(tmp_path)

    return _copy_data
