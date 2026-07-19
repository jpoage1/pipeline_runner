"""Tests for main_test."""

import runpy
from unittest.mock import MagicMock, patch


@patch("pipeline_runner.core.pipeline_runner.runner")
def test_main_execution(mock_runner: MagicMock) -> None:
    """Verify execution of runner via __main__ entry point."""
    runpy.run_module("pipeline_runner.__main__", run_name="__main__")
    mock_runner.assert_called_once()
