import pytest
from unittest.mock import MagicMock, patch
from pipeline_runner.tasks.example_tasks import ExampleTask, ExampleTaskRunner


class ConcreteExampleRunner(ExampleTaskRunner):
    def _run(self):
        return super()._run()


def test_example_task_execution():
    """Verify ExampleTask outputs the correct string."""
    owner = MagicMock()
    task = ExampleTask(parent=MagicMock(), owner=owner)

    with patch.object(task, "print") as mock_print:
        task._run()
        mock_print.assert_called_once_with("Hello World")


@patch("argparse.ArgumentParser.parse_args")
def test_example_task_runner_initialization(mock_parse):
    """Verify ExampleTaskRunner initializes and _run acts as a pass-through."""
    mock_parse.return_value = MagicMock(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )
    runner = ConcreteExampleRunner()

    assert runner.skip is False
    assert runner._stage.value == "any"
    assert runner._run() is None
