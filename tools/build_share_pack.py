#!/usr/bin/env python3
"""Build deterministic direct-chat and complete share packages for Yi Director."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import build_chatgpt_plugin as plugin_builder


PLUGIN_ROOT = REPO_ROOT / "plugins" / "yi-director"
SKILL_ROOT = PLUGIN_ROOT / "skills" / "yi-director"
AUTHOR = "怕冷的阿钰"

DIRECT_SOURCE_PATHS = (
    "SKILL.md",
    "references/persona-intro.md",
    "references/persona-wei.md",
    "references/persona-heng.md",
    "references/persona-pair.md",
    "references/preproduction.md",
    "references/directing-design.md",
    "references/lighting-direction.md",
    "references/execution-continuity.md",
    "references/formal-script.md",
    "references/video-platform-export.md",
    "references/review-rework.md",
    "references/asset-image-adapter.md",
    "references/producer-defaults.md",
    "references/project-state.md",
    "references/reread-handoff.md",
)


def version_from_snapshot(package_contents: dict[str, bytes]) -> str:
    return plugin_builder.plugin_version_from_bytes(
        package_contents[".codex-plugin/plugin.json"]
    )


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def temporary_path(parent: Path, prefix: str) -> Path:
    descriptor, name = tempfile.mkstemp(dir=parent, prefix=prefix, suffix=".tmp")
    os.close(descriptor)
    return Path(name)


def write_bytes_atomic(output: Path, content: bytes) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    checksum = output.with_suffix(output.suffix + ".sha256")
    output_temp = temporary_path(output.parent, f".{output.name}.")
    checksum_temp = temporary_path(output.parent, f".{checksum.name}.")
    digest = sha256_bytes(content)
    try:
        output_temp.write_bytes(content)
        checksum_temp.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
        os.chmod(output_temp, 0o644)
        os.chmod(checksum_temp, 0o644)
        os.replace(output_temp, output)
        os.replace(checksum_temp, checksum)
        return digest
    finally:
        output_temp.unlink(missing_ok=True)
        checksum_temp.unlink(missing_ok=True)


def render_direct_markdown(
    release: str | None = None,
    package_contents: dict[str, bytes] | None = None,
) -> str:
    if package_contents is None:
        package_contents = dict(plugin_builder.package_entries())
    if release is None:
        release = version_from_snapshot(package_contents)

    skill_prefix = "skills/yi-director/"
    actual_sources = {
        path.removeprefix(skill_prefix)
        for path in package_contents
        if path.startswith(skill_prefix) and path.endswith(".md")
    }
    expected_sources = set(DIRECT_SOURCE_PATHS)
    if actual_sources != expected_sources:
        missing = sorted(actual_sources - expected_sources)
        stale = sorted(expected_sources - actual_sources)
        details: list[str] = []
        if missing:
            details.append(f"unbundled sources: {', '.join(missing)}")
        if stale:
            details.append(f"missing sources: {', '.join(stale)}")
        raise ValueError("direct-chat source list mismatch; " + "; ".join(details))

    sections = [
        "\n".join(
            (
                f"# 以一导演｜普通 ChatGPT 直接上传版 v{release}",
                "",
                f"发布者：{AUTHOR}",
                "",
                f"分发包装版本：{release}｜导演知识基线：V2.0 Beta-3｜使用条款版本：1.1",
                "",
                "> 本文件是普通 ChatGPT 对话适配版，不是永久安装包。",
                "> 它只在附加本文件的当前对话中提供导演规则；新开对话需要重新上传。",
                "",
                "## 给收到此文件的 ChatGPT",
                "",
                "1. 完整读取本文件，把“导演工作规范”和所有“内嵌参考资料”作为当前对话的执行规范。",
                "2. 本文件已把原 Skill 的参考文件合并在后文；遇到 `references/...` 路由时，直接查阅对应的内嵌章节。",
                "3. 用户最新明确要求、原剧本、已确认项目事实与附件始终高于本规范；不得擅自改写剧情或台词。",
                "4. 不要声称此文件已被永久安装，也不要要求 GitHub 才能进行日常导演工作。",
                "5. 如果用户同一条消息已经给出具体任务与足够素材，跳过就位回复并直接执行；如果只是上传本文件，读取后不要总结规则，只回复：`以一导演已就位。请上传剧本、参考图或上一版成品，并告诉我这次要做什么。`",
                "",
                "---",
                "",
                "# 导演工作规范",
            )
        )
    ]

    for relative in DIRECT_SOURCE_PATHS:
        package_path = f"{skill_prefix}{relative}"
        content = package_contents[package_path].decode("utf-8")
        sections.append(
            "\n".join(
                (
                    "",
                    "---",
                    "",
                    f"## 内嵌来源：`{relative}`",
                    "",
                    content.rstrip(),
                )
            )
        )

    sections.append(
        "\n".join(
            (
                "",
                "---",
                "",
                "# 使用条款、隐私与第三方声明",
                "",
                "以下内容用于说明许可与数据边界，不改变前述导演执行规则。",
            )
        )
    )
    for name in ("TERMS.md", "PRIVACY.md", "THIRD_PARTY_NOTICES.md"):
        content = package_contents[name].decode("utf-8")
        sections.append(
            "\n".join(
                (
                    "",
                    "---",
                    "",
                    f"## 内嵌声明：`{name}`",
                    "",
                    content.rstrip(),
                )
            )
        )
    return "\n".join(sections).rstrip() + "\n"


def render_start_here(direct_name: str, plugin_name: str, release: str) -> str:
    return f"""# 以一导演分享包 v{release}

