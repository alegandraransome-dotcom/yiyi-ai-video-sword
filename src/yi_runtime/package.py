from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

from .errors import ManifestError, PackageError
from .manifest import load_manifest, parse_manifest, safe_relative_path


MAX_PACKAGE_BYTES = 128 * 1024 * 1024
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_source_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = load_manifest(root / "manifest.yaml")
    for module in manifest["modules"]:
        relative = safe_relative_path(module["path"])
        declared = root / relative
        _reject_symlink_components(root, declared, f"module must not be a symlink: {relative}")
        path = declared.resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise PackageError(f"missing module file: {relative}")

    order_relative = safe_relative_path(manifest["runtime"]["canonical_order_file"])
    order_path = root / order_relative
    _reject_symlink_components(
        root,
        order_path,
        f"canonical order must not be a symlink: {order_relative}",
    )
    order = _parse_canonical_order(order_path.read_bytes(), order_relative)
    expected_order = [
        safe_relative_path(module["path"])
        for module in sorted(manifest["modules"], key=lambda item: item["order"])
    ]
    if order != expected_order:
        raise PackageError("canonical order must match the fixed module order exactly")
    recomposed = b"".join((root / safe_relative_path(item)).read_bytes() for item in order)
    expected_hash = manifest["system"]["canonical_source_sha256"]
    actual_hash = sha256_bytes(recomposed)
    if actual_hash != expected_hash:
        raise PackageError(
            f"canonical source drift: expected {expected_hash}, got {actual_hash}"
        )
    return manifest


