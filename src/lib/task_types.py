import threading
import os
import sys
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
from shlex import split as shlex_split

from lib.printer import Printer
from lib.exceptions import TaskError
from lib.types import typename


if TYPE_CHECKING:
    from types import Stage
    from task_types import PipelineSuite


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
            task_name = Task.get_key(task)
            print(f"Registring {task_name}")
            Task._registry[task_name] = task
        return

    # 2. Add a dependency from the registry
    @staticmethod
    def add(key):
        """Adds a depndency only if it exists in the registry"""
        key = Task.get_key(key)

        # 1. Determine if the key exists in the registry
        if not Task.exists(key):
            raise ValueError(f"Dependency {key} does not exist in the registry")

        # 2. Determine if the key has been initialized
        if Task.initialized(key):
            print(f"Fetching task: {key}")
            # Return the key if already initialized
            return Task._loaded[key]

        # 3. Initialize the key
        print(f"Initializing {key}")
        dep = Task._registry[key]
        task = dep(Task._owner, owner=Task._owner)
        Task._loaded[key] = task
        return task

    @staticmethod
    def exists(key):
        key = Task.get_key(key)
        return key in Task._registry.keys()

    @staticmethod
    def initialized(key):
        """Returns the initialized object"""
        key = Task.get_key(key)
        return key in Task._completed.keys()

    # 3. Run the task
    @staticmethod
    def run(key):
        """Runs a task from the registry"""
        key = Task.get_key(key)

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
    def get_key(key):
        """Convert a raw class to a key"""
        if type(key) is not str:
            key = key.__name__
        return key

    @staticmethod
    def completed(key):
        """Returns a bool if the task has been completed or not"""
        key = Task.get_key(key)
        return key in Task._completed.keys()

    @staticmethod
    def get_owner():
        return Task._owner


