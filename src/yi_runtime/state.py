from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterator

try:  # pragma: no cover - platform selection
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None  # type: ignore[assignment]
    import msvcrt

from .errors import StateError


HANDOFF_FIELDS = ("POSITION", "STATE", "LOCKS", "PROTECTED", "NEXT", "REREAD")
TOP_LEVEL_FIELDS = {
    "schema_version",
    "revision",
    "project_id",
    "project",
    "updated_at",
    "long_term",
    "entities",
    "HANDOFF",
}


def new_project_state(
    project: str,
    *,
    format_name: str | None = None,
    pipeline: str | None = None,
) -> dict[str, Any]:
    if not project.strip():
        raise StateError("project name must not be empty")
    return {
        "schema_version": 1,
        "revision": 0,
        "project_id": str(uuid.uuid4()),
        "project": project.strip(),
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "long_term": {
            "format": format_name,
            "pipeline": pipeline,
            "characters": {},
            "locations": {},
            "baseline": {"visual": None, "camera": None, "lighting": None, "sound": None},
            "world_rules": [],
            "frozen_decisions": [],
            "protected": [],
        },
        "entities": {},
        "HANDOFF": {
            "POSITION": "尚未开拍",
            "STATE": {},
            "LOCKS": [],
            "PROTECTED": [],
            "NEXT": "读取剧本并进入统筹",
            "REREAD": [],
            "REREAD_DEBT": [],
        },
    }


def validate_project_state(data: Any) -> dict[str, Any]:
    validate_json_value(data, "project state")
    if not isinstance(data, dict):
        raise StateError("project state root must be an object")
    if set(data) != TOP_LEVEL_FIELDS:
        missing = sorted(TOP_LEVEL_FIELDS.difference(data))
        extra = sorted(set(data).difference(TOP_LEVEL_FIELDS))
        raise StateError(f"project state field mismatch: missing={missing}, extra={extra}")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise StateError("schema_version must be 1")
    if type(data.get("revision")) is not int or data["revision"] < 0:
        raise StateError("revision must be a non-negative integer")
    project_id = data.get("project_id")
    try:
        parsed_project_id = uuid.UUID(project_id) if isinstance(project_id, str) else None
    except ValueError as exc:
        raise StateError("project_id must be a canonical UUID") from exc
    if parsed_project_id is None or str(parsed_project_id) != project_id:
        raise StateError("project_id must be a canonical UUID")
    if not isinstance(data.get("project"), str) or not data["project"].strip():
        raise StateError("project must be a non-empty string")
    if not isinstance(data.get("updated_at"), str):
        raise StateError("updated_at must be a date-time string")
    try:
        updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise StateError("updated_at must be a valid date-time string") from exc
    if updated_at.tzinfo is None:
        raise StateError("updated_at must include a timezone")
    long_term = data.get("long_term")
    if not isinstance(long_term, dict):
        raise StateError("long_term must be an object")
    for field in (
        "format",
        "pipeline",
        "characters",
        "locations",
        "baseline",
        "world_rules",
        "frozen_decisions",
        "protected",
    ):
        if field not in long_term:
            raise StateError(f"long_term missing field: {field}")
    for field in ("format", "pipeline"):
        if long_term[field] is not None and not isinstance(long_term[field], str):
            raise StateError(f"long_term.{field} must be a string or null")
    for field in ("characters", "locations", "baseline"):
        if not isinstance(long_term[field], dict):
            raise StateError(f"long_term.{field} must be an object")
    for field, value in long_term["baseline"].items():
        if value is not None and not isinstance(value, (str, dict)):
            raise StateError(
                f"long_term.baseline.{field} must be a string, object or null"
            )
    for field in ("world_rules", "frozen_decisions", "protected"):
        if not isinstance(long_term[field], list):
            raise StateError(f"long_term.{field} must be an array")

    handoff = data.get("HANDOFF")
    if not isinstance(handoff, dict):
        raise StateError("HANDOFF must be an object")
    missing = [field for field in HANDOFF_FIELDS if field not in handoff]
    if missing:
        raise StateError(f"HANDOFF missing fields: {missing}")
    allowed_handoff = set(HANDOFF_FIELDS) | {"REREAD_DEBT"}
    extra_handoff = sorted(set(handoff).difference(allowed_handoff))
    if extra_handoff:
        raise StateError(f"HANDOFF has unknown fields: {extra_handoff}")
    if not isinstance(handoff["POSITION"], (str, dict)):
        raise StateError("HANDOFF.POSITION must be a string or object")
    for field in ("LOCKS", "PROTECTED", "REREAD", "REREAD_DEBT"):
        if field == "REREAD_DEBT" and field not in handoff:
            continue
        if not isinstance(handoff[field], list):
            raise StateError(f"HANDOFF.{field} must be an array")
        if any(not isinstance(item, (str, dict)) for item in handoff[field]):
            raise StateError(f"HANDOFF.{field} items must be strings or objects")
    if not isinstance(handoff["STATE"], dict):
        raise StateError("HANDOFF.STATE must be an object")
    if not isinstance(handoff["NEXT"], str):
        raise StateError("HANDOFF.NEXT must be a string")

    entities = data.get("entities", {})
    if not isinstance(entities, dict):
        raise StateError("entities must be an object")
    for entity_id, entity in entities.items():
        if not isinstance(entity_id, str):
            raise StateError("entity ids must be strings")
        if not isinstance(entity, dict):
            raise StateError(f"entity {entity_id} must be an object")
        required = {"base_state", "accumulated_changes", "current_state"}
        if set(entity) != required:
            missing_entity = sorted(required.difference(entity))
            extra_entity = sorted(set(entity).difference(required))
            raise StateError(
                f"entity {entity_id} field mismatch: "
                f"missing={missing_entity}, extra={extra_entity}"
            )
        if not isinstance(entity["base_state"], dict):
            raise StateError(f"entity {entity_id}.base_state must be an object")
        if not isinstance(entity["accumulated_changes"], list):
            raise StateError(f"entity {entity_id}.accumulated_changes must be an array")
        if any(not isinstance(item, dict) for item in entity["accumulated_changes"]):
            raise StateError(
                f"entity {entity_id}.accumulated_changes items must be objects"
            )
        if not isinstance(entity["current_state"], dict):
            raise StateError(f"entity {entity_id}.current_state must be an object")
    return data


