"""Render an audit/validate envelope as a markdown report. Numbers are copied, never recomputed."""

from __future__ import annotations

from typing import Any, Dict, List


def _fmt_score(v: Any) -> str:
    return "not scored" if v is None else f"{v}/100"


def _num(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def render_markdown(env: Dict[str, Any]) -> str:
    lines: List[str] = []
    scores = env.get("scores") or {}
    target = env.get("target", "")
    command = env.get("command", "audit")
    title = {"report": "Social Media Report", "audit": "Social Media Audit",
             "validate-post": "Post Review"}.get(command, command.replace("-", " ").title())
    lines.append(f"# {title} — {target}")
    lines.append("")
    lines.append(f"**{_fmt_score(scores.get('composite'))} ({scores.get('tier', '')})** · evidence "
                 f"`{env.get('evidence', {}).get('stamp', '—')}` · scoring `{env.get('scoring_version')}` · "
                 f"data `{env.get('data_version')}`")
    lines.append("")
    if env.get("error"):
        err = env["error"]
        lines.append(f"**Error:** {err.get('message')}")
        lines.append("")
        lines.append(f"> {err.get('hint')}")
        return "\n".join(lines) + "\n"

    cats = scores.get("categories") or {}
    if cats:
        lines.append("## Category scores")
        lines.append("")
        lines.append("| Category | Score |")
        lines.append("|----------|-------|")
        for name, val in cats.items():
            lines.append(f"| {name} | {_fmt_score(val)} |")
        lines.append("")

    signals = env.get("signals") or []
    if signals:
        lines.append("## Signals")
        lines.append("")
        lines.append("| Signal | Value | Max | Class | Note |")
        lines.append("|--------|-------|-----|-------|------|")
        for s in signals:
            note = s.get("skipped_reason") or ""
            lines.append(f"| {s['id']} | {_num(s.get('value'))} | {s.get('max')} | {s.get('class')} | {note} |")
        lines.append("")

    findings = env.get("findings") or []
    if findings:
        lines.append("## Prioritized findings")
        lines.append("")
        for f in findings:
            lines.append(f"{f['priority']}. **{f['title']}** — {f['severity']}, effort {f['effort']}, "
                         f"~{f['points_lost']} pts")
            lines.append(f"   - {f['detail']}")
        lines.append("")

    plan = env.get("calendar")
    if plan and plan.get("ok"):
        lines.append("## Calendar")
        lines.append("")
        lines.append(f"{plan['slot_count']} slots from {plan['start']} over {plan['weeks']} week(s).")
        lines.append("")
        lines.append("| Date | Day | Platform | Pillar |")
        lines.append("|------|-----|----------|--------|")
        for slot in plan["slots"]:
            lines.append(f"| {slot['date']} | {slot['weekday']} | {slot['platform']} | {slot['pillar']} |")
        lines.append("")

    lines.append(f"_Generated {env.get('generated_at')} by doddle-social-media toolkit {env.get('toolkit_version')}._")
    return "\n".join(lines) + "\n"
