import re
import subprocess

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Union

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-jklmnpqtyuvwyz])")


def typename(t):
    return type(t).__name__


class Stage(Enum):
    ANY = "any"
    BOOTSTRAP = "bootstrap"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"


class TaskStatus(Enum):
    MISSING = "missing"  # Not in registry
    REGISTERED = "registered"  # In registry, but not instantiated
    LOADED = "loaded"  # Instantiated, but not run
    COMPLETED = "completed"  # Run and result stored


@dataclass(frozen=True)
class LogRecord:
    timestamp: datetime
    level: int
    message: str
    instance_id: Any
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)


class ShellException(Exception):
    """Exception raised when a shell command fails, wrapping the original error."""

    def __init__(self, original_exception: Exception):
        self.original = original_exception
        super().__init__(f"Shell command failed: {original_exception}")


@dataclass
class ShellOutput:
    stdout: list[str] = field(default_factory=list)
    stderr: list[str] = field(default_factory=list)
    returncode: int = 0

    @classmethod
    def from_subprocess(
        cls, result: Union[subprocess.CompletedProcess, subprocess.CalledProcessError]
    ) -> "ShellOutput":
        # Extract and clean strings immediately
        def clean(out):
            if not out:
                return []
            text = out if isinstance(out, str) else out.decode("utf-8", errors="ignore")
            # Strip ANSI escape codes
            text = ANSI_ESCAPE.sub("", text)
            return [line.strip() for line in text.splitlines() if line.strip()]

        return cls(
            stdout=clean(result.stdout),
            stderr=clean(result.stderr),
            returncode=result.returncode,
        )

    @staticmethod
    def wrap_exception(e: Exception) -> ShellException:
        """Wraps a standard exception into a ShellException for consistent error handling."""
        return ShellException(e)
