"""Sub-task implementation with parent-child counter tracking."""

from typing import TYPE_CHECKING, Any, ClassVar, Optional

from .suite_task import SuiteTask

if TYPE_CHECKING:
    from pipeline_runner.core.suite import PipelineSuite


class SuiteSubTask(SuiteTask):
    """A sub-task that tracks a counter per parent and uses tuple-based IDs."""

    _owner: Optional["PipelineSuite"]
    _parent: SuiteTask | None
    _attach_printer: bool = False
    _assigns_own_id: bool = False

    _sub_counter: ClassVar[dict[int, int]] = {}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize as a sub-task with a tuple ID linking parent to sub-index."""
        super().__init__(*args, **kwargs)

        if SuiteTask.get_count() not in SuiteSubTask._sub_counter:
            SuiteSubTask._sub_counter[SuiteTask.get_count()] = 0

        self._id = (
            SuiteTask.get_count(),
            SuiteSubTask._sub_counter[SuiteTask.get_count()],
        )
        self.attach_printer(self._require_owner())

    def msg(self, *args: Any, **kwargs: Any) -> None:
        """Log a message and increment the sub-task counter."""
        SuiteSubTask.inc_count()

        if self._parent is None:
            name = type(self).__name__
            msg = f"{name} has no parent set"
            raise ValueError(msg)
        self._parent.msg(*args, **kwargs)

    @staticmethod
    def inc_count() -> None:
        """Increment the sub-task counter for the current global counter."""
        SuiteSubTask._sub_counter[SuiteTask.get_count()] += 1

    @staticmethod
    def get_sub_counters() -> dict[int, int]:
        """Return the per-parent sub-task counter mapping.

        This is distinct from SuiteTask.get_count() - it tracks sub-tasks
        per parent rather than the global task count.
        """
        return SuiteSubTask._sub_counter
