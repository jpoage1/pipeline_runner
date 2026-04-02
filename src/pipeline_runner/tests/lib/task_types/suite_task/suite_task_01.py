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
def reset_suite_task():
    """Resets the SuiteTask class-level state before every test."""
    SuiteTask._global_counter = 0
    SuiteTask._initialized = False
    # Also reset Task registry mock if necessary
    with patch("pipeline_runner.lib.task_types.Task.add"):
        yield


## Initialization and State Tests


def test_suitetask_init_requires_owner_and_parent():
    """Verify that None values for owner or parent raise ValueError."""
    with pytest.raises(ValueError, match="Owner is not set"):
        ConcreteTask(parent=MagicMock(), owner=None)

    with pytest.raises(ValueError, match="Parent is not set"):
        ConcreteTask(parent=None, owner=MagicMock())


def test_suitetask_id_increment():
    """Verify that each new task instance increments the global counter."""
    owner = MockOwner()
    parent = MagicMock()

    t1 = ConcreteTask(parent, owner)
    t2 = ConcreteTask(parent, owner)

    assert t1._id == 0
    assert t2._id == 1
    assert SuiteTask.get_count() == 2


def test_suitetask_cwd_inheritance():
    """Verify that CWD is inherited from parent if not explicitly provided."""
    owner = MockOwner()
    parent = MagicMock()
    parent.get_cwd.return_value = Path("/inherited/path")

    task = ConcreteTask(parent, owner)
    assert task._cwd == Path("/inherited/path")


def test_suitetask_cwd_default_to_getcwd():
    """Verify fallback to os.getcwd() if no parent CWD is available."""
    owner = MockOwner()
    parent = MagicMock()
    parent.get_cwd.side_effect = Exception("No CWD")

    task = ConcreteTask(parent, owner, cwd=None)
    assert task._cwd == Path(os.getcwd())


## Dependency Integration


@patch("pipeline_runner.lib.task_types.Task.add")
def test_add_deps_called_on_init(mock_task_add):
    """Verify that dependencies are registered during initialization."""

    class DepTask:
        pass

    class TaskWithDeps(ConcreteTask):
        _deps = [DepTask]

    owner = MockOwner()
    TaskWithDeps(MagicMock(), owner)

    mock_task_add.assert_called_once_with(DepTask)


## Logic and Properties


def test_skip_task_property():
    """Verify the skip_task property logic."""
    owner = MockOwner()
    task = ConcreteTask(MagicMock(), owner)

    assert task.skip_task is False
    task.skip = True
    assert task.skip_task is True


def test_get_arg_utility():
    """Verify retrieval of arguments from the owner object."""
    owner = MockOwner()
    owner.args["test_key"] = "test_value"
    task = ConcreteTask(MagicMock(), owner)

    assert task.get_arg("test_key") == "test_value"
    assert task.get_arg("non_existent") is None


def test_get_path_resolution():
    """Verify path resolution and joining logic."""
    owner = MockOwner()
    owner.paths["bin"] = Path("/usr/bin")
    task = ConcreteTask(MagicMock(), owner)

    # Base path
    assert task.get_path("bin") == Path("/usr/bin")
    # Joined path
    assert task.get_path("bin", "python") == Path("/usr/bin/python")


## Printer Integration


@patch("pipeline_runner.lib.printer.Printer")
def test_attach_printer_on_init(mock_printer_class):
    """Verify that a Printer instance is attached during initialization."""
    owner = MockOwner()
    parent = MagicMock()

    task = ConcreteTask(parent, owner, attach_printer=True)

    mock_printer_class.assert_called_once_with(parent, task)
    assert hasattr(task, "printer")


def test_proxy_methods_to_printer():
    """Verify that suite task print/msg methods delegate to the printer."""
    owner = MockOwner()
    task = ConcreteTask(MagicMock(), owner)
    task.printer = MagicMock()

    task.print("hello", key="value")
    task.printer.print.assert_called_once_with("hello", key="value")

    task.msg("system message")
    task.printer.msg.assert_called_once_with("system message")
