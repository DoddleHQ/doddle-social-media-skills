"""Validate a single social post against a platform spec.

Deterministic: the same text + spec always yields the same signals. Judgement about *what* to
say belongs to the skill; this module only measures the text and computes a readiness score.

Signals carry points earned (0..max) with the raw measurement in ``detail``, matching the
envelope contract used across the pack.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import platforms
from .envelope import Finding, Signal, tier_for
from .hashtags import analyze as analyze_hashtags

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF]"
)
CTA_RE = re.compile(
    r"\b(learn more|sign up|get started|try (it|now|free)|book|shop|download|subscribe|"
    r"register|join|follow|comment|share|save|dm|link in bio|tap|swipe|read|watch|"
    r"discover|grab|claim|reserve|buy|start)\b",
    re.IGNORECASE,
)


@dataclass
class PostReport:
    ok: bool
    platform: str
    text: str
    signals: List[Signal] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    composite: Optional[float] = None
    detail: Dict[str, Any] = field(default_factory=dict)


def _band(recommended: Optional[str]) -> Optional[tuple]:
    if not recommended:
        return None
    nums = [int(n) for n in re.findall(r"\d+", recommended)]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None


def _first_line(text: str) -> str:
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()
    return (text or "").strip()


def _finding(id: str, severity: str, effort: str, lost: float, title: str, detail: str) -> Finding:
    return Finding(id=id, priority=0, severity=severity, effort=effort,
                   points_lost=round(lost, 1), title=title, detail=detail)


def validate(
    text: str,
    platform: str,
    *,
    has_media: Optional[bool] = None,
    has_alt_text: Optional[bool] = None,
) -> PostReport:
    spec = platforms.get(platform)
    text = text or ""
    if spec is None:
        return PostReport(ok=False, platform=platform, text=text,
                          missing=[f"unknown platform '{platform}'"])

    signals: List[Signal] = []
    findings: List[Finding] = []

    # --- length ---------------------------------------------------------
    limit = spec.get("caption_limit")
    chars = len(text)
    if limit:
        if chars <= limit:
            pts, sev = 30.0, None
        else:
            pts = round(30.0 * limit / chars, 1)
            sev = "high"
        signals.append(Signal("post.length", pts, 30, detail={"chars": chars, "limit": limit}))
        if sev:
            findings.append(_finding(
                "post.length", sev, "low", 30 - pts,
                f"Over the {limit}-char caption limit",
                f"The caption is {chars} characters; {spec['name']} allows {limit}.",
            ))
    else:
        signals.append(Signal("post.length", None, 30, detail={"chars": chars, "limit": None},
                              skipped_reason="not applicable: no documented caption limit"))

    # --- hashtags -------------------------------------------------------
    h = analyze_hashtags(text)
    count = h["count"]
    cap = spec.get("hashtag_cap")
    band = _band(spec.get("hashtag_recommended"))
    if cap and count > cap:
        hpts, hsev = 0.0, "high"
        htitle = f"Over the {cap}-hashtag cap"
        hdetail = f"{count} hashtags; {spec['name']} caps at {cap}."
    elif band and count == 0:
        hpts, hsev = 12.0, "low"
        htitle = "No hashtags"
        hdetail = f"0 hashtags; the pack's starting range for {spec['name']} is {spec['hashtag_recommended']}."
    elif band and band[0] <= count <= band[1]:
        hpts, hsev = 20.0, None
        htitle = hdetail = ""
    elif band and count < band[0]:
        hpts, hsev = 14.0, "low"
        htitle = "Fewer hashtags than the starting range"
        hdetail = f"{count} hashtags; started range is {spec['hashtag_recommended']}."
    else:  # above band but within cap
        hpts, hsev = 12.0, "low"
        htitle = "More hashtags than the starting range"
        hdetail = f"{count} hashtags; started range is {spec['hashtag_recommended']}."
    signals.append(Signal("post.hashtags", hpts, 20,
                          detail={"count": count, "recommended": spec.get("hashtag_recommended"),
                                  "cap": cap, "duplicates": h["duplicates"]}))
    if hsev:
        findings.append(_finding("post.hashtags", hsev, "low", 20 - hpts, htitle, hdetail))

    # --- media / alt text ----------------------------------------------
    if spec.get("alt_text") and has_media:
        ok_alt = bool(has_alt_text)
        mpts = 15.0 if ok_alt else 0.0
        signals.append(Signal("post.media_alt", mpts, 15, detail={"has_media": True, "has_alt_text": ok_alt}))
        if not ok_alt:
            findings.append(_finding(
                "post.media_alt", "medium", "low", 15.0,
                "Media has no alt text",
                f"{spec['name']} supports alt text; adding it costs nothing and is accessible.",
            ))
    else:
        reason = ("not applicable: platform has no alt-text field"
                  if not spec.get("alt_text") else
                  "not applicable: post has no media")
        signals.append(Signal("post.media_alt", None, 15, detail={}, skipped_reason=reason))

    # --- hook (first line) ---------------------------------------------
    fl = _first_line(text)
    fl_len = len(fl)
    if fl_len == 0:
        signals.append(Signal("post.hook", None, 15, detail={}, skipped_reason="not applicable: empty post"))
    else:
        if 40 <= fl_len <= 125:
            pts, sev = 15.0, None
        elif fl_len < 40:
            pts, sev = 9.0, "low"
        else:
            pts = max(3.0, 15.0 - (fl_len - 125) / 10.0)
            sev = "medium"
        signals.append(Signal("post.hook", round(pts, 1), 15, detail={"first_line_chars": fl_len}))
        if sev:
            verb = "shorter than" if fl_len < 40 else "longer than"
            findings.append(_finding(
                "post.hook", sev, "medium", 15 - pts,
                "First line is outside the scannable range",
                f"The first line is {fl_len} characters, {verb} the 40-125 char band most feeds show before truncating.",
            ))

    # --- call to action -------------------------------------------------
    has_cta = bool(CTA_RE.search(text))
    cpts = 10.0 if has_cta else 4.0
    signals.append(Signal("post.cta", cpts, 10, detail={"has_cta": has_cta}))
    if not has_cta:
        findings.append(_finding("post.cta", "low", "low", 6.0,
                                 "No call to action",
                                 "No recognisable CTA verb; state the one action you want."))

    # --- emoji load -----------------------------------------------------
    emojis = EMOJI_RE.findall(text)
    ecount = len(emojis)
    if ecount <= 3:
        epts, esev = 10.0, None
    elif ecount <= 6:
        epts, esev = 6.0, "low"
    else:
        epts, esev = 2.0, "low"
    signals.append(Signal("post.emoji", epts, 10, detail={"emoji_count": ecount}))
    if esev:
        findings.append(_finding("post.emoji", esev, "low", 10 - epts,
                                 "Heavy emoji use",
                                 f"{ecount} emoji; keep to a few so screen readers and scanners stay clean."))

    measured = [s for s in signals if s.value is not None]
    earned = sum(s.value for s in measured)
    possible = sum(s.max for s in measured)
    composite = round(100.0 * earned / possible, 1) if possible else None
    for i, f in enumerate(sorted(findings, key=lambda f: (-f.points_lost, f.id)), start=1):
        f.priority = i
    return PostReport(
        ok=True, platform=spec["slug"], text=text,
        signals=signals, findings=list(findings), composite=composite,
        detail={"spec": spec, "hashtags": h, "tier": tier_for(composite)},
    )
