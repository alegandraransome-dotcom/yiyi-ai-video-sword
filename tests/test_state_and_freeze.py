from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path

from yi_runtime.compiler import RuntimeCompiler
from yi_runtime.errors import StateError
from yi_runtime.freeze import (
    compilation_context_digest,
    freeze_wei_report,
    load_frozen_wei_report,
    route_digest,
    validate_wei_report,
)
from yi_runtime.state import (
    commit_project_state,
    load_project_state,
    new_project_state,
    project_state_digest,
    save_project_state,
    validate_project_state,
)


ROOT = Path(__file__).resolve().parents[1]


class StateAndFreezeTests(unittest.TestCase):
    def test_state_compare_and_swap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            state = new_project_state("测试项目")
            save_project_state(path, state)
            candidate = deepcopy(state)
            candidate["HANDOFF"]["NEXT"] = "进入03导演设计"
            committed = commit_project_state(path, candidate, expected_revision=0)
            self.assertEqual(committed["revision"], 1)
            self.assertEqual(load_project_state(path)["HANDOFF"]["NEXT"], "进入03导演设计")
            with self.assertRaises(StateError):
                commit_project_state(path, candidate, expected_revision=0)

    def test_state_compare_and_swap_is_atomic_between_writers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            state = new_project_state("并发测试")
            save_project_state(path, state)
            barrier = threading.Barrier(2)

            def commit(next_value: str) -> object:
                candidate = deepcopy(state)
                candidate["HANDOFF"]["NEXT"] = next_value
                barrier.wait()
                try:
                    return commit_project_state(path, candidate, expected_revision=0)
                except StateError as exc:
                    return exc

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(commit, ("A", "B")))

            successes = [item for item in results if isinstance(item, dict)]
            conflicts = [item for item in results if isinstance(item, StateError)]
            self.assertEqual(len(successes), 1)
            self.assertEqual(len(conflicts), 1)
            self.assertIn("revision conflict", str(conflicts[0]))
            self.assertEqual(load_project_state(path)["revision"], 1)

    def test_state_initialization_is_create_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            original = new_project_state("原项目")
            replacement = new_project_state("覆盖项目")
            save_project_state(path, original)
            with self.assertRaises(StateError):
                save_project_state(path, replacement)
            self.assertEqual(load_project_state(path)["project_id"], original["project_id"])

    def test_state_validation_matches_security_sensitive_schema_rules(self) -> None:
        cases = []
        revision_bool = new_project_state("状态校验")
        revision_bool["revision"] = True
        cases.append(revision_bool)
        invalid_date = new_project_state("状态校验")
        invalid_date["updated_at"] = "not-a-date"
        cases.append(invalid_date)
        extra_field = new_project_state("状态校验")
        extra_field["unexpected"] = True
        cases.append(extra_field)
        invalid_debt = new_project_state("状态校验")
        invalid_debt["HANDOFF"]["REREAD_DEBT"] = "missing"
        cases.append(invalid_debt)
        invalid_uuid = new_project_state("状态校验")
        invalid_uuid["project_id"] = "not-a-uuid"
        cases.append(invalid_uuid)
        invalid_baseline = new_project_state("状态校验")
        invalid_baseline["long_term"]["baseline"]["visual"] = 5
        cases.append(invalid_baseline)
        non_finite = new_project_state("状态校验")
        non_finite["HANDOFF"]["STATE"]["score"] = float("nan")
        cases.append(non_finite)
        non_string_key = new_project_state("状态校验")
        non_string_key["entities"][7] = {
            "base_state": {},
            "accumulated_changes": [],
            "current_state": {},
        }
        cases.append(non_string_key)
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(StateError):
                    validate_project_state(data)

    def test_state_loader_rejects_non_standard_json_constants(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            state = new_project_state("非标准 JSON")
            state["HANDOFF"]["STATE"]["score"] = float("nan")
            path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaises(StateError):
                load_project_state(path)

    def test_frozen_report_is_content_addressed_and_context_bound(self) -> None:
        compiler = RuntimeCompiler.from_source(ROOT)
        modules = tuple(module.id for module in compiler.select_modules("wei-first-read"))
        expected_route = route_digest("wei-first-read", modules)
        state = new_project_state("冻结测试")
        state["revision"] = 3
        state_text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
        expected_compilation = compilation_context_digest(
            "wei-first-read",
            modules,
            injections={"PROJECT_STATE": state_text},
            compiled_text=compiler.compile(
                "wei-first-read", injections={"PROJECT_STATE": state_text}
            ).text,
        )
        report = {
            "schema_version": 1,
            "run_id": "run-001",
            "task_id": "task-001",
            "project_id": state["project_id"],
            "system_version": compiler.manifest["system"]["version"],
            "source_digest": compiler.manifest["system"]["canonical_source_sha256"],
            "state_revision": 3,
            "state_digest": project_state_digest(state),
            "route_digest": expected_route,
            "compilation_digest": expected_compilation,
            "wei_skills": [],
            "observations": ["人物关系可信，但A的掩饰缺少行为出口。"],
            "flags": [{"code": "WEI-K", "content": "保护A听见真相后的选择微停。"}],
            "protected_values": ["选择微停"],
            "open_questions": [],
        }
        invalid_uuid_report = deepcopy(report)
        invalid_uuid_report["project_id"] = "not-a-uuid"
        with self.assertRaises(StateError):
            validate_wei_report(invalid_uuid_report)
        non_finite_report = deepcopy(report)
        non_finite_report["observations"] = [{"confidence": float("inf")}]
        with self.assertRaises(StateError):
            validate_wei_report(non_finite_report)
        with tempfile.TemporaryDirectory() as temporary:
            frozen = freeze_wei_report(report, Path(temporary))
            loaded = load_frozen_wei_report(
                frozen,
                source_digest=report["source_digest"],
                system_version=report["system_version"],
                project_id=state["project_id"],
                state_revision=3,
                state_digest=report["state_digest"],
                expected_route_digest=expected_route,
                expected_compilation_digest=expected_compilation,
                expected_run_id="run-001",
                expected_task_id="task-001",
            )
            self.assertEqual(json.loads(loaded.text), report)
            with self.assertRaises(StateError):
                load_frozen_wei_report(
                    frozen,
                    source_digest=report["source_digest"],
                    system_version=report["system_version"],
                    project_id=state["project_id"],
                    state_revision=4,
                    state_digest=report["state_digest"],
                    expected_route_digest=expected_route,
                    expected_compilation_digest=expected_compilation,
                    expected_run_id="run-001",
                    expected_task_id="task-001",
                )

            other = new_project_state("另一个项目")
            other["revision"] = 3
            with self.assertRaises(StateError):
                load_frozen_wei_report(
                    frozen,
                    source_digest=report["source_digest"],
                    system_version=report["system_version"],
                    project_id=other["project_id"],
                    state_revision=3,
                    state_digest=project_state_digest(other),
                    expected_route_digest=expected_route,
                    expected_compilation_digest=expected_compilation,
                    expected_run_id="run-001",
                    expected_task_id="task-001",
                )


if __name__ == "__main__":
    unittest.main()
