from pipeline_runner.lib.task_types.helpers import get_task_name


def test_get_task_name_variations():
    assert get_task_name("SimpleString") == "SimpleString"
    assert get_task_name(MockTaskClass) == "MockTaskClass"
    assert get_task_name(123) == "123"
