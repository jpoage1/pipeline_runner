"""Tests for lib.exceptions.fuzzing_test."""

from typing import Any

import pytest

from pipeline_runner.lib.exceptions import SuiteError


@pytest.mark.parametrize("bad_parent", [None, 123, [], {}])
def test_suite_error_fuzz_parent_input(bad_parent: Any) -> None:
    """Fuzzing check for unexpected parent types."""
    with pytest.raises(Exception, match="There was an error") as e:
        SuiteError(bad_parent, "Fuzzing")

    assert "There was an error while handling an exception" in str(e.value)
