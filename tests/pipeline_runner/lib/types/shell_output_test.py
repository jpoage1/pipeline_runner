"""Tests for lib.types.shell_output_test."""

import subprocess
from unittest.mock import MagicMock

from pipeline_runner.lib.types import ShellOutput


def test_shell_output_ansi_stripping() -> None:
    """Verify that ANSI escape codes are removed from stdout/stderr."""
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    # Green "active", Red "error"
    mock_result.stdout = "\x1b[32mactive\x1b[0m\nline2"
    mock_result.stderr = "\x1b[31mfatal error\x1b[0m"
    mock_result.returncode = 0

    output = ShellOutput.from_subprocess(mock_result)

    assert output.stdout == ["active", "line2"]
    assert output.stderr == ["fatal error"]
    assert output.returncode == 0


def test_shell_output_handles_malformed_encoding() -> None:
    """Verify handling of non-utf8 bytes in subprocess output."""
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    # Binary data mixed with text
    mock_result.stdout = b"valid text\xff\xfeinvalid"
    mock_result.stderr = b""
    mock_result.returncode = 1

    output = ShellOutput.from_subprocess(mock_result)

    assert "valid text" in output.stdout[0]
    assert output.returncode == 1


def test_shell_output_empty_inputs() -> None:
    """Boundary condition: Ensure empty stdout/stderr don't crash the cleaner."""
    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    mock_result.stdout = ""
    mock_result.stderr = None
    mock_result.returncode = 0

    output = ShellOutput.from_subprocess(mock_result)

    assert output.stdout == []
    assert output.stderr == []


def test_shell_output_from_called_process_error() -> None:
    """Verify factory works with exception objects (CalledProcessError)."""
    error = subprocess.CalledProcessError(
        returncode=3,
        cmd="systemctl is-active slapd",
        output="inactive",
        stderr="failed",
    )

    output = ShellOutput.from_subprocess(error)

    assert output.returncode == 3
    assert output.stdout == ["inactive"]
