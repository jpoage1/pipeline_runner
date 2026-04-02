import threading
import os
import sys
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Any, Union, Optional
from shlex import split as shlex_split

from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.exceptions import TaskError
from pipeline_runner.lib.types import typename, ShellOutput, Stage
from pipeline_runner.lib.task_types.task import Task
from pipeline_runner.lib.task_types.suite_task_helpers import (
    prepare_command,
    resolve_cwd,
    should_skip,
)


if TYPE_CHECKING:
    from pipeline_runner.core.suite import PipelineSuite


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
    _last_run: ShellOutput = ShellOutput()

    def __init__(
        self,
        parent,
        owner: Optional["PipelineSuite"],
        cwd: Path | str | None = None,
        attach_printer: bool = True,
    ):
        self.add_deps()

        if owner is None and not type(self)._initialized:
            raise ValueError("Owner is not set")
        if parent is None:
            raise ValueError("Parent is not set")
        # print(kwargs, self.__class__.__name__)
        # if kwargs and self.__class__.__name__ in self.get_arg("skip_list"):
        #     self.skip = True
        #     return
        type(self)._initialized = True

        if cwd is not None:
            cwd = Path(cwd)
        if cwd is None and parent is not None:
            try:
                cwd = parent.cwd
            except (OSError, ValueError):
                pass
        if cwd is None:
            cwd = os.getcwd()

        self._cwd = Path(cwd)

        self._owner = owner
        self._parent = parent
        self.args = self._owner.args

        from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask

        if not isinstance(self, SuiteSubTask):
            self._id = SuiteTask._global_counter
            SuiteTask._global_counter += 1
        if attach_printer:
            self.attach_printer(parent)

    def add_deps(self) -> None:
        for dep in self._deps:
            Task.add(dep)

    def run_deps(self) -> None:
        for dep in self._deps:
            Task.run(dep)

    @property
    def skip_task(self) -> bool:
        if self.skip:
            return True

        return False

    def get_arg(self, arg):
        return self._owner.args.get(arg)

    def get_path(self, component: str, path: Path | str | None = None) -> Path:
        if path is not None:
            return self._owner.paths.get(component) / Path(path)
        return self._owner.paths.get(component)

    def do_dry_run(self) -> bool:
        do_dry_run = self.args.get("dry_run", False)
        return do_dry_run

    def attach_printer(self, parent) -> None:
        self.printer = Printer(parent, self)

    @staticmethod
    def inc_count() -> None:
        SuiteTask._global_counter += 1

    @staticmethod
    def get_count() -> int:
        return SuiteTask._global_counter

    def dump_print_queue(self) -> None:
        """Standardized message logger."""
        self.printer.dump()

    def print(self, *args, **kwargs) -> None:
        """Standardized message logger."""
        self.printer.print(*args, **kwargs)

    def msg(self, *args, **kwargs) -> None:
        """Standardized message logger."""
        self.printer.msg(*args, **kwargs)

    @abstractmethod
    def _run(self) -> bool:
        pass

    def dry_run(self) -> bool:
        self.msg(self.name)
        if self.skip_task:
            self.print("Skipping")
            return True
        return self.do_dry_run()

    def disable_dry_run(self) -> None:
        def func():
            self.print(f"Dry run disabled for {type(self).__name__}")
            return False

        # the Printer object has not been initialized yet
        print(f"Disabling dry run for {typename(self)}")

        self.do_dry_run = func

    def run(self) -> bool:
        # self.run_deps()
        dry_run = self.dry_run()
        if dry_run:
            return dry_run
        return self._run()

    def fail(self, *args, critical: bool = False, **kwargs) -> None:
        """Helper to raise the state-aware exception."""

        raise TaskError(self, critical=critical, *args, **kwargs)

    def sh(
        self,
        cmd: Union[str, List[str]],
        cwd: Path | None = None,
        handle_exception=True,
        dry_run=None,
        check=True,
        shell=True,
        shlex=False,
        disabled=False,
    ) -> ShellOutput:
        """Helper to run shell commands within the project context."""
        if shlex:
            shell = False
            if isinstance(cmd, str):
                cmd = shlex_split(cmd)

        if cwd is not None:
            self.print(f"  [CWD] {cwd}")

        if disabled:
            self.msg(f"[DISABLED]  [EXEC] {cmd}")
            return ShellOutput()

        if self.do_dry_run() and dry_run is not False:
            self.msg(f"  [DRY-RUN] [EXEC] {cmd}")
            return ShellOutput()

        working_dir: str = str(cwd or os.getcwd())
        self.msg(f"  [EXEC] {cmd}")

        try:
            result = subprocess.run(cmd, shell=shell, check=check, cwd=working_dir)
            return ShellOutput.from_subprocess(result)
        except subprocess.CalledProcessError as e:
            if handle_exception:
                self.fail(e)
            raise ShellOutput.wrap_exception(e) from e

    # def sh(
    #     self,
    #     cmd: str,
    #     cwd: Path | None = None,
    #     handle_exception=True,
    #     dry_run=None,  # This is the force_run parameter
    #     check=True,
    #     shell=True,
    #     shlex=False,
    #     disabled=False,
    # ) -> ShellOutput:
    #     # 1. Prepare Command
    #     exec_cmd, exec_shell = prepare_command(cmd, shell, shlex)

    #     # 2. Resolve Pathing
    #     working_dir = resolve_cwd(cwd)
    #     if cwd:
    #         self.print(f"  [CWD] {working_dir}")

    #     # 3. Decision Logic
    #     if should_skip(disabled, self.do_dry_run(), dry_run) is True:
    #         status = "[DISABLED]" if disabled else "[DRY-RUN]"
    #         self.msg(f"{status}  [EXEC] {cmd}")
    #         return None

    #     # 4. Execution
    #     self.msg(f"  [EXEC] {cmd}")
    #     try:
    #         result = subprocess.run(
    #             exec_cmd, shell=exec_shell, check=check, cwd=working_dir
    #         )
    #         if result:
    #             return result
    #     except subprocess.CalledProcessError as e:
    #         if handle_exception:
    #             self.fail(e)
    #         raise Exception(e) from e
    #     return None

    def sh_thread(self, cmd: str, cwd: Path | None = None) -> ShellOutput:
        """
        Runs shell commands, streams output to CLI in real-time,
        and captures it for later analysis.
        """
        self.msg(f"  [EXEC] {cmd}")
        if self.do_dry_run():
            return ShellOutput()

        # Store captured output
        self._last_run.stdout = []
        self._last_run.stderr = []

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
            target=stream_pipe, args=(process.stdout, sys.stdout, self._last_run.stdout)
        )
        t2 = threading.Thread(
            target=stream_pipe, args=(process.stderr, sys.stderr, self._last_run.stderr)
        )

        t1.start()
        t2.start()

        # Wait for completion
        exit_code = process.wait()
        t1.join()
        t2.join()

        if exit_code != 0:
            self.fail(f"\n[ERROR] Command failed with code {exit_code}", code=exit_code)

        return ShellOutput(
            stdout=["".join(self._last_run.stdout)],
            stderr=["".join(self._last_run.stderr)],
        )

    # Properties

    @property
    def owner(self) -> Any:
        return self._owner

    @property
    def parent(self) -> "SuiteTask":
        return self._parent

    @property
    def cwd(self) -> str:
        try:
            return str(self._cwd or os.getcwd())
        except AttributeError:
            return os.getcwd()

    @property
    def id(self) -> int:
        return self._id

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def last_run(self) -> ShellOutput:
        return self._last_run

    # Legacy getters

    def get_id(self) -> int:
        return self.id

    def get_stage(self) -> Stage:
        return self.stage

    def get_cwd(self) -> str:
        return self.cwd
