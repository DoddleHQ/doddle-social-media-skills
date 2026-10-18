"""``dsocial`` — the deterministic command line for doddle-social-media-skills.

Skills call these commands and read the JSON. The CLI computes; the model narrates.

Commands::

    dsocial version
    dsocial specs  [--platform SLUG] [--json]
    dsocial validate-post PLATFORM [--text T | --file F] [--media] [--alt] [--json]
    dsocial hashtags [--text T | --file F] [--platform SLUG] [--json]
    dsocial calendar --start YYYY-MM-DD --weeks N --platform SLUG:C [--pillars a,b] [--json]
    dsocial audit  <export.json|csv> [--json]
    dsocial report <export.json|csv> [--out FILE] [--json]
    dsocial doctor
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from . import DATA_VERSION, SCORING_VERSION, TOOLKIT_VERSION
from . import hashtags as hashtags_mod
from . import platforms as platforms_mod
from . import planner
from .audit import audit_export
from .envelope import CURRENT, make_envelope, tier_for, utc_now
from .posts import validate as validate_post
from .report import render_markdown


def _emit(obj: Any, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(_human(obj) + "\n")


def _human(obj: Dict[str, Any]) -> str:
    command = obj.get("command")
    if obj.get("error"):
        e = obj["error"]
        return f"ERROR: {e.get('message')}\n  hint: {e.get('hint')}"
    if command == "report":
        return obj.get("markdown", "")
    if command in ("audit", "validate-post"):
        s = obj.get("scores") or {}
        head = (f"{command} {obj.get('target')}: {s.get('composite')}/100 ({s.get('tier')}) · "
                f"evidence {obj.get('evidence', {}).get('stamp')}")
        lines = [head]
        for f in (obj.get("findings") or [])[:6]:
            lines.append(f"  #{f['priority']} [{f['severity']}] {f['title']} (~{f['points_lost']} pts)")
        return "\n".join(lines)
    if command == "specs":
        rows = obj.get("platforms") or []
        return "\n".join(platforms_mod.spec_summary(r) for r in rows)
    if command == "hashtags":
        return "\n".join(hashtags_mod.stats_lines(obj["hashtags"]))
    if command == "calendar":
        plan = obj.get("calendar") or {}
        if not plan.get("ok"):
            return f"ERROR: {plan.get('error')}"
        return f"{plan['slot_count']} slots from {plan['start']} over {plan['weeks']} week(s)"
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _wants_json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False)) or not sys.stdout.isatty()


def _read_text(args: argparse.Namespace) -> str:
    if getattr(args, "text", None) is not None:
        return args.text
    if getattr(args, "file", None):
        with open(args.file, encoding="utf-8") as fh:
            return fh.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def cmd_version(args: argparse.Namespace) -> int:
    payload = {
        "toolkit": "doddle-social-media",
        "toolkit_version": TOOLKIT_VERSION,
        "scoring_version": SCORING_VERSION,
        "data_version": DATA_VERSION,
        "platforms": platforms_mod.slugs(),
        "python": sys.version.split()[0],
    }
    _emit(payload, True)
    return 0


def cmd_specs(args: argparse.Namespace) -> int:
    if args.platform:
        spec = platforms_mod.get(args.platform)
        if spec is None:
            _emit({"ok": False, "command": "specs", "error": {
                "message": f"unknown platform '{args.platform}'",
                "hint": "Known: " + ", ".join(platforms_mod.slugs())}}, _wants_json(args))
            return 1
        payload = {"ok": True, "command": "specs", "target": spec["slug"], "platforms": [spec],
                   "registry_version": platforms_mod.REGISTRY_VERSION, "checked": platforms_mod.CHECKED}
    else:
        payload = {"ok": True, "command": "specs", "target": "all", "platforms": platforms_mod.all_specs(),
                   "registry_version": platforms_mod.REGISTRY_VERSION, "checked": platforms_mod.CHECKED}
    _emit(payload, _wants_json(args))
    return 0


def cmd_validate_post(args: argparse.Namespace) -> int:
    text = _read_text(args)
    if not text:
        _emit({"ok": False, "command": "validate-post", "target": args.platform, "error": {
            "message": "no post text provided",
            "hint": "Pass --text, --file, or pipe the caption on stdin."}}, _wants_json(args))
        return 1
    report = validate_post(text, args.platform, has_media=args.media, has_alt_text=args.alt)
    if not report.ok:
        _emit({"ok": False, "command": "validate-post", "target": args.platform, "error": {
            "message": report.missing[0] if report.missing else "invalid input",
            "hint": "Known platforms: " + ", ".join(platforms_mod.slugs())}}, _wants_json(args))
        return 1
    env = make_envelope(
        "validate-post", report.platform,
        toolkit_version=TOOLKIT_VERSION, scoring_version=SCORING_VERSION, data_version=DATA_VERSION,
        signal_count=sum(1 for s in report.signals if s.value is not None), signal_total=len(report.signals),
        missing=[s.id for s in report.signals if s.value is None],
        scores={"composite": report.composite, "tier": tier_for(report.composite)},
        signals=report.signals, findings=report.findings,
    )
    env["spec"] = report.detail["spec"]
    env["hashtags"] = report.detail["hashtags"]
    _emit(env, _wants_json(args))
    return 0


def cmd_hashtags(args: argparse.Namespace) -> int:
    text = _read_text(args)
    data = hashtags_mod.analyze(text)
    payload: Dict[str, Any] = {
        "ok": True, "command": "hashtags", "target": args.platform or "text",
        "generated_at": utc_now(), "toolkit_version": TOOLKIT_VERSION, "data_version": DATA_VERSION,
        "evidence": {"stamp": CURRENT}, "hashtags": data,
    }
    spec = platforms_mod.get(args.platform) if args.platform else None
    if spec:
        payload["platform"] = {"slug": spec["slug"], "hashtag_cap": spec.get("hashtag_cap"),
                               "hashtag_recommended": spec.get("hashtag_recommended")}
        over = spec.get("hashtag_cap") and data["count"] > spec["hashtag_cap"]
        payload["summary"] = (f"{data['count']} hashtags"
                              + (f" — OVER the {spec['hashtag_cap']} cap" if over else
                                 f" — within the {spec['hashtag_cap']} cap" if spec.get("hashtag_cap") else
                                 f" ({spec['name']} has no documented cap)"))
    else:
        payload["summary"] = f"{data['count']} hashtags ({data['unique_count']} unique)"
    _emit(payload, _wants_json(args))
    return 0


def _parse_platform_arg(value: str) -> Dict[str, Any]:
    if ":" in value:
        slug, _, cadence = value.partition(":")
        return {"platform": slug.strip(), "cadence": int(cadence) if cadence.strip().isdigit() else 0}
    return {"platform": value.strip(), "cadence": 0}


def cmd_calendar(args: argparse.Namespace) -> int:
    platforms = [_parse_platform_arg(v) for v in (args.platform or [])]
    pillars = [p.strip() for p in (args.pillars or "").split(",") if p.strip()]
    result = planner.plan(args.start, args.weeks, platforms, pillars)
    payload = {
        "ok": bool(result.get("ok")), "command": "calendar", "target": args.start,
        "generated_at": utc_now(), "toolkit_version": TOOLKIT_VERSION, "data_version": DATA_VERSION,
        "evidence": {"stamp": CURRENT}, "calendar": result,
    }
    if not result.get("ok"):
        payload["error"] = {"message": result.get("error", "invalid calendar input"),
                            "hint": "Use --start YYYY-MM-DD --weeks N --platform slug:cadence (cadence 1-7)."}
    _emit(payload, _wants_json(args))
    return 0 if result.get("ok") else 1


def cmd_audit(args: argparse.Namespace) -> int:
    env = audit_export(args.export)
    _emit(env, _wants_json(args))
    return 0 if env["ok"] else 1


def cmd_report(args: argparse.Namespace) -> int:
    env = audit_export(args.export)
    env["command"] = "report"
    env["markdown"] = render_markdown(env)
    _emit(env, _wants_json(args))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(env["markdown"])
    return 0 if env["ok"] else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = [
        {"name": "python", "ok": sys.version_info >= (3, 9), "detail": sys.version.split()[0]},
        {"name": "toolkit_import", "ok": True, "detail": TOOLKIT_VERSION},
        {"name": "platforms", "ok": len(platforms_mod.slugs()) >= 1, "detail": f"{len(platforms_mod.slugs())} registered"},
        {"name": "stdout_tty", "ok": True, "detail": str(sys.stdout.isatty())},
    ]
    ok = all(c["ok"] for c in checks)
    _emit({"ok": ok, "command": "doctor", "checks": checks}, True)
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="force JSON output")

    p = argparse.ArgumentParser(prog="dsocial", description="Doddle Social Media deterministic toolkit")
    p.add_argument("--version", action="store_true", help="print toolkit version and exit")
    sub = p.add_subparsers(dest="subcommand")

    sp = sub.add_parser("version", help="print versions")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_version)

    sp = sub.add_parser("specs", parents=[common], help="platform-spec registry")
    sp.add_argument("--platform", help="one platform slug")
    sp.set_defaults(func=cmd_specs)

    sp = sub.add_parser("validate-post", parents=[common], help="validate a caption against a platform")
    sp.add_argument("platform")
    sp.add_argument("--text")
    sp.add_argument("--file")
    sp.add_argument("--media", action="store_true", help="the post has media")
    sp.add_argument("--alt", action="store_true", help="media has alt text")
    sp.set_defaults(func=cmd_validate_post)

    sp = sub.add_parser("hashtags", parents=[common], help="hashtag stats for a caption")
    sp.add_argument("--text")
    sp.add_argument("--file")
    sp.add_argument("--platform")
    sp.set_defaults(func=cmd_hashtags)

    sp = sub.add_parser("calendar", parents=[common], help="deterministic content calendar")
    sp.add_argument("--start", required=True)
    sp.add_argument("--weeks", type=int, default=4)
    sp.add_argument("--platform", action="append", help="slug:cadence (repeatable)")
    sp.add_argument("--pillars", help="comma-separated pillar names")
    sp.set_defaults(func=cmd_calendar)

    sp = sub.add_parser("audit", parents=[common], help="audit a post export (JSON/CSV)")
    sp.add_argument("export")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("report", parents=[common], help="audit an export and render markdown")
    sp.add_argument("export")
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("doctor", help="check the environment")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_doctor)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False):
        return cmd_version(argparse.Namespace(subcommand="version", json=True))
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