def build_package(source_root: Path, output_path: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    # Keep the lexical path long enough to detect an output path placed beneath an
    # included directory, even when the output itself is an existing symlink.
    output_path = Path(os.path.abspath(output_path))
    if output_path.suffix != ".yios":
        raise PackageError("package output must use the .yios extension")
    manifest = validate_source_tree(source_root)
    _reject_included_output(
        source_root=source_root,
        includes=manifest["package"]["include"],
        output_path=output_path,
    )
    files = _collect_included_files(source_root, manifest["package"]["include"])

    payloads: dict[str, bytes] = {}
    for relative, path in files.items():
        payloads[relative] = path.read_bytes()

    index = {
        "format_version": 1,
        "system_id": manifest["system"]["id"],
        "system_version": manifest["system"]["version"],
        "files": {
            relative: {"sha256": sha256_bytes(content), "size": len(content)}
            for relative, content in sorted(payloads.items())
        },
    }
    payloads["index.json"] = (
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            ordered_names = ["mimetype"] + sorted(name for name in payloads if name != "mimetype")
            for relative in ordered_names:
                content = payloads[relative]
                info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, content, compress_type=zipfile.ZIP_STORED)
        verification = verify_package(temporary)
        package_sha256 = sha256_bytes(temporary.read_bytes())
        temporary.replace(output_path)
    finally:
        if temporary.exists():
            temporary.unlink()

    verification["package_sha256"] = package_sha256
    return verification


def verify_package(package_path: Path) -> dict[str, Any]:
    _, _, verification = _load_verified_package(package_path)
    return verification


def _load_verified_package(
    package_path: Path,
) -> tuple[dict[str, bytes], dict[str, Any], dict[str, Any]]:
    package_path = package_path.resolve()
    try:
        with zipfile.ZipFile(package_path, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise PackageError("package contains duplicate entries")
            for info in infos:
                _validate_archive_name(info.filename)
                if info.is_dir():
                    raise PackageError(f"directory entries are not permitted: {info.filename}")
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise PackageError(f"symlink entries are not permitted: {info.filename}")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise PackageError(f"package entry must use ZIP_STORED: {info.filename}")
                if info.date_time != FIXED_ZIP_TIME:
                    raise PackageError(f"package entry has non-canonical timestamp: {info.filename}")
                if (
                    info.create_system != 3
                    or not stat.S_ISREG(mode)
                    or stat.S_IMODE(mode) != 0o644
                ):
                    raise PackageError(f"package entry has non-canonical mode: {info.filename}")
            total = sum(info.file_size for info in infos)
            if total > MAX_PACKAGE_BYTES:
                raise PackageError(f"package expands beyond {MAX_PACKAGE_BYTES} bytes")
            required = {"mimetype", "manifest.yaml", "index.json"}
            missing = required.difference(names)
            if missing:
                raise PackageError(f"package missing required entries: {sorted(missing)}")
            payloads = {name: archive.read(name) for name in names}
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise PackageError(f"cannot open package: {exc}") from exc

    if names[0] != "mimetype":
        raise PackageError("mimetype must be the first package entry")
    if payloads["mimetype"] != b"application/vnd.yi-director.yios\n":
        raise PackageError("invalid package mimetype")

    try:
        index = json.loads(payloads["index.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"invalid index.json: {exc}") from exc
    if not isinstance(index, dict):
        raise PackageError("index.json root must be a mapping")
    if type(index.get("format_version")) is not int or index["format_version"] != 1:
        raise PackageError("index.json format_version must be integer 1")
    for field in ("system_id", "system_version"):
        if not isinstance(index.get(field), str) or not index[field]:
            raise PackageError(f"index.json {field} must be a non-empty string")

    indexed = index.get("files")
    if not isinstance(indexed, dict):
        raise PackageError("index.json files must be a mapping")
    actual_names = set(payloads).difference({"index.json"})
    if set(indexed) != actual_names:
        raise PackageError("index does not match package entries")
    for name, metadata in indexed.items():
        if not isinstance(name, str):
            raise PackageError("index.json file names must be strings")
        if not isinstance(metadata, dict):
            raise PackageError(f"index metadata must be a mapping: {name}")
        size = metadata.get("size")
        digest = metadata.get("sha256")
        if type(size) is not int or size < 0:
            raise PackageError(f"index size must be a non-negative integer: {name}")
        if not _is_sha256(digest):
            raise PackageError(f"index sha256 must be a lowercase SHA-256 digest: {name}")
        content = payloads[name]
        if size != len(content):
            raise PackageError(f"size mismatch: {name}")
        if digest != sha256_bytes(content):
            raise PackageError(f"checksum mismatch: {name}")

    try:
        manifest = parse_manifest(payloads["manifest.yaml"].decode("utf-8"))
    except (UnicodeDecodeError, ManifestError, AttributeError, KeyError, TypeError, ValueError) as exc:
        raise PackageError(f"invalid packaged manifest: {exc}") from exc
    try:
        system_id = manifest["system"]["id"]
        system_version = manifest["system"]["version"]
    except (AttributeError, KeyError, TypeError) as exc:
        raise PackageError(f"invalid packaged system metadata: {exc}") from exc
    if not isinstance(system_id, str) or not system_id:
        raise PackageError("manifest system.id must be a non-empty string")
    if not isinstance(system_version, str) or not system_version:
        raise PackageError("manifest system.version must be a non-empty string")
    if index.get("system_id") != system_id:
        raise PackageError("index system_id does not match manifest")
    if index.get("system_version") != system_version:
        raise PackageError("index system_version does not match manifest")

    _verify_include_coverage(payloads, manifest)
    _verify_canonical_payload(payloads, manifest)
    verification = {
        "system": manifest["system"],
        "file_count": len(payloads),
        "expanded_bytes": sum(len(value) for value in payloads.values()),
    }
    return payloads, manifest, verification


class PackageReader:
    def __init__(self, package_path: Path):
        files, manifest, _ = _load_verified_package(package_path)
        self._files = MappingProxyType(files)
        self._manifest = deepcopy(manifest)

    @property
    def manifest(self) -> dict[str, Any]:
        return deepcopy(self._manifest)

    def read_text(self, path: str) -> str:
        safe = safe_relative_path(path)
        try:
            return self._files[safe].decode("utf-8")
        except KeyError as exc:
            raise PackageError(f"package file not found: {safe}") from exc
        except UnicodeDecodeError as exc:
            raise PackageError(f"package file is not UTF-8 text: {safe}") from exc


def _collect_included_files(root: Path, includes: list[str]) -> dict[str, Path]:
    collected: dict[str, Path] = {}
    for raw in includes:
        relative = safe_relative_path(raw)
        declared = root / relative
        _reject_symlink_components(
            root,
            declared,
            f"symlinks are not permitted: {relative}",
        )
        target = declared.resolve()
        if not target.is_relative_to(root) or not target.exists():
            raise PackageError(f"included path does not exist: {relative}")
        candidates = [target] if target.is_file() else sorted(target.rglob("*"))
        for candidate in candidates:
            _reject_symlink_components(
                root,
                candidate,
                f"symlinks are not permitted: {candidate.relative_to(root).as_posix()}",
            )
            if candidate.is_dir():
                continue
            item = candidate.relative_to(root).as_posix()
            collected[item] = candidate
    return collected


def _verify_canonical_payload(payloads: dict[str, bytes], manifest: dict[str, Any]) -> None:
    try:
        raw_order_path = manifest["runtime"]["canonical_order_file"]
        order_path = safe_relative_path(raw_order_path)
        expected_order = [
            safe_relative_path(module["path"])
            for module in sorted(manifest["modules"], key=lambda item: item["order"])
        ]
        module_paths = set(expected_order)
        expected_hash = manifest["system"]["canonical_source_sha256"]
    except (ManifestError, AttributeError, KeyError, TypeError, ValueError) as exc:
        raise PackageError(f"invalid canonical source declaration: {exc}") from exc

    if not _is_sha256(expected_hash):
        raise PackageError("system.canonical_source_sha256 must be a lowercase SHA-256 digest")
    if order_path not in payloads:
        raise PackageError(f"package missing canonical order file: {order_path}")

    order = _parse_canonical_order(payloads[order_path], order_path)
    if order != expected_order:
        raise PackageError("canonical order must match the fixed module order exactly")

    missing_modules = sorted(module_paths.difference(payloads))
    if missing_modules:
        raise PackageError(f"package missing declared modules: {missing_modules}")
    actual_hash = sha256_bytes(b"".join(payloads[path] for path in order))
    if actual_hash != expected_hash:
        raise PackageError(
            f"canonical source drift: expected {expected_hash}, got {actual_hash}"
        )


def _verify_include_coverage(
    payloads: dict[str, bytes], manifest: dict[str, Any]
) -> None:
    actual = set(payloads).difference({"index.json"})
    covered: set[str] = set()
    for raw in manifest["package"]["include"]:
        include = safe_relative_path(raw)
        if include in actual:
            matches = {include}
        else:
            prefix = f"{include}/"
            matches = {name for name in actual if name.startswith(prefix)}
        if not matches:
            raise PackageError(f"package include has no matching members: {include}")
        covered.update(matches)
    extra = sorted(actual.difference(covered))
    if extra:
        raise PackageError(f"package contains undeclared members: {extra}")


def _parse_canonical_order(content: bytes, source: str) -> list[str]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise PackageError(f"canonical order is not UTF-8 text: {source}") from exc
    order: list[str] = []
    for line in lines:
        if not line:
            continue
        try:
            order.append(safe_relative_path(line))
        except (ManifestError, TypeError) as exc:
            raise PackageError(f"unsafe canonical order path: {line!r}") from exc
    return order


def _reject_symlink_components(root: Path, target: Path, message: str) -> None:
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise PackageError(f"path escapes source root: {target}") from exc
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise PackageError(message)


def _reject_included_output(
    source_root: Path,
    includes: list[str],
    output_path: Path,
) -> None:
    resolved_output = output_path.resolve()
    for raw in includes:
        relative = safe_relative_path(raw)
        declared = source_root / relative
        resolved = declared.resolve()
        if resolved.is_dir():
            if output_path.is_relative_to(declared) or resolved_output.is_relative_to(resolved):
                raise PackageError(f"package output is inside included directory: {relative}")
        elif output_path == declared or resolved_output == resolved:
            raise PackageError(f"package output replaces included file: {relative}")


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_archive_name(name: str) -> None:
    if "\\" in name or "\x00" in name:
        raise PackageError(f"unsafe archive path: {name}")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise PackageError(f"unsafe archive path: {name}")
    if path.as_posix() != name or any(part in {"", "."} for part in path.parts):
        raise PackageError(f"non-canonical archive path: {name}")
