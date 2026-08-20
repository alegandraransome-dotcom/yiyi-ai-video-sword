from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from yi_runtime.compiler import RuntimeCompiler, SnapshotReader
from yi_runtime.errors import ManifestError, PackageError
from yi_runtime.freeze import (
    compilation_context_digest,
    freeze_wei_report,
    load_frozen_wei_report,
    route_digest,
)
from yi_runtime.package import build_package
from yi_runtime.state import new_project_state, project_state_digest


ROOT = Path(__file__).resolve().parents[1]


class CompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compiler = RuntimeCompiler.from_source(ROOT)

    def test_full_runtime_is_byte_identical_to_frozen_beta3(self) -> None:
        compilation = self.compiler.compile("full-runtime")
        frozen = (ROOT / "archive/beta3/frozen-monolith.md").read_bytes()
        self.assertEqual(compilation.text.encode("utf-8"), frozen)
        self.assertEqual(
            hashlib.sha256(frozen).hexdigest(),
            self.compiler.manifest["system"]["canonical_source_sha256"],
        )

    def test_every_mode_has_00_and_08_shared_core_once(self) -> None:
        for mode in self.compiler.available_modes():
            with self.subTest(mode=mode):
                ids = [module.id for module in self.compiler.select_modules(mode)]
                for expected in ("kernel-entry", "kernel-routing", "project-state"):
                    self.assertEqual(ids.count(expected), 1)

    def test_formal_and_asset_routes_do_not_contaminate_each_other(self) -> None:
        formal = {module.id for module in self.compiler.select_modules("formal-production")}
        assets = {module.id for module in self.compiler.select_modules("asset-production")}
        self.assertTrue({"directing-design", "execution-continuity", "formal-script"} <= formal)
        self.assertNotIn("asset-image-adapter", formal)
        self.assertIn("asset-image-adapter", assets)
        self.assertNotIn("formal-script", assets)

    def test_persona_module_isolation(self) -> None:
        wei = self.compiler.compile("wei-first-read")
        self.assertNotIn("kernel-heng-seed", wei.module_ids)
        self.assertNotIn("persona-heng", wei.module_ids)
        self.assertNotIn("# 三｜定衡｜恒", wei.text)

        with self.assertRaises(ManifestError):
            self.compiler.compile("heng-decision")
        with self.assertRaises(ManifestError):
            self.compiler.compile(
                "heng-decision", injections={"WEI_REPORT": "NOT FROZEN"}
            )

        state = new_project_state("编译隔离测试")
        state_text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
        modules = tuple(
            module.id for module in self.compiler.select_modules("wei-first-read")
        )
        route = route_digest("wei-first-read", modules)
        context = compilation_context_digest(
            "wei-first-read",
            modules,
            injections={"PROJECT_STATE": state_text},
            compiled_text=self.compiler.compile(
                "wei-first-read", injections={"PROJECT_STATE": state_text}
            ).text,
        )
        report = {
            "schema_version": 1,
            "run_id": "run-compiler",
            "task_id": "task-compiler",
            "project_id": state["project_id"],
            "system_version": self.compiler.manifest["system"]["version"],
            "source_digest": self.compiler.manifest["system"][
                "canonical_source_sha256"
            ],
            "state_revision": 0,
            "state_digest": project_state_digest(state),
            "route_digest": route,
            "compilation_digest": context,
            "wei_skills": [],
            "observations": [],
            "flags": [],
            "protected_values": [],
            "open_questions": [],
        }
        with tempfile.TemporaryDirectory() as temporary:
            frozen = freeze_wei_report(report, Path(temporary))
            verified = load_frozen_wei_report(
                frozen,
                source_digest=report["source_digest"],
                system_version=report["system_version"],
                project_id=state["project_id"],
                state_revision=0,
                state_digest=report["state_digest"],
                expected_route_digest=route,
                expected_compilation_digest=context,
                expected_run_id="run-compiler",
                expected_task_id="task-compiler",
            )
            heng = self.compiler.compile(
                "heng-decision",
                injections={"PROJECT_STATE": state_text, "WEI_REPORT": verified},
                run_id="run-compiler",
                task_id="task-compiler",
            )
            self.assertNotIn("kernel-wei-seed", heng.module_ids)
            self.assertNotIn("persona-wei", heng.module_ids)
            self.assertNotIn("# 二｜见微｜薇", heng.text)

            other_state = new_project_state("另一个项目")
            other_state_text = json.dumps(
                other_state, ensure_ascii=False, indent=2, sort_keys=True
            )
            with self.assertRaisesRegex(ManifestError, "stale WEI_REPORT context"):
                self.compiler.compile(
                    "heng-decision",
                    injections={
                        "PROJECT_STATE": other_state_text,
                        "WEI_REPORT": verified,
                    },
                    run_id="run-compiler",
                    task_id="task-compiler",
                )

            changed_manifest = deepcopy(self.compiler.manifest)
            changed_manifest["system"]["canonical_source_sha256"] = "0" * 64
            snapshot = {
                changed_manifest["runtime"]["canonical_order_file"]: (
                    ROOT / changed_manifest["runtime"]["canonical_order_file"]
                ).read_text(encoding="utf-8")
            }
            snapshot.update(
                {
                    module["path"]: (ROOT / module["path"]).read_text(encoding="utf-8")
                    for module in changed_manifest["modules"]
                }
            )
            with self.assertRaisesRegex(ManifestError, "canonical source drift"):
                RuntimeCompiler(changed_manifest, SnapshotReader(snapshot))

            with self.assertRaisesRegex(ManifestError, "stale WEI_REPORT context"):
                self.compiler.compile(
                    "heng-decision",
                    injections={"PROJECT_STATE": state_text, "WEI_REPORT": verified},
                    run_id="another-run",
                    task_id="task-compiler",
                )

    def test_wei_rejects_heng_decision_injection(self) -> None:
        with self.assertRaises(ManifestError):
            self.compiler.compile("wei-first-read", injections={"HENG_DECISION": "hidden"})
        for name in ("HENG_MEMORY", "HENG_DECISION_V2", "HENG_PRIVATE_OUTPUT"):
            with self.subTest(name=name), self.assertRaises(ManifestError):
                self.compiler.compile("wei-first-read", injections={name: "hidden"})

    def test_skills_cannot_cross_formal_asset_mode_boundaries(self) -> None:
        with self.assertRaises(ManifestError):
            self.compiler.select_modules("asset-production", skills=("video-execution",))
        with self.assertRaises(ManifestError):
            self.compiler.select_modules("formal-production", skills=("asset-production",))

        for mode in self.compiler.available_modes():
            baseline = set(
                module.id for module in self.compiler.select_modules(mode)
            )
            for skill in self.compiler.manifest["internal_skills"]:
                try:
                    selected = set(
                        module.id
                        for module in self.compiler.select_modules(mode, skills=(skill,))
                    )
                except ManifestError:
                    continue
                with self.subTest(mode=mode, skill=skill):
                    self.assertTrue(selected <= baseline)

    def test_package_compiler_matches_source_compiler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            build_package(ROOT, package)
            packaged = RuntimeCompiler.from_package(package)
            self.assertEqual(
                packaged.compile("formal-production").text,
                self.compiler.compile("formal-production").text,
            )

    def test_source_compiler_rejects_canonical_runtime_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            shutil.copy2(ROOT / "manifest.yaml", source / "manifest.yaml")
            shutil.copytree(ROOT / "runtime", source / "runtime")
            entry = source / "runtime/modules/00-kernel/00-entry.md"
            entry.write_text(
                entry.read_text(encoding="utf-8") + "\nUNDECLARED SOURCE DRIFT\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PackageError, "canonical source drift"):
                RuntimeCompiler.from_source(source)

    def test_source_compiler_uses_immutable_validated_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            shutil.copy2(ROOT / "manifest.yaml", source / "manifest.yaml")
            shutil.copytree(ROOT / "runtime", source / "runtime")
            compiler = RuntimeCompiler.from_source(source)
            entry = source / "runtime/modules/00-kernel/00-entry.md"
            entry.write_text(
                entry.read_text(encoding="utf-8")
                + "\nPOST_CONSTRUCTION_SOURCE_DRIFT\n",
                encoding="utf-8",
            )
            compiled = compiler.compile("wei-first-read")
            self.assertNotIn("POST_CONSTRUCTION_SOURCE_DRIFT", compiled.text)

    def test_custom_reader_is_snapshotted_once(self) -> None:
        manifest = self.compiler.manifest
        files = {
            manifest["runtime"]["canonical_order_file"]: (
                ROOT / manifest["runtime"]["canonical_order_file"]
            ).read_text(encoding="utf-8")
        }
        files.update(
            {
                module["path"]: (ROOT / module["path"]).read_text(encoding="utf-8")
                for module in manifest["modules"]
            }
        )

        class StatefulReader:
            def __init__(self) -> None:
                self.counts: dict[str, int] = {}

            def read_text(self, path: str) -> str:
                count = self.counts.get(path, 0)
                self.counts[path] = count + 1
                value = files[path]
                return value if count == 0 else value + "\nSTATEFUL_READER_DRIFT\n"

        compiler = RuntimeCompiler(manifest, StatefulReader())
        self.assertNotIn(
            "STATEFUL_READER_DRIFT", compiler.compile("wei-first-read").text
        )


if __name__ == "__main__":
    unittest.main()
