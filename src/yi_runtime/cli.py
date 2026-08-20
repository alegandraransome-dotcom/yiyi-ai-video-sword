from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .compiler import RuntimeCompiler
from .errors import YIError
from .evals import load_eval_suite
from .freeze import (
    compilation_context_digest,
    freeze_wei_report,
    load_frozen_wei_report,
    route_digest,
)
from .package import PackageReader, build_package, verify_package
from .router import TaskRouter
from .state import (
    active_mode,
    load_project_state,
    new_project_state,
    project_state_digest,
    save_project_state,
)
from .validation import validate_target


def compiler_from_args(args: argparse.Namespace) -> RuntimeCompiler:
    if getattr(args, "package", None):
        return RuntimeCompiler.from_package(args.package)
    return RuntimeCompiler.from_source(getattr(args, "source", None) or Path.cwd())


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def write_text(path: Path | None, content: str) -> None:
    if path is None:
        sys.stdout.write(content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def parse_injections(values: list[str]) -> dict[str, str]:
    injections: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise YIError(f"injection must use NAME=PATH: {value}")
        name, raw_path = value.split("=", 1)
        if name in injections:
            raise YIError(f"duplicate injection: {name}")
        injections[name] = Path(raw_path).read_text(encoding="utf-8")
    return injections


def add_state_injection(injections: dict[str, str], state: dict[str, Any]) -> None:
    if "PROJECT_STATE" in injections:
        raise YIError("PROJECT_STATE is supplied by --state and must not be injected twice")
    injections["PROJECT_STATE"] = json.dumps(
        state, ensure_ascii=False, indent=2, sort_keys=True
    )


def command_build(args: argparse.Namespace) -> None:
    result = build_package(args.source_root, args.output)
    result["output"] = str(args.output.resolve())
    print_json(result)


def command_validate(args: argparse.Namespace) -> None:
    print_json(validate_target(args.target.resolve()))


def command_inspect(args: argparse.Namespace) -> None:
    verification = verify_package(args.package)
    reader = PackageReader(args.package)
    verification["runtime_modes"] = list(reader.manifest["runtime_modes"])
    verification["pipelines"] = list(reader.manifest["pipelines"])
    print_json(verification)


def command_route(args: argparse.Namespace) -> None:
    compiler = compiler_from_args(args)
    current = None
    if args.state:
        current = active_mode(load_project_state(args.state))
    decision = TaskRouter(compiler.manifest).route(args.task, current_mode=current)
    print_json(
        {
            "mode": decision.mode,
            "matched_pattern": decision.matched_pattern,
            "priority": decision.priority,
            "reason": decision.reason,
            "current_mode": current,
        }
    )


def command_compile(args: argparse.Namespace) -> None:
    compiler = compiler_from_args(args)
    state = load_project_state(args.state) if args.state else None
    if args.task:
        current = active_mode(state) if state else None
        mode = TaskRouter(compiler.manifest).route(args.task, current_mode=current).mode
    else:
        mode = args.mode

    injections = parse_injections(args.inject)
    if state is not None:
        add_state_injection(injections, state)

    if mode == "heng-decision":
        if "WEI_REPORT" in injections:
            raise YIError("Heng must receive WEI_REPORT through --wei-report, not --inject")
        if args.wei_report is None or state is None or not args.run_id or not args.task_id:
            raise YIError(
                "heng-decision requires --wei-report, --state, --run-id and --task-id"
            )
        wei_skills = tuple(sorted(set(args.wei_skill)))
        wei_compilation = compiler.compile(
            "wei-first-read", skills=wei_skills, injections=injections
        )
        wei_modules = wei_compilation.module_ids
        expected_route = route_digest("wei-first-read", wei_modules)
        expected_compilation = compilation_context_digest(
            "wei-first-read",
            wei_modules,
            skills=wei_skills,
            injections=injections,
            compiled_text=wei_compilation.text,
        )
        injections["WEI_REPORT"] = load_frozen_wei_report(
            args.wei_report,
            source_digest=compiler.manifest["system"]["canonical_source_sha256"],
            system_version=compiler.manifest["system"]["version"],
            project_id=state["project_id"],
            state_revision=state["revision"],
            state_digest=project_state_digest(state),
            expected_route_digest=expected_route,
            expected_compilation_digest=expected_compilation,
            expected_run_id=args.run_id,
            expected_task_id=args.task_id,
            expected_wei_skills=wei_skills,
        )
    elif args.wei_report is not None:
        raise YIError("--wei-report is only valid for heng-decision")

    compilation = compiler.compile(
        mode,
        skills=tuple(args.skill),
        injections=injections,
        run_id=args.run_id,
        task_id=args.task_id,
    )
    write_text(args.output, compilation.text)
    if args.metadata:
        print_json(
            {
                "mode": compilation.mode,
                "persona": compilation.persona,
                "modules": list(compilation.module_ids),
                "output": str(args.output.resolve()) if args.output else None,
            }
        )


def command_plan(args: argparse.Namespace) -> None:
    print_json(compiler_from_args(args).pipeline_plan(args.pipeline))


def command_state_init(args: argparse.Namespace) -> None:
    data = new_project_state(args.project, format_name=args.format, pipeline=args.pipeline)
    save_project_state(args.output, data)
    print_json({"output": str(args.output.resolve()), "revision": data["revision"]})


def command_state_validate(args: argparse.Namespace) -> None:
    data = load_project_state(args.state)
    print_json(
        {"project": data["project"], "revision": data["revision"], "valid": True}
    )


def command_wei_template(args: argparse.Namespace) -> None:
    compiler = compiler_from_args(args)
    state = load_project_state(args.state)
    skills = tuple(sorted(set(args.skill)))
    injections = parse_injections(args.inject)
    add_state_injection(injections, state)
    compilation = compiler.compile(
        "wei-first-read", skills=skills, injections=injections
    )
    modules = compilation.module_ids
    report = {
        "schema_version": 1,
        "run_id": args.run_id,
        "task_id": args.task_id,
        "project_id": state["project_id"],
        "system_version": compiler.manifest["system"]["version"],
        "source_digest": compiler.manifest["system"]["canonical_source_sha256"],
        "state_revision": state["revision"],
        "state_digest": project_state_digest(state),
        "route_digest": route_digest("wei-first-read", modules),
        "compilation_digest": compilation_context_digest(
            "wei-first-read",
            modules,
            skills=skills,
            injections=injections,
            compiled_text=compilation.text,
        ),
        "wei_skills": list(skills),
        "observations": [],
        "flags": [],
        "protected_values": [],
        "open_questions": [],
    }
    write_text(args.output, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def command_freeze_wei(args: argparse.Namespace) -> None:
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise YIError(f"invalid WEI_REPORT JSON: {exc}") from exc
    frozen = freeze_wei_report(report, args.output_dir)
    print_json({"frozen_report": str(frozen.resolve()), "sha256": frozen.stem})


def command_eval_list(args: argparse.Namespace) -> None:
    compiler = compiler_from_args(args)
    if args.package:
        reader = PackageReader(args.package)
        suite = __import__("yaml").safe_load(reader.read_text(compiler.manifest["evals"]["cases"]))
    else:
        root = args.source or Path.cwd()
        suite = load_eval_suite(root / compiler.manifest["evals"]["cases"])
    print_json(
        {
            "suite": suite["suite"],
            "cases": [
                {"id": case["id"], "title": case["title"], "mode": case["mode"]}
                for case in suite["cases"]
            ],
        }
    )


def add_source_or_package(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--source", type=Path)
    group.add_argument("--package", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yi", description="YI Director Runtime tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build a deterministic .yios package")
    build.add_argument("source_root", nargs="?", type=Path, default=Path.cwd())
    build.add_argument(
        "--output",
        type=Path,
        default=Path("dist/YI_Director_Runtime_v2.0.0-beta.4.yios"),
    )
    build.set_defaults(handler=command_build)

    validate = subparsers.add_parser("validate", help="validate a source tree or package")
    validate.add_argument("target", nargs="?", type=Path, default=Path.cwd())
    validate.set_defaults(handler=command_validate)

    inspect = subparsers.add_parser("inspect", help="inspect a .yios package")
    inspect.add_argument("package", type=Path)
    inspect.set_defaults(handler=command_inspect)

    route = subparsers.add_parser("route", help="route a production task")
    add_source_or_package(route)
    route.add_argument("task")
    route.add_argument("--state", type=Path)
    route.set_defaults(handler=command_route)

    compile_parser = subparsers.add_parser("compile", help="compile a runtime prompt")
    add_source_or_package(compile_parser)
    mode_group = compile_parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--mode")
    mode_group.add_argument("--task")
    compile_parser.add_argument("--skill", action="append", default=[])
    compile_parser.add_argument("--inject", action="append", default=[], metavar="NAME=PATH")
    compile_parser.add_argument("--state", type=Path)
    compile_parser.add_argument("--wei-report", type=Path)
    compile_parser.add_argument("--wei-skill", action="append", default=[])
    compile_parser.add_argument("--run-id")
    compile_parser.add_argument("--task-id")
    compile_parser.add_argument("--output", type=Path)
    compile_parser.add_argument("--metadata", action="store_true")
    compile_parser.set_defaults(handler=command_compile)

    plan = subparsers.add_parser("plan", help="show an isolated multi-pass plan")
    add_source_or_package(plan)
    plan.add_argument("pipeline", nargs="?", default="co-directing")
    plan.set_defaults(handler=command_plan)

    state_init = subparsers.add_parser("state-init", help="create project state")
    state_init.add_argument("--project", required=True)
    state_init.add_argument("--format")
    state_init.add_argument("--pipeline")
    state_init.add_argument("--output", required=True, type=Path)
    state_init.set_defaults(handler=command_state_init)

    state_validate = subparsers.add_parser("state-validate", help="validate project state")
    state_validate.add_argument("state", type=Path)
    state_validate.set_defaults(handler=command_state_validate)

    wei_template = subparsers.add_parser("wei-template", help="create a bound WEI_REPORT template")
    add_source_or_package(wei_template)
    wei_template.add_argument("--state", required=True, type=Path)
    wei_template.add_argument("--run-id", required=True)
    wei_template.add_argument("--task-id", required=True)
    wei_template.add_argument("--skill", action="append", default=[])
    wei_template.add_argument("--inject", action="append", default=[], metavar="NAME=PATH")
    wei_template.add_argument("--output", required=True, type=Path)
    wei_template.set_defaults(handler=command_wei_template)

    freeze_wei = subparsers.add_parser("freeze-wei", help="freeze a canonical WEI_REPORT")
    freeze_wei.add_argument("report", type=Path)
    freeze_wei.add_argument("--output-dir", required=True, type=Path)
    freeze_wei.set_defaults(handler=command_freeze_wei)

    eval_list = subparsers.add_parser("eval-list", help="list Beta-3 behavioral evals")
    add_source_or_package(eval_list)
    eval_list.set_defaults(handler=command_eval_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (YIError, OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
