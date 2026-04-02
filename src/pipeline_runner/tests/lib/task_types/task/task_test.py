import pytest
from unittest.mock import MagicMock, patch
from pipeline_runner.lib.task_types.task import Task
from pipeline_runner.lib.types import TaskStatus


class MockTaskClass:
    def __init__(self, parent, owner=None):
        self.parent = parent
        self.owner = owner

    def run(self):
        return "task_success"


@pytest.fixture(autouse=True)
def reset_task_state():
    """Resets the Task class-level state before every test."""
    Task._initialized = False
    Task._registry = {}
    Task._loaded = {}
    Task._completed = {}
    Task._owner = None


## Registry and Initialization Tests


def test_task_init_registration():
    """Verify Task.__init__ populates the registry and sets the owner."""
    owner = "TestOwner"
    tasks = [MockTaskClass]

    Task.__init__(owner, tasks)

    assert Task._owner == owner
    assert "MockTaskClass" in Task._registry
    assert Task._registry["MockTaskClass"] == MockTaskClass


def test_task_init_singleton_lock():
    """Verify Task.__init__ does not overwrite state if already initialized."""
    Task._initialized = True
    Task._owner = "OriginalOwner"

    Task.__init__("NewOwner", [])
    assert Task._owner == "OriginalOwner"


## Dependency Management (add)


def test_add_missing_task_raises_error():
    """Verify ValueError when trying to add a task not in the registry."""
    with pytest.raises(ValueError, match="Dependency MissingTask does not exist"):
        Task.add("MissingTask")


def test_add_new_task_initialization():
    """Verify add() instantiates a task and stores it in _loaded."""
    Task._owner = "Owner"
    Task._registry["MockTaskClass"] = MockTaskClass

    instance = Task.add(MockTaskClass)

    assert isinstance(instance, MockTaskClass)
    assert Task._loaded["MockTaskClass"] == instance
    assert instance.parent == "Owner"
    assert instance.owner == "Owner"


def test_add_existing_task_returns_cached_instance():
    mock_instance = MagicMock()
    # Populate the registry so get_task_status doesn't return MISSING
    Task._registry["MockTaskClass"] = MagicMock()
    Task._loaded["MockTaskClass"] = mock_instance

    with patch(
        "pipeline_runner.lib.task_types.helpers.get_task_status",
        return_value=TaskStatus.LOADED,
    ):
        result = Task.add("MockTaskClass")
        assert result == mock_instance


## Execution Orchestration (run)


def test_run_executes_and_stores_result():
    """Verify run() executes a task and caches the result in _completed."""
    Task._owner = "Owner"
    Task._registry["MockTaskClass"] = MockTaskClass

    result = Task.run(MockTaskClass)

    assert result == "task_success"
    assert Task._completed["MockTaskClass"] == "task_success"


def test_run_returns_cached_result():
    """Verify run() fetches result from _completed without re-running."""
    Task._completed["MockTaskClass"] = "cached_success"

    with patch.object(Task, "add") as mock_add:
        result = Task.run("MockTaskClass")

        assert result == "cached_success"
        mock_add.assert_not_called()


## Helper Method Tests


def test_exists_and_completed_checks():
    """Verify boolean helper methods correctly query state."""
    Task._registry["ExistTask"] = MockTaskClass
    Task._completed["DoneTask"] = True

    assert Task.exists("ExistTask") is True
    assert Task.exists("NonExistent") is False
    assert Task.completed("DoneTask") is True
    assert Task.completed("ExistTask") is False


def test_get_task_name_resolution():
    """Verify resolution of names from both strings and classes."""
    assert Task.get_task_name(MockTaskClass) == "MockTaskClass"
    assert Task.get_task_name("StaticName") == "StaticName"
