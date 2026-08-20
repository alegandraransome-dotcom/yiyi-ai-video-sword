from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
from typing import Any, Protocol

import yaml

from .errors import ManifestError


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
INJECTION = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CANONICAL_MODULE_LAYOUT = {
    "bootstrap": ("runtime/bootstrap.md", 0),
    "kernel-entry": ("runtime/modules/00-kernel/00-entry.md", 10),
    "kernel-wei-seed": ("runtime/modules/00-kernel/10-wei-seed.md", 11),
    "kernel-heng-seed": ("runtime/modules/00-kernel/20-heng-seed.md", 12),
    "kernel-routing": ("runtime/modules/00-kernel/30-routing.md", 13),
    "persona-intro": ("runtime/modules/01-personas/00-intro.md", 20),
    "persona-wei": ("runtime/modules/01-personas/10-wei.md", 21),
    "persona-heng": ("runtime/modules/01-personas/20-heng.md", 22),
    "persona-pair": ("runtime/modules/01-personas/30-pair.md", 23),
    "preproduction": ("runtime/modules/02-preproduction.md", 30),
    "directing-design": ("runtime/modules/03-directing-design.md", 40),
    "execution-continuity": ("runtime/modules/04-execution-continuity.md", 50),
    "formal-script": ("runtime/modules/05-formal-script.md", 60),
    "reread-handoff": ("runtime/modules/06-reread-handoff.md", 70),
    "review-rework": ("runtime/modules/07-review-rework.md", 80),
    "project-state": ("runtime/modules/08-project-state.md", 90),
    "migration-tests": ("runtime/modules/09-migration-tests.md", 100),
    "asset-image-adapter": ("runtime/modules/10-asset-image-adapter.md", 110),
}
EXPECTED_RUNTIME_MODES = {
    "startup",
    "preproduction",
    "directing",
    "formal-production",
    "continuation",
    "local-revision",
    "review-rework",
    "asset-production",
    "wei-first-read",
    "heng-decision",
    "maintenance",
    "full-runtime",
}


class TextReader(Protocol):
    def read_text(self, path: str) -> str: ...


@dataclass(frozen=True)
class Module:
    id: str
    path: str
    order: int
    role: str
    tags: tuple[str, ...]


