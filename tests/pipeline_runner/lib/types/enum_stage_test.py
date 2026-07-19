"""Tests for lib.types.enum_stage_test."""

from typing import Any

import pytest

from pipeline_runner.lib.types import Stage


def test_stage_enum_values() -> None:
    """Verify that Stage enum members have the expected string values."""
    assert Stage.ANY.value == "any"
    assert Stage.BOOTSTRAP.value == "bootstrap"
    assert Stage.BUILD.value == "build"
    assert Stage.TEST.value == "test"
    assert Stage.DEPLOY.value == "deploy"


def test_stage_enum_iteration() -> None:
    """Ensure all defined stages are present and iterable."""
    expected_stages = {"any", "bootstrap", "build", "test", "deploy"}
    actual_stages = {s.value for s in Stage}
    assert actual_stages == expected_stages


@pytest.mark.parametrize("member_name", ["ANY", "BOOTSTRAP", "BUILD", "TEST", "DEPLOY"])
def test_stage_member_access(member_name: Any) -> None:
    """Verify access by attribute name."""
    assert hasattr(Stage, member_name)


def test_stage_invalid_comparison() -> None:
    """Verify that Stage members do not equate to unrelated strings."""
    assert Stage.BUILD != "build"  # Enum members are not their values
    assert Stage.BUILD.value == "build"


def test_stage_immutability() -> None:
    """Verify that the Stage enum cannot be modified at runtime. Uses.

    setattr() rather than a direct assignment: the assignment is
    genuinely dynamic here (the whole point is exercising the runtime
    rejection), not a static one a type checker could ever validate.
    """
    with pytest.raises((AttributeError, TypeError)):
        object.__setattr__(Stage, "ANY", "new")
