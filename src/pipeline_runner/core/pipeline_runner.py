import sys
import traceback


from pipeline_runner.core.suite import PipelineSuite
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pipeline_runner.lib.task_types import SuiteTask


def runner(tasks: Optional[List["SuiteTask"]] = None):

    runner = PipelineSuite(all_tasks=tasks)
    exit_code = 0

    try:
        runner.run()
        print("🚀 Pipeline Successful")
        exit_code = 0
    except KeyboardInterrupt:
        runner.dump_print_queue()
        traceback.print_exc()
        runner.print("\n[System] Termination signal received. Cleaning up...")
        exit_code = 0
    except Exception as e:
        runner.dump_print_queue()
        traceback.print_exc()
        print(f"❌ Deployment Failed at: {e.with_traceback(e.__traceback__)}")
        exit_code = 1
    if exit_code != 0:
        print(exit_code)
        sys.exit(exit_code or 1)
    runner.dump_print_queue()
