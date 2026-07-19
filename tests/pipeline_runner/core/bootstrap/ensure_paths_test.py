"""Tests for core.bootstrap.ensure_paths_test."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.core.bootstrap import EnsurePaths


@pytest.fixture
def task_context() -> Iterator[tuple[MagicMock, MagicMock]]:
    """Provides a mocked owner and parent for task initialization."""
    owner = MagicMock()
    owner.args = {"dry_run": False}
    parent = MagicMock()
    # Mocking Task.add as it is called in SuiteTask.__init__
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield parent, owner


def test_ensure_paths_creates_directories(task_context: Any, tmp_path: Any) -> None:
    """Verify EnsurePaths creates the specified directory structure."""
    parent, owner = task_context

    # Define test directories within a temporary path
    path_a = tmp_path / "build"
    path_b = tmp_path / "dist" / "assets"

    class ConcreteEnsurePaths(EnsurePaths):
        def __init__(
            self,
            parent: Any,
            owner: Any,
            /,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            self._dirs = [path_a, path_b]
            super().__init__(parent, owner, *args, **kwargs)

    task = ConcreteEnsurePaths(parent, owner)
    task._run()

    assert path_a.exists()
    assert path_b.exists()
    assert path_b.is_dir()


def test_ensure_paths_mkdir_arguments(task_context: Any) -> None:
    """Verify mkdir is called with parents=True and exist_ok=True."""
    parent, owner = task_context
    # mock_path is a MagicMock, not a real Path - @patch.object(Path,
    # "mkdir") would never intercept a call made through it (that only
    # patches the real class), so assert on the mock's own auto-generated
    # .mkdir attribute directly instead.
    mock_path = MagicMock(spec=Path)

    class ConcreteEnsurePaths(EnsurePaths):
        def __init__(
            self,
            parent: Any,
            owner: Any,
            /,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            self._dirs = [mock_path]
            super().__init__(parent, owner, *args, **kwargs)

    task = ConcreteEnsurePaths(parent, owner)
    task._run()

    mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