def canonical_project_state_bytes(data: dict[str, Any]) -> bytes:
    validate_project_state(data)
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def project_state_digest(data: dict[str, Any]) -> str:
    return sha256(canonical_project_state_bytes(data)).hexdigest()


def load_project_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant
        )
    except (OSError, json.JSONDecodeError, StateError) as exc:
        raise StateError(f"cannot load project state: {exc}") from exc
    return validate_project_state(data)


def save_project_state(path: Path, data: dict[str, Any]) -> None:
    validate_project_state(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _state_lock(path):
        if path.exists():
            raise StateError(
                f"refusing to overwrite existing state; use revision CAS: {path}"
            )
        _write_state_atomic(path, data)


def commit_project_state(
    path: Path,
    data: dict[str, Any],
    *,
    expected_revision: int,
) -> dict[str, Any]:
    if type(expected_revision) is not int or expected_revision < 0:
        raise StateError("expected_revision must be a non-negative integer")
    path.parent.mkdir(parents=True, exist_ok=True)
    with _state_lock(path):
        current = load_project_state(path)
        if current["revision"] != expected_revision:
            raise StateError(
                f"state revision conflict: expected {expected_revision}, "
                f"got {current['revision']}"
            )
        if data.get("project_id") != current["project_id"]:
            raise StateError("project_id cannot change during a state commit")
        candidate = dict(data)
        candidate["revision"] = expected_revision + 1
        candidate["updated_at"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        validate_project_state(candidate)
        _write_state_atomic(path, candidate)
        return candidate


def active_mode(data: dict[str, Any]) -> str | None:
    value = data.get("HANDOFF", {}).get("STATE", {}).get("active_mode")
    return value if isinstance(value, str) else None


@contextmanager
def _state_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_name(f".{path.name}.lock")
    with lock_path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        else:  # pragma: no cover - exercised on Windows
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - exercised on Windows
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _write_state_atomic(path: Path, data: dict[str, Any]) -> None:
    content = (
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        _fsync_directory(path.parent)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:  # pragma: no cover - Windows does not open directories this way
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_json_value(value: Any, field: str = "value") -> None:
    if value is None or isinstance(value, (str, bool)) or type(value) is int:
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StateError(f"{field} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{field}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise StateError(f"{field} contains a non-string object key")
            validate_json_value(item, f"{field}.{key}")
        return
    raise StateError(f"{field} contains a non-JSON value: {type(value).__name__}")


def _reject_json_constant(value: str) -> None:
    raise StateError(f"non-standard JSON constant is forbidden: {value}")
