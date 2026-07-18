"""
Build SuiteTask subclasses from plain dict specs, so a task can be declared
as data (e.g. one entry in a YAML file) instead of the usual four manual
steps: write a class, import it, add it to a task list, wire that list into
a PipelineSuite.

This module has no opinion on what "kinds" of task exist - callers supply a
`type_registry` mapping a spec's `type` string to whatever SuiteTask
subclass should back it (e.g. a project's own ServiceTask/HttpTask/
CommandTask base classes). All other spec keys become plain class
attributes on the generated class, exactly as if they'd been written by
hand as `class Foo(Base): key = value`.

Two things this deliberately leans on, both already true of the framework
before this module existed:
  - Task.get_task_name() (lib/task_types/helpers.py) already treats a plain
    string the same as a class reference when resolving `_deps` - so a
    spec's `deps: [OtherTaskId]` list of id strings works with zero special
    handling here.
  - PipelineSuite._run() (core/suite.py) runs `all_tasks` in list order,
    not dependency order - `_deps` only drives instantiation-on-demand and
    downstream aggregation (e.g. a task reading Task._completed), not
    scheduling. Spec order in the list you pass to build_task_classes() is
    therefore the run order; keep dependents after their dependencies.
"""

from typing import Any, Mapping

import yaml

from pipeline_runner.lib.task_types.suite_task import SuiteTask


def build_task_class(
    spec: dict[str, Any], type_registry: Mapping[str, type[SuiteTask]]
) -> type[SuiteTask]:
    """Build a single SuiteTask subclass from one spec dict.

    Required keys: `id` (becomes the Python class name / Task registry key
    / what `deps` lists reference) and `type` (looked up in type_registry
    for the base class). An optional `deps` key becomes `_deps` on the
    class. Every other key - including `name`, the human-readable display
    string SuiteTask itself already uses in messages (self.msg(self.name))
    - is set verbatim as a class attribute. `id` and `name` are
    deliberately separate fields, not one dual-purpose one: every
    hand-written check class already has this same split (a Python class
    name distinct from its `name = "Check Whatever"` attribute), and
    reusing `name` for the registry key here would silently shadow that
    attribute instead of setting it.
    """
    spec = dict(spec)  # never mutate the caller's dict

    class_id = spec.pop("id", None)
    if not class_id:
        raise ValueError(f"Task spec missing required 'id' field: {spec!r}")

    kind = spec.pop("type", None)
    if kind is None:
        raise ValueError(f"Task spec {class_id!r} missing required 'type' field")
    if kind not in type_registry:
        raise ValueError(
            f"Task spec {class_id!r} has unknown type {kind!r}; "
            f"known types: {sorted(type_registry)}"
        )
    base = type_registry[kind]

    if "deps" in spec:
        spec["_deps"] = spec.pop("deps")

    return type(class_id, (base,), spec)


def build_task_classes(
    specs: list[dict[str, Any]], type_registry: Mapping[str, type[SuiteTask]]
) -> list[type[SuiteTask]]:
    """Build a list of SuiteTask subclasses from a list of spec dicts, in
    the given order. See module docstring: spec order is run order."""
    return [build_task_class(spec, type_registry) for spec in specs]


def load_task_classes_from_yaml(
    path: str, type_registry: Mapping[str, type[SuiteTask]]
) -> list[type[SuiteTask]]:
    """Convenience: read a YAML file of task specs and build classes from
    it. PyYAML is a real declared dependency of this module (see
    package.nix's runtimeDeps / pyproject.toml's dependencies), not an
    optional one hidden behind a deferred import."""
    with open(path) as f:
        specs = yaml.safe_load(f) or []
    return build_task_classes(specs, type_registry)
