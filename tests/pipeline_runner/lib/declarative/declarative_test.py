"""Tests for lib.declarative.declarative_test."""

import argparse
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.core.suite import PipelineSuite
from pipeline_runner.lib.declarative import (
    build_task_class,
    build_task_classes,
)
from pipeline_runner.lib.task_types.suite_task import SuiteTask
from pipeline_runner.lib.task_types.task import Task
from pipeline_runner.lib.types import TaskResult


class RecordingTask(SuiteTask):
    """Minimal concrete SuiteTask used as a `type:` target in specs.

    should_pass is the only behavior a spec can't set directly (it isn't a
    plain data attribute in the base health-check task types either -
    behavior always comes from the base class, only data comes from the
    spec), so it's set here instead of via build_task_class.
    """

    name: str = "Recording Task"
    should_pass: bool = True
    run_log: ClassVar[list[str]] = []

    def _run(self) -> bool:
        type(self).run_log.append(type(self).__name__)
        return self.should_pass


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Verify reset_state."""
    Task._initialized = False
    Task._registry = {}
    Task._loaded = {}
    Task._completed = {}
    Task._owner = None
    RecordingTask.run_log = []


TYPE_REGISTRY = {"recording": RecordingTask}


## build_task_class / build_task_classes


def test_build_task_class_sets_id_as_class_name() -> None:
    """Verify build_task_class_sets_id_as_class_name."""
    cls = build_task_class(
        {"id": "CheckThing", "type": "recording", "skip": True},
        TYPE_REGISTRY,
    )

    assert cls.__name__ == "CheckThing"
    assert issubclass(cls, RecordingTask)
    # skip is a real attribute declared on SuiteTask itself (the actual
    # parent class here) - this is a genuine, statically-verifiable
    # override, not an invented field.
    assert cls.skip is True


def test_build_task_class_leaves_name_attribute_untouched() -> None:
    """Verify `id` and `name` attributes are preserved separately.

    `id` (registry key / class name) and `name` (SuiteTask's own
    separate fields - setting `name` in a spec must not collide with `id`
    or get dropped, the same as any other hand-written check class.
    """
    cls = build_task_class(
        {"id": "CheckThing", "type": "recording", "name": "Check the thing"},
        TYPE_REGISTRY,
    )

    assert cls.__name__ == "CheckThing"
    assert cls.name == "Check the thing"


def test_build_task_class_deps_becomes_underscore_deps() -> None:
    """Verify build_task_class_deps_becomes_underscore_deps."""
    cls = build_task_class(
        {"id": "Dependent", "type": "recording", "deps": ["Other"]},
        TYPE_REGISTRY,
    )

    assert cls._deps == ["Other"]


def test_build_task_class_missing_id_raises() -> None:
    """Verify build_task_class_missing_id_raises."""
    with pytest.raises(ValueError, match="missing required 'id'"):
        build_task_class({"type": "recording"}, TYPE_REGISTRY)


def test_build_task_class_missing_type_raises() -> None:
    """Verify build_task_class_missing_type_raises."""
    with pytest.raises(ValueError, match="missing required 'type'"):
        build_task_class({"id": "Foo"}, TYPE_REGISTRY)


def test_build_task_class_unknown_type_raises() -> None:
    """Verify build_task_class_unknown_type_raises."""
    with pytest.raises(ValueError, match="unknown type 'bogus'"):
        build_task_class({"id": "Foo", "type": "bogus"}, TYPE_REGISTRY)


def test_build_task_class_does_not_mutate_input_spec() -> None:
    """Verify build_task_class_does_not_mutate_input_spec."""
    spec = {"id": "Foo", "type": "recording", "deps": ["Bar"]}
    build_task_class(spec, TYPE_REGISTRY)

    assert spec == {"id": "Foo", "type": "recording", "deps": ["Bar"]}


def test_build_task_classes_preserves_order() -> None:
    """Verify build_task_classes_preserves_order."""
    specs = [
        {"id": "First", "type": "recording"},
        {"id": "Second", "type": "recording"},
        {"id": "Third", "type": "recording"},
    ]
    classes = build_task_classes(specs, TYPE_REGISTRY)

    assert [c.__name__ for c in classes] == ["First", "Second", "Third"]


## Integration: string deps + dependency execution, against the real
## Task/PipelineSuite machinery. This is the load-bearing assumption the
## whole loader rests on (see declarative.py's module docstring), so it's
## proven end to end rather than mocked.


@patch("argparse.ArgumentParser.parse_args")
def test_string_deps_resolve_and_run_before_dependents(mock_parse: MagicMock) -> None:
    """Verify string_deps_resolve_and_run_before_dependents."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    specs = [
        # Listed BEFORE its dependency on purpose: proves run order comes
        # from the dependency graph where a task declares deps, not only
        # from list position.
        {"id": "Dependent", "type": "recording", "deps": ["Dependency"]},
        {"id": "Dependency", "type": "recording"},
    ]
    classes = build_task_classes(specs, TYPE_REGISTRY)
    dependent_cls, _dependency_cls = classes

    suite = PipelineSuite(all_tasks=classes)
    suite.printer = MagicMock()
    suite._run()

    assert RecordingTask.run_log == ["Dependency", "Dependent"]

    # The string dep resolved correctly (not a raised "does not exist").
    assert Task.exists("Dependency")
    assert dependent_cls._deps == ["Dependency"]

    # Both tasks actually executed and recorded a real pass/fail result -
    # this is the {task_name: bool} registry health_check's own aggregation
    # (HealthPipelineSuite/run_health_suite) reads from.
    assert Task._completed["Dependent"] is True
    assert Task._completed["Dependency"] is True


@patch("argparse.ArgumentParser.parse_args")
def test_failing_string_dep_skips_dependent_task(mock_parse: MagicMock) -> None:
    """Verify failing_string_dep_skips_dependent_task."""
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    specs = [
        {"id": "Dependent", "type": "recording", "deps": ["Dependency"]},
        {"id": "Dependency", "type": "recording", "should_pass": False},
    ]
    classes = build_task_classes(specs, TYPE_REGISTRY)

    suite = PipelineSuite(all_tasks=classes)
    suite.printer = MagicMock()
    suite._run()

    assert RecordingTask.run_log == ["Dependency"]
    assert Task._completed["Dependency"] is False
    assert Task._completed["Dependent"] is TaskResult.SKIPPED


@patch("argparse.ArgumentParser.parse_args")
def test_a_failing_task_result_is_still_recorded_not_raised(
    mock_parse: MagicMock,
) -> None:
    """Verify a failing task result is still recorded, not raised.

    pipeline_runner's own design goal (see health_runner.py's docstring
    in the health_check project) is to keep running and record False rather
    than raise/crash on an ordinary check failure - confirm a spec-built
    task participates in that the same way a hand-written one does.
    """
    mock_parse.return_value = argparse.Namespace(
        task=None,
        full_pipeline=True,
        root=None,
        stage=None,
        dry_run=False,
        tasks=None,
        skip=None,
    )

    specs = [
        {"id": "WillFail", "type": "recording", "should_pass": False},
        {"id": "WillPass", "type": "recording"},
    ]
    classes = build_task_classes(specs, TYPE_REGISTRY)

    suite = PipelineSuite(all_tasks=classes)
    suite.printer = MagicMock()
    suite._run()

    assert Task._completed["WillFail"] is False
    assert Task._completed["WillPass"] is True
