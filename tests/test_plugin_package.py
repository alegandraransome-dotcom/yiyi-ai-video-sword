from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import zipfile

import yaml

from tools import build_chatgpt_plugin as plugin_builder


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "yi-director"
MANIFEST_PATH = PLUGIN / ".codex-plugin" / "plugin.json"
SKILL = PLUGIN / "skills" / "yi-director"
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:(?:0|[1-9]\d*)|(?:\d*[A-Za-z-][0-9A-Za-z-]*))"
    r"(?:\.(?:(?:0|[1-9]\d*)|(?:\d*[A-Za-z-][0-9A-Za-z-]*)))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def contrast_with_white(color: str) -> float:
    components = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
    luminance = 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
    return 1.05 / (luminance + 0.05)


class PluginPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_values_meet_known_final_listing_limits(self) -> None:
        manifest = self.manifest
        self.assertIsInstance(manifest["name"], str)
        self.assertRegex(manifest["name"], r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
        self.assertIsInstance(manifest["version"], str)
        self.assertLessEqual(len(manifest["version"]), 64)
        self.assertRegex(manifest["version"], SEMVER)
        self.assertIsInstance(manifest["description"], str)
        self.assertTrue(manifest["description"].strip())
        self.assertLessEqual(len(manifest["description"]), 1024)
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertTrue(manifest["author"]["name"].strip())
        self.assertLessEqual(len(manifest["author"]["name"]), 120)
        self.assertEqual(manifest["author"]["name"], manifest["interface"]["developerName"])

        interface = manifest["interface"]
        for key in ("displayName", "shortDescription", "longDescription", "developerName"):
            self.assertIsInstance(interface[key], str)
            self.assertTrue(interface[key].strip())
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertNotIn("\n", interface["shortDescription"])
        self.assertLessEqual(len(interface["longDescription"]), 4000)
        self.assertLessEqual(len(interface["developerName"]), 80)
        self.assertEqual(interface["category"], "Creativity")
        self.assertLessEqual(len(interface["capabilities"]), 20)
        self.assertTrue(
            all(
                isinstance(item, str) and item.strip() and len(item) <= 120 and "\n" not in item
                for item in interface["capabilities"]
            )
        )

        prompts = interface["defaultPrompt"]
        self.assertGreaterEqual(len(prompts), 1)
        self.assertLessEqual(len(prompts), 3)
        self.assertEqual(len(prompts), len(set(prompts)))
        self.assertTrue(all(len(item) <= 128 and "\n" not in item and "@" not in item for item in prompts))

        color = interface["brandColor"]
        self.assertRegex(color, r"^#[0-9A-Fa-f]{6}$")
        self.assertGreaterEqual(contrast_with_white(color), 2.0)

        urls = [
            manifest["author"]["url"],
            manifest["homepage"],
            manifest["repository"],
            interface["websiteURL"],
            interface["supportURL"],
            interface["privacyPolicyURL"],
            interface["termsOfServiceURL"],
        ]
        for value in urls:
            self.assertIsInstance(value, str)
            self.assertLessEqual(len(value), 1024)
            parsed = urlparse(value)
            self.assertEqual(parsed.scheme, "https")
            self.assertTrue(parsed.netloc)
            self.assertIsNone(parsed.username)
            self.assertIsNone(parsed.password)

    def test_declared_plugin_paths_exist_and_stay_inside_package(self) -> None:
        root = PLUGIN.resolve()
        paths = [
            self.manifest["skills"],
            self.manifest["interface"]["logo"],
            self.manifest["interface"]["composerIcon"],
        ]
        for value in paths:
            self.assertTrue(value.startswith("./"), value)
            resolved = (PLUGIN / value).resolve()
            resolved.relative_to(root)
            self.assertTrue(resolved.exists(), value)

    def test_brand_icons_are_square_and_at_least_48_pixels(self) -> None:
        icons = [
            PLUGIN / self.manifest["interface"]["logo"],
            PLUGIN / self.manifest["interface"]["composerIcon"],
            SKILL / "assets" / "icon.svg",
        ]
        for icon in icons:
            self.assertLessEqual(icon.stat().st_size, 5 * 1024 * 1024)
            root = ET.parse(icon).getroot()
            width = float(re.match(r"\d+(?:\.\d+)?", root.attrib["width"]).group())
            height = float(re.match(r"\d+(?:\.\d+)?", root.attrib["height"]).group())
            view_box = [float(value) for value in root.attrib["viewBox"].split()]
            self.assertEqual(width, height)
            self.assertGreaterEqual(width, 48)
            self.assertLessEqual(width, 4096)
            self.assertEqual(view_box[2], view_box[3])
            self.assertGreaterEqual(view_box[2], 48)
            self.assertLessEqual(view_box[2], 4096)

    def test_skills_only_package_has_no_mcp_apps_or_screenshots(self) -> None:
        self.assertNotIn("mcpServers", self.manifest)
        self.assertNotIn("apps", self.manifest)
        self.assertNotIn("screenshots", self.manifest["interface"])
        forbidden_files = {".mcp.json", ".app.json"}
        forbidden_dirs = {"apps"}
        for path in PLUGIN.rglob("*"):
            self.assertFalse(path.is_symlink(), path)
            self.assertNotIn(path.name, forbidden_files)
            if path.is_dir():
                self.assertNotIn(path.name, forbidden_dirs)

    def test_skill_metadata_and_all_references_are_valid(self) -> None:
        skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill_text.startswith("---\n"))
        _, frontmatter, _ = skill_text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual(metadata["name"], "yi-director")
        self.assertTrue(metadata["description"])

        links = re.findall(r"\]\((references/[^)#]+\.md)\)", skill_text)
        self.assertGreaterEqual(len(set(links)), 13)
        for link in links:
            self.assertTrue((SKILL / link).is_file(), link)

        agent = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(agent["policy"]["products"]), {"CHAT", "CODEX"})
        self.assertIs(agent["policy"]["allow_implicit_invocation"], True)
        self.assertIn("$yi-director", agent["interface"]["default_prompt"])
        for key in ("icon_small", "icon_large"):
            icon = agent["interface"][key]
            self.assertTrue(icon.startswith("./assets/"))
            self.assertTrue((SKILL / icon).is_file())

    def test_submission_eval_set_has_exactly_five_positive_and_three_negative(self) -> None:
        cases = yaml.safe_load(
            (ROOT / "evals" / "plugin-submission-cases.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(len(cases["positive"]), 5)
        self.assertEqual(len(cases["negative"]), 3)
        ids = [case["id"] for group in ("positive", "negative") for case in cases[group]]
        self.assertEqual(len(ids), len(set(ids)))
        for group in ("positive", "negative"):
            for case in cases[group]:
                self.assertTrue(case["prompt"].strip())
                self.assertTrue(case["expected_behavior"].strip())

    def test_lighting_and_platform_regression_set_is_well_formed(self) -> None:
        suite = yaml.safe_load(
            (ROOT / "evals" / "lighting-platform-regression.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(suite["status"], "partial-forward-test-passed")
        self.assertGreaterEqual(len(suite["cases"]), 10)
        ids = [case["id"] for case in suite["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        passed = suite["passed_cases"]
        remaining = suite["remaining_cases"]
        self.assertTrue(passed)
        self.assertFalse(set(passed) & set(remaining))
        self.assertEqual(set(ids), set(passed) | set(remaining))
        self.assertTrue((ROOT / suite["result_record"]).is_file())
        for case in suite["cases"]:
            self.assertTrue(case["prompt"].strip())
            self.assertTrue(case["must"])
            self.assertTrue(case["must_not"])

    def test_plugin_contains_privacy_terms_and_third_party_notice(self) -> None:
        privacy = (PLUGIN / "PRIVACY.md").read_text(encoding="utf-8")
        terms = (PLUGIN / "TERMS.md").read_text(encoding="utf-8")
        notices = (PLUGIN / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("不包含 MCP 服务器", privacy)
        self.assertIn("安装、更新和运行插件", terms)
        self.assertIn("MIT License", notices)
        self.assertIn("O-Side Media", notices)

    def test_repository_marketplace_points_to_plugin(self) -> None:
        path = ROOT / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(marketplace["plugins"][0]["name"], "yi-director")
        source = marketplace["plugins"][0]["source"]
        self.assertEqual(source, {"source": "local", "path": "./plugins/yi-director"})
        self.assertEqual(
            marketplace["plugins"][0]["policy"],
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        )

    def test_portal_zip_build_is_deterministic_and_has_plugin_at_archive_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            command = [sys.executable, str(ROOT / "tools" / "build_chatgpt_plugin.py")]
            subprocess.run(command + ["--output", str(first)], check=True, capture_output=True)
            subprocess.run(command + ["--output", str(second)], check=True, capture_output=True)
            self.assertEqual(hashlib.sha256(first.read_bytes()).digest(), hashlib.sha256(second.read_bytes()).digest())
            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            self.assertEqual(names, set(plugin_builder.PACKAGE_PATHS))
            self.assertIn(".codex-plugin/plugin.json", names)
            self.assertIn("skills/yi-director/SKILL.md", names)
            self.assertFalse(any(name.startswith("plugins/yi-director/") for name in names))

    def test_portal_zip_builder_rejects_self_inclusion(self) -> None:
        output = PLUGIN / ".self-test.zip"
        self.assertFalse(output.exists())
        process = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "build_chatgpt_plugin.py"),
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("outside the plugin package", process.stderr)
        self.assertFalse(output.exists())

    def test_portal_zip_builder_rejects_unexpected_files_without_overwriting_output(self) -> None:
        unexpected = PLUGIN / ".env"
        self.assertFalse(unexpected.exists())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing.zip"
            output.write_bytes(b"known-good-package")
            try:
                unexpected.write_text("PRIVATE_TOKEN=do-not-package\n", encoding="utf-8")
                process = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "tools" / "build_chatgpt_plugin.py"),
                        "--output",
                        str(output),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            finally:
                unexpected.unlink(missing_ok=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("unexpected files: .env", process.stderr)
            self.assertEqual(output.read_bytes(), b"known-good-package")


if __name__ == "__main__":
    unittest.main()
