import pytest
import runpy
from unittest.mock import patch


@patch("pipeline_runner.core.pipeline_runner.runner")
def test_main_execution(mock_runner):
    """Verify execution of runner via __main__ entry point."""
    runpy.run_module("pipeline_runner.__main__", run_name="__main__")
    mock_runner.assert_called_once()
