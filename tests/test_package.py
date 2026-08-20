from __future__ import annotations

import hashlib
import json
import shutil
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any, Callable
from unittest import mock

import yaml

from yi_runtime.errors import PackageError
from yi_runtime.package import (
    FIXED_ZIP_TIME,
    PackageReader,
    build_package,
    sha256_bytes,
    validate_source_tree,
    verify_package,
)


ROOT = Path(__file__).resolve().parents[1]


def _read_payloads(package: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(package) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _write_payloads(
    package: Path,
    payloads: dict[str, bytes],
    mutate_info: Callable[[str, zipfile.ZipInfo], None] | None = None,
) -> None:
    with zipfile.ZipFile(package, "w") as archive:
        names = ["mimetype"] + sorted(name for name in payloads if name != "mimetype")
        for name in names:
            info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED
            if mutate_info is not None:
                mutate_info(name, info)
            archive.writestr(info, payloads[name], compress_type=info.compress_type)


def _refresh_index(payloads: dict[str, bytes]) -> None:
    index = json.loads(payloads["index.json"].decode("utf-8"))
    index["files"] = {
        name: {"sha256": sha256_bytes(content), "size": len(content)}
        for name, content in sorted(payloads.items())
        if name != "index.json"
    }
    payloads["index.json"] = (
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _copy_package_source(destination: Path) -> None:
    destination.mkdir()
    for relative in ("manifest.yaml", "mimetype", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / relative, destination / relative)
    for relative in ("runtime", "schemas", "evals", "internal-skills"):
        shutil.copytree(ROOT / relative, destination / relative)


class PackageTests(unittest.TestCase):
    def test_build_is_reproducible_and_stored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.yios"
            second = Path(temporary) / "second.yios"
            build_package(ROOT, first)
            build_package(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                hashlib.sha256(second.read_bytes()).hexdigest(),
            )
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.namelist()[0], "mimetype")
                self.assertTrue(all(item.compress_type == zipfile.ZIP_STORED for item in archive.infolist()))

    def test_verify_detects_duplicate_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            tampered = Path(temporary) / "tampered.yios"
            build_package(ROOT, package)
            shutil.copyfile(package, tampered)
            with zipfile.ZipFile(tampered, "a") as archive:
                archive.writestr("manifest.yaml", b"tampered")
            with self.assertRaises(PackageError):
                verify_package(tampered)

    def test_verify_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            malicious = Path(temporary) / "malicious.yios"
            with zipfile.ZipFile(malicious, "w") as archive:
                archive.writestr("../escape", b"x")
            with self.assertRaises(PackageError):
                verify_package(malicious)

    def test_verify_rejects_backslash_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            malicious = Path(temporary) / "malicious.yios"
            with zipfile.ZipFile(malicious, "w") as archive:
                archive.writestr("folder\\escape", b"x")
            with self.assertRaises(PackageError):
                verify_package(malicious)

    def test_verify_validates_index_format_and_metadata_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            build_package(ROOT, package)

            def root_list(_index: dict[str, Any]) -> Any:
                return []

            def string_version(index: dict[str, Any]) -> Any:
                index["format_version"] = "1"
                return index

            def future_version(index: dict[str, Any]) -> Any:
                index["format_version"] = 2
                return index

            def list_metadata(index: dict[str, Any]) -> Any:
                index["files"]["mimetype"] = []
                return index

            def boolean_size(index: dict[str, Any]) -> Any:
                index["files"]["mimetype"]["size"] = True
                return index

            def numeric_digest(index: dict[str, Any]) -> Any:
                index["files"]["mimetype"]["sha256"] = 7
                return index

            cases = {
                "root-list": root_list,
                "string-version": string_version,
                "future-version": future_version,
                "list-metadata": list_metadata,
                "boolean-size": boolean_size,
                "numeric-digest": numeric_digest,
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    payloads = _read_payloads(package)
                    index = json.loads(payloads["index.json"].decode("utf-8"))
                    payloads["index.json"] = (
                        json.dumps(mutate(index), ensure_ascii=False, sort_keys=True) + "\n"
                    ).encode("utf-8")
                    tampered = Path(temporary) / f"{name}.yios"
                    _write_payloads(tampered, payloads)
                    with self.assertRaises(PackageError):
                        verify_package(tampered)

    def test_verify_rejects_invalid_canonical_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            build_package(ROOT, package)
            original = _read_payloads(package)
            order_path = "runtime/canonical-order.txt"
            lines = original[order_path].decode("utf-8").splitlines()
            cases = {
                "unsafe": ["../escape.md", *lines[1:]],
                "duplicate": [*lines, lines[0]],
                "incomplete": lines[:-1],
            }
            for name, changed_lines in cases.items():
                with self.subTest(name=name):
                    payloads = dict(original)
                    payloads[order_path] = ("\n".join(changed_lines) + "\n").encode("utf-8")
                    _refresh_index(payloads)
                    tampered = Path(temporary) / f"order-{name}.yios"
                    _write_payloads(tampered, payloads)
                    with self.assertRaises(PackageError):
                        verify_package(tampered)

    def test_verify_rejects_missing_declared_module_after_reindex(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            tampered = Path(temporary) / "missing-module.yios"
            build_package(ROOT, package)
            payloads = _read_payloads(package)
            del payloads["runtime/bootstrap.md"]
            _refresh_index(payloads)
            _write_payloads(tampered, payloads)
            with self.assertRaisesRegex(PackageError, "missing declared modules"):
                verify_package(tampered)

    def test_verify_rejects_canonical_source_drift_after_reindex(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            tampered = Path(temporary) / "source-drift.yios"
            build_package(ROOT, package)
            payloads = _read_payloads(package)
            payloads["runtime/bootstrap.md"] += b"\n<!-- tampered -->\n"
            _refresh_index(payloads)
            _write_payloads(tampered, payloads)
            with self.assertRaisesRegex(PackageError, "canonical source drift"):
                verify_package(tampered)

    def test_verify_rejects_undeclared_members_after_reindex(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            tampered = Path(temporary) / "extra-member.yios"
            build_package(ROOT, package)
            payloads = _read_payloads(package)
            payloads["archive/secret.txt"] = b"not part of the yios format\n"
            _refresh_index(payloads)
            _write_payloads(tampered, payloads)
            with self.assertRaisesRegex(PackageError, "undeclared members"):
                verify_package(tampered)

    def test_verify_rejects_manifest_core_bypass_after_reindex(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            tampered = Path(temporary) / "core-bypass.yios"
            build_package(ROOT, package)
            payloads = _read_payloads(package)
            manifest = yaml.safe_load(payloads["manifest.yaml"])
            manifest["runtime"]["always_on"]["shared"] = []
            payloads["manifest.yaml"] = yaml.safe_dump(
                manifest, allow_unicode=True, sort_keys=False
            ).encode("utf-8")
            _refresh_index(payloads)
            _write_payloads(tampered, payloads)
            with self.assertRaisesRegex(PackageError, "00/08 persona core"):
                verify_package(tampered)

    def test_package_reader_opens_and_verifies_one_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            build_package(ROOT, package)
            real_zip_file = zipfile.ZipFile
            with mock.patch(
                "yi_runtime.package.zipfile.ZipFile",
                wraps=real_zip_file,
            ) as zip_file:
                reader = PackageReader(package)
            self.assertEqual(zip_file.call_count, 1)
            self.assertEqual(reader.manifest["system"]["id"], "yi-director-runtime")

    def test_build_rejects_output_inside_included_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            _copy_package_source(source)
            output = source / "runtime" / "generated" / "runtime.yios"
            with self.assertRaisesRegex(PackageError, "inside included directory"):
                build_package(source, output)
            self.assertFalse(output.exists())

    def test_source_validation_rejects_in_tree_module_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            _copy_package_source(source)
            module = source / "runtime" / "bootstrap.md"
            real_module = source / "runtime" / "bootstrap-real.md"
            module.rename(real_module)
            module.symlink_to(real_module.name)
            with self.assertRaisesRegex(PackageError, "symlink"):
                validate_source_tree(source)

    def test_verify_rejects_symlink_and_noncanonical_zip_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "runtime.yios"
            build_package(ROOT, package)
            payloads = _read_payloads(package)

            def symlink(name: str, info: zipfile.ZipInfo) -> None:
                if name == "runtime/bootstrap.md":
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16

            def compressed(name: str, info: zipfile.ZipInfo) -> None:
                if name == "runtime/bootstrap.md":
                    info.compress_type = zipfile.ZIP_DEFLATED

            def timestamp(name: str, info: zipfile.ZipInfo) -> None:
                if name == "runtime/bootstrap.md":
                    info.date_time = (1981, 1, 1, 0, 0, 0)

            def mode(name: str, info: zipfile.ZipInfo) -> None:
                if name == "runtime/bootstrap.md":
                    info.external_attr = (stat.S_IFREG | 0o600) << 16

            for name, mutate in {
                "symlink": symlink,
                "compressed": compressed,
                "timestamp": timestamp,
                "mode": mode,
            }.items():
                with self.subTest(name=name):
                    tampered = Path(temporary) / f"metadata-{name}.yios"
                    _write_payloads(tampered, payloads, mutate)
                    with self.assertRaises(PackageError):
                        verify_package(tampered)

    def test_build_does_not_replace_output_before_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "runtime.yios"
            output.write_bytes(b"known-good-existing-package")
            with mock.patch(
                "yi_runtime.package.verify_package",
                side_effect=PackageError("simulated verification failure"),
            ):
                with self.assertRaises(PackageError):
                    build_package(ROOT, output)
            self.assertEqual(output.read_bytes(), b"known-good-existing-package")


if __name__ == "__main__":
    unittest.main()
