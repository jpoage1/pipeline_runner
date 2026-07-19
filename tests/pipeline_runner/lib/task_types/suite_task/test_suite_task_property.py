"""Tests for lib.task_types.suite_task.test_suite_task_property."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.core.suite import PipelineSuite
from pipeline_runner.lib.task_types.suite_task import SuiteTask


# Concrete implementation for testing abstract class
class ConcreteTask(SuiteTask):
    """Mock class."""

    def _run(self) -> str:
        return "success"


class MockOwner(PipelineSuite):
    """A real PipelineSuite subclass (matches SuiteTask.__init__'s.

    owner: Optional[PipelineSuite] contract) that skips the real
    constructor's argparse/CLI setup entirely - these tests only need
    .args/.paths present, not a fully wired-up suite.
    """

    def __init__(self) -> None:
        """Initialize the mock."""
        self.args = {"dry_run": False}
        self.paths = {"root": Path("/mock/work")}


@pytest.fixture(autouse=True)
def reset_suite_task_state() -> Iterator[Any]:
    """Resets the SuiteTask class-level state before every test."""
    SuiteTask._global_counter = 0
    SuiteTask._initialized = False
    # Use patch to prevent Task registry side effects during SuiteTask init
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield


## Initialization & Validation Tests


def test_suitetask_init_raises_on_missing_args() -> None:
    """Verify ValueError when owner or parent is missing."""
    with pytest.raises(ValueError, match="Owner is not set"):
        ConcreteTask(parent=MagicMock(), owner=None)

    with pytest.raises(ValueError, match="Parent is not set"):
        ConcreteTask(parent=None, owner=MagicMock())


def test_suitetask_identity_increment() -> None:
    """Verify that each task gets a unique incrementing ID."""
    owner = MockOwner()
    parent = MagicMock()

    t1 = ConcreteTask(parent, owner)
    t2 = ConcreteTask(parent, owner)

    assert t1.id == 0
    assert t2.id == 1
    assert SuiteTask._global_counter == 2


## CWD Inheritance Logic


def test_suitetask_cwd_inheritance() -> None:
    """Verify CWD is pulled from parent if not provided."""
    owner = MockOwner()
    parent = MagicMock()
    # Mock parent having a cwd property
    parent.cwd = "/inherited/path"

    task = ConcreteTask(parent, owner)
    assert task.cwd == "/inherited/path"


def test_suitetask_cwd_fallback_to_os_getcwd() -> None:
    """Verify fallback to system getcwd if parent lacks cwd."""
    owner = MockOwner()
    parent = MagicMock()

    parent.cwd = None
    parent._cwd = None

    task = ConcreteTask(parent, owner, cwd=None)
    assert task.cwd == str(Path.cwd())


def test_suitetask_explicit_cwd() -> None:
    """Verify explicit CWD overrides all inheritance."""
    owner = MockOwner()
    explicit_path = "/explicit/path"
    task = ConcreteTask(MagicMock(), owner, cwd=Path(explicit_path))
    assert task.cwd == explicit_path


## Property & Logic Tests


def test_suitetask_properties() -> None:
    """Verify read-only properties reflect internal state."""
    owner = MockOwner()
    parent = MagicMock()
    task = ConcreteTask(parent, owner)

    assert task.owner == owner
    assert task.parent == parent
    assert task.skip_task is False

    task.skip = True
    assert task.skip_task is True


@patch("pipeline_runner.lib.task_types.task.Task.add")
def test_suitetask_dependency_registration(mock_task_add: MagicMock) -> None:
    """Verify that _deps are registered in Task during __init__."""

    class TaskWithDeps(ConcreteTask):
        pass

    TaskWithDeps._deps = ["MockDep"]

    owner = MockOwner()
    TaskWithDeps(MagicMock(), owner)

    mock_task_add.assert_called_once_with("MockDep")


## Printer Integration


@patch("pipeline_runner.lib.task_types.suite_task.Printer")
def test_suitetask_printer_attachment(mock_printer_class: MagicMock) -> None:
    """Verify Printer is instantiated with the correct context."""
    owner = MockOwner()
    parent = MagicMock()
    task = ConcreteTask(parent, owner)

    mock_printer_class.assert_called_once_with(parent, task)
