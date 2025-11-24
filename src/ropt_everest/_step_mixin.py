from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ropt.plugins.event_handler.base import EventHandler
from ropt.workflow import create_event_handler

from ._store import EverestStoreHandler
from ._tracker import EverestTrackerHandler

if TYPE_CHECKING:
    from ropt.plugins.event_handler import EventHandler


class StepMixin:
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self._table: EventHandler | None = None

    def add_tracker(
        self,
        *,
        what: Literal["best", "last"] = "best",
        constraint_tolerance: float | None = None,
    ) -> EverestTrackerHandler:
        """Adds a tracker to the optimizer or ensemble evaluator.

        Trackers monitor the progress of the optimization or evaluation and
        record relevant results. They provide a way to capture and analyze the
        outcomes of during the execution of the workflow. You can configure a
        tracker to save the best or the last results generated.

        Invoking this method returns an
        [`EverestTrackerHandler`][ropt_everest.EverestTrackerHandler] object,
        which provides various methods to access the tracked results.

        A tracker is configured by three arguments:

        **what:** This argument determines which results the tracker should
        record. You can choose from the following options:

        - `"best"`: Only the best result found so far is tracked.
        - `"last"`: Only the most recently generated result is tracked.

        The default value is `"best"`.

        **constraint_tolerance:** This optional argument specifies the tolerance
        for constraint satisfaction. It is used to determine whether a result is
        considered feasible, meaning it satisfies the defined constraints within
        the specified tolerance. Only feasible results will be recorded. If it
        is not set, constraints are not tested.

        Args:
            what:                 Which results to track ("best" or "last").
            constraint_tolerance: Tolerance for constraint satisfaction.

        Returns:
            An `EverestTrackerHandler` object.
        """
        tracker = create_event_handler(
            "everest/tracker", what=what, constraint_tolerance=constraint_tolerance
        )
        assert isinstance(tracker, EverestTrackerHandler)
        self.add_event_handler(tracker)  # type: ignore[attr-defined]
        return tracker

    def add_store(self) -> EverestStoreHandler:
        """Adds a results store to the optimizer or ensemble evaluator.

        Stores the results of the optimization or evaluation.

        Invoking this method returns an
        [`EverestStoreHandler`][ropt_everest.EverestStoreHandler] object, which
        provides various methods to access the stored results.

        Returns:
            An `EverestStoreHandler` object.
        """
        store = create_event_handler("everest/store")
        assert isinstance(store, EverestStoreHandler)
        self.add_event_handler(store)  # type: ignore[attr-defined]
        return store

    def add_table(self, table: EventHandler | None = None) -> EventHandler:
        """Adds an event handler that creates a table with results on disk.

        This event handler will monitor the progress of the optimization or
        evaluation and record relevant results. A set of tables will then be
        generated and saved in the output directory.

        Args:
            table: Optional existing table to add, if `None` a new table is created.

        Note:
            This requires that the `everest-table` plugin for `ropt` is
            installed. If it is not installed, this method will do nothing and
            return `None`. In this case, no tables will be generated.

        Returns:
            An `EverestTableHandler` object.
        """
        self._table = (
            create_event_handler("everest_table/table") if table is None else table
        )
        self.add_event_handler(self._table)  # type: ignore[attr-defined]
        return self._table
