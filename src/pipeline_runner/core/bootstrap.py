"""Bootstrap tasks for environment setup and dependency verification."""

import os
import shutil
from pathlib import Path
from typing import Any, ClassVar

from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.types import Stage


class CheckNix(SuiteTask):
    """Check the environment for Nix, since Nix should resolve its own dependency."""

    _stage = Stage.BOOTSTRAP

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the nix check task."""
        super().__init__(*args, **kwargs)
        self.name = "Checking if we are in a nix shell..."

    def _run(self) -> bool:
        if not shutil.which("nix"):
            self.print("⬡ Nix tools not found in PATH.")
            return False

        shell_type = os.environ.get("IN_NIX_SHELL")
        if shell_type:
            self._in_nix_shell = shell_type
        return True


class EnsurePaths(SuiteTask):
    """A base class for ensuring build paths exist."""

    _deps: ClassVar[list[str]] = []
    _can_skip = False

    _stage = Stage.BOOTSTRAP
    _dirs: list[Path]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the path setup task."""
        super().__init__(*args, **kwargs)
        self.name = "Setting up build path"

    def _run(self) -> bool:
        """Ensure build directory exists."""
        for dir_path in self._dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        return True


class VerifySystemDependencies(SuiteTask):
    """A basic skeleton for dependency checking."""

    _can_skip = False
    _stage = Stage.BOOTSTRAP

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the dependency verification task."""
        super().__init__(*args, **kwargs)
        self.name = "Verifying System Dependencies"

    def _run(self) -> bool:
        """A basic dependency check."""
        if self._require_owner().in_nix_shell:
            self.print("Skipping: in nix shell")
        return True
