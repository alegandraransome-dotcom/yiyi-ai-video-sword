from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

from .compiler import RuntimeCompiler
from .errors import ManifestError, PackageError
from .evals import load_eval_suite
from .manifest import safe_relative_path
from .package import validate_source_tree, verify_package


def validate_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = validate_source_tree(root)
    compiler = RuntimeCompiler.from_source(root)
    load_eval_suite(root / manifest["evals"]["cases"])
    _verify_archive_hashes(root)
    _verify_runtime_text(root, manifest)
    _verify_project_metadata(root, manifest)
    _verify_internal_skill_descriptors(root, manifest)
    _verify_schema_documents(root, manifest)

    shared_required = {"kernel-entry", "kernel-routing", "project-state"}
    compiled_modes: dict[str, tuple[str, ...]] = {}
    for mode in compiler.available_modes():
        selected = tuple(module.id for module in compiler.select_modules(mode))
        compiled_modes[mode] = selected
        if not shared_required.issubset(selected):
            raise ManifestError(f"mode {mode} bypasses 00/08 shared core")
        if len(selected) != len(set(selected)):
            raise ManifestError(f"mode {mode} loads duplicate modules")

    if "migration-tests" in compiled_modes["formal-production"]:
        raise ManifestError("formal-production must not load Module 09")
    if "asset-image-adapter" in compiled_modes["formal-production"]:
        raise ManifestError("formal-production must not load Module 10 by default")
    if "formal-script" in compiled_modes["asset-production"]:
        raise ManifestError("asset-production must not load formal-script")
    for required in ("directing-design", "execution-continuity", "formal-script"):
        if required not in compiled_modes["formal-production"]:
            raise ManifestError(f"formal-production missing {required}")
    if "migration-tests" not in compiled_modes["maintenance"]:
        raise ManifestError("maintenance mode must include Module 09")

    wei = set(compiled_modes["wei-first-read"])
    heng = set(compiled_modes["heng-decision"])
    if wei.intersection({"kernel-heng-seed", "persona-heng"}):
        raise ManifestError("Wei runtime leaks Heng persona modules")
    if heng.intersection({"kernel-wei-seed", "persona-wei"}):
        raise ManifestError("Heng runtime leaks Wei persona modules")

    full = compiler.compile("full-runtime")
    digest = hashlib.sha256(full.text.encode("utf-8")).hexdigest()
    expected = manifest["system"]["canonical_source_sha256"]
    if digest != expected:
        raise PackageError(f"full-runtime digest mismatch: {digest} != {expected}")

    return {
        "system": manifest["system"],
        "mode_count": len(compiled_modes),
        "module_count": len(compiler.modules),
        "full_runtime_sha256": digest,
        "eval_suite": manifest["evals"]["cases"],
    }


def validate_target(path: Path) -> dict[str, Any]:
    return verify_package(path) if path.is_file() else validate_repository(path)


