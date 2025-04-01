"""This module implements a workflow_job step."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any

from ert.config import Workflow
from ert.config.workflow_job import workflow_job_from_file
from ert.substitutions import Substitutions
from ert.workflow_runner import WorkflowRunner
from ropt.plugins.plan.base import PlanStep

if TYPE_CHECKING:
    from everest.config import EverestConfig


class EverestWorkflowJob(PlanStep):
    def run(self, config: EverestConfig, jobs: list[str]) -> Any:  # noqa: ANN401
        installed_jobs = {
            item.name: workflow_job_from_file(item.source, item.name)
            for item in config.install_workflow_jobs
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
            return runner.workflowReport()
        finally:
            file_name.unlink(missing_ok=True)
