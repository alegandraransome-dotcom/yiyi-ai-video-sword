from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import StateError
from .state import validate_json_value


DIGEST = re.compile(r"^[0-9a-f]{64}$")
REPORT_KEYS = {
    "schema_version",
    "run_id",
    "task_id",
    "project_id",
    "system_version",
    "source_digest",
    "state_revision",
    "state_digest",
    "route_digest",
    "compilation_digest",
    "wei_skills",
    "observations",
    "flags",
    "protected_values",
    "open_questions",
}
FLAG_CODES = {"WEI-R", "WEI-W", "WEI-K", "WEI-Q"}
_VERIFICATION_SEAL = object()


@dataclass(frozen=True, init=False)
class VerifiedWeiReport:
    """Opaque value accepted by the Heng compiler after frozen-report validation."""

    text: str
    digest: str
    run_id: str
    task_id: str
    project_id: str
    system_version: str
    source_digest: str
    state_revision: int
    state_digest: str
    route_digest: str
    compilation_digest: str
    wei_skills: tuple[str, ...]

    def __init__(
        self,
        text: str,
        digest: str,
        data: dict[str, Any],
        *,
        _seal: object,
    ) -> None:
        if _seal is not _VERIFICATION_SEAL:
            raise StateError("VerifiedWeiReport can only be created by frozen validation")
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "digest", digest)
        for field in (
            "run_id",
            "task_id",
            "project_id",
            "system_version",
            "source_digest",
            "state_revision",
            "state_digest",
            "route_digest",
            "compilation_digest",
        ):
            object.__setattr__(self, field, data[field])
        object.__setattr__(self, "wei_skills", tuple(data["wei_skills"]))


