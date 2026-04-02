from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union


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

    @classmethod
    def from_subprocess(
        cls, result: Union[subprocess.CompletedProcess, subprocess.CalledProcessError]
    ) -> "ShellOutput":
        """Factory method to create ShellOutput from a subprocess result."""
        return cls(
            stdout=(result.stdout or "").splitlines(),
            stderr=(result.stderr or "").splitlines(),
        )

    @staticmethod
    def wrap_exception(e: Exception) -> ShellException:
        """Wraps a standard exception into a ShellException for consistent error handling."""
        return ShellException(e)