class SuiteTask(ABC):
    _owner: "PipelineSuite"
    _parent: "SuiteTask"
    _global_counter: int = 0
    _id: int
    _cwd: Path | None
    message: str
    name: str
    printer: Printer
    skip: bool = False
    _can_skip: bool = True
    _stage: "Stage"
    _initialized = False
    _deps = []
    complete: bool = False
    skip_list: List = []

    def __init__(
        self,
        parent,
        owner: "TDDSuite",
        cwd: Path | str | None = None,
        attach_printer: bool = True,
    ):
        self.add_deps()

        from lib.task_types import SuiteTask

        if owner is None and not SuiteTask._initialized:
            raise ValueError("Owner is not set")
        if parent is None:
            raise ValueError("Parent is not set")
        # print(kwargs, self.__class__.__name__)
        # if kwargs and self.__class__.__name__ in self.get_arg("skip_list"):
        #     self.skip = True
        #     return
        SuiteTask._initialized = True

        if cwd is not None:
            cwd = Path(cwd)
        if cwd is None and parent is not None:
            try:
                cwd = parent.get_cwd()
            except:
                pass
        if cwd is None:
            cwd = os.getcwd()
        self._cwd = cwd

        self._owner = owner
        self._parent = parent
        self.args = self._owner.args

        from lib.task_types import SuiteTask

        if not isinstance(self, SuiteSubTask):
            self._id = SuiteTask._global_counter
            SuiteTask._global_counter += 1
        if attach_printer:
            self.attach_printer(parent)

    def initialize_deps():
        for dep in self._deps:
            dep_name = dep.__name__
            if not Task.initalized(dep_name):
                Task.load(dep)

    def add_deps(self):
        for dep in self._deps:
            Task.add(dep)

    def run_deps(self):
        for dep in self._deps:
            Task.run(dep)

    def skip_task(self):
        if self.skip:
            return True

        return False

    def get_arg(self, arg):
        return self._owner.args.get(arg)

    def get_path(self, component: str, path: Path | str | None = None) -> Path:
        if path is not None:
            return self._owner.paths.get(component) / Path(path)
        return self._owner.paths.get(component)

    def do_dry_run(self):
        do_dry_run = self.args.get("dry_run", False)
        return do_dry_run

    def attach_printer(self, parent):
        self.printer = Printer(parent, self)

    @staticmethod
    def inc_count():
        SuiteSubTask._global_counter += 1

    @staticmethod
    def get_count():
        return SuiteTask._global_counter

    def dump_print_queue(self):
        """Standardized message logger."""
        self.printer.dump()

    def print(self, *args, **kwargs):
        """Standardized message logger."""
        self.printer.print(*args, **kwargs)

    def msg(self, *args, **kwargs):
        """Standardized message logger."""
        self.printer.msg(*args, **kwargs)

    @abstractmethod
    def _run(self):
        pass

    def dry_run(self):
        self.msg(self.name)
        if self.skip_task():
            self.print("Skipping")
            return True
        return self.do_dry_run()

    def disable_dry_run(self):
        def func():
            self.print(f"Dry run disabled for {type(self).__name__}")
            return False

        # the Printer object has not been initialized yet
        print(f"Disabling dry run for {typename(self)}")

        self.do_dry_run = func

    def run(self):
        dry_run = self.dry_run()
        if dry_run:
            return dry_run
        else:
            return self._run()

    def fail(self, *args, critical: bool = False, **kwargs):
        """Helper to raise the state-aware exception."""

        raise TaskError(self, critical=critical, *args, **kwargs)

    def sh(
        self,
        cmd: str,
        cwd: Path | None = None,
        handle_exception=True,
        dry_run=None,
        check=True,
        shell=True,
        shlex=False,
        disabled=False,
    ):
        """Helper to run shell commands within the project context."""
        if shlex:
            cmd = shlex_split(cmd)
            shell = False

        if cwd is not None:
            self.print(f"  [CWD] {cwd}")
        if disabled:
            self.msg(f"[DISABLED]  [EXEC] {cmd}")
            return

        cwd = str(cwd or os.getcwd())
        self.msg(f"  [EXEC] {cmd}")
        if self.do_dry_run() and dry_run is not False:
            return

        try:
            return subprocess.run(cmd, shell=shell, check=check, cwd=cwd)
        except subprocess.CalledProcessError as e:
            if handle_exception:
                self.fail(e)
            raise Exception(e)

    def sh_thread(self, cmd: str, cwd: Path | None = None):
        """
        Runs shell commands, streams output to CLI in real-time,
        and captures it for later analysis.
        """
        self.msg(f"  [EXEC] {cmd}")
        if self.do_dry_run:
            return

        # Store captured output
        self.last_stdout = []
        self.last_stderr = []

        # Start the process with piped outputs
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(cwd or self.get_path("root")),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        def stream_pipe(pipe, relay, accumulator):
            """Reads from pipe, writes to relay (stdout/err), and saves to list."""
            for line in iter(pipe.readline, ""):
                if line:
                    accumulator.append(line)
                    relay.write(line)
                    relay.flush()
            pipe.close()

        # Use threads to prevent the pipes from clogging (which causes deadlocks)
        t1 = threading.Thread(
            target=stream_pipe, args=(process.stdout, sys.stdout, self.last_stdout)
        )
        t2 = threading.Thread(
            target=stream_pipe, args=(process.stderr, sys.stderr, self.last_stderr)
        )

        t1.start()
        t2.start()

        # Wait for completion
        exit_code = process.wait()
        t1.join()
        t2.join()

        if exit_code != 0:
            self.fail(f"\n[ERROR] Command failed with code {exit_code}", code=exit_code)

        return ["".join(self.last_stdout), "".join(self.last_stdout)]

    def get_cwd(self):
        return self._cwd

    def get_id(self):
        return self._id

    def get_stage(self):
        return self._stage


class SuiteSubTask(SuiteTask):
    _owner: "TDDSuite"
    _parent: SuiteTask

    _sub_counter: dict[int] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, attach_printer=False, **kwargs)

        if SuiteTask._global_counter not in SuiteSubTask._sub_counter.keys():
            SuiteSubTask._sub_counter[SuiteTask._global_counter] = 0

        self._id = (SuiteTask._global_counter, SuiteSubTask._sub_counter)

        self.attach_printer(self._owner)

    def msg(self, *args, **kwargs):
        """Standardized message logger."""
        SuiteSubTask.inc_count()

        self._parent.msg(*args, **kwargs)

    @staticmethod
    def inc_count():

        print(SuiteSubTask._sub_counter)
        SuiteSubTask._sub_counter[SuiteTask._global_counter] += 1

    @staticmethod
    def get_count():
        return SuiteSubTask._sub_counter
