import pytest
from unittest.mock import MagicMock
from pipeline_runner.lib.task_types.suite_sub_task import SuiteSubTask
from pipeline_runner.lib.task_types.suite_task import SuiteTask


class ConcreteSubTask(SuiteSubTask):
    def _run(self):
        return True


def test_suite_sub_task_init_and_msg():
    """Verify SubTask identity mapping and messaging delegation."""
    SuiteTask._global_counter = 1
    SuiteSubTask._sub_counter = {}

    parent_task = MagicMock()
    owner = MagicMock()

    sub_task = ConcreteSubTask(parent_task, owner)
    assert sub_task._id == (1, 0)

    sub_task.msg("test msg")
    parent_task.msg.assert_called_once_with("test msg")
    assert SuiteSubTask.get_count()[1] == 1
