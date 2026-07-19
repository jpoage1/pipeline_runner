"""Pure helper functions for shell command execution within tasks."""

from pathlib import Path
from shlex import split as shlex_split
from typing import Any


def prepare_command(
    cmd: str,
    shell: Any,
    use_shlex: Any,
) -> tuple[list[str] | str, bool]:
    """Prepare the command and shell flag for execution."""
    if use_shlex:
        return shlex_split(cmd), False
    return cmd, shell


def resolve_cwd(provided_cwd: Path | None) -> str:
    """Resolve the working directory to a string."""
    return str(provided_cwd or Path.cwd())


def should_skip(
    disabled: Any,
    dry_run_active: Any,
    force_run: Any,
) -> bool:
    """Determine if the command execution should be bypassed.

    Duck-typed on truthiness - the Any types reflect real, tested callers
    (see test_should_skip_boundary_conditions), not a hedge.
    """
    if disabled:
        return True
    return bool(dry_run_active and force_run is not False)
