from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
from ropt.enums import EventType
from ropt.plugins.plan.base import EventHandler, PlanComponent
from ropt.results import Results, results_to_dataframe
from tabulate import tabulate

from ._utils import TABLE_COLUMNS, TABLE_TYPE_MAP, rename_columns, reorder_columns

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ropt.plan import Event, Plan


class EverestDefaultTableHandler(EventHandler):
    def __init__(
        self,
        plan: Plan,
        tags: set[str] | None = None,
        sources: set[PlanComponent | str] | None = None,
    ) -> None:
        super().__init__(plan, tags, sources)
        self._path: Path | None = None
        self._tables = []
        for type_, table_type in TABLE_TYPE_MAP.items():
            self._tables.append(
                ResultsTable(
                    f"{type_}.txt",
                    TABLE_COLUMNS[type_],
                    table_type=table_type,
                    min_header_len=3,
                )
            )

    def handle_event(self, event: Event) -> None:
        if "results" in event.data:
            results = tuple(
                item.transform_from_optimizer() for item in event.data["results"]
            )
            if self._path is None:
                self._path = Path(results[0].config.optimizer.output_dir)
                if self._path.exists() and not self._path.is_dir():
                    msg = f"Cannot write table to: {self._path}"
                    raise RuntimeError(msg)
            else:
                self._path.mkdir(parents=True, exist_ok=True)
            for table in self._tables:
                table.add_results(results, self._path)

    @property
    def event_types(self) -> set[EventType]:
        return {EventType.FINISHED_EVALUATION}


class ResultsTable:
    def __init__(
        self,
        file_name: str,
        columns: dict[str, str],
        *,
        table_type: Literal["functions", "gradients"] = "functions",
        min_header_len: int | None = None,
    ) -> None:
        self._file_name = file_name
        self._columns = columns
        self._results_type = table_type
        self._min_header_len = min_header_len
        self._frames: list[pd.DataFrame] = []

    def add_results(self, results: Sequence[Results], path: Path) -> None:
        columns = deepcopy(self._columns)
        if results[0].metadata is not None:
            for item in results[0].metadata:
                columns[f"metadata.{item}"] = item
        frame = results_to_dataframe(
            results,
            set(columns),
            result_type=self._results_type,
        )
        if not frame.empty:
            self._frames.append(frame)
            self._save(columns, path / self._file_name)

    def _save(self, columns: dict[str, str], path: Path) -> None:
        data = pd.concat(self._frames)
        if not data.empty:
            # Turn the multi-index into columns:
            data = data.reset_index()

            # Reorder the columns to match the order of the headers:
            data = reorder_columns(data, columns)

            # Rename the columns:
            data = rename_columns(data, columns)

            # Add newlines to the headers to make them all the same length:
            max_lines = max(len(str(column).split("\n")) for column in data.columns)
            if self._min_header_len is not None and max_lines < self._min_header_len:
                max_lines = self._min_header_len
            data = data.rename(
                columns={
                    column: str(column)
                    + (max_lines - len(str(column).split("\n"))) * "\n"
                    for column in data.columns
                },
            )

            # Write the table to a file:
            table_data = {str(column): data[column] for column in data}
            path.write_text(
                tabulate(
                    table_data, headers="keys", tablefmt="simple", showindex=False
                ),
            )
