"""A handler for creating report tables."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pandas as pd
from ropt.enums import EventType
from ropt.plugins.plan.base import PlanHandler
from ropt.results import Results, results_to_dataframe
from tabulate import tabulate

from ._utils import (
    TABLE_COLUMNS,
    TABLE_TYPE_MAP,
    get_names,
    rename_columns,
    reorder_columns,
)

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from everest.config import EverestConfig
    from ropt.plan import Event, Plan


class EverestDefaultTableHandler(PlanHandler):
    def __init__(
        self,
        plan: Plan,
        *,
        everest_config: EverestConfig,
        sources: set[uuid.UUID] | None = None,
    ) -> None:
        super().__init__(plan)
        self._sources = sources
        self._tables = []
        names = get_names(everest_config)
        for type_, table_type in TABLE_TYPE_MAP.items():
            self._tables.append(
                ResultsTable(
                    TABLE_COLUMNS[type_],
                    Path(everest_config.optimization_output_dir) / f"{type_}.txt",
                    table_type=table_type,
                    names=names,
                    min_header_len=3,
                )
            )

    def handle_event(self, event: Event) -> None:
        if (
            event.event_type == EventType.FINISHED_EVALUATION
            and "results" in event.data
            and (self._sources is None or event.source in self._sources)
        ):
            results = tuple(
                item.transform_from_optimizer(event.config.transforms)
                for item in event.data["results"]
            )
            for table in self._tables:
                table.add_results(results)


class ResultsTable:
    def __init__(
        self,
        columns: dict[str, str],
        path: Path,
        *,
        table_type: Literal["functions", "gradients"] = "functions",
        names: dict[str, Sequence[str | int] | None] | None = None,
        min_header_len: int | None = None,
    ) -> None:
        if path.parent.exists():
            if not path.parent.is_dir():
                msg = f"Cannot write table to: {path}"
                raise RuntimeError(msg)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)

        self._columns = columns
        self._path = path
        self._names = names
        self._results_type = table_type
        self._min_header_len = min_header_len
        self._frames: list[pd.DataFrame] = []

    def add_results(self, results: Sequence[Results]) -> None:
        columns = deepcopy(self._columns)
        if results[0].metadata is not None:
            for item in results[0].metadata:
                columns[f"metadata.{item}"] = item
        frame = results_to_dataframe(
            results,
            set(columns),
            result_type=self._results_type,
            names=self._names,
        )
        if not frame.empty:
            self._frames.append(frame)
            self.save(columns)

    def save(self, columns: dict[str, str]) -> None:
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
            self._path.write_text(
                tabulate(
                    table_data, headers="keys", tablefmt="simple", showindex=False
                ),
            )
