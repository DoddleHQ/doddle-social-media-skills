"""Audit a social account from a recorded post export.

Input is data, not scraping: a JSON or CSV export the user provides (their own analytics
export, an approved API pull, or a saved snapshot). Every number is computed from those rows.
Nothing is fetched from a platform.
"""

from __future__ import annotations

import csv
import datetime
import json
from typing import Any, Dict, List, Optional

from . import DATA_VERSION, SCORING_VERSION, TOOLKIT_VERSION
from . import platforms
from .envelope import CURRENT, Finding, Signal, make_envelope, tier_for
from .hashtags import analyze as analyze_hashtags

DATE_KEYS = ("posted_at", "date", "published_at", "timestamp")
TEXT_KEYS = ("text", "caption", "body", "message")
PLATFORM_KEYS = ("platform", "network", "channel")
IMPRESSION_KEYS = ("impressions", "reach", "views")
MEDIA_KEYS = ("media_type", "format", "type")
ALT_KEYS = ("has_alt_text", "alt_text", "alt")
ENGAGEMENT_FIELDS = ("likes", "comments", "shares", "saves")


def _pick(row: Dict[str, Any], keys: tuple) -> Any:
    for k in keys:
        for rk in row:
            if rk.lower().strip() == k:
                return row[rk]
    return None


def _as_date(value: Any) -> Optional[datetime.date]:
    if value in (None, ""):
        return None
    text = str(value).strip()[:10]
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        return None


def _as_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return None


