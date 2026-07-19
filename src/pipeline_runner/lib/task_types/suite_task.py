"""Abstract base class for all pipeline tasks with shell execution support."""

import contextlib
import subprocess
import sys
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from shlex import split as shlex_split
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pipeline_runner.lib.exceptions import TaskError
from pipeline_runner.lib.printer import Printer
from pipeline_runner.lib.task_types.task import Task
from pipeline_runner.lib.types import ShellOutput, Stage, TaskResult, typename

if TYPE_CHECKING:
    from pipeline_runner.core.suite import PipelineSuite


class SuiteTask(ABC):
    """Abstract base class for pipeline tasks with dependency and shell support."""

    _owner: Optional["PipelineSuite"]
    _parent: Optional["SuiteTask"]
    _global_counter: int = 0
    _id: int | tuple[int, int]
    _cwd: Path | None
    _attach_printer: bool = True

    message: str
    name: str
    printer: Printer
    skip: bool = False
    _can_skip: bool = True
    _stage: "Stage"
    _initialized = False
    _deps: ClassVar[list[str]] = []
    complete: bool = False
    skip_list: ClassVar[list[str]]
    _last_run: ShellOutput
    args: dict[str, Any]
    _assigns_own_id: bool = True

    def __init__(
        self,
        parent: Optional["SuiteTask"],
        owner: Optional["PipelineSuite"],
        cwd: Path | str | None = None,
    ) -> None:
        """Initialize the task with parent, owner, and optional working directory."""
        self.add_deps()

        if owner is None and not SuiteTask._initialized:
            msg = "Owner is not set"
            raise ValueError(msg)
        if parent is None:
            msg = "Parent is not set"
            raise ValueError(msg)
        SuiteTask._initialized = True

        if cwd is not None:
            cwd = Path(cwd)
        if cwd is None:
            with contextlib.suppress(OSError, ValueError):
                cwd = parent.cwd
        if cwd is None:
            cwd = Path.cwd()

        self._cwd = Path(cwd)

        self._owner = owner
        self._parent = parent
        self.args = self._require_owner().args

        if self._assigns_own_id:
            self._id = SuiteTask._global_counter
            SuiteTask._global_counter += 1
        self._last_run = ShellOutput()
        if self._attach_printer:
            self.attach_printer(parent)

    def add_deps(self) -> None:
        """Register all declared dependencies with the Task registry."""
        for dep in self._deps:
            Task.add(dep)

    def run_deps(self) -> list[str]:
        """Run all declared dependencies and return names of failed ones."""
        failed: list[str] = []
        for dep in self._deps:
            result = Task.run(dep)
            if result is False or result is TaskResult.SKIPPED:
                failed.append(Task.get_task_name(dep))
        return failed

    @property
    def skip_task(self) -> bool:
        """Return whether this task should be skipped."""
        return bool(self.skip)

    def _require_owner(self) -> "PipelineSuite":
        """Return the owner, raising clearly if not set."""
        if self._owner is None:
            msg = f"{typename(self)} has no owner set"
            raise ValueError(msg)
        return self._owner

    def get_arg(self, arg: str) -> Any:
        """Return a CLI argument value from the owner's parsed args."""
        return self._require_owner().args.get(arg)

    def get_path(self, component: str, path: Path | str | None = None) -> Path:
        """Resolve a path from the owner's path registry."""
        base = self._require_owner().paths[component]
        if path is not None:
            return base / Path(path)
        return base

    def do_dry_run(self) -> bool:
        """Check if dry-run mode is active."""
        return bool(self.args.get("dry_run", False))

    def attach_printer(self, parent: Optional["SuiteTask"]) -> None:
        """Attach a printer instance for structured logging."""
        self.printer = Printer(parent, self)

    @staticmethod
    def inc_count() -> None:
        """Increment the global task counter."""
        SuiteTask._global_counter += 1

    @staticmethod
    def get_count() -> int:
        """Return the current global task counter value."""
        return SuiteTask._global_counter

    def dump_print_queue(self) -> None:
        """Flush all queued messages to the logger."""
        self.printer.dump()

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Log a message via the attached printer."""
        self.printer.print(*args, **kwargs)

    def msg(self, *args: Any, **kwargs: Any) -> None:
        """Log a prefixed message via the attached printer."""
        self.printer.msg(*args, **kwargs)

    @abstractmethod
    def _run(self) -> bool | str | None | ShellOutput | TaskResult:
        """Execute the task body. Subclasses must override this."""

    def dry_run(self) -> bool:
        """Evaluate dry-run state and print skip message if applicable."""
        self.msg(self.name)
        if self.skip_task:
            self.print("Skipping")
            return True
        return self.do_dry_run()

    def disable_dry_run(self) -> None:
        """Disable dry-run mode for this task instance."""

        def func() -> bool:
            self.print(f"Dry run disabled for {type(self).__name__}")
            return False

        self.do_dry_run = func

    def run(self) -> bool | str | None | ShellOutput | TaskResult:
        """Execute the task: check dry-run, run deps, then run body."""
        dry_run = self.dry_run()
        if dry_run:
            return dry_run
        failed_deps = self.run_deps()
        if failed_deps:
            self.print(
                "Skipping because dependencies did not pass: " + ", ".join(failed_deps),
            )
            return TaskResult.SKIPPED
        return self._run()

    def fail(self, *args: Any, critical: bool = False, **kwargs: Any) -> None:
        """Raise a TaskError to signal failure."""
        raise TaskError(self, *args, critical=critical, **kwargs)

    def sh(
        self,
        cmd: str | list[str],
        cwd: Path | None = None,
        *,
        handle_exception: bool = True,
        dry_run: bool | None = None,
        check: bool = True,
        shell: bool = True,
        shlex: bool = False,
        disabled: bool = False,
    ) -> ShellOutput:
        """Run a shell command within the project context."""
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

        working_dir: str = str(cwd or Path.cwd())
        self.msg(f"  [EXEC] {cmd}")

        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=check,
                cwd=working_dir,
                capture_output=True,
            )
            return ShellOutput.from_subprocess(result)
        except subprocess.CalledProcessError as e:
            if handle_exception:
                self.fail(e)
            raise ShellOutput.wrap_exception(e) from e

    def sh_thread(self, cmd: str, cwd: Path | None = None) -> ShellOutput:
        """Run a shell command with real-time streaming output."""
        self.msg(f"  [EXEC] {cmd}")
        if self.do_dry_run():
            return ShellOutput()

        self._last_run.stdout = []
        self._last_run.stderr = []

        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=str(cwd or self.get_path("root")),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        def stream_pipe(pipe: Any, relay: Any, accumulator: list[str]) -> None:
            """Read from pipe, write to relay, and save to list."""
            for line in iter(pipe.readline, ""):
                if line:
                    accumulator.append(line)
                    relay.write(line)
                    relay.flush()
            pipe.close()

        t1 = threading.Thread(
            target=stream_pipe,
            args=(process.stdout, sys.stdout, self._last_run.stdout),
        )
        t2 = threading.Thread(
            target=stream_pipe,
            args=(process.stderr, sys.stderr, self._last_run.stderr),
        )

        t1.start()
        t2.start()

        exit_code = process.wait()
        t1.join()
        t2.join()

        if exit_code != 0:
            self.fail(f"\n[ERROR] Command failed with code {exit_code}", code=exit_code)

        return ShellOutput(
            stdout=["".join(self._last_run.stdout)],
            stderr=["".join(self._last_run.stderr)],
        )

    @property
    def owner(self) -> Optional["PipelineSuite"]:
        """Return the task's owner."""
        return self._owner

    @property
    def parent(self) -> Optional["SuiteTask"]:
        """Return the task's parent."""
        return self._parent

    @property
    def cwd(self) -> str:
        """Return the working directory as a string."""
        try:
            return str(self._cwd or Path.cwd())
        except AttributeError:
            return str(Path.cwd())

    @property
    def id(self) -> int | tuple[int, int]:
        """Return the task's unique identifier."""
        return self._id

    @property
    def stage(self) -> Stage:
        """Return the pipeline stage this task belongs to."""
        return self._stage

    @property
    def last_run(self) -> ShellOutput:
        """Return the output from the last shell command execution."""
        return self._last_run

    # Legacy getters

    def get_id(self) -> int | tuple[int, int]:
        """Return the task id (legacy wrapper)."""
        return self.id

    def get_stage(self) -> Stage:
        """Return the task stage (legacy wrapper)."""
        return self.stage

    def get_cwd(self) -> str:
        """Return the working directory (legacy wrapper)."""
        return self.cwd
