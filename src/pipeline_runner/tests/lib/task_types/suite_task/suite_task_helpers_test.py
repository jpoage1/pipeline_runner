import pytest
import os
from pathlib import Path
from pipeline_runner.lib.task_types.suite_task_helpers import (
    prepare_command,
    resolve_cwd,
    should_skip,
)

## prepare_command Tests


def test_prepare_command_standard_shell():
    """Verify that standard shell commands return as a string with shell=True."""
    cmd = "ls -la /tmp"
    result_cmd, result_shell = prepare_command(cmd, shell=True, use_shlex=False)

    assert result_cmd == "ls -la /tmp"
    assert result_shell is True


def test_prepare_command_with_shlex():
    """Verify that shlex splits the string into a list and sets shell=False."""
    cmd = "echo 'hello world'"
    result_cmd, result_shell = prepare_command(cmd, shell=True, use_shlex=True)

    assert result_cmd == ["echo", "hello world"]
    assert result_shell is False


## resolve_cwd Tests


def test_resolve_cwd_with_path_object():
    """Verify that a Path object is correctly converted to a string."""
    path = Path("/srv/projects")
    assert resolve_cwd(path) == "/srv/projects"


def test_resolve_cwd_fallback_to_getcwd():
    """Verify that passing None returns the current working directory."""
    result = resolve_cwd(None)
    assert result == os.getcwd()
    assert isinstance(result, str)


## should_skip Tests


@pytest.mark.parametrize(
    "disabled, dry_run, force_run, expected",
    [
        # 1. Explicitly disabled should always skip
        (True, False, False, True),
        (True, True, True, True),
        # 2. Dry run active should skip unless force_run is explicitly False
        (False, True, True, True),
        (False, True, None, True),
        # 3. Dry run active but force_run is False should NOT skip
        (False, True, False, False),
        # 4. Standard execution (not disabled, no dry run) should NOT skip
        (False, False, False, False),
    ],
)
def test_should_skip_logic_matrix(disabled, dry_run, force_run, expected):
    """Verify the skip logic across the matrix of possible states."""
    assert should_skip(disabled, dry_run, force_run) is expected


def test_should_skip_boundary_conditions():
    """Verify behavior with truthy/falsy inputs that aren't strict booleans."""
    # dry_run_active is truthy, force_run is None (effectively True for skipping)
    assert should_skip(False, 1, None) is True
    # disabled is truthy
    assert should_skip("yes", False, False) is True