def load_export(path: str) -> List[Dict[str, Any]]:
    """Load rows from a JSON array/object or a CSV file."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    if path.lower().endswith(".csv"):
        return [dict(r) for r in csv.DictReader(raw.splitlines())]
    data = json.loads(raw)
    if isinstance(data, dict):
        for key in ("posts", "items", "data", "records"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("export must be a JSON array/object or CSV")


def audit_export(path: str, *, target: Optional[str] = None) -> Dict[str, Any]:
    try:
        rows = load_export(path)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user
        return make_envelope(
            "audit", target or path,
            toolkit_version=TOOLKIT_VERSION, scoring_version=SCORING_VERSION, data_version=DATA_VERSION,
            evidence_stamp="PARTIAL",
            error={"message": f"could not read export: {exc}",
                   "hint": "Provide a JSON array of posts or a CSV with columns like posted_at, platform, text, media_type, has_alt_text, impressions, likes."},
        )
    if not rows:
        return make_envelope(
            "audit", target or path,
            toolkit_version=TOOLKIT_VERSION, scoring_version=SCORING_VERSION, data_version=DATA_VERSION,
            error={"message": "export contains no posts",
                   "hint": "Check the file has a non-empty list of post rows."},
        )

    norm = [_normalise(r) for r in rows]
    return _audit(norm, target or path)


def _normalise(row: Dict[str, Any]) -> Dict[str, Any]:
    text = str(_pick(row, TEXT_KEYS) or "")
    platform = str(_pick(row, PLATFORM_KEYS) or "").strip().lower()
    media_raw = _pick(row, MEDIA_KEYS)
    media = str(media_raw).strip().lower() if media_raw not in (None, "") else None
    alt_raw = _pick(row, ALT_KEYS)
    has_alt = None
    if alt_raw is not None:
        has_alt = str(alt_raw).strip().lower() in ("1", "true", "yes", "y") or (
            isinstance(alt_raw, str) and len(alt_raw.strip()) > 3 and alt_raw.strip().lower() not in ("false", "no", "none"))
    has_media = media is not None and media not in ("text", "none", "")
    return {
        "platform": platform,
        "text": text,
        "date": _as_date(_pick(row, DATE_KEYS)),
        "media": media,
        "has_media": has_media,
        "has_alt_text": has_alt,
        "impressions": _as_int(_pick(row, IMPRESSION_KEYS)),
        "engagement": sum(v for v in (_as_int(row.get(f, row.get(f.capitalize()))) or 0 for f in ENGAGEMENT_FIELDS)),
    }


def _audit(rows: List[Dict[str, Any]], target: str) -> Dict[str, Any]:
    signals: List[Signal] = []
    findings: List[Finding] = []
    notes: List[str] = []

    dated = [r for r in rows if r["date"]]
    span_days = 0
    if dated:
        lo = min(r["date"] for r in dated)
        hi = max(r["date"] for r in dated)
        span_days = (hi - lo).days + 1
    span_weeks = max(span_days / 7.0, 1.0) if dated else None

    # cadence -----------------------------------------------------------
    if span_weeks:
        cadence = round(len(dated) / span_weeks, 2)
        cpts = 25.0 if cadence >= 3 else round(25.0 * cadence / 3.0, 1)
        signals.append(Signal("audit.cadence", cpts, 25,
                              detail={"posts": len(dated), "span_days": span_days, "per_week": cadence}))
        if cadence < 3:
            findings.append(Finding("audit.cadence", 0, "medium", "low", 25 - cpts,
                                    "Posting cadence is below the 3-per-week starting line",
                                    f"{len(dated)} posts over {span_days} days = {cadence}/week."))
    else:
        signals.append(Signal("audit.cadence", None, 25, detail={"posts": len(rows)},
                              skipped_reason="not applicable: no dated posts to compute a rate"))
        notes.append("Cadence not measured: no post dates in the export.")

    # caption compliance ------------------------------------------------
    checked = [r for r in rows if platforms.get(r["platform"]) and r["text"]]
    if checked:
        over = []
        for r in checked:
            spec = platforms.get(r["platform"])
            limit = spec.get("caption_limit")
            if limit and len(r["text"]) > limit:
                over.append((r["platform"], len(r["text"]), limit))
        rate = round(100.0 * (len(checked) - len(over)) / len(checked), 1)
        cpts = round(25.0 * rate / 100.0, 1)
        signals.append(Signal("audit.caption_compliance", cpts, 25,
                              detail={"checked": len(checked), "over_limit": len(over), "rate_pct": rate}))
        if over:
            findings.append(Finding("audit.caption_compliance", 0, "high", "low", 25 - cpts,
                                    f"{len(over)} caption(s) exceed the platform limit",
                                    "; ".join(f"{p} {n}>{lim}" for p, n, lim in over[:5])))
    else:
        signals.append(Signal("audit.caption_compliance", None, 25, detail={},
                              skipped_reason="not applicable: no posts with a known platform and text"))

    # alt-text coverage -------------------------------------------------
    media_rows = [r for r in rows if r["has_media"]]
    if media_rows:
        knowable = [r for r in media_rows if r["has_alt_text"] is not None]
        if knowable:
            good = sum(1 for r in knowable if r["has_alt_text"])
            rate = round(100.0 * good / len(knowable), 1)
            apts = round(15.0 * rate / 100.0, 1)
            signals.append(Signal("audit.alt_coverage", apts, 15,
                                  detail={"media_posts": len(media_rows), "with_alt": good, "rate_pct": rate}))
            if rate < 100:
                findings.append(Finding("audit.alt_coverage", 0, "medium", "low", 15 - apts,
                                        "Some media posts have no alt text",
                                        f"{good}/{len(knowable)} media posts carry alt text."))
        else:
            signals.append(Signal("audit.alt_coverage", None, 15, detail={},
                                  skipped_reason="not applicable: export has no alt-text field"))
    else:
        signals.append(Signal("audit.alt_coverage", None, 15, detail={},
                              skipped_reason="not applicable: no media posts"))

    # hashtag fit -------------------------------------------------------
    if checked:
        fits = 0
        total_tags = 0
        for r in checked:
            spec = platforms.get(r["platform"])
            n = analyze_hashtags(r["text"])["count"]
            total_tags += n
            band = spec.get("hashtag_recommended") or ""
            nums = [int(x) for x in band.replace(" ", "").split("-") if x.isdigit()]
            if nums and nums[0] <= n <= nums[-1]:
                fits += 1
        rate = round(100.0 * fits / len(checked), 1)
        hpts = round(10.0 * rate / 100.0, 1)
        signals.append(Signal("audit.hashtag_fit", hpts, 10,
                              detail={"checked": len(checked), "in_band": fits, "rate_pct": rate,
                                      "avg_per_post": round(total_tags / len(checked), 2)}))
    else:
        signals.append(Signal("audit.hashtag_fit", None, 10, detail={},
                              skipped_reason="not applicable: no posts with a known platform and text"))

    # engagement --------------------------------------------------------
    with_impr = [r for r in rows if r["impressions"]]
    if with_impr:
        total_er = sum((r["engagement"] / r["impressions"]) for r in with_impr if r["impressions"])
        er = round(100.0 * total_er / len(with_impr), 3)
        epts = min(10.0, round(10.0 * min(er, 5.0) / 5.0, 1))
        signals.append(Signal("audit.engagement", epts, 10,
                              detail={"posts": len(with_impr), "avg_rate_pct": er}))
    else:
        signals.append(Signal("audit.engagement", None, 10, detail={},
                              skipped_reason="not applicable: export has no impressions/reach column"))

    measured = [s for s in signals if s.value is not None]
    earned = sum(s.value for s in measured)
    possible = sum(s.max for s in measured)
    composite = round(100.0 * earned / possible, 1) if possible else None
    categories = {
        "cadence": signals[0].value,
        "compliance": round(sum(s.value for s in signals if s.id in ("audit.caption_compliance", "audit.hashtag_fit"))
                            / max(sum(s.max for s in signals if s.id in ("audit.caption_compliance", "audit.hashtag_fit")), 1) * 100, 1),
    }
    for i, f in enumerate(sorted(findings, key=lambda f: (-f.points_lost, f.id)), start=1):
        f.priority = i
    return make_envelope(
        "audit", target,
        toolkit_version=TOOLKIT_VERSION, scoring_version=SCORING_VERSION, data_version=DATA_VERSION,
        evidence_stamp=CURRENT, pages_ok=len(rows),
        notes=notes, categories=categories, missing=[s.id for s in signals if s.value is None],
        signal_count=len(measured), signal_total=len(signals),
        scores={"composite": composite, "tier": tier_for(composite), "categories": categories},
        signals=signals, findings=findings,
    )
