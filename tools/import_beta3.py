#!/usr/bin/env python3
"""Split the frozen Beta-3 monolith into byte-recomposable source modules."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MODULE_PATHS = {
    "02": "runtime/modules/02-preproduction.md",
    "03": "runtime/modules/03-directing-design.md",
    "04": "runtime/modules/04-execution-continuity.md",
    "05": "runtime/modules/05-formal-script.md",
    "06": "runtime/modules/06-reread-handoff.md",
    "07": "runtime/modules/07-review-rework.md",
    "08": "runtime/modules/08-project-state.md",
    "09": "runtime/modules/09-migration-tests.md",
    "10": "runtime/modules/10-asset-image-adapter.md",
}


def split_once(text: str, marker: str) -> tuple[str, str]:
    index = text.find(marker)
    if index < 0:
        raise ValueError(f"missing split marker: {marker}")
    return text[:index], text[index:]


def parse_modules(text: str) -> tuple[str, dict[str, str]]:
    begin_pattern = re.compile(r"(?m)^<!-- BEGIN MODULE (\d{2}) -->$")
    matches = list(begin_pattern.finditer(text))
    if [match.group(1) for match in matches] != [f"{value:02d}" for value in range(11)]:
        raise ValueError("expected exactly ordered modules 00 through 10")

    preamble = text[: matches[0].start()]
    modules: dict[str, str] = {}
    for index, match in enumerate(matches):
        module_id = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[match.start() : end]
        expected_end = f"<!-- END MODULE {module_id} -->"
        if chunk.count(expected_end) != 1:
            raise ValueError(f"module {module_id} must contain one end marker")
        modules[module_id] = chunk
    return preamble, modules


def split_kernel(module: str) -> list[tuple[str, str]]:
    entry, rest = split_once(module, "# 三｜薇 × 恒常驻人格种子")
    wei, rest = split_once(rest, "## 恒\n")
    heng, routing = split_once(rest, "## 协作可见性｜筹备阶段必须真的“见到他们”")
    return [
        ("runtime/modules/00-kernel/00-entry.md", entry),
        ("runtime/modules/00-kernel/10-wei-seed.md", wei),
        ("runtime/modules/00-kernel/20-heng-seed.md", heng),
        ("runtime/modules/00-kernel/30-routing.md", routing),
    ]


def split_personas(module: str) -> list[tuple[str, str]]:
    intro, rest = split_once(module, "# 二｜见微｜薇")
    wei, rest = split_once(rest, "# 三｜定衡｜恒")
    heng, pair = split_once(rest, "# 四｜搭档关系与Taste Firewall")
    return [
        ("runtime/modules/01-personas/00-intro.md", intro),
        ("runtime/modules/01-personas/10-wei.md", wei),
        ("runtime/modules/01-personas/20-heng.md", heng),
        ("runtime/modules/01-personas/30-pair.md", pair),
    ]


def write_new(root: Path, relative: str, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    target.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_root", type=Path)
    args = parser.parse_args()

    source_text = args.source.read_text(encoding="utf-8")
    preamble, modules = parse_modules(source_text)
    pieces: list[tuple[str, str]] = [("runtime/bootstrap.md", preamble)]
    pieces.extend(split_kernel(modules["00"]))
    pieces.extend(split_personas(modules["01"]))
    pieces.extend((path, modules[module_id]) for module_id, path in MODULE_PATHS.items())

    recomposed = "".join(content for _, content in pieces)
    if recomposed != source_text:
        raise ValueError("split modules do not recompose to the frozen source")

    for relative, content in pieces:
        write_new(args.output_root, relative, content)

    order_path = args.output_root / "runtime/canonical-order.txt"
    order_path.write_text(
        "".join(f"{relative}\n" for relative, _ in pieces),
        encoding="utf-8",
        newline="\n",
    )
    print(f"imported {len(pieces)} byte-recomposable files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
