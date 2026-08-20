from __future__ import annotations

import json
import unittest
from pathlib import Path

from yi_runtime.evals import load_eval_suite
from yi_runtime.compiler import RuntimeCompiler
from yi_runtime.router import TaskRouter
from yi_runtime.validation import validate_repository


ROOT = Path(__file__).resolve().parents[1]


class EvalAndValidationTests(unittest.TestCase):
    def test_beta3_suite_is_complete(self) -> None:
        suite = load_eval_suite(ROOT / "evals/beta3-regression.yaml")
        self.assertEqual([case["id"] for case in suite["cases"]], [f"T{n}" for n in range(1, 11)])
        self.assertEqual(suite["suite"]["total_score"], 20)

    def test_repository_gate(self) -> None:
        result = validate_repository(ROOT)
        self.assertEqual(result["module_count"], 18)
        self.assertEqual(result["mode_count"], 12)

    def test_project_state_schema_has_only_package_local_handoff_ref(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/project-state.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["HANDOFF"]["$ref"], "#/$defs/turn_handoff")
        self.assertIn("turn_handoff", schema["$defs"])

    def test_every_beta3_fixture_routes_to_its_declared_mode(self) -> None:
        suite = load_eval_suite(ROOT / "evals/beta3-regression.yaml")
        router = TaskRouter(RuntimeCompiler.from_source(ROOT).manifest)
        for case in suite["cases"]:
            current_mode = case.get("fixture_state", {}).get("active_mode")
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    router.route(case["prompt"], current_mode=current_mode).mode,
                    case["mode"],
                )


if __name__ == "__main__":
    unittest.main()
