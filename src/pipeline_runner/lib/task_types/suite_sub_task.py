from typing import Optional, TYPE_CHECKING

from .suite_task import SuiteTask

if TYPE_CHECKING:
    from pipeline_runner.core.suite import PipelineSuite


class SuiteSubTask(SuiteTask):
    # Optional to match SuiteTask's own base declaration exactly - a
    # mutable attribute override must be invariant with its base type, not
    # just a narrowing of it.
    _owner: Optional["PipelineSuite"]
    _parent: Optional[SuiteTask]

    _sub_counter: dict[int, int] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, attach_printer=False, **kwargs)

        if SuiteTask._global_counter not in SuiteSubTask._sub_counter.keys():
            SuiteSubTask._sub_counter[SuiteTask._global_counter] = 0

        self._id = (
            SuiteTask._global_counter,
            SuiteSubTask._sub_counter[SuiteTask._global_counter],
        )
        self.attach_printer(self._require_owner())

    def msg(self, *args, **kwargs):
        """Standardized message logger."""
        SuiteSubTask.inc_count()

        if self._parent is None:
            raise ValueError(f"{type(self).__name__} has no parent set")
        self._parent.msg(*args, **kwargs)

    @staticmethod
    def inc_count():

        print(SuiteSubTask._sub_counter)
        SuiteSubTask._sub_counter[SuiteTask._global_counter] += 1

    @staticmethod
    def get_sub_counters() -> dict[int, int]:
        """Distinct from SuiteTask.get_count() (the global task counter) -
        this returns the per-parent sub-task counter mapping, a different
        concept that happened to share a name by accident, not a real
        override of the base method."""
        return SuiteSubTask._sub_counter