def _verify_archive_hashes(root: Path) -> None:
    archive_root = root / "archive"
    for checksum_file in (
        archive_root / "SHA256SUMS",
        archive_root / "beta-r2/SHA256SUMS",
    ):
        _verify_checksum_file(checksum_file)

    sources_file = archive_root / "SOURCES.yaml"
    try:
        sources = yaml.safe_load(sources_file.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PackageError(f"invalid archive/SOURCES.yaml: {exc}") from exc
    if not isinstance(sources, dict) or sources.get("format_version") != 1:
        raise PackageError("archive/SOURCES.yaml format_version must be 1")
    inputs = sources.get("input_archives")
    if not isinstance(inputs, list):
        raise PackageError("archive/SOURCES.yaml input_archives must be an array")
    for item in inputs:
        if not isinstance(item, dict) or not _is_sha256(item.get("sha256")):
            raise PackageError("archive source entry has an invalid SHA-256")
        retained = item.get("retained_as")
        if retained is None:
            continue
        relative = safe_relative_path(retained)
        target = (archive_root / relative).resolve()
        if not target.is_relative_to(archive_root) or not target.is_file():
            raise PackageError(f"missing retained archive source: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise PackageError(f"retained archive source drift: {relative}")


def _verify_checksum_file(checksum_file: Path) -> None:
    base = checksum_file.parent.resolve()
    seen: set[str] = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise PackageError(f"malformed checksum line in {checksum_file}: {line!r}")
        expected, raw_relative = match.groups()
        relative = safe_relative_path(raw_relative)
        if relative in seen:
            raise PackageError(f"duplicate checksum path: {relative}")
        seen.add(relative)
        target = (base / relative).resolve()
        if not target.is_relative_to(base) or not target.is_file():
            raise PackageError(f"missing frozen archive file: {relative}")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise PackageError(f"frozen archive drift: {relative}")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _verify_runtime_text(root: Path, manifest: dict[str, Any]) -> None:
    chunks: list[str] = []
    for module in sorted(manifest["modules"], key=lambda item: int(item["order"])):
        content = (root / module["path"]).read_bytes()
        if content.startswith(b"\xef\xbb\xbf"):
            raise PackageError(f"UTF-8 BOM is forbidden: {module['path']}")
        if b"\r" in content:
            raise PackageError(f"runtime text must use LF endings: {module['path']}")
        chunks.append(content.decode("utf-8"))
    full = "".join(chunks)
    if full.count("```") % 2:
        raise PackageError("canonical runtime has an unpaired code fence")
    for module_id in range(11):
        begin = f"<!-- BEGIN MODULE {module_id:02d} -->"
        end = f"<!-- END MODULE {module_id:02d} -->"
        if full.count(begin) != 1 or full.count(end) != 1:
            raise PackageError(f"module marker mismatch: {module_id:02d}")


def _verify_project_metadata(root: Path, manifest: dict[str, Any]) -> None:
    try:
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        raise PackageError(f"invalid pyproject.toml: {exc}") from exc
    expected = manifest["system"]["runtime_min_version"]
    if project.get("version") != expected:
        raise PackageError(
            f"version mismatch: pyproject={project.get('version')!r}, manifest={expected!r}"
        )


def _verify_internal_skill_descriptors(root: Path, manifest: dict[str, Any]) -> None:
    for skill_id, declaration in manifest["internal_skills"].items():
        path = root / "internal-skills" / f"{skill_id}.yaml"
        try:
            descriptor = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise PackageError(f"invalid internal skill descriptor {skill_id}: {exc}") from exc
        if not isinstance(descriptor, dict) or descriptor.get("id") != skill_id:
            raise PackageError(f"internal skill descriptor id mismatch: {skill_id}")
        if descriptor.get("loads") != declaration["loads"]:
            raise PackageError(f"internal skill loads drift: {skill_id}")
        for field in ("name", "purpose"):
            if not isinstance(descriptor.get(field), str) or not descriptor[field]:
                raise PackageError(f"internal skill {skill_id} missing {field}")
        for field in ("triggers", "constraints", "upstream_evidence"):
            values = descriptor.get(field)
            if not isinstance(values, list) or not values:
                raise PackageError(f"internal skill {skill_id} missing {field}")
        for raw in descriptor["upstream_evidence"]:
            relative = safe_relative_path(raw)
            evidence = (root / relative).resolve()
            if not evidence.is_relative_to(root) or not evidence.is_file():
                raise PackageError(
                    f"internal skill {skill_id} missing upstream evidence: {relative}"
                )


def _verify_schema_documents(root: Path, manifest: dict[str, Any]) -> None:
    schema_paths = {
        manifest["runtime"]["state_schema"],
        manifest["runtime"]["handoff_schema"],
        "schemas/wei-report.schema.json",
    }
    for raw in schema_paths:
        relative = safe_relative_path(raw)
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise PackageError(f"missing schema document: {relative}")
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PackageError(f"invalid schema document {relative}: {exc}") from exc
        if not isinstance(schema, dict) or schema.get("type") != "object":
            raise PackageError(f"schema document root must describe an object: {relative}")
