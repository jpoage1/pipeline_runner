import pytest
from unittest.mock import MagicMock
from pipeline_runner.lib.task_types.suite_task import SuiteTask


class RealShellTask(SuiteTask):
    def _run(self):
        # Testing real 'echo' to verify string/list piping
        return self.sh("echo 'unit test'", check=True)


def test_sh_method_integration():
    """Validate that self.sh returns the new ShellOutput object correctly."""
    owner = MagicMock()
    owner.args = {"dry_run": False}
    parent = MagicMock()

    task = RealShellTask(parent, owner)
    task.printer = MagicMock()

    result = task._run()

    assert result.returncode == 0
    assert result.stdout == ["unit test"]
