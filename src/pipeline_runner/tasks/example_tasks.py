from abc import abstractmethod

from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import Stage
from pipeline_runner.core.suite import PipelineSuite

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ExampleTask(SuiteTask):
    """An example task"""

    _stage = Stage.ANY
    _deps = []
    name: str = "Start an example task"

    def _run(self):
        self.print("Hello World")


class ExampleTaskRunner(PipelineSuite):
    """
    An example child task runner
    """

    _stage = Stage.ANY
    _deps = []
    skip: bool = False
    _tasks: []
    name: str
    root_dir: Optional["Path"]
    _in_nix_shell: bool
    _owner: "PipelineSuite"

    def __init__(self, *args, **kwargs):
        """An example constructor"""
        super().__init__(*args, **kwargs)

    @abstractmethod
    def _run(self):
        """An example implementation"""
        pass