def route_digest(mode: str, module_ids: tuple[str, ...]) -> str:
    payload = json.dumps(
        {"mode": mode, "modules": list(module_ids)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compilation_context_digest(
    mode: str,
    module_ids: tuple[str, ...],
    *,
    skills: tuple[str, ...] = (),
    injections: Mapping[str, str] | None = None,
    compiled_text: str,
) -> str:
    input_digests = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in sorted((injections or {}).items())
    }
    payload = json.dumps(
        {
            "mode": mode,
            "modules": list(module_ids),
            "skills": sorted(skills),
            "inputs": input_digests,
            "compiled_text_sha256": hashlib.sha256(
                compiled_text.encode("utf-8")
            ).hexdigest(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_wei_report(data: Any) -> dict[str, Any]:
    validate_json_value(data, "WEI_REPORT")
    if not isinstance(data, dict):
        raise StateError("WEI_REPORT must be an object")
    if set(data) != REPORT_KEYS:
        missing = sorted(REPORT_KEYS.difference(data))
        extra = sorted(set(data).difference(REPORT_KEYS))
        raise StateError(f"WEI_REPORT field mismatch: missing={missing}, extra={extra}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise StateError("WEI_REPORT schema_version must be 1")
    for field in ("run_id", "task_id", "project_id", "system_version"):
        if not isinstance(data[field], str) or not data[field]:
            raise StateError(f"WEI_REPORT {field} must be a non-empty string")
    try:
        parsed_project_id = uuid.UUID(data["project_id"])
    except ValueError as exc:
        raise StateError("WEI_REPORT project_id must be a canonical UUID") from exc
    if str(parsed_project_id) != data["project_id"]:
        raise StateError("WEI_REPORT project_id must be a canonical UUID")
    for field in (
        "source_digest",
        "state_digest",
        "route_digest",
        "compilation_digest",
    ):
        if not isinstance(data[field], str) or not DIGEST.fullmatch(data[field]):
            raise StateError(f"WEI_REPORT {field} must be a SHA-256 digest")
    if type(data["state_revision"]) is not int or data["state_revision"] < 0:
        raise StateError("WEI_REPORT state_revision must be a non-negative integer")
    for field in ("observations", "flags", "protected_values", "open_questions"):
        if not isinstance(data[field], list):
            raise StateError(f"WEI_REPORT {field} must be an array")
    for field in ("observations", "protected_values", "open_questions"):
        if any(not isinstance(item, (str, dict)) for item in data[field]):
            raise StateError(f"WEI_REPORT {field} items must be strings or objects")
    skills = data["wei_skills"]
    if (
        not isinstance(skills, list)
        or any(not isinstance(skill, str) or not skill for skill in skills)
        or skills != sorted(set(skills))
    ):
        raise StateError("WEI_REPORT wei_skills must be a sorted unique string array")
    for flag in data["flags"]:
        if not isinstance(flag, dict) or set(flag) != {"code", "content"}:
            raise StateError("each WEI_REPORT flag must contain only code and content")
        if flag["code"] not in FLAG_CODES:
            raise StateError(f"unknown WEI_REPORT flag code: {flag['code']}")
        if not isinstance(flag["content"], str) or not flag["content"]:
            raise StateError("WEI_REPORT flag content must be non-empty")
    return data


def canonical_report_bytes(data: dict[str, Any]) -> bytes:
    validate_wei_report(data)
    return (
        json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def freeze_wei_report(data: dict[str, Any], directory: Path) -> Path:
    content = canonical_report_bytes(data)
    digest = hashlib.sha256(content).hexdigest()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{digest}.json"
    try:
        with target.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        if target.read_bytes() != content:
            raise StateError(f"content-addressed WEI_REPORT collision: {target}")
    return target


def load_frozen_wei_report(
    path: Path,
    *,
    source_digest: str,
    system_version: str,
    project_id: str,
    state_revision: int,
    state_digest: str,
    expected_route_digest: str,
    expected_compilation_digest: str,
    expected_run_id: str,
    expected_task_id: str,
    expected_wei_skills: tuple[str, ...] = (),
) -> VerifiedWeiReport:
    content = path.read_bytes()
    actual_digest = hashlib.sha256(content).hexdigest()
    if path.stem != actual_digest:
        raise StateError("frozen WEI_REPORT filename does not match its content digest")
    try:
        data = json.loads(
            content.decode("utf-8"), parse_constant=_reject_json_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, StateError) as exc:
        raise StateError(f"invalid frozen WEI_REPORT: {exc}") from exc
    validate_wei_report(data)
    if canonical_report_bytes(data) != content:
        raise StateError("frozen WEI_REPORT is not canonical JSON")
    expected = {
        "run_id": expected_run_id,
        "task_id": expected_task_id,
        "project_id": project_id,
        "system_version": system_version,
        "source_digest": source_digest,
        "state_revision": state_revision,
        "state_digest": state_digest,
        "route_digest": expected_route_digest,
        "compilation_digest": expected_compilation_digest,
        "wei_skills": list(sorted(set(expected_wei_skills))),
    }
    stale = {key: (data[key], value) for key, value in expected.items() if data[key] != value}
    if stale:
        raise StateError(f"stale WEI_REPORT context: {stale}")
    return VerifiedWeiReport(
        content.decode("utf-8"), actual_digest, data, _seal=_VERIFICATION_SEAL
    )


def validate_verified_wei_report(report: VerifiedWeiReport) -> dict[str, Any]:
    content = report.text.encode("utf-8")
    actual_digest = hashlib.sha256(content).hexdigest()
    if actual_digest != report.digest:
        raise StateError("verified WEI_REPORT token content digest changed")
    try:
        data = json.loads(report.text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, StateError) as exc:
        raise StateError(f"verified WEI_REPORT token is invalid JSON: {exc}") from exc
    validate_wei_report(data)
    if canonical_report_bytes(data) != content:
        raise StateError("verified WEI_REPORT token is not canonical JSON")
    stored = {
        "run_id": report.run_id,
        "task_id": report.task_id,
        "project_id": report.project_id,
        "system_version": report.system_version,
        "source_digest": report.source_digest,
        "state_revision": report.state_revision,
        "state_digest": report.state_digest,
        "route_digest": report.route_digest,
        "compilation_digest": report.compilation_digest,
        "wei_skills": list(report.wei_skills),
    }
    changed = {key: (data[key], value) for key, value in stored.items() if data[key] != value}
    if changed:
        raise StateError(f"verified WEI_REPORT token context changed: {changed}")
    return data


def _reject_json_constant(value: str) -> None:
    raise StateError(f"non-standard JSON constant is forbidden: {value}")
