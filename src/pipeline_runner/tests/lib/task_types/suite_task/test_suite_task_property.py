import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from pipeline_runner.lib.task_types.suite_task import SuiteTask


# Concrete implementation for testing abstract class
class ConcreteTask(SuiteTask):
    def _run(self):
        return "success"


class MockOwner:
    def __init__(self):
        self.args = {"dry_run": False}
        self.paths = {"root": Path("/tmp")}


@pytest.fixture(autouse=True)
def reset_suite_task_state():
    """Resets the SuiteTask class-level state before every test."""
    SuiteTask._global_counter = 0
    SuiteTask._initialized = False
    # Use patch to prevent Task registry side effects during SuiteTask init
    with patch("pipeline_runner.lib.task_types.task.Task.add"):
        yield


## Initialization & Validation Tests


def test_suitetask_init_raises_on_missing_args():
    """Verify ValueError when owner or parent is missing."""
    with pytest.raises(ValueError, match="Owner is not set"):
        ConcreteTask(parent=MagicMock(), owner=None)

    with pytest.raises(ValueError, match="Parent is not set"):
        ConcreteTask(parent=None, owner=MagicMock())


def test_suitetask_identity_increment():
    """Verify that each task gets a unique incrementing ID."""
    owner = MockOwner()
    parent = MagicMock()

    t1 = ConcreteTask(parent, owner)
    t2 = ConcreteTask(parent, owner)

    assert t1.id == 0
    assert t2.id == 1
    assert SuiteTask._global_counter == 2


## CWD Inheritance Logic


def test_suitetask_cwd_inheritance():
    """Verify CWD is pulled from parent if not provided."""
    owner = MockOwner()
    parent = MagicMock()
    # Mock parent having a cwd property
    parent.cwd = Path("/inherited/path")

    task = ConcreteTask(parent, owner)
    assert task.cwd == Path("/inherited/path")


def test_suitetask_cwd_fallback_to_os_getcwd():
    """Verify fallback to system getcwd if parent lacks cwd."""
    owner = MockOwner()
    parent = MagicMock()
    # Delete cwd attribute if it exists on the mock
    if hasattr(parent, "cwd"):
        del parent.cwd

    task = ConcreteTask(parent, owner, cwd=None)
    assert task.cwd == Path(os.getcwd())


def test_suitetask_explicit_cwd():
    """Verify explicit CWD overrides all inheritance."""
    owner = MockOwner()
    explicit_path = Path("/explicit/path")
    task = ConcreteTask(MagicMock(), owner, cwd=explicit_path)
    assert task.cwd == explicit_path


## Property & Logic Tests


def test_suitetask_properties():
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
def test_suitetask_dependency_registration(mock_task_add):
    """Verify that _deps are registered in Task during __init__."""

    class MockDep:
        pass

    class TaskWithDeps(ConcreteTask):
        _deps = [MockDep]

    owner = MockOwner()
    TaskWithDeps(MagicMock(), owner)

    mock_task_add.assert_called_once_with(MockDep)


## Printer Integration


@patch("pipeline_runner.lib.printer.Printer")
def test_suitetask_printer_attachment(mock_printer_class):
    """Verify Printer is instantiated with the correct context."""
    owner = MockOwner()
    parent = MagicMock()
    task = ConcreteTask(parent, owner, attach_printer=True)

    mock_printer_class.assert_called_once_with(parent, task)
