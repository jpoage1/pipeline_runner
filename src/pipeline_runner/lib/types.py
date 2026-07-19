"""Core type definitions for the pipeline runner."""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-jklmnpqtyuvwyz])")


def typename(t: Any) -> str:
    """Return the type name of the given object."""
    return type(t).__name__


class Stage(Enum):
    """Pipeline stage enum."""

    ANY = "any"
    BOOTSTRAP = "bootstrap"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"


class TaskStatus(Enum):
    """Task lifecycle status."""

    MISSING = "missing"
    REGISTERED = "registered"
    LOADED = "loaded"
    COMPLETED = "completed"


class TaskResult(Enum):
    """Task execution result values."""

    SKIPPED = "skipped"


@dataclass(frozen=True)
class LogRecord:
    """Structured log entry for the printer system."""

    timestamp: datetime
    level: int
    message: str
    instance_id: Any
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict[str, Any])


class ShellError(Exception):
    """Exception raised when a shell command fails, wrapping the original error."""

    def __init__(self, original_exception: Exception) -> None:
        """Wrap the original exception from shell execution."""
        self.original = original_exception
        super().__init__(f"Shell command failed: {original_exception}")


@dataclass
class ShellOutput:
    """Captured output from a shell command execution."""

    stdout: list[str] = field(default_factory=list[str])
    stderr: list[str] = field(default_factory=list[str])
    returncode: int = 0

    @classmethod
    def from_subprocess(
        cls,
        result: subprocess.CompletedProcess[bytes] | subprocess.CalledProcessError,
    ) -> "ShellOutput":
        """Build ShellOutput from a subprocess result, cleaning ANSI codes."""

        def clean(out: Any) -> list[str]:
            if not out:
                return []
            text = out if isinstance(out, str) else out.decode("utf-8", errors="ignore")
            text = ANSI_ESCAPE.sub("", text)
            return [line.strip() for line in text.splitlines() if line.strip()]

        return cls(
            stdout=clean(result.stdout),
            stderr=clean(result.stderr),
            returncode=result.returncode,
        )

    @staticmethod
    def wrap_exception(e: Exception) -> ShellError:
        """Wraps a standard exception into a ShellError."""
        return ShellError(e)
