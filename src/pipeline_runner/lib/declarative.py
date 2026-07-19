"""Build SuiteTask subclasses from plain dict specs.

This module allows a task to be declared as data (e.g. one entry in a YAML
file) instead of the usual four manual steps: write a class, import it, add
it to a task list, wire that list into a PipelineSuite.

This module has no opinion on what "kinds" of task exist -- callers supply a
`type_registry` mapping a spec's `type` string to whatever SuiteTask subclass
should back it. All other spec keys become plain class attributes on the
generated class.

Two design notes, both already true of the framework before this module:
  - Task.get_task_name() already treats a plain string the same as a class
    reference when resolving `_deps`, so a spec's ``deps: [OtherTaskId]`` list
    works with zero special handling here.
  - PipelineSuite._run() runs ``all_tasks`` in list order, not dependency
    order -- ``_deps`` only drives instantiation-on-demand and downstream
    aggregation, not scheduling. Spec order in the list you pass to
    build_task_classes() is therefore the run order.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from pipeline_runner.lib.task_types.suite_task import SuiteTask


def build_task_class(
    spec: dict[str, Any],
    type_registry: Mapping[str, type[SuiteTask]],
) -> type[SuiteTask]:
    """Build a single SuiteTask subclass from one spec dict.

    Required keys: ``id`` (becomes the Python class name / Task registry key
    / what ``deps`` lists reference) and ``type`` (looked up in
    type_registry for the base class). An optional ``deps`` key becomes
    ``_deps`` on the class. Every other key is set verbatim as a class
    attribute.
    """
    spec = dict(spec)

    class_id = spec.pop("id", None)
    if not class_id:
        msg = f"Task spec missing required 'id' field: {spec!r}"
        raise ValueError(msg)

    kind = spec.pop("type", None)
    if kind is None:
        msg = f"Task spec {class_id!r} missing required 'type' field"
        raise ValueError(msg)
    if kind not in type_registry:
        msg = (
            f"Task spec {class_id!r} has unknown type {kind!r}; "
            f"known types: {sorted(type_registry)}"
        )
        raise ValueError(msg)
    base = type_registry[kind]

    if "deps" in spec:
        spec["_deps"] = spec.pop("deps")

    return type(class_id, (base,), spec)


def build_task_classes(
    specs: list[dict[str, Any]],
    type_registry: Mapping[str, type[SuiteTask]],
) -> list[type[SuiteTask]]:
    """Build a list of SuiteTask subclasses from a list of spec dicts.

    Spec order is run order.
    """
    return [build_task_class(spec, type_registry) for spec in specs]


def load_task_classes_from_yaml(
    path: str,
    type_registry: Mapping[str, type[SuiteTask]],
) -> list[type[SuiteTask]]:
    """Read a YAML file of task specs and build classes from it.

    PyYAML is a real declared dependency of this module (see package.nix's
    runtimeDeps / pyproject.toml's dependencies), not an optional one hidden
    behind a deferred import.
    """
    with Path(path).open() as f:
        raw: list[dict[str, Any]] = yaml.safe_load(f) or []
    return build_task_classes(raw, type_registry)
