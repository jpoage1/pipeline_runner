"""Custom exceptions for the pipeline runner."""

import sys
import traceback
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _Dumpable(Protocol):
    """Protocol for objects that can dump their print queue."""

    def dump_print_queue(self) -> None: ...


_STRING_PARENT_MSG = "Um... this is embarrassing. Where's my mommy? "
_HANDLER_ERROR_MSG = "There was an error while handling an exception: {}"


class _HandlerError(Exception):
    """Internal error when the SuiteError handler itself fails."""


class PipelineSignalError(Exception):
    """Signal that the pipeline completed successfully."""


class SuiteError(Exception):
    """Base exception for pipeline suite errors. Handles cleanup and exit."""

    def __init__(
        self,
        parent: _Dumpable | str,
        *args: Any,
        critical: bool = False,
        code: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the suite error with parent context and exit behavior."""
        super().__init__(*args, **kwargs)
        if isinstance(parent, str):
            raise _HandlerError(_STRING_PARENT_MSG, parent)

        def _do_critical() -> None:
            if critical:
                raise RuntimeError(*args, **kwargs)

        def _do_exit() -> None:
            if code is not None:
                sys.exit(code)

        try:
            parent.dump_print_queue()
            traceback.print_stack()
            sys.stderr.write(" ".join(map(str, args)) + "\n")

            _do_exit()
            _do_critical()
        except RuntimeError:
            raise
        except Exception as e:
            raise _HandlerError(_HANDLER_ERROR_MSG.format(e)) from e
        sys.exit(1)


class TaskError(SuiteError):
    """Exception for individual task failures within a suite."""

    def __init__(
        self,
        parent: _Dumpable,
        *args: Any,
        critical: bool = False,
        code: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the task error with parent context and exit behavior."""
        super().__init__(parent, *args, critical=critical, code=code, **kwargs)
        if critical:
            raise RuntimeError(*args, **kwargs)
        sys.stderr.write(" ".join(map(str, args)) + "\n")
        traceback.print_stack()
