"""Static registry-based task lifecycle management."""

from collections.abc import Sequence
from typing import Any, ClassVar

from pipeline_runner.lib.types import TaskStatus

from .helpers import get_task_name, get_task_status, prepare_task_init


class Task:
    """Manages task registration, instantiation, and execution."""

    _initialized: bool = False
    _registry: ClassVar[dict[str, type[Any]]] = {}
    _loaded: ClassVar[dict[str, Any]] = {}
    _completed: ClassVar[dict[str, Any]] = {}
    _owner: Any = None

    @staticmethod
    def __init__(owner: Any, task_list: Sequence[Any] | None = None) -> None:
        """Initialize the task registry with a list of task classes."""
        if Task._initialized:
            return
        Task._owner = owner
        for task in task_list or ():
            task_name = get_task_name(task)
            Task._registry[task_name] = task

    @staticmethod
    def add(key: Any) -> Any:
        """Register and instantiate a task, returning the cached instance."""
        name = get_task_name(key)
        status = get_task_status(name, Task._registry, Task._loaded, Task._completed)

        if status == TaskStatus.MISSING:
            msg = f"Dependency {name} does not exist"
            raise ValueError(msg)
        if status in [TaskStatus.LOADED, TaskStatus.COMPLETED]:
            return Task._loaded[name]

        dep_class, args = prepare_task_init(name, Task._registry, Task._owner)
        if dep_class is None or args is None:
            msg = f"Dependency {name} does not exist"
            raise ValueError(msg)
        task_instance = dep_class(*args)

        Task._loaded[name] = task_instance
        return task_instance

    @staticmethod
    def exists(key: Any) -> bool:
        """Check if a task exists in the registry."""
        name = get_task_name(key)
        return name in Task._registry

    @staticmethod
    def initialized(key: Any) -> bool:
        """Check if a task has been initialized."""
        key = get_task_name(key)
        return key in Task._completed

    @staticmethod
    def run(key: Any) -> Any:
        """Run a task from the registry, returning the cached or fresh result."""
        key = get_task_name(key)

        if Task.completed(key):
            return Task._completed[key]

        task = Task.add(key)
        result = task.run()
        Task._completed[key] = result

        return result

    @staticmethod
    def get_task_name(key: Any) -> str:
        """Convert a raw class to a key."""
        if type(key) is not str:
            key = key.__name__
        return key

    @staticmethod
    def completed(key: Any) -> bool:
        """Return whether a task has been completed."""
        key = get_task_name(key)
        return key in Task._completed

    @staticmethod
    def get_owner() -> Any:
        """Return the current owner of the task registry."""
        return Task._owner
