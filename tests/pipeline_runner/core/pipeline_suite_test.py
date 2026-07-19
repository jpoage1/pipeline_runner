"""Tests for core.pipeline_suite_test."""

import argparse
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from pipeline_runner.core.suite import PipelineSuite, load_parser
from pipeline_runner.lib.exceptions import SuiteError
from pipeline_runner.lib.task_types.suite_task import SuiteTask


class MockTask(SuiteTask):
    """A real SuiteTask subclass (matches PipelineSuite.all_tasks'.

    list[type[SuiteTask]] contract) rather than a bare duck-typed class -
    never actually instantiated in these tests (Task.__init__/Task.run are
    mocked out), only passed around as a class reference, so no __init__
    override or behavior beyond the required abstract _run() is needed.
    """

    def _run(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def reset_suite_state() -> Any:
    """Resets the Task registry and Suite initialization state."""
    with (
        patch("pipeline_runner.lib.task_types.task.Task.__init__"),
        patch("pipeline_runner.lib.task_types.task.Task.run"),
        patch(
            "pipeline_runner.lib.task_types.suite_task.SuiteTask._initialized",
            new=False,
        ),
    ):
        yield


## Parser Tests


def test_load_parser_defaults() -> None:
    """Verify default values and types for the argument parser."""
    parser = load_parser()
    # Simulate no arguments
    args = parser.parse_args([])

    assert args.full_pipeline is True
    assert args.dry_run is False
    assert args.task is None
    assert args.tasks is None


def test_load_parser_custom_values() -> None:
    """Verify that the parser correctly handles provided CLI flags."""
    parser = load_parser()
    cli_args = ["--task", "TestTask", "--dry-run", "--tasks", "1", "2"]
    args = parser.parse_args(cli_args)

    assert args.task == "TestTask"
    assert args.dry_run is True
    assert args.tasks == [1, 2]


## PipelineSuite Tests


@patch("argparse.ArgumentParser.parse_args")
def test_suite_initialization(mock_parse: MagicMock, tmp_path: Any) -> None:
    """Verify Suite initializes with correct attributes and parsed args."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=str(tmp_path),
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    suite = PipelineSuite(root=str(tmp_path), all_tasks=[MockTask])

    assert suite.root_dir == tmp_path
    assert suite.args["full_pipeline"] is True
    # Verify singleton parser lock
    suite._parser(None)  # Should print "Parser already initialized"


@patch("pipeline_runner.lib.task_types.task.Task.run")
@patch("pipeline_runner.lib.task_types.task.Task.__init__")
@patch("argparse.ArgumentParser.parse_args")
def test_run_full_pipeline(
    mock_parse: MagicMock,
    mock_task_init: MagicMock,
    mock_task_run: MagicMock,
) -> None:
    """Verify that _run executes all tasks when full_pipeline is True."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    tasks = [MockTask, MockTask]
    suite = PipelineSuite(all_tasks=tasks)
    suite.printer = MagicMock()  # Mock printer for msg calls

    suite._run()

    mock_task_init.assert_called_once_with(suite, tasks)
    assert mock_task_run.call_count == 3  # 2 from loop + 1 from trailing Task.run(task)


@patch("pipeline_runner.lib.task_types.task.Task.run")
@patch("argparse.ArgumentParser.parse_args")
def test_run_single_task(mock_parse: MagicMock, mock_task_run: MagicMock) -> None:
    """Verify that _run executes only the specific task provided in args."""
    mock_parse.return_value = argparse.Namespace(
        task="MockTask",
        full_pipeline=False,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    suite = PipelineSuite(all_tasks=[MockTask])
    suite.printer = MagicMock()

    suite._run()

    # Verify Task.run was called with the specific task name string
    mock_task_run.assert_has_calls([call("MockTask"), call("MockTask")])


def test_fail_raises_suite_error() -> None:
    """Verify that the fail method raises the correct custom exception."""
    with patch("argparse.ArgumentParser.parse_args"):
        suite = PipelineSuite()

        with pytest.raises((SuiteError, SystemExit)):
            suite.fail("Error message")


@patch("argparse.ArgumentParser.parse_args")
def test_run_no_tasks_selected(mock_parse: MagicMock) -> None:
    """Verify _run fails if neither task nor full_pipeline is specified."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=False,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )
    suite = PipelineSuite()

    with pytest.raises((SuiteError, SystemExit)):
        suite._run()


@patch("argparse.ArgumentParser.parse_args")
@patch("sys.stderr")
def test_suite_initialization_lock(
    mock_stderr: MagicMock,
    mock_parse: MagicMock,
) -> None:
    """Verify the parser enforces a singleton lock and logs warnings."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )
    suite = PipelineSuite()
    suite._parser(None)
    mock_stderr.write.assert_called_with("Parser already initialized\n")
