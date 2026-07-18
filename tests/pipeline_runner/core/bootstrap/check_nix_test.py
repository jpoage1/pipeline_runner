import pytest
import os
from unittest.mock import MagicMock, patch
from pipeline_runner.core.bootstrap import CheckNix


@pytest.fixture
def task_context():
    """Provides a mocked owner and parent for task initialization."""
    owner = MagicMock()
    owner.args = {"dry_run": False}
    parent = MagicMock()
    # Mocking Task.add as it is called in SuiteTask.__init__
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield parent, owner


## CheckNix Tests


@patch("shutil.which")
def test_check_nix_not_found(mock_which, task_context):
    """Verify CheckNix handles missing nix binary gracefully."""
    mock_which.return_value = None
    parent, owner = task_context
    task = CheckNix(parent, owner)
    task.printer = MagicMock()

    result = task._run()

    assert result is False
    task.printer.print.assert_called_with("⬡ Nix tools not found in PATH.")


@patch("shutil.which")
def test_check_nix_in_shell(mock_which, task_context):
    """Verify CheckNix detects the IN_NIX_SHELL environment variable."""
    mock_which.return_value = "/run/current-system/sw/bin/nix"
    parent, owner = task_context
    task = CheckNix(parent, owner)

    with patch.dict(os.environ, {"IN_NIX_SHELL": "pure"}):
        result = task._run()

        assert result is True
        assert task._in_nix_shell == "pure"