def safe_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"relative path must be a non-empty string: {value!r}")
    if "\\" in value or "\x00" in value:
        raise ManifestError(f"unsafe relative path: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ManifestError(f"unsafe relative path: {value}")
    if any(part in {"", "."} for part in path.parts):
        raise ManifestError(f"non-canonical relative path: {value}")
    return path.as_posix()


def parse_manifest(text: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a mapping")
    validate_manifest(data)
    return data


def load_manifest(path: Path) -> dict[str, Any]:
    return parse_manifest(path.read_text(encoding="utf-8"))


def modules_from_manifest(data: dict[str, Any]) -> list[Module]:
    modules: list[Module] = []
    for raw in data["modules"]:
        modules.append(
            Module(
                id=raw["id"],
                path=safe_relative_path(raw["path"]),
                order=int(raw["order"]),
                role=raw["role"],
                tags=tuple(raw.get("tags", [])),
            )
        )
    return modules


def validate_manifest(data: dict[str, Any]) -> None:
    if type(data.get("format_version")) is not int or data["format_version"] != 1:
        raise ManifestError("format_version must be 1")
    for key in (
        "system",
        "runtime",
        "personas",
        "modules",
        "internal_skills",
        "runtime_modes",
        "routes",
        "pipelines",
        "evals",
        "package",
    ):
        if key not in data:
            raise ManifestError(f"missing manifest key: {key}")

    system = _mapping(data["system"], "system")
    for field in (
        "id",
        "name",
        "version",
        "status",
        "language",
        "package_extension",
        "runtime_min_version",
        "canonical_source_sha256",
        "baseline",
    ):
        if not isinstance(system.get(field), str) or not system[field]:
            raise ManifestError(f"system.{field} must be a non-empty string")
    if not IDENTIFIER.fullmatch(system["id"]):
        raise ManifestError("system.id must be a lowercase identifier")
    if system["package_extension"] != ".yios":
        raise ManifestError("system.package_extension must be .yios")
    if not SHA256.fullmatch(system["canonical_source_sha256"]):
        raise ManifestError("system.canonical_source_sha256 must be a SHA-256 digest")

    runtime = _mapping(data["runtime"], "runtime")
    always_on = _mapping(runtime.get("always_on"), "runtime.always_on")
    for group in ("shared", "pair", "wei", "heng"):
        if group not in always_on:
            raise ManifestError(f"runtime.always_on missing group: {group}")
    accepted_common = _injection_list(
        runtime.get("accepted_injections", []), "runtime.accepted_injections"
    )
    for field in ("canonical_order_file", "state_schema", "handoff_schema"):
        safe_relative_path(runtime.get(field))

    if not isinstance(data["modules"], list) or not data["modules"]:
        raise ManifestError("modules must be a non-empty list")

    ids: set[str] = set()
    paths: set[str] = set()
    orders: set[int] = set()
    layout: dict[str, tuple[str, int]] = {}
    for raw in data["modules"]:
        if not isinstance(raw, dict):
            raise ManifestError("each module must be a mapping")
        for key in ("id", "path", "order", "role"):
            if key not in raw:
                raise ManifestError(f"module missing {key}: {raw}")
        module_id = raw["id"]
        if not isinstance(module_id, str) or not IDENTIFIER.fullmatch(module_id):
            raise ManifestError(f"invalid module id: {module_id!r}")
        path = safe_relative_path(raw["path"])
        if type(raw["order"]) is not int:
            raise ManifestError(f"module order must be an integer: {module_id}")
        order = raw["order"]
        if not isinstance(raw["role"], str) or not raw["role"]:
            raise ManifestError(f"module role must be a non-empty string: {module_id}")
        tags = raw.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ManifestError(f"module tags must be an array of strings: {module_id}")
        if module_id in ids:
            raise ManifestError(f"duplicate module id: {module_id}")
        if path in paths:
            raise ManifestError(f"duplicate module path: {path}")
        if order in orders:
            raise ManifestError(f"duplicate module order: {order}")
        ids.add(module_id)
        paths.add(path)
        orders.add(order)
        layout[module_id] = (path, order)

    if layout != CANONICAL_MODULE_LAYOUT:
        missing = sorted(set(CANONICAL_MODULE_LAYOUT).difference(layout))
        extra = sorted(set(layout).difference(CANONICAL_MODULE_LAYOUT))
        changed = sorted(
            module_id
            for module_id in set(layout).intersection(CANONICAL_MODULE_LAYOUT)
            if layout[module_id] != CANONICAL_MODULE_LAYOUT[module_id]
        )
        raise ManifestError(
            f"canonical module layout mismatch: missing={missing}, "
            f"extra={extra}, changed={changed}"
        )

    for group, values in always_on.items():
        if not isinstance(group, str):
            raise ManifestError("runtime.always_on group names must be strings")
        _validate_module_refs(values, ids, f"runtime.always_on.{group}")
    expected_always = {
        "shared": ["kernel-entry", "kernel-routing", "project-state"],
        "pair": ["kernel-wei-seed", "kernel-heng-seed"],
        "wei": ["kernel-wei-seed"],
        "heng": ["kernel-heng-seed"],
    }
    if always_on != expected_always:
        raise ManifestError("runtime.always_on violates the fixed 00/08 persona core")

    personas = _mapping(data["personas"], "personas")
    for persona in ("wei", "heng"):
        config = _mapping(personas.get(persona), f"personas.{persona}")
        for field in ("seed", "core"):
            if config.get(field) not in ids:
                raise ManifestError(
                    f"personas.{persona}.{field} references unknown module: "
                    f"{config.get(field)!r}"
                )
        accepted = _injection_list(
            config.get("accepted_injections", []),
            f"personas.{persona}.accepted_injections",
        )
        forbidden = _injection_list(
            config.get("forbidden_injections", []),
            f"personas.{persona}.forbidden_injections",
        )
        if accepted.intersection(forbidden):
            raise ManifestError(f"personas.{persona} accepts and forbids the same injection")

    runtime_modes = _mapping(data["runtime_modes"], "runtime_modes")
    if not runtime_modes:
        raise ManifestError("runtime_modes must not be empty")
    if set(runtime_modes) != EXPECTED_RUNTIME_MODES:
        missing = sorted(EXPECTED_RUNTIME_MODES.difference(runtime_modes))
        extra = sorted(set(runtime_modes).difference(EXPECTED_RUNTIME_MODES))
        raise ManifestError(
            f"runtime mode set mismatch: missing={missing}, extra={extra}"
        )
    for name, config in runtime_modes.items():
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
            raise ManifestError(f"invalid runtime mode name: {name!r}")
        if not isinstance(config, dict):
            raise ManifestError(f"runtime mode {name} must be a mapping")
        persona = config.get("persona", "pair")
        if persona not in {"pair", "wei", "heng"}:
            raise ManifestError(f"runtime mode {name} has invalid persona: {persona}")
        _validate_module_refs(config.get("loads", []), ids, f"runtime_modes.{name}.loads")
        _validate_module_refs(config.get("forbids", []), ids, f"runtime_modes.{name}.forbids")
        if set(config.get("loads", [])).intersection(config.get("forbids", [])):
            raise ManifestError(f"runtime mode {name} loads a forbidden module")
        required_injections = _injection_list(
            config.get("requires_injections", []),
            f"runtime_modes.{name}.requires_injections",
        )
        persona_accepted = set(
            personas.get(persona, {}).get("accepted_injections", [])
        )
        unavailable = required_injections.difference(accepted_common | persona_accepted)
        if unavailable:
            raise ManifestError(
                f"runtime mode {name} requires unavailable injections: {sorted(unavailable)}"
            )

    _validate_runtime_invariants(data, ids)

    internal_skills = _mapping(data["internal_skills"], "internal_skills")
    for skill, config in internal_skills.items():
        if not isinstance(skill, str) or not IDENTIFIER.fullmatch(skill):
            raise ManifestError(f"invalid internal skill id: {skill!r}")
        config = _mapping(config, f"internal_skills.{skill}")
        if not isinstance(config.get("description"), str) or not config["description"]:
            raise ManifestError(f"internal_skills.{skill}.description must be text")
        _validate_module_refs(config.get("loads", []), ids, f"internal_skills.{skill}.loads")

    mode_names = set(runtime_modes)
    if not isinstance(data["routes"], list) or not data["routes"]:
        raise ManifestError("routes must be a non-empty list")
    for route in data["routes"]:
        route = _mapping(route, "route")
        if route.get("mode") not in mode_names:
            raise ManifestError(f"route references unknown mode: {route.get('mode')}")
        if type(route.get("priority")) is not int:
            raise ManifestError(f"route priority must be an integer: {route}")
        patterns = route.get("patterns")
        if (
            not isinstance(patterns, list)
            or not patterns
            or any(not isinstance(pattern, str) or not pattern for pattern in patterns)
        ):
            raise ManifestError(f"route has no patterns: {route}")

    pipelines = _mapping(data["pipelines"], "pipelines")
    for pipeline_name, pipeline in pipelines.items():
        if not isinstance(pipeline_name, str) or not IDENTIFIER.fullmatch(pipeline_name):
            raise ManifestError(f"invalid pipeline id: {pipeline_name!r}")
        pipeline = _mapping(pipeline, f"pipelines.{pipeline_name}")
        passes = pipeline.get("passes", [])
        if not isinstance(passes, list) or not passes:
            raise ManifestError(f"pipeline {pipeline_name} has no passes")
        pass_ids: set[str] = set()
        for runtime_pass in passes:
            runtime_pass = _mapping(runtime_pass, f"pipelines.{pipeline_name}.pass")
            pass_id = runtime_pass.get("id")
            if not isinstance(pass_id, str) or not IDENTIFIER.fullmatch(pass_id):
                raise ManifestError(f"pipeline {pipeline_name} has invalid pass id")
            if pass_id in pass_ids:
                raise ManifestError(f"pipeline {pipeline_name} has duplicate pass: {pass_id}")
            pass_ids.add(pass_id)
            if runtime_pass.get("mode") not in mode_names:
                raise ManifestError(
                    f"pipeline {pipeline_name} references unknown mode: {runtime_pass.get('mode')}"
                )
            pass_requires = _injection_list(
                runtime_pass.get("requires", []),
                f"pipelines.{pipeline_name}.{pass_id}.requires",
            )
            mode_requires = set(
                runtime_modes[runtime_pass["mode"]].get("requires_injections", [])
            )
            missing_requires = mode_requires.difference(pass_requires)
            if missing_requires:
                raise ManifestError(
                    f"pipeline {pipeline_name} pass {pass_id} omits mode requirements: "
                    f"{sorted(missing_requires)}"
                )

    evals = _mapping(data["evals"], "evals")
    for field in ("cases", "source_protocol"):
        safe_relative_path(evals.get(field))
    if type(evals.get("pass_score")) is not int or evals["pass_score"] < 0:
        raise ManifestError("evals.pass_score must be a non-negative integer")

    package = _mapping(data["package"], "package")
    includes = package.get("include")
    if not isinstance(includes, list) or not includes:
        raise ManifestError("package.include must be a non-empty list")
    safe_includes = [safe_relative_path(value) for value in includes]
    if len(safe_includes) != len(set(safe_includes)):
        raise ManifestError("package.include contains duplicate paths")
    expected_includes = {
        "mimetype",
        "manifest.yaml",
        "LICENSE",
        "runtime",
        "schemas",
        "evals",
        "internal-skills",
        "THIRD_PARTY_NOTICES.md",
    }
    if set(safe_includes) != expected_includes:
        missing = sorted(expected_includes.difference(safe_includes))
        extra = sorted(set(safe_includes).difference(expected_includes))
        raise ManifestError(
            f"package.include field mismatch: missing={missing}, extra={extra}"
        )


def _validate_module_refs(values: Any, known: set[str], field: str) -> None:
    if not isinstance(values, list):
        raise ManifestError(f"{field} must be a list")
    if any(not isinstance(value, str) for value in values):
        raise ManifestError(f"{field} must contain only strings")
    if len(values) != len(set(values)):
        raise ManifestError(f"{field} contains duplicate module references")
    unknown = [value for value in values if value not in known]
    if unknown:
        raise ManifestError(f"{field} references unknown modules: {unknown}")


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{field} must be a mapping")
    return value


def _injection_list(value: Any, field: str) -> set[str]:
    if not isinstance(value, list):
        raise ManifestError(f"{field} must be a list")
    if any(not isinstance(item, str) or not INJECTION.fullmatch(item) for item in value):
        raise ManifestError(f"{field} contains an invalid injection name")
    if len(value) != len(set(value)):
        raise ManifestError(f"{field} contains duplicate injection names")
    return set(value)


def _validate_runtime_invariants(data: dict[str, Any], ids: set[str]) -> None:
    personas = data["personas"]
    expected_personas = {
        "wei": ("kernel-wei-seed", "persona-wei"),
        "heng": ("kernel-heng-seed", "persona-heng"),
    }
    for persona, (seed, core) in expected_personas.items():
        if personas[persona].get("seed") != seed or personas[persona].get("core") != core:
            raise ManifestError(f"personas.{persona} seed/core identity is fixed")

    common_inputs = set(data["runtime"].get("accepted_injections", []))
    expected_common = {"PROJECT_STATE", "CURRENT_SCRIPT", "CURRENT_ASSETS", "TASK_CONTEXT"}
    if common_inputs != expected_common:
        raise ManifestError("runtime accepted injection allowlist is fixed")
    if set(personas["wei"].get("accepted_injections", [])):
        raise ManifestError("Wei must not accept persona-private injections")
    if set(personas["heng"].get("accepted_injections", [])) != {"WEI_REPORT"}:
        raise ManifestError("Heng must accept only the verified WEI_REPORT extension")

    modes = data["runtime_modes"]
    expected_persona = {name: "pair" for name in EXPECTED_RUNTIME_MODES}
    expected_persona["wei-first-read"] = "wei"
    expected_persona["heng-decision"] = "heng"
    always = data["runtime"]["always_on"]
    selections: dict[str, set[str]] = {}
    for name, config in modes.items():
        persona = config.get("persona", "pair")
        if persona != expected_persona[name]:
            raise ManifestError(f"runtime mode {name} has a fixed persona")
        selected = set(always["shared"]) | set(always[persona]) | set(config["loads"])
        if not {"kernel-entry", "kernel-routing", "project-state"}.issubset(selected):
            raise ManifestError(f"runtime mode {name} bypasses the 00/08 core")
        if selected.intersection(config.get("forbids", [])):
            raise ManifestError(f"runtime mode {name} selects a forbidden module")
        selections[name] = selected

    wei = selections["wei-first-read"]
    if not {"kernel-wei-seed", "persona-wei"}.issubset(wei) or wei.intersection(
        {"kernel-heng-seed", "persona-heng"}
    ):
        raise ManifestError("wei-first-read violates persona isolation")
    if not {"kernel-heng-seed", "persona-heng"}.issubset(
        selections["heng-decision"]
    ) or selections["heng-decision"].intersection(
        {"kernel-wei-seed", "persona-wei"}
    ):
        raise ManifestError("heng-decision violates persona isolation")

    formal = selections["formal-production"]
    if not {"directing-design", "execution-continuity", "formal-script"}.issubset(
        formal
    ) or formal.intersection({"migration-tests", "asset-image-adapter"}):
        raise ManifestError("formal-production violates the 03/04/05 boundary")
    assets = selections["asset-production"]
    if "asset-image-adapter" not in assets or assets.intersection(
        {"formal-script", "migration-tests"}
    ):
        raise ManifestError("asset-production violates the Module 10 boundary")

    for name, selected in selections.items():
        if name not in {"maintenance", "full-runtime"} and "migration-tests" in selected:
            raise ManifestError(f"runtime mode {name} illegally loads Module 09")
        if name not in {"asset-production", "maintenance", "full-runtime"} and (
            "asset-image-adapter" in selected
        ):
            raise ManifestError(f"runtime mode {name} illegally loads Module 10")

    if "migration-tests" not in selections["maintenance"]:
        raise ManifestError("maintenance must load Module 09")
    if selections["full-runtime"] != ids or modes["full-runtime"].get("exact_source") is not True:
        raise ManifestError("full-runtime must select the exact canonical module set")
    if set(modes["heng-decision"].get("requires_injections", [])) != {
        "PROJECT_STATE",
        "WEI_REPORT",
    }:
        raise ManifestError("heng-decision input gate is fixed")