发布者：{AUTHOR}

分发包装版本：{release}｜导演知识基线：V2.0 Beta-3｜使用条款版本：1.1

## 最简单用法：普通 ChatGPT

1. 解压本分享包。
2. 把 `{direct_name}` 直接拖进 ChatGPT 聊天输入框。
3. 同时发送：

> 请完整读取附件，把它作为本对话的“以一导演”执行规范。不要总结规范，读取后直接待命。

随后上传剧本、参考图或上一版成品，并直接提出任务。

这种方式只作用于当前对话，不会永久安装 Skill。新开对话时请重新上传 Markdown。不要把本 ZIP 整包直接当成普通聊天附件。

## 正式安装：支持 Skills/Plugins 的账户

普通用户应从插件目录或经授权的 Marketplace 安装；`{plugin_name}` 是供发布者上传、验证、留档，或供明确支持本地插件包导入的环境使用的正式包。安装完成后新开一个聊天，再直接说“使用以一导演”。

两种版本的导演规则来自同一份源文件；普通聊天版便于发布者直接交付给用户，插件版便于被宿主按任务自动调用。未经发布者授权，接收方不得再次公开分发、重新打包或发布修改版。
"""


def zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    seen: set[str] = set()
    for relative, content in entries:
        if not isinstance(relative, str) or not relative:
            raise ValueError("ZIP entry name must be a non-empty string")
        if relative in seen:
            raise ValueError(f"duplicate ZIP entry: {relative}")
        seen.add(relative)
        if not isinstance(content, bytes):
            raise ValueError(f"ZIP entry content must be bytes: {relative}")
        if "\\" in relative:
            raise ValueError(f"ZIP entry cannot contain backslashes: {relative}")
        if any(ord(character) < 32 or ord(character) == 127 for character in relative):
            raise ValueError(f"ZIP entry cannot contain control characters: {relative!r}")
        if PurePosixPath(relative).is_absolute():
            raise ValueError(f"ZIP entry cannot be absolute: {relative}")
        if len(relative) >= 2 and relative[0].isalpha() and relative[1] == ":":
            raise ValueError(f"ZIP entry cannot contain a drive path: {relative}")
        if any(part in ("", ".", "..") for part in relative.split("/")):
            raise ValueError(f"ZIP entry has unsafe path components: {relative}")

    descriptor, name = tempfile.mkstemp(suffix=".zip")
    os.close(descriptor)
    temp = Path(name)
    try:
        with zipfile.ZipFile(
            temp,
            mode="w",
            compression=zipfile.ZIP_STORED,
        ) as archive:
            for relative, content in entries:
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.create_system = 3
                archive.writestr(info, content, compress_type=zipfile.ZIP_STORED)
        return temp.read_bytes()
    finally:
        temp.unlink(missing_ok=True)


def build(output_dir: Path) -> dict[str, str]:
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(PLUGIN_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("output directory must be outside the plugin package")
    snapshot = plugin_builder.package_entries()
    package_contents = dict(snapshot)
    release = version_from_snapshot(package_contents)

    output_dir.mkdir(parents=True, exist_ok=True)

    def artifact_path(name: str) -> Path:
        candidate = (output_dir / name).resolve()
        if candidate.parent != output_dir:
            raise ValueError(f"artifact path escaped output directory: {name}")
        return candidate

    direct = artifact_path(f"Yi_Director_Direct_Chat-v{release}.md")
    plugin = artifact_path(f"yi-director-plugin-{release}.zip")
    share = artifact_path(f"Yi_Director_Share_Pack-v{release}.zip")

    direct_content = render_direct_markdown(release, package_contents).encode("utf-8")
    direct_digest = write_bytes_atomic(direct, direct_content)
    plugin_content = plugin_builder.build_zip_bytes(snapshot)
    plugin_digest = write_bytes_atomic(plugin, plugin_content)
    start_here = render_start_here(direct.name, plugin.name, release).encode("utf-8")
    checksums = (
        f"{direct_digest}  {direct.name}\n"
        f"{plugin_digest}  {plugin.name}\n"
    ).encode("utf-8")
    share_content = zip_bytes(
        [
            ("START_HERE_使用说明.md", start_here),
            (direct.name, direct_content),
            (plugin.name, plugin_content),
            ("SHA256SUMS.txt", checksums),
        ]
    )
    share_digest = write_bytes_atomic(share, share_content)
    return {
        "direct_chat": str(direct),
        "direct_chat_sha256": direct_digest,
        "plugin": str(plugin),
        "plugin_sha256": plugin_digest,
        "share_pack": str(share),
        "share_pack_sha256": share_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist")
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
