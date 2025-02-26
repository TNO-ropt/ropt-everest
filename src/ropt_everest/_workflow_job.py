"""This module implements a workflow_job step."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from ert.config import Workflow, WorkflowJob
from ert.substitutions import Substitutions
from ert.workflow_runner import WorkflowRunner
from ropt.plugins.plan.base import PlanStep

if TYPE_CHECKING:
    from everest.config import EverestConfig


class EverestWorkflowJob(PlanStep):
    def run(self, jobs: list[str]) -> None:  # type: ignore[override]
        everest_config: EverestConfig = self.plan["everest_config"]

        installed_jobs = {
            item.name: WorkflowJob.from_file(item.source, item.name)
            for item in everest_config.install_workflow_jobs
        }

        with NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".workflow", delete=False
        ) as fp:
            for job in jobs:
                fp.writelines(job + "\n")
            file_name = Path(fp.name)

        try:
            workflow = Workflow.from_file(file_name, Substitutions(), installed_jobs)
            runner = WorkflowRunner(workflow, fixtures={})
            runner.run_blocking()
            if not all(v["completed"] for v in runner.workflowReport().values()):
                msg = "workflow job failed"
                raise RuntimeError(msg)
        finally:
            file_name.unlink(missing_ok=True)
