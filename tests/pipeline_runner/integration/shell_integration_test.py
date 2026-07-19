"""Tests for integration.shell_integration_test."""

from unittest.mock import MagicMock

from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import ShellOutput


class RealShellTask(SuiteTask):
    """Mock class."""

    def _run(self) -> ShellOutput:
        # Testing real 'echo' to verify string/list piping
        return self.sh("echo 'unit test'", check=True)


def test_sh_method_integration() -> None:
    """Validate that self.sh returns the new ShellOutput object correctly."""
    owner = MagicMock()
    owner.args = {"dry_run": False}
    parent = MagicMock()

    task = RealShellTask(parent, owner)
    task.printer = MagicMock()

    result = task._run()

    assert result.returncode == 0
    assert result.stdout == ["unit test"]
