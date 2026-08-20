from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .errors import ManifestError, StateError
from .freeze import (
    VerifiedWeiReport,
    compilation_context_digest,
    route_digest,
    validate_verified_wei_report,
)
from .manifest import (
    Module,
    TextReader,
    modules_from_manifest,
    safe_relative_path,
    validate_manifest,
)
from .state import project_state_digest, validate_project_state


INJECTION_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
InjectionValue = str | VerifiedWeiReport


class SnapshotReader:
    def __init__(self, files: Mapping[str, str]):
        self._files = dict(files)

    def read_text(self, path: str) -> str:
        safe = safe_relative_path(path)
        try:
            return self._files[safe]
        except KeyError as exc:
            raise ManifestError(f"source snapshot file not found: {safe}") from exc


@dataclass(frozen=True)
class Compilation:
    mode: str
    persona: str
    module_ids: tuple[str, ...]
    text: str


class RuntimeCompiler:
    def __init__(self, manifest: dict[str, Any], reader: TextReader):
        validate_manifest(manifest)
        self._manifest = deepcopy(manifest)
        self._modules = tuple(modules_from_manifest(self._manifest))
        self._module_map = {module.id: module for module in self._modules}
        self._module_texts = MappingProxyType(self._snapshot_canonical_reader(reader))

    @property
    def manifest(self) -> dict[str, Any]:
        return deepcopy(self._manifest)

    @property
    def modules(self) -> tuple[Module, ...]:
        return self._modules

    @classmethod
    def from_source(cls, root: Path) -> "RuntimeCompiler":
        from .package import validate_source_tree

        root = root.resolve()
        manifest = validate_source_tree(root)
        paths = {
            safe_relative_path(manifest["runtime"]["canonical_order_file"]),
            *(safe_relative_path(module["path"]) for module in manifest["modules"]),
        }
        snapshot: dict[str, str] = {}
        for relative in paths:
            try:
                snapshot[relative] = (root / relative).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise ManifestError(
                    f"cannot snapshot runtime source {relative}: {exc}"
                ) from exc
        return cls(manifest, SnapshotReader(snapshot))

    @classmethod
    def from_package(cls, package_path: Path) -> "RuntimeCompiler":
        from .package import PackageReader

        reader = PackageReader(package_path)
        return cls(reader.manifest, reader)

    def available_modes(self) -> tuple[str, ...]:
        return tuple(self._manifest["runtime_modes"])

    def _snapshot_canonical_reader(self, reader: TextReader) -> dict[str, str]:
        order_path = safe_relative_path(
            self._manifest["runtime"]["canonical_order_file"]
        )
        order = [
            safe_relative_path(line)
            for line in reader.read_text(order_path).splitlines()
            if line
        ]
        expected_order = [
            module.path for module in sorted(self._modules, key=lambda item: item.order)
        ]
        if order != expected_order:
            raise ManifestError(
                "canonical order must match the fixed module order exactly"
            )
        module_texts = {path: reader.read_text(path) for path in order}
        actual = hashlib.sha256(
            "".join(module_texts[path] for path in order).encode("utf-8")
        ).hexdigest()
        expected = self._manifest["system"]["canonical_source_sha256"]
        if actual != expected:
            raise ManifestError(
                f"canonical source drift: expected {expected}, got {actual}"
            )
        return module_texts

    def select_modules(
        self,
        mode: str,
        *,
        skills: tuple[str, ...] = (),
    ) -> tuple[Module, ...]:
        try:
            config = self._manifest["runtime_modes"][mode]
        except KeyError as exc:
            raise ManifestError(f"unknown runtime mode: {mode}") from exc

        persona = config.get("persona", "pair")
        always = self._manifest["runtime"]["always_on"]
        selected = set(always.get("shared", []))
        selected.update(always.get(persona, []))
        selected.update(config.get("loads", []))
        mode_boundary = set(selected)

        for skill in skills:
            try:
                skill_modules = set(
                    self._manifest["internal_skills"][skill].get("loads", [])
                )
            except KeyError as exc:
                raise ManifestError(f"unknown internal skill: {skill}") from exc
            outside = skill_modules.difference(mode_boundary)
            if outside:
                raise ManifestError(
                    f"internal skill {skill} crosses mode {mode} boundary: "
                    f"{sorted(outside)}"
                )
            selected.update(skill_modules)

        forbidden = set(config.get("forbids", []))
        conflict = selected.intersection(forbidden)
        if conflict:
            raise ManifestError(f"mode {mode} selected forbidden modules: {sorted(conflict)}")

        return tuple(
            sorted(
                (self._module_map[item] for item in selected),
                key=lambda item: item.order,
            )
        )

    def compile(
        self,
        mode: str,
        *,
        skills: tuple[str, ...] = (),
        injections: Mapping[str, InjectionValue] | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
    ) -> Compilation:
        config = self._manifest["runtime_modes"].get(mode)
        if config is None:
            raise ManifestError(f"unknown runtime mode: {mode}")
        persona = config.get("persona", "pair")
        injections = dict(injections or {})
        self._validate_injections(
            mode,
            persona,
            config,
            injections,
            run_id=run_id,
            task_id=task_id,
        )

        modules = self.select_modules(mode, skills=skills)
        text = "".join(self._module_texts[module.path] for module in modules)
        if injections:
            text += self._render_injections(injections)

        return Compilation(
            mode=mode,
            persona=persona,
            module_ids=tuple(module.id for module in modules),
            text=text,
        )

    def pipeline_plan(self, name: str) -> dict[str, Any]:
        try:
            pipeline = self._manifest["pipelines"][name]
        except KeyError as exc:
            raise ManifestError(f"unknown pipeline: {name}") from exc
        passes: list[dict[str, Any]] = []
        for item in pipeline["passes"]:
            mode = item["mode"]
            config = self._manifest["runtime_modes"][mode]
            modules = [module.id for module in self.select_modules(mode)]
            passes.append(
                {
                    "id": item["id"],
                    "mode": mode,
                    "persona": config.get("persona", "pair"),
                    "modules": modules,
                    "requires": item.get("requires", []),
                    "output": item.get("output"),
                    "freeze_output": bool(item.get("freeze_output", False)),
                }
            )
        return {"pipeline": name, "passes": passes}

    def _validate_injections(
        self,
        mode: str,
        persona: str,
        config: dict[str, Any],
        injections: dict[str, InjectionValue],
        *,
        run_id: str | None,
        task_id: str | None,
    ) -> None:
        for name in injections:
            if not INJECTION_NAME.fullmatch(name):
                raise ManifestError(f"invalid injection name: {name}")

        missing = set(config.get("requires_injections", [])).difference(injections)
        if missing:
            raise ManifestError(f"mode {mode} requires injections: {sorted(missing)}")

        common = set(self._manifest["runtime"].get("accepted_injections", []))
        persona_config = self._manifest.get("personas", {}).get(persona, {})
        allowed = common | set(persona_config.get("accepted_injections", []))
        unexpected = set(injections).difference(allowed)
        if unexpected:
            raise ManifestError(
                f"persona {persona} does not accept injections: {sorted(unexpected)}"
            )

        if persona == "wei":
            private = sorted(name for name in injections if name.startswith("HENG_"))
            if private:
                raise ManifestError(f"Wei forbids Heng-private injections: {private}")
        if persona == "heng":
            private = sorted(
                name
                for name in injections
                if name.startswith("WEI_") and name != "WEI_REPORT"
            )
            if private:
                raise ManifestError(f"Heng forbids Wei-private injections: {private}")

        for name, content in injections.items():
            if name == "WEI_REPORT":
                if mode != "heng-decision" or not isinstance(content, VerifiedWeiReport):
                    raise ManifestError(
                        "heng-decision requires a verified frozen WEI_REPORT token"
                    )
            elif not isinstance(content, str):
                raise ManifestError(f"injection {name} must be text")

        if mode == "heng-decision":
            report = injections.get("WEI_REPORT")
            if not isinstance(report, VerifiedWeiReport):
                raise ManifestError(
                    "heng-decision requires a verified frozen WEI_REPORT token"
                )
            self._validate_heng_context(
                report,
                injections,
                run_id=run_id,
                task_id=task_id,
            )
        elif run_id is not None or task_id is not None:
            raise ManifestError("run_id/task_id are only valid for heng-decision")

    def _validate_heng_context(
        self,
        report: VerifiedWeiReport,
        injections: dict[str, InjectionValue],
        *,
        run_id: str | None,
        task_id: str | None,
    ) -> None:
        if not run_id or not task_id:
            raise ManifestError("heng-decision requires run_id and task_id")
        try:
            validate_verified_wei_report(report)
        except StateError as exc:
            raise ManifestError(f"invalid verified WEI_REPORT token: {exc}") from exc

        system = self._manifest["system"]
        expected_scalar = {
            "run_id": run_id,
            "task_id": task_id,
            "system_version": system["version"],
            "source_digest": system["canonical_source_sha256"],
        }
        stale = {
            key: (getattr(report, key), value)
            for key, value in expected_scalar.items()
            if getattr(report, key) != value
        }

        state_text = injections.get("PROJECT_STATE")
        if not isinstance(state_text, str):
            raise ManifestError("heng-decision requires PROJECT_STATE text")
        try:
            state = validate_project_state(json.loads(state_text))
        except (json.JSONDecodeError, StateError) as exc:
            raise ManifestError(f"invalid PROJECT_STATE injection: {exc}") from exc
        expected_state = {
            "project_id": state["project_id"],
            "state_revision": state["revision"],
            "state_digest": project_state_digest(state),
        }
        stale.update(
            {
                key: (getattr(report, key), value)
                for key, value in expected_state.items()
                if getattr(report, key) != value
            }
        )

        wei_inputs = {
            name: value
            for name, value in injections.items()
            if name != "WEI_REPORT" and isinstance(value, str)
        }
        wei_compilation = self.compile(
            "wei-first-read",
            skills=report.wei_skills,
            injections=wei_inputs,
        )
        expected_route = route_digest("wei-first-read", wei_compilation.module_ids)
        expected_compilation = compilation_context_digest(
            "wei-first-read",
            wei_compilation.module_ids,
            skills=report.wei_skills,
            injections=wei_inputs,
            compiled_text=wei_compilation.text,
        )
        if report.route_digest != expected_route:
            stale["route_digest"] = (report.route_digest, expected_route)
        if report.compilation_digest != expected_compilation:
            stale["compilation_digest"] = (
                report.compilation_digest,
                expected_compilation,
            )
        if stale:
            raise ManifestError(f"stale WEI_REPORT context: {stale}")

    @staticmethod
    def _render_injections(injections: Mapping[str, InjectionValue]) -> str:
        blocks: list[str] = []
        for name in sorted(injections):
            value = injections[name]
            content = (value.text if isinstance(value, VerifiedWeiReport) else value).rstrip(
                "\n"
            )
            blocks.append(
                f"\n<!-- BEGIN RUNTIME INPUT {name} -->\n"
                f"<{name}>\n{content}\n</{name}>\n"
                f"<!-- END RUNTIME INPUT {name} -->\n"
            )
        return "".join(blocks)
