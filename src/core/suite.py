import argparse
from pathlib import Path

from lib.exceptions import SuiteError
from lib.task_types import SuiteTask, Task

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from lib.task_types import SuiteTask


def load_parser():
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
    """
    Orchestrates the Hexascript logic verification pipeline.
    Replaces tdd_loop.sh with zero subprocess overhead for Python logic.
    """

    name = "Pipeline Runner"
    root_dir: Path | None
    _in_nix_shell: bool
    _owner: "PipelineSuite"
    all_tasks: Optional[List["SuiteTask"]] = None

    def __init__(
        self,
        *args,
        all_tasks: Optional[List["SuiteTask"]] = None,
        root: str | None = None,
        parser: Optional[argparse.ArgumentParser] = None,
        **kwargs,
    ):
        self.disable_dry_run()
        self._in_nix_shell = False
        self.args: dict = dict()

        self._owner = self
        self._parser(parser)
        super().__init__(self, *args, owner=self, *kwargs)

        self._parent = self

        self.root_dir = Path(root) if root else None

        self.kwargs = kwargs
        self._all_tasks = all_tasks

    def _parser(self, parser: argparse.ArgumentParser):

        parser = load_parser()
        self._owner.args = vars(parser.parse_args())

        def initialized():
            print("Parser already initialized")

        self._parser = initialized

    def fail(self, *args, **kwargs):
        """Helper to raise the state-aware exception."""
        raise SuiteError(self, *args, **kwargs)

    def _run(self):

        Task.__init__(self._owner, self._all_tasks)
        task = self.get_arg("task")
        if task:
            self.msg(f"Starting task: {typename(task)}")
            Task.run(task)
        elif self.get_arg("full_pipeline") is True:
            for task in self._all_tasks:
                self.msg(f"Running task: {task}")
                Task.run(task)
        else:
            self.fail("No tasks have been selected")

        Task.run(task)
        return self
