import pytest
import subprocess
import threading
import io
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import ShellException


class ConcreteTask(SuiteTask):
    def __init__(self, parent, owner):
        self.name = "TestTask"
        super().__init__(parent, owner)

    def _run(self):
        return "success"


class MockOwner:
    def __init__(self):
        self.args = {"dry_run": False}
        self.paths = {"root": Path("/tmp/project")}


@pytest.fixture
def task_context():
    owner = MockOwner()
    parent = MagicMock()
    parent.cwd = "/tmp"
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        task = ConcreteTask(parent, owner)
        # Mock printer to avoid console noise and verify calls
        task.printer = MagicMock()
        return task


## Shell Execution (sh) Tests


@patch("subprocess.run")
def test_sh_executes_correctly(mock_run, task_context):
    """Verify sh passes correct arguments to subprocess.run."""
    task_context.sh("ls -la", cwd=Path("/tmp"))

    mock_run.assert_called_once_with("ls -la", shell=True, check=True, cwd="/tmp")


@patch("subprocess.run")
def test_sh_handles_exception(mock_run, task_context):
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")

    # If handle_exception is True, it calls self.fail()
    # If it falls through, it raises ShellException.
    # Adjust based on your handle_exception logic:
    with pytest.raises(ShellException):
        task_context.sh("bad_cmd", handle_exception=False)


@patch("subprocess.run")
def test_sh_respects_dry_run(mock_run, task_context):
    """Verify sh bypasses execution if should_skip returns True."""
    task_context.args["dry_run"] = True

    task_context.sh("echo Hello World")

    mock_run.assert_not_called()
    task_context.printer.msg.assert_any_call("  [DRY-RUN] [EXEC] echo Hello World")


## Threaded Shell Execution (sh_thread) Tests


@patch("subprocess.Popen")
def test_sh_thread_captures_output(mock_popen, task_context):
    """Verify sh_thread correctly streams and captures stdout/stderr."""
    # Mock process behavior
    mock_process = MagicMock()
    mock_process.stdout = io.StringIO("output line\n")
    mock_process.stderr = io.StringIO("error line\n")
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    # Patch sys.stdout/err to verify relay
    with patch("sys.stdout", new=io.StringIO()) as fake_out, patch(
        "sys.stderr", new=io.StringIO()
    ) as fake_err:

        task_context.sh_thread("echo 'hello'")

        assert "output line\n" in fake_out.getvalue()
        assert "error line\n" in fake_err.getvalue()
        assert task_context.last_run.stdout == ["output line\n"]
        assert task_context.last_run.stderr == ["error line\n"]


## Dry Run & Run Logic Tests


def test_disable_dry_run_overrides_method(task_context):
    """Verify disable_dry_run replaces do_dry_run with a function returning False."""
    task_context.args["dry_run"] = True
    assert task_context.do_dry_run() is True

    task_context.disable_dry_run()
    assert task_context.do_dry_run() is False


def test_run_lifecycle_skip(task_context):
    """Verify run() short-circuits if dry_run/skip_task is True."""
    task_context.skip = True
    with patch.object(task_context, "_run") as mock_run_logic:
        result = task_context.run()
        assert result is True  # dry_run returns True when skipping
        mock_run_logic.assert_not_called()


def test_run_lifecycle_execution(task_context):
    """Verify run() calls _run() when not skipping."""
    with patch.object(task_context, "_run", return_value="done") as mock_run_logic:
        result = task_context.run()
        assert result == "done"
        mock_run_logic.assert_called_once()


## Property Mapping Tests


def test_legacy_getters_match_properties(task_context):
    """Ensure legacy getter methods correctly map to new properties."""
    task_context._id = 99
    task_context._stage = "BUILD"

    assert task_context.get_id() == 99
    assert task_context.get_stage() == "BUILD"
    assert task_context.get_cwd() == task_context.cwd
