from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.tasks.bootstrap import EnsurePaths


@pytest.fixture
def task_context():
    """Provides a mocked owner and parent for task initialization."""
    owner = MagicMock()
    owner.args = {"dry_run": False}
    parent = MagicMock()
    # Mocking Task.add as it is called in SuiteTask.__init__
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield parent, owner


def test_ensure_paths_creates_directories(task_context, tmp_path):
    """Verify EnsurePaths creates the specified directory structure."""
    parent, owner = task_context

    # Define test directories within a temporary path
    path_a = tmp_path / "build"
    path_b = tmp_path / "dist" / "assets"

    class ConcreteEnsurePaths(EnsurePaths):
        _dirs = [path_a, path_b]

    task = ConcreteEnsurePaths(parent, owner)
    task._run()

    assert path_a.exists()
    assert path_b.exists()
    assert path_b.is_dir()


@patch.object(Path, "mkdir")
def test_ensure_paths_mkdir_arguments(mock_mkdir, task_context):
    """Verify mkdir is called with parents=True and exist_ok=True."""
    parent, owner = task_context
    mock_path = MagicMock(spec=Path)

    class ConcreteEnsurePaths(EnsurePaths):
        _dirs = [mock_path]

    task = ConcreteEnsurePaths(parent, owner)
    task._run()

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
