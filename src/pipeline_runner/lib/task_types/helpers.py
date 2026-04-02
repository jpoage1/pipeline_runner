from pipeline_runner.lib.types import TaskStatus


def get_task_name(task_input):
    """Pure function to resolve a task key."""
    if isinstance(task_input, str):
        return task_input
    return getattr(task_input, "__name__", str(task_input))


def get_task_status(name, registry, loaded, completed):
    """
    Purely determines the lifecycle status of a task.
    """
    if name not in registry:
        return TaskStatus.MISSING
    if name in completed:
        return TaskStatus.COMPLETED
    if name in loaded:
        return TaskStatus.LOADED
    return TaskStatus.REGISTERED


def prepare_task_init(name, registry, owner):
    """
    Purely prepares the components needed for instantiation.
    Returns (callable, args_tuple)
    """
    if name not in registry:
        return None, None

    dep_class = registry[name]
    # We return the arguments as a tuple to maintain positional integrity
    # as defined in your requirement: task = dep(owner, owner)
    init_args = (owner, owner)

    return dep_class, init_args


def validate_task_list(task_list):
    """
    Purely validates and formats a list of task classes for registration.
    Returns a list of (name, class_obj) tuples.
    """
    validated = []
    for task in task_list:
        name = getattr(task, "__name__", None)
        if not name or not callable(task):
            # Logic can be expanded here to handle or skip malformed tasks
            continue
        validated.append((name, task))
    return validated


def format_task_result(name, result):
    """
    Purely formats a task result for storage.
    """
    return {name: result}
