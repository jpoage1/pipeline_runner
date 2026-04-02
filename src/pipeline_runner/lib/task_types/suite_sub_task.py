from .suite_task import SuiteTask


class SuiteSubTask(SuiteTask):
    _owner: "TDDSuite"
    _parent: SuiteTask

    _sub_counter: dict[int] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, attach_printer=False, **kwargs)

        if SuiteTask._global_counter not in SuiteSubTask._sub_counter.keys():
            SuiteSubTask._sub_counter[SuiteTask._global_counter] = 0

        self._id = (SuiteTask._global_counter, SuiteSubTask._sub_counter)

        self.attach_printer(self._owner)

    def msg(self, *args, **kwargs):
        """Standardized message logger."""
        SuiteSubTask.inc_count()

        self._parent.msg(*args, **kwargs)

    @staticmethod
    def inc_count():

        print(SuiteSubTask._sub_counter)
        SuiteSubTask._sub_counter[SuiteTask._global_counter] += 1

    @staticmethod
    def get_count():
        return SuiteSubTask._sub_counter
