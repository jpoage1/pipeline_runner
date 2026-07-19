"""Tests for lib.task_types.suite_task.suite_task_helpers_test."""

from pathlib import Path
from typing import Any

import pytest

from pipeline_runner.lib.task_types.suite_task_helpers import (
    prepare_command,
    resolve_cwd,
    should_skip,
)

## prepare_command Tests


def test_prepare_command_standard_shell() -> None:
    """Verify that standard shell commands return as a string with shell=True."""
    cmd = "ls -la /tmp"
    use_shell = True
    result_cmd, result_shell = prepare_command(cmd, shell=use_shell, use_shlex=False)

    assert result_cmd == "ls -la /tmp"
    assert result_shell is True


def test_prepare_command_with_shlex() -> None:
    """Verify that shlex splits the string into a list and sets shell=False."""
    cmd = "echo 'hello world'"
    use_shell = True
    result_cmd, result_shell = prepare_command(cmd, shell=use_shell, use_shlex=True)

    assert result_cmd == ["echo", "hello world"]
    assert result_shell is False


## resolve_cwd Tests


def test_resolve_cwd_with_path_object() -> None:
    """Verify that a Path object is correctly converted to a string."""
    path = Path("/srv/projects")
    assert resolve_cwd(path) == "/srv/projects"


def test_resolve_cwd_fallback_to_getcwd() -> None:
    """Verify that passing None returns the current working directory."""
    result = resolve_cwd(None)
    assert result == str(Path.cwd())
    assert isinstance(result, str)


## should_skip Tests


@pytest.mark.parametrize(
    ("disabled", "dry_run", "force_run", "expected"),
    [
        (True, False, False, True),
        (True, True, True, True),
        (False, True, True, True),
        (False, True, None, True),
        (False, True, False, False),
        (False, False, False, False),
    ],
)
def test_should_skip_logic_matrix(
    disabled: Any,
    dry_run: Any,
    force_run: Any,
    expected: Any,
) -> None:
    """Verify the skip logic across the matrix of possible states."""
    assert should_skip(disabled, dry_run, force_run) is expected


def test_should_skip_boundary_conditions() -> None:
    """Verify behavior with truthy/falsy inputs that aren't strict booleans."""
    assert should_skip(disabled=False, dry_run_active=1, force_run=None) is True
    assert should_skip(disabled="yes", dry_run_active=False, force_run=False) is True
