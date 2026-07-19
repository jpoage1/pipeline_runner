"""Pipeline suite orchestration with argument parsing and task management."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Never, Optional

from pipeline_runner.lib.exceptions import SuiteError
from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.task_types.task import Task
from pipeline_runner.lib.types import ShellOutput, typename


def load_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser for the pipeline suite."""
    parser = argparse.ArgumentParser(description="Pipeline Suite")

    parser.add_argument("--task", type=str)
    parser.add_argument("--full-pipeline", default=True, action="store_true")
    parser.add_argument("--root", type=str, help="The root directory of the project")
    parser.add_argument("--stage", type=str, help="Run a specific stage of the build")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a trial run without executing tasks",
    )

    # --tasks 1 2 5
    parser.add_argument("--tasks", nargs="+", type=int, help="List of task IDs to run")

    # --skip 0 3
    parser.add_argument("--skip", nargs="+", type=int, help="List of task IDs to skip")
    return parser


class PipelineSuite(SuiteTask):
    """Orchestrates the Hexascript logic verification pipeline.

    Replaces tdd_loop.sh with zero subprocess overhead for Python logic.
    """

    name = "Pipeline Runner"
    root_dir: Path | None
    _in_nix_shell: bool

    @property
    def in_nix_shell(self) -> bool:
        """Return whether the pipeline is running inside a Nix shell."""
        return self._in_nix_shell

    # Always self in practice (set in __init__) - Optional only because a
    # mutable attribute override must match its base declaration exactly
    # (SuiteTask._owner: Optional["PipelineSuite"]), not narrow it.
    _owner: Optional["PipelineSuite"]
    # Real attribute, not just something test mocks happen to set on a
    # MagicMock owner - SuiteTask.get_path()/_require_owner() rely on this
    # actually existing on a real PipelineSuite instance.
    paths: dict[str, Path]
    # Every real caller (health_check's run_health_suite, this module's own
    # _run() via Task.run(task), and pipeline_runner's own test suite)
    # passes task *classes*, not instances - Task.add()/Task.run() take a
    # class or a class name string and instantiate it themselves. The
    # previous `List["SuiteTask"]` annotation described instances, which
    # nothing here ever actually passes; fixed at the source rather than
    # suppressed at each call site, since this project is the source of
    # truth other projects (e.g. health_check) build on, not the reverse.
    all_tasks: Sequence[type["SuiteTask"]] | None = None

    def __init__(
        self,
        *args: Any,
        all_tasks: Sequence[type["SuiteTask"]] | None = None,
        root: str | None = None,
        parser: argparse.ArgumentParser | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the pipeline suite with tasks and parser."""
        self.disable_dry_run()
        self._in_nix_shell = False
        self.args: dict[str, Any] = {}

        self._owner = self
        self._parser(parser)
        super().__init__(self, *args, owner=self, **kwargs)

        self._parent = self

        self.root_dir = Path(root) if root else None
        self.paths = {"root": self.root_dir} if self.root_dir else {}

        self.kwargs = kwargs
        self._all_tasks = all_tasks

    def _parser(self, parser: argparse.ArgumentParser | None = None) -> None:

        if self.args:
            sys.stderr.write("Parser already initialized\n")
            return

        parser = parser or load_parser()
        self._require_owner().args = vars(parser.parse_args())

    def fail(self, *args: Any, **kwargs: Any) -> Never:
        """Helper to raise the state-aware exception."""
        raise SuiteError(self, *args, **kwargs)

    def _run(self) -> bool | str | None | ShellOutput:
        # Declared type matches SuiteTask._run()'s own contract, not
        # narrowed to bool - PipelineSuite is itself a SuiteTask fulfilling
        # the same abstraction, and subclasses (e.g. ExampleTaskRunner)
        # legitimately override with narrower concrete behavior of their
        # own (including returning None), which requires this class not
        # to have narrowed the contract first.
        Task.__init__(self._owner, self._all_tasks)
        task = self.get_arg("task")
        if task:
            self.msg(f"Starting task: {typename(task)}")
            Task.run(task)
        elif self.get_arg("full_pipeline") is True:
            # _all_tasks defaults to None (no all_tasks= passed to __init__)
            # - iterate an empty list rather than crashing on `for x in None`.
            for task in self._all_tasks or []:
                self.msg(f"Running task: {task}")
                Task.run(task)
        else:
            self.fail("No tasks have been selected")

        Task.run(task)
        return True
