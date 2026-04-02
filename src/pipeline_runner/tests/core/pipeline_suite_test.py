import pytest
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from pipeline_runner.core.suite import PipelineSuite, load_parser


class MockTask:
    __name__ = "MockTask"

    def __init__(self, parent, owner):
        self.parent = parent
        self.owner = owner


@pytest.fixture(autouse=True)
def reset_suite_state():
    """Resets the Task registry and Suite initialization state."""
    with patch("pipeline_runner.lib.task_types.task.Task.__init__"), patch(
        "pipeline_runner.lib.task_types.task.Task.run"
    ), patch("pipeline_runner.lib.task_types.suite_task.SuiteTask._initialized", False):
        yield


## Parser Tests


def test_load_parser_defaults():
    """Verify default values and types for the argument parser."""
    parser = load_parser()
    # Simulate no arguments
    args = parser.parse_args([])

    assert args.full_pipeline is True
    assert args.dry_run is False
    assert args.task is None
    assert args.tasks is None


def test_load_parser_custom_values():
    """Verify that the parser correctly handles provided CLI flags."""
    parser = load_parser()
    cli_args = ["--task", "TestTask", "--dry-run", "--tasks", "1", "2"]
    args = parser.parse_args(cli_args)

    assert args.task == "TestTask"
    assert args.dry_run is True
    assert args.tasks == [1, 2]


## PipelineSuite Tests


@patch("argparse.ArgumentParser.parse_args")
def test_suite_initialization(mock_parse, tmp_path):
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
def test_run_full_pipeline(mock_parse, mock_task_init, mock_task_run):
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
def test_run_single_task(mock_parse, mock_task_run):
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


def test_fail_raises_suite_error():
    """Verify that the fail method raises the correct custom exception."""
    with patch("argparse.ArgumentParser.parse_args"):
        suite = PipelineSuite()
        from pipeline_runner.lib.exceptions import SuiteError

        with pytest.raises(SuiteError):
            suite.fail("Error message")
