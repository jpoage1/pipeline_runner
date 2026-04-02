from .helpers import get_task_name, prepare_task_init, get_task_status
from pipeline_runner.lib.types import TaskStatus


class Task:
    _initialized: bool = False
    _registry: dict = {}
    _loaded: dict = {}
    _completed: dict = {}
    _owner = None

    # 1. The owner initializes the class
    @staticmethod
    def __init__(owner, task_list):
        if Task._initialized:
            return
        Task._owner = owner
        for task in task_list:
            # task_name = get_task_name(task)
            task_name = get_task_name(task)
            print(f"Registring {task_name}")
            Task._registry[task_name] = task
        return

    @staticmethod
    def add(key):
        name = get_task_name(key)
        status = get_task_status(name, Task._registry, Task._loaded, Task._completed)

        if status == TaskStatus.MISSING:
            raise ValueError(f"Dependency {name} does not exist")
        if status in [TaskStatus.LOADED, TaskStatus.COMPLETED]:
            return Task._loaded[name]

        dep_class, args = prepare_task_init(name, Task._registry, Task._owner)
        task_instance = dep_class(*args)

        Task._loaded[name] = task_instance
        return task_instance

    @staticmethod
    def exists(key):
        name = get_task_name(key)
        return name in Task._registry

    @staticmethod
    def initialized(key):
        """Returns the initialized object"""
        key = get_task_name(key)
        return key in Task._completed.keys()

    # 3. Run the task
    @staticmethod
    def run(key):
        """Runs a task from the registry"""
        key = get_task_name(key)

        # 1. Determine if the task has already ran
        if Task.completed(key):
            print(f"fetching result for {key}")
            return Task._completed[key]

        # 2. Initialize the dependency
        # This is harmless if already initialized
        # due to internal checks
        task = Task.add(key)  # Also provides the object

        # 3. Run the task and store its result
        print(f"Running task: {key}")
        result = task.run()
        Task._completed[key] = result

        return result

    @staticmethod
    def get_task_name(key):
        """Convert a raw class to a key"""
        if type(key) is not str:
            key = key.__name__
        return key

    @staticmethod
    def completed(key):
        """Returns a bool if the task has been completed or not"""
        key = get_task_name(key)
        return key in Task._completed.keys()

    @staticmethod
    def get_owner():
        return Task._owner
