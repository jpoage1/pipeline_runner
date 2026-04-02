import pytest
import os
import subprocess
import threading
import io
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import ShellException


class ConcreteTask(SuiteTask):
    def __init__(self, parent, owner, **kwargs):
        self.name = "TestTask"
        super().__init__(parent, owner, **kwargs)

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


def test_suitetask_skip_task_false(task_context):
    """Cover skip_task returning False explicitly."""
    task_context.skip = False
    assert task_context.skip_task is False


def test_suitetask_get_count():
    """Cover get_count static evaluation."""
    from pipeline_runner.lib.task_types.suite_task import SuiteTask

    count = SuiteTask.get_count()
    assert isinstance(count, int)


def test_suitetask_print_msg_delegation(task_context):
    """Cover print and msg direct delegations to the Printer object."""
    with patch.object(task_context.printer, "print") as mock_print:
        task_context.print("test_print")
        mock_print.assert_called_once_with("test_print")

    with patch.object(task_context.printer, "msg") as mock_msg:
        task_context.msg("test_msg")
        mock_msg.assert_called_once_with("test_msg")


def test_suitetask_cwd_oserror_fallback():
    """Cover OSError suppression when evaluating parent working directories."""
    from pipeline_runner.lib.task_types.suite_task import SuiteTask

    owner = MockOwner()
    parent = MagicMock()
    type(parent).cwd = property(MagicMock(side_effect=OSError))

    task = ConcreteTask(parent, owner, cwd=None)
    assert task.cwd == str(Path(os.getcwd()))


def test_suitetask_properties_and_getters(task_context):
    """Evaluate remaining property and getter logic mappings."""
    task_context._stage = MagicMock()
    _ = task_context.owner
    _ = task_context.parent
    _ = task_context.stage
    _ = task_context.last_run
    _ = task_context.get_id()
    _ = task_context.get_stage()
    _ = task_context.get_cwd()


@patch("subprocess.run")
def test_sh_disabled(mock_run, task_context):
    """Verify sh returns an empty ShellOutput early if disabled=True."""
    res = task_context.sh("cmd", disabled=True)
    mock_run.assert_not_called()
    assert res.stdout == []


@patch("subprocess.run")
def test_sh_called_process_error_handled(mock_run, task_context):
    """Verify sh intercepts and escalates CalledProcessError exceptions."""
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
    with pytest.raises(SystemExit):
        task_context.sh("bad_cmd", handle_exception=True)


def test_dry_run_skips(task_context):
    """Cover dry_run skipping logic."""
    task_context.skip = True
    with patch.object(task_context.printer, "print") as mock_print:
        assert task_context.dry_run() is True
        mock_print.assert_called_with("Skipping")


@patch("subprocess.run")
def test_sh_disabled_returns_empty(mock_run, task_context):
    """Cover sh command bypassing when disabled is True."""
    res = task_context.sh("test", disabled=True)
    mock_run.assert_not_called()
    assert res.stdout == []


def test_suitetask_get_count_explicit():
    """Cover static get_count."""
    from pipeline_runner.lib.task_types.suite_task import SuiteTask

    SuiteTask._global_counter = 42
    assert SuiteTask.get_count() == 42


@patch("pipeline_runner.lib.task_types.task.Task.run")
def test_run_deps(mock_run, task_context):
    """Cover dependency execution iteration."""
    task_context._deps = ["dep1", "dep2"]
    task_context.run_deps()
    assert mock_run.call_count == 2


def test_get_path_and_cwd(task_context):
    """Cover dictionary and property proxy mappings."""
    from pathlib import Path

    task_context.owner.paths = {"root": Path("/mock/root")}
    assert task_context.get_path("root") == Path("/mock/root")
    assert task_context.get_path("root", "subdir") == Path("/mock/root/subdir")

    task_context._cwd = "/mock/cwd"
    assert task_context.get_cwd() == "/mock/cwd"


import pytest
import runpy
import sys
import traceback
from unittest.mock import MagicMock, patch

from pipeline_runner.core.pipeline_runner import runner


@patch("pipeline_runner.core.pipeline_runner.PipelineSuite")
@patch("builtins.print")
def test_runner_successful_execution(mock_print, mock_suite_class):
    """Verify normal runner lifecycle output and configuration."""
    mock_suite_instance = MagicMock()
    mock_suite_class.return_value = mock_suite_instance

    with patch("sys.exit") as mock_exit:
        runner(tasks=[])
        mock_suite_instance.run.assert_called_once()
        mock_print.assert_called_with("🚀 Pipeline Successful")
        mock_suite_instance.dump_print_queue.assert_called_once()


@patch("pipeline_runner.core.pipeline_runner.PipelineSuite")
@patch("traceback.print_exc")
def test_runner_keyboard_interrupt(mock_print_exc, mock_suite_class):
    """Verify keyboard interruption gracefully unwinds the process."""
    mock_suite_instance = MagicMock()
    mock_suite_instance.run.side_effect = KeyboardInterrupt()
    mock_suite_class.return_value = mock_suite_instance

    with patch("sys.exit") as mock_exit:
        runner(tasks=[])
        mock_print_exc.assert_called_once()
        mock_suite_instance.print.assert_called_with(
            "\n[System] Termination signal received. Cleaning up..."
        )


@patch("pipeline_runner.core.pipeline_runner.PipelineSuite")
@patch("traceback.print_exc")
@patch("builtins.print")
def test_runner_unhandled_exception(mock_print, mock_print_exc, mock_suite_class):
    """Verify unhandled error trapping and exit code escalation."""
    mock_suite_instance = MagicMock()
    mock_suite_instance.run.side_effect = ValueError("Fatal crash")
    mock_suite_class.return_value = mock_suite_instance

    with patch("sys.exit") as mock_exit:
        runner(tasks=[])
        mock_print_exc.assert_called_once()
        mock_exit.assert_called_with(1)
