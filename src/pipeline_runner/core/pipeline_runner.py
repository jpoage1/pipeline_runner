"""Entry point for the pipeline runner execution."""

import sys
import traceback
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pipeline_runner.core.suite import PipelineSuite

if TYPE_CHECKING:
    from pipeline_runner.lib.task_types.suite_task import SuiteTask


def runner(tasks: Sequence[type["SuiteTask"]] | None = None) -> None:
    """Run the pipeline with the given set of tasks."""
    suite = PipelineSuite(all_tasks=tasks)
    exit_code = 0

    try:
        suite.run()
        suite.print("Pipeline Successful")
        exit_code = 0
    except KeyboardInterrupt:
        suite.dump_print_queue()
        traceback.print_exc()
        suite.print("\n[System] Termination signal received. Cleaning up...")
        exit_code = 0
    except Exception as e:
        suite.dump_print_queue()
        traceback.print_exc()
        suite.print(f"Deployment Failed at: {e}")
        exit_code = 1
    if exit_code != 0:
        sys.exit(exit_code or 1)
    suite.dump_print_queue()
