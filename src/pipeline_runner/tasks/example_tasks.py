"""Example task implementations for demonstration and testing."""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pipeline_runner.core.suite import PipelineSuite
from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import Stage

if TYPE_CHECKING:
    from pathlib import Path


class ExampleTask(SuiteTask):
    """An example task that prints a greeting."""

    _stage = Stage.ANY
    _deps: ClassVar[list[str]] = []
    name: str = "Start an example task"

    def _run(self) -> bool:
        self.print("Hello World")
        return True


class ExampleTaskRunner(PipelineSuite):
    """An example child task runner."""

    _stage = Stage.ANY
    _deps: ClassVar[list[str]] = []
    skip: bool = False
    name: str
    root_dir: Optional["Path"]
    _in_nix_shell: bool
    _owner: Optional["PipelineSuite"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the example task runner."""
        super().__init__(*args, **kwargs)

    @abstractmethod
    def _run(self) -> None:
        """Run the example task."""
