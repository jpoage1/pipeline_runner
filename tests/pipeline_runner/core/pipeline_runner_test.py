import pytest
from unittest.mock import MagicMock, patch
from pipeline_runner.core.pipeline_runner import runner
from pipeline_runner.lib.task_types.suite_task import SuiteTask


class MockTask(SuiteTask):
    """A real SuiteTask subclass (matches runner()'s
    list[type[SuiteTask]] contract) - PipelineSuite itself is mocked out
    in every test in this file, so this is never actually instantiated,
    only passed through by reference."""

    def _run(self) -> bool:
        return True


@pytest.fixture
def mock_pipeline_suite():
    """Patches PipelineSuite to prevent actual CLI parsing and task execution."""
    with patch("pipeline_runner.core.pipeline_runner.PipelineSuite") as mock:
        suite_instance = mock.return_value
        suite_instance.run = MagicMock()
        suite_instance.dump_print_queue = MagicMock()
        suite_instance.print = MagicMock()
        yield suite_instance


## Success Path


def test_runner_success(mock_pipeline_suite):
    """Verify runner completes and dumps queue on success."""
    runner(tasks=[])

    mock_pipeline_suite.run.assert_called_once()
    mock_pipeline_suite.dump_print_queue.assert_called()
    # Should not call sys.exit on success based on provided logic (exit_code 0)


## Exception Handling


def test_runner_keyboard_interrupt(mock_pipeline_suite):
    """Verify cleanup logic when KeyboardInterrupt is raised."""
    mock_pipeline_suite.run.side_effect = KeyboardInterrupt()

    with patch("traceback.print_exc") as mock_trace:
        runner(tasks=[])

        mock_trace.assert_called_once()
        mock_pipeline_suite.dump_print_queue.assert_called()
        mock_pipeline_suite.print.assert_called_with(
            "\n[System] Termination signal received. Cleaning up..."
        )


def test_runner_general_exception(mock_pipeline_suite):
    """Verify sys.exit(1) and error reporting on generic Exception."""
    mock_pipeline_suite.run.side_effect = Exception("Crash")

    with patch("traceback.print_exc"), patch("sys.exit") as mock_exit:

        runner(tasks=[])

        # Verify queue was dumped before exiting
        mock_pipeline_suite.dump_print_queue.assert_called()
        # Verify exit code 1 was sent to sys.exit
        mock_exit.assert_called_once_with(1)


## Logic Verification


def test_runner_initializes_with_tasks(mock_pipeline_suite):
    """Verify that the provided task list is passed to PipelineSuite."""
    tasks = [MockTask, MockTask]

    with patch(
        "pipeline_runner.core.pipeline_runner.PipelineSuite"
    ) as mock_suite_class:
        runner(tasks=tasks)
        mock_suite_class.assert_called_once_with(all_tasks=tasks)
