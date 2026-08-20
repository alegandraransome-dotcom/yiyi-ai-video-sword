from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import zipfile

import yaml

from tools import build_share_pack


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "yi-director"


class SharePackageTests(unittest.TestCase):
    def test_public_attribution_is_consistent(self) -> None:
        expected = "怕冷的阿钰"
        retired = "幻" + "星文化"
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], "0.1.1")
        self.assertEqual(manifest["author"]["name"], expected)
        self.assertEqual(manifest["interface"]["developerName"], expected)

        paths = [
            ROOT / "LICENSE",
            ROOT / "pyproject.toml",
            ROOT / "README.md",
            PLUGIN / "LICENSE",
            PLUGIN / "README.md",
            PLUGIN / "TERMS.md",
            PLUGIN / "PRIVACY.md",
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn(expected, text, path)
            self.assertNotIn(retired, text, path)

    def test_versions_are_consistent(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        cases = yaml.safe_load(
            (ROOT / "evals" / "plugin-submission-cases.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(cases["plugin_version"], manifest["version"])
        self.assertIn(
            f"插件版本：`{manifest['version']}`",
            (PLUGIN / "README.md").read_text(encoding="utf-8"),
        )

    def test_direct_chat_document_is_self_contained(self) -> None:
        text = build_share_pack.render_direct_markdown()
        self.assertIn("普通 ChatGPT 直接上传版", text)
        self.assertIn("只在附加本文件的当前对话中", text)
        self.assertIn("以一导演已就位", text)
        self.assertIn("同一条消息已经给出具体任务", text)
        self.assertIn("导演知识基线：V2.0 Beta-3", text)
        self.assertIn("## 内嵌来源：`SKILL.md`", text)
        for relative in build_share_pack.DIRECT_SOURCE_PATHS:
            self.assertIn(f"## 内嵌来源：`{relative}`", text)
        for name in ("TERMS.md", "PRIVACY.md", "THIRD_PARTY_NOTICES.md"):
            self.assertIn(f"## 内嵌声明：`{name}`", text)
        self.assertLess(len(text.split()), 2_000_000)

    def test_share_builder_rejects_output_inside_plugin_package(self) -> None:
        output = PLUGIN / ".share-test-output"
        self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, "outside the plugin package"):
            build_share_pack.build(output)
        self.assertFalse(output.exists())

    def test_direct_chat_builder_rejects_symlinked_package_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied_plugin = Path(directory) / "yi-director"
            shutil.copytree(PLUGIN, copied_plugin)
            secret = Path(directory) / "secret.txt"
            secret.write_text("must-not-be-bundled", encoding="utf-8")
            terms = copied_plugin / "TERMS.md"
            terms.unlink()
            terms.symlink_to(secret)
            with mock.patch.object(build_share_pack.plugin_builder, "PLUGIN_ROOT", copied_plugin):
                with self.assertRaisesRegex(ValueError, "symlinks"):
                    build_share_pack.render_direct_markdown()

    def test_complete_share_pack_is_deterministic_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = build_share_pack.build(Path(first_dir))
            second = build_share_pack.build(Path(second_dir))
            first_zip = Path(first["share_pack"])
            second_zip = Path(second["share_pack"])
            self.assertEqual(
                hashlib.sha256(first_zip.read_bytes()).digest(),
                hashlib.sha256(second_zip.read_bytes()).digest(),
            )
            with zipfile.ZipFile(first_zip) as archive:
                names = archive.namelist()
                self.assertEqual(
                    names,
                    [
                        "START_HERE_使用说明.md",
                        Path(first["direct_chat"]).name,
                        Path(first["plugin"]).name,
                        "SHA256SUMS.txt",
                    ],
                )
                self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in archive.infolist()))
                guide = archive.read("START_HERE_使用说明.md").decode("utf-8")
                self.assertIn("不要把本 ZIP 整包直接当成普通聊天附件", guide)
                checksum_lines = archive.read("SHA256SUMS.txt").decode("utf-8").splitlines()
                checksums = {
                    filename: digest
                    for digest, filename in (line.split("  ", 1) for line in checksum_lines)
                }
                expected_checksums = {
                    Path(first["direct_chat"]).name: first["direct_chat_sha256"],
                    Path(first["plugin"]).name: first["plugin_sha256"],
                }
                self.assertEqual(checksums, expected_checksums)
                for filename, digest in checksums.items():
                    self.assertEqual(hashlib.sha256(archive.read(filename)).hexdigest(), digest)

    def test_share_pack_uses_in_memory_artifacts_when_output_files_are_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            original_zip_bytes = build_share_pack.zip_bytes

            def replace_intermediate_files(entries: list[tuple[str, bytes]]) -> bytes:
                (output_dir / "Yi_Director_Direct_Chat-v0.1.1.md").write_bytes(
                    b"replaced-direct-chat"
                )
                (output_dir / "yi-director-plugin-0.1.1.zip").write_bytes(
                    b"replaced-plugin"
                )
                return original_zip_bytes(entries)

            with mock.patch.object(
                build_share_pack,
                "zip_bytes",
                side_effect=replace_intermediate_files,
            ):
                result = build_share_pack.build(output_dir)

            with zipfile.ZipFile(result["share_pack"]) as archive:
                checksum_lines = archive.read("SHA256SUMS.txt").decode("utf-8").splitlines()
                checksums = {
                    filename: digest
                    for digest, filename in (line.split("  ", 1) for line in checksum_lines)
                }
                for filename, digest in checksums.items():
                    self.assertEqual(
                        hashlib.sha256(archive.read(filename)).hexdigest(),
                        digest,
                    )
                self.assertNotEqual(
                    archive.read("Yi_Director_Direct_Chat-v0.1.1.md"),
                    b"replaced-direct-chat",
                )
                self.assertNotEqual(
                    archive.read("yi-director-plugin-0.1.1.zip"),
                    b"replaced-plugin",
                )

    def test_zip_builder_rejects_unsafe_or_duplicate_names(self) -> None:
        unsafe = (
            "../escape",
            "folder/../escape",
            "folder\\..\\escape",
            "/absolute",
            "C:/drive",
            "folder//file",
            "folder/./file",
            "control\nname",
        )
        for name in unsafe:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    build_share_pack.zip_bytes([(name, b"content")])
        with self.assertRaisesRegex(ValueError, "duplicate ZIP entry"):
            build_share_pack.zip_bytes([("same", b"one"), ("same", b"two")])


if __name__ == "__main__":
    unittest.main()
