import pytest
from unittest.mock import MagicMock, patch
from pipeline_runner.core.bootstrap import VerifySystemDependencies


@pytest.fixture
def task_context():
    owner = MagicMock()
    owner._in_nix_shell = False
    parent = MagicMock()
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield parent, owner


def test_verify_dependencies_skips_in_nix_shell(task_context):
    """Verify that the task skips execution if the owner is in a Nix shell."""
    parent, owner = task_context
    owner._in_nix_shell = "pure"

    task = VerifySystemDependencies(parent, owner)
    task.printer = MagicMock()

    result = task._run()

    assert result is True
    task.printer.print.assert_called_with("Skipping: in nix shell")


def test_verify_dependencies_continues_when_not_in_nix(task_context):
    """Verify that the task does not skip when not in a Nix shell."""
    parent, owner = task_context
    owner._in_nix_shell = False

    task = VerifySystemDependencies(parent, owner)

    # _run returns None by default if it falls through (as defined in your src)
    result = task._run()
    assert result is None
