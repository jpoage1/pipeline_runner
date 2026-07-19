"""Tests for lib.types.typename_test."""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from pipeline_runner.lib.types import typename


def test_typename_standard_types() -> None:
    """Verify typename returns correct strings for builtin types."""
    assert typename("string") == "str"
    assert typename(123) == "int"
    assert typename([]) == "list"
    assert typename({}) == "dict"
    assert typename(None) == "NoneType"


def test_typename_custom_class() -> None:
    """Verify typename correctly identifies custom class names."""

    class MockTask:
        pass

    task = MockTask()
    assert typename(task) == "MockTask"


@given(st.one_of(st.integers(), st.floats(), st.text(), st.booleans()))
def test_typename_fuzzing(input_val: Any) -> None:
    """Fuzzing test to ensure typename never raises an exception on primitive types."""
    result = typename(input_val)
    assert isinstance(result, str)
    assert len(result) > 0
