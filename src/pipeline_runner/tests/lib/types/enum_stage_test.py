import pytest
from pipeline_runner.lib.types import Stage


def test_stage_enum_values():
    """Verify that Stage enum members have the expected string values."""
    assert Stage.ANY.value == "any"
    assert Stage.BOOTSTRAP.value == "bootstrap"
    assert Stage.BUILD.value == "build"
    assert Stage.TEST.value == "test"
    assert Stage.DEPLOY.value == "deploy"


def test_stage_enum_iteration():
    """Ensure all defined stages are present and iterable."""
    expected_stages = {"any", "bootstrap", "build", "test", "deploy"}
    actual_stages = {s.value for s in Stage}
    assert actual_stages == expected_stages


@pytest.mark.parametrize("member_name", ["ANY", "BOOTSTRAP", "BUILD", "TEST", "DEPLOY"])
def test_stage_member_access(member_name):
    """Verify access by attribute name."""
    assert hasattr(Stage, member_name)


def test_stage_invalid_comparison():
    """Verify that Stage members do not equate to unrelated strings."""
    assert Stage.BUILD != "build"  # Enum members are not their values
    assert Stage.BUILD.value == "build"


def test_stage_immutability():
    """Verify that the Stage enum cannot be modified at runtime."""
    with pytest.raises(AttributeError):
        Stage.NEW_STAGE = "new"
