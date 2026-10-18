"""Deterministic content-calendar planner.

Given a start date, a horizon in weeks, a cadence per platform, and a list of pillars, emit a
fixed set of dated slots. Same inputs always produce the same calendar — the model fills in the
ideas, but the dates, weekdays, platforms and pillar rotation are computed here.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

# Fixed weekday choices (Mon=0 .. Sun=6) for a given posts-per-week cadence. Chosen to spread
# posting evenly across the working week and onward; stable so calendars are reproducible.
WEEKDAY_PLANS: Dict[int, List[int]] = {
    1: [2],
    2: [1, 3],
    3: [1, 3, 5],
    4: [1, 2, 4, 5],
    5: [0, 1, 2, 3, 4],
    6: [0, 1, 2, 3, 4, 5],
    7: [0, 1, 2, 3, 4, 5, 6],
}
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def plan(
    start: str,
    weeks: int,
    platforms: List[Dict[str, Any]],
    pillars: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a calendar.

    ``platforms`` is a list of ``{"platform": slug, "cadence": int}``. ``cadence`` is posts per
    week (1-7). ``pillars`` rotate round-robin per platform.
    """
    try:
        d0 = datetime.date.fromisoformat(start)
    except ValueError:
        return {"ok": False, "error": f"invalid start date '{start}' (use YYYY-MM-DD)"}
    if weeks < 1:
        return {"ok": False, "error": "weeks must be >= 1"}
    pillars = [p for p in (pillars or []) if p] or ["General"]
    slots: List[Dict[str, Any]] = []
    errors: List[str] = []
    for entry in platforms:
        slug = (entry.get("platform") or "").strip().lower()
        cadence = int(entry.get("cadence") or 0)
        if cadence < 1 or cadence > 7:
            errors.append(f"{slug or '?'}: cadence must be 1-7, got {cadence}")
            continue
        weekdays = WEEKDAY_PLANS[cadence]
        idx = 0
        for week in range(weeks):
            week_start = d0 + datetime.timedelta(days=7 * week)
            week_start -= datetime.timedelta(days=week_start.weekday())  # align to Monday
            for wd in weekdays:
                day = week_start + datetime.timedelta(days=wd)
                if day < d0:
                    continue
                slots.append({
                    "date": day.isoformat(),
                    "weekday": WEEKDAYS[wd],
                    "week": week + 1,
                    "platform": slug,
                    "pillar": pillars[idx % len(pillars)],
                })
                idx += 1
    slots.sort(key=lambda s: (s["date"], s["platform"]))
    return {
        "ok": True,
        "start": start,
        "weeks": weeks,
        "pillars": pillars,
        "slot_count": len(slots),
        "by_platform": _counts(slots, "platform"),
        "by_pillar": _counts(slots, "pillar"),
        "slots": slots,
        "errors": errors,
    }


def _counts(slots: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for s in slots:
        out[s[key]] = out.get(s[key], 0) + 1
    return out
