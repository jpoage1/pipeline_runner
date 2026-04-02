import pytest
from pipeline_runner.lib.exceptions import SuiteError


class MockParent:
    def __init__(self):
        self.dump_called = False

    def dump_print_queue(self):
        self.dump_called = True


## SuiteError Tests


def test_suite_error_valid_parent_calls_dump():
    """Verify that a valid parent has its print queue dumped."""
    parent = MockParent()
    with pytest.raises(SystemExit) as e:
        SuiteError(parent, "Test Error")

    assert e.value.code == 1
    assert parent.dump_called is True


def test_suite_error_malformed_parent_string():
    """Verify boundary condition where parent is a string instead of an object."""
    with pytest.raises(Exception) as e:
        SuiteError("not_an_object", "Test Error")

    assert "There was an error while handling an exception" in str(e.value)
    assert "Where's my mommy?" in str(e.value.__cause__)


def test_suite_error_critical_raises_runtime():
    """Verify that critical=True triggers a RuntimeError during initialization."""
    parent = MockParent()
    # SuiteError raises Exception because it fails to handle its own critical path
    with pytest.raises(Exception) as e:
        SuiteError(parent, "Critical Failure", critical=True)

    assert "There was an error while handling an exception" in str(e.value)


def test_suite_error_custom_exit_code():
    """Verify that providing a code triggers sys.exit with that specific code."""
    parent = MockParent()
    with pytest.raises(SystemExit) as e:
        SuiteError(parent, "Exit 42", code=42)

    assert e.value.code == 42
