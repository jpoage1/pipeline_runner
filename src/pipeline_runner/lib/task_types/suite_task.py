import threading
import os
import sys
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Union, Optional
from shlex import split as shlex_split

from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.exceptions import TaskError
from pipeline_runner.lib.types import typename, ShellOutput, Stage, TaskResult
from pipeline_runner.lib.task_types.task import Task


if TYPE_CHECKING:
    from pipeline_runner.core.suite import PipelineSuite


class SuiteTask(ABC):
    # Optional, not "PipelineSuite"/"SuiteTask" outright: __init__ accepts
    # owner=None (guarded by the _initialized check, not unconditionally
    # rejected) and assigns it straight through - the previous non-Optional
    # annotations described the common case, not what's actually possible.
    _owner: Optional["PipelineSuite"]
    _parent: Optional["SuiteTask"]
    _global_counter: int = 0
    # int for a regular SuiteTask; SuiteSubTask uses a (global, sub) tuple
    # to distinguish sub-tasks within the same parent - real, deliberate
    # usage on both sides, not one "correct" case and one bug.
    _id: int | tuple[int, int]
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
        parent: Optional["SuiteTask"],
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
        self.args = self._require_owner().args

        from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask

        if not isinstance(self, SuiteSubTask):
            self._id = SuiteTask._global_counter
            SuiteTask._global_counter += 1
        if attach_printer:
            self.attach_printer(parent)

    def add_deps(self) -> None:
        for dep in self._deps:
            Task.add(dep)

    def run_deps(self) -> list[str]:
        failed = []
        for dep in self._deps:
            result = Task.run(dep)
            if result is False or result is TaskResult.SKIPPED:
                failed.append(Task.get_task_name(dep))
        return failed

    @property
    def skip_task(self) -> bool:
        if self.skip:
            return True

        return False

    def _require_owner(self) -> "PipelineSuite":
        """Narrows self._owner to non-None, raising clearly instead of
        letting a bare AttributeError surface later on a None access."""
        if self._owner is None:
            raise ValueError(f"{typename(self)} has no owner set")
        return self._owner

    def get_arg(self, arg):
        return self._require_owner().args.get(arg)

    def get_path(self, component: str, path: Path | str | None = None) -> Path:
        base = self._require_owner().paths[component]
        if path is not None:
            return base / Path(path)
        return base

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
    def _run(self) -> bool | str | None | ShellOutput | TaskResult:
        """Task result: True/False (or a str/None a subclass treats as a
        completion signal) for a plain pass/fail check, or a ShellOutput
        for a task whose whole point is exposing what a command produced
        (e.g. an integration test asserting on stdout/returncode). This
        Union is the real, observed set of return values across the
        codebase's own tasks and tests - not a placeholder for "anything"."""
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

    def run(self) -> bool | str | None | ShellOutput | TaskResult:
        # self.run_deps()
        dry_run = self.dry_run()
        if dry_run:
            return dry_run
        failed_deps = self.run_deps()
        if failed_deps:
            self.print(
                "Skipping because dependencies did not pass: " + ", ".join(failed_deps)
            )
            return TaskResult.SKIPPED
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
            # capture_output=True (not text=True): ShellOutput.from_subprocess
            # already handles bytes with tolerant decoding (see
            # test_shell_output_handles_malformed_encoding) - forcing text
            # mode here would make subprocess.run itself raise on invalid
            # UTF-8 instead of going through that tested path. Without
            # capture_output, stdout/stderr were never actually collected -
            # every self.sh() caller silently got empty output.
            result = subprocess.run(
                cmd, shell=shell, check=check, cwd=working_dir, capture_output=True
            )
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
    def owner(self) -> Optional["PipelineSuite"]:
        return self._owner

    @property
    def parent(self) -> Optional["SuiteTask"]:
        return self._parent

    @property
    def cwd(self) -> str:
        try:
            return str(self._cwd or os.getcwd())
        except AttributeError:
            return os.getcwd()

    @property
    def id(self) -> int | tuple[int, int]:
        return self._id

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def last_run(self) -> ShellOutput:
        return self._last_run

    # Legacy getters

    def get_id(self) -> int | tuple[int, int]:
        return self.id

    def get_stage(self) -> Stage:
        return self.stage

    def get_cwd(self) -> str:
        return self.cwd
