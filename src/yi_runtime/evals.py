from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import ManifestError


def load_eval_suite(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ManifestError(f"cannot load eval suite: {exc}") from exc
    validate_eval_suite(data)
    return data


def validate_eval_suite(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("suite"), dict):
        raise ManifestError("eval suite metadata is missing")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ManifestError("eval suite must contain cases")
    ids: set[str] = set()
    points = 0
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or case_id in ids:
            raise ManifestError(f"invalid or duplicate eval case id: {case_id}")
        ids.add(case_id)
        if not case.get("prompt") or not case.get("mode"):
            raise ManifestError(f"eval case {case_id} is missing prompt or mode")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            raise ManifestError(f"eval case {case_id} has no assertions")
        for assertion in assertions:
            point_value = assertion.get("points")
            if not isinstance(point_value, int) or point_value < 1:
                raise ManifestError(f"eval case {case_id} has invalid points")
            if not assertion.get("require"):
                raise ManifestError(f"eval case {case_id} has an empty requirement")
            points += point_value
    expected = data["suite"].get("total_score")
    if points != expected:
        raise ManifestError(f"eval score mismatch: cases={points}, suite={expected}")
    return data
