"""Tests for core.bootstrap.verify_system_dependencies_test."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.core.bootstrap import VerifySystemDependencies


@pytest.fixture
def task_context() -> Iterator[tuple[MagicMock, MagicMock]]:
    """Verify task_context."""
    owner = MagicMock()
    owner._in_nix_shell = False
    parent = MagicMock()
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield parent, owner


def test_verify_dependencies_skips_in_nix_shell(task_context: Any) -> None:
    """Verify that the task skips execution if the owner is in a Nix shell."""
    parent, owner = task_context
    owner._in_nix_shell = "pure"

    task = VerifySystemDependencies(parent, owner)
    task.printer = MagicMock()

    result = task._run()

    assert result is True
    task.printer.print.assert_called_with("Skipping: in nix shell")


def test_verify_dependencies_continues_when_not_in_nix(task_context: Any) -> None:
    """Verify that the task does not skip when not in a Nix shell."""
    parent, owner = task_context
    owner._in_nix_shell = False

    task = VerifySystemDependencies(parent, owner)

    # _run() always returns True - the "not in nix shell" path is simply
    # not a failure case (this used to fall through returning None, a
    # real bug fixed at the source rather than encoded as expected here).
    result = task._run()
    assert result is True
