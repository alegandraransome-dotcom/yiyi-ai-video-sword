from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class RouteDecision:
    mode: str
    matched_pattern: str | None
    priority: int
    reason: str


class TaskRouter:
    def __init__(self, manifest: dict[str, Any]):
        self.routes = sorted(
            manifest["routes"], key=lambda item: int(item.get("priority", 0)), reverse=True
        )

    def route(self, task: str, *, current_mode: str | None = None) -> RouteDecision:
        explicit = _last_explicit_switch(task, self.routes)
        if explicit is not None:
            mode, phrase = explicit
            return RouteDecision(
                mode=mode,
                matched_pattern=phrase,
                priority=2000,
                reason=f"任务显式切换模式：{phrase}",
            )

        if current_mode == "asset-production" and any(
            _has_positive_occurrence(task, marker)
            for marker in ("只改", "局部修改", "其他所有东西不变")
        ):
            return RouteDecision(
                mode="asset-production",
                matched_pattern="active asset patch",
                priority=1000,
                reason="局部修改继承当前资产成品类型。",
            )

        for route in self.routes:
            for pattern in route["patterns"]:
                if _has_positive_occurrence(task, pattern):
                    return RouteDecision(
                        mode=route["mode"],
                        matched_pattern=pattern,
                        priority=int(route.get("priority", 0)),
                        reason=f"任务命中路由词：{pattern}",
                    )
        return RouteDecision(
            mode="directing",
            matched_pattern=None,
            priority=0,
            reason="没有命中专项路由，进入导演设计。",
        )


def _has_positive_occurrence(task: str, pattern: str) -> bool:
    for match in re.finditer(re.escape(pattern), task, flags=re.IGNORECASE):
        if not _is_negated(task, match.start()):
            return True
    return False


def _is_negated(task: str, start: int) -> bool:
    prefix = task[max(0, start - 10) : start]
    clause_prefix = re.split(r"[，。！？；,.!?;]", prefix)[-1]
    if re.search(
        r"(?:不可能|不得|不能|不是|并非|没有)"
        r"[^，。！？；,.!?;]{0,6}(?:不|没(?:有)?|无(?:需|须|法|可))"
        r"[^，。！？；,.!?;]{0,5}$",
        clause_prefix,
    ):
        return False
    return bool(
        re.search(
            r"(?:不要|不写|不做|不想(?:做|写)?|不打算(?:做|写)?|"
            r"不得(?:做|写)?|不能(?:做|写)?|不可能(?:做|写)?|"
            r"不可以(?:做|写)?|"
            r"先不|暂不|无需|不用|不需要|不是|并非|别(?!的)).{0,5}$",
            clause_prefix,
        )
    )


def _last_explicit_switch(
    task: str, routes: list[dict[str, Any]]
) -> tuple[str, str] | None:
    candidates: list[tuple[int, str, str]] = []
    verbs = r"(?:切到|切回|转到|回到|改为|进入)"
    for route in routes:
        for pattern in route["patterns"]:
            expression = re.compile(
                rf"{verbs}\s*{re.escape(pattern)}", flags=re.IGNORECASE
            )
            for match in expression.finditer(task):
                if not _is_negated(task, match.start()):
                    candidates.append((match.start(), route["mode"], match.group(0)))
    if not candidates:
        return None
    _, mode, phrase = max(candidates, key=lambda item: item[0])
    return mode, phrase
