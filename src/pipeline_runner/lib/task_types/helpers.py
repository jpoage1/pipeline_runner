"""Pure helper functions for task lifecycle management."""

from collections.abc import Callable
from typing import Any

from pipeline_runner.lib.types import TaskStatus


def get_task_name(task_input: Any) -> str:
    """Pure function to resolve a task key."""
    if isinstance(task_input, str):
        return task_input
    return getattr(task_input, "__name__", str(task_input))


def get_task_status(
    name: str,
    registry: dict[str, type[Any]],
    loaded: dict[str, Any],
    completed: dict[str, Any],
) -> TaskStatus:
    """Determine the lifecycle status of a task."""
    if name not in registry:
        return TaskStatus.MISSING
    if name in completed:
        return TaskStatus.COMPLETED
    if name in loaded:
        return TaskStatus.LOADED
    return TaskStatus.REGISTERED


def prepare_task_init(
    name: str,
    registry: dict[str, type[Any]],
    owner: Any,
) -> tuple[Callable[..., Any] | None, tuple[Any, ...] | None]:
    """Prepare the components needed for task instantiation.

    Returns (callable, args_tuple).
    """
    if name not in registry:
        return None, None
    dep_class = registry[name]
    init_args = (owner, owner)
    return dep_class, init_args


def validate_task_list(
    task_list: list[type[Any]],
) -> list[tuple[str, Callable[..., Any]]]:
    """Validate and format a list of task classes for registration.

    Returns a list of (name, class_obj) tuples.
    """
    validated: list[tuple[str, Callable[..., Any]]] = []
    for task in task_list:
        name = getattr(task, "__name__", None)
        if not name or not callable(task):
            continue
        validated.append((name, task))
    return validated


def format_task_result(name: str, result: Any) -> dict[str, Any]:
    """Format a task result for storage."""
    return {name: result}
