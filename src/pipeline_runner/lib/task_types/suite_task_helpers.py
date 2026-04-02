import os
from shlex import split as shlex_split
from pathlib import Path


def prepare_command(cmd: str, shell: bool, use_shlex: bool):
    """Purely prepares the command and shell flag."""
    if use_shlex:
        return shlex_split(cmd), False
    return cmd, shell


def resolve_cwd(provided_cwd: Path | None) -> str:
    """Purely resolves the CWD to a string."""
    return str(provided_cwd or os.getcwd())


def should_skip(disabled: bool, dry_run_active: bool, force_run: bool) -> bool:
    """Determines if the command execution should be bypassed."""
    if disabled:
        return True
    if dry_run_active and force_run is not False:
        return True
    return False
