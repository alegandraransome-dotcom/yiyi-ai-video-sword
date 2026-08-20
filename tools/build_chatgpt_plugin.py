#!/usr/bin/env python3
"""Build a deterministic, portal-ready ZIP for the yi-director plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "yi-director"
PACKAGE_PATHS = (
    ".codex-plugin/plugin.json",
    "LICENSE",
    "PRIVACY.md",
    "README.md",
    "TERMS.md",
    "THIRD_PARTY_NOTICES.md",
    "assets/composer-icon.svg",
    "assets/logo.svg",
    "skills/yi-director/SKILL.md",
    "skills/yi-director/agents/openai.yaml",
    "skills/yi-director/assets/icon.svg",
    "skills/yi-director/references/asset-image-adapter.md",
    "skills/yi-director/references/directing-design.md",
    "skills/yi-director/references/execution-continuity.md",
    "skills/yi-director/references/formal-script.md",
    "skills/yi-director/references/lighting-direction.md",
    "skills/yi-director/references/persona-heng.md",
    "skills/yi-director/references/persona-intro.md",
    "skills/yi-director/references/persona-pair.md",
    "skills/yi-director/references/persona-wei.md",
    "skills/yi-director/references/preproduction.md",
    "skills/yi-director/references/producer-defaults.md",
    "skills/yi-director/references/project-state.md",
    "skills/yi-director/references/reread-handoff.md",
    "skills/yi-director/references/review-rework.md",
    "skills/yi-director/references/video-platform-export.md",
)
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:(?:0|[1-9]\d*)|(?:\d*[A-Za-z-][0-9A-Za-z-]*))"
    r"(?:\.(?:(?:0|[1-9]\d*)|(?:\d*[A-Za-z-][0-9A-Za-z-]*)))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def validate_plugin_version(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("plugin version must be a string")
    if len(value) > 64 or SEMVER.fullmatch(value) is None:
        raise ValueError("plugin version must be a valid SemVer string")
    return value


def plugin_version_from_bytes(content: bytes) -> str:
    manifest = json.loads(content.decode("utf-8"))
    return validate_plugin_version(manifest.get("version"))


def plugin_version() -> str:
    content = (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_bytes()
    return plugin_version_from_bytes(content)


def package_entries() -> list[tuple[str, bytes]]:
    expected = set(PACKAGE_PATHS)
    actual: set[str] = set()
    for path in PLUGIN_ROOT.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"plugin package cannot contain symlinks: {path}")
        if path.is_file():
            actual.add(path.relative_to(PLUGIN_ROOT).as_posix())
        elif not path.is_dir():
            raise ValueError(f"plugin package contains a special file: {path}")

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing files: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected files: {', '.join(unexpected)}")
        raise ValueError("plugin package file list mismatch; " + "; ".join(details))

    return [(relative, (PLUGIN_ROOT / relative).read_bytes()) for relative in PACKAGE_PATHS]


def temporary_path(parent: Path, prefix: str) -> Path:
    descriptor, name = tempfile.mkstemp(dir=parent, prefix=prefix, suffix=".tmp")
    os.close(descriptor)
    return Path(name)


def validated_entries(
    entries: list[tuple[str, bytes]] | None = None,
) -> list[tuple[str, bytes]]:
    snapshot = package_entries() if entries is None else list(entries)
    names = [relative for relative, _ in snapshot]
    if names != list(PACKAGE_PATHS) or len(names) != len(set(names)):
        raise ValueError("plugin package snapshot does not match the package whitelist")
    if not all(isinstance(content, bytes) for _, content in snapshot):
        raise ValueError("plugin package snapshot content must be bytes")
    return snapshot


def write_zip(output: Path, entries: list[tuple[str, bytes]] | None = None) -> str:
    output = output.resolve()
    try:
        output.relative_to(PLUGIN_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("output ZIP must be outside the plugin package")

    snapshot = validated_entries(entries)
    output.parent.mkdir(parents=True, exist_ok=True)
    checksum = output.with_suffix(output.suffix + ".sha256")
    archive_temp = temporary_path(output.parent, f".{output.name}.")
    checksum_temp = temporary_path(output.parent, f".{checksum.name}.")
    try:
        with zipfile.ZipFile(
            archive_temp,
            mode="w",
            compression=zipfile.ZIP_STORED,
        ) as archive:
            for relative, content in snapshot:
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.create_system = 3
                archive.writestr(info, content, compress_type=zipfile.ZIP_STORED)

        digest = hashlib.sha256(archive_temp.read_bytes()).hexdigest()
        checksum_temp.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
        os.chmod(archive_temp, 0o644)
        os.chmod(checksum_temp, 0o644)
        os.replace(archive_temp, output)
        os.replace(checksum_temp, checksum)
        return digest
    finally:
        archive_temp.unlink(missing_ok=True)
        checksum_temp.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default = REPO_ROOT / "dist" / f"yi-director-plugin-{plugin_version()}.zip"
    parser.add_argument("--output", type=Path, default=default)
    args = parser.parse_args()

    digest = write_zip(args.output.resolve())
    print(json.dumps({"output": str(args.output.resolve()), "sha256": digest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
