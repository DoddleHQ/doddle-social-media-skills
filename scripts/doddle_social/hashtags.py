"""Hashtag extraction and deterministic stats.

Pure functions over a string. No network, no guessing. A hashtag is ``#`` followed by at
least one word character (Unicode letters/digits/underscore). The analysis never judges a
tag's *relevance* — that is the model's advisory job — it only measures what is in the text.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

TAG_RE = re.compile(r"#([\w]+)", re.UNICODE)
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
CAMEL_RE = re.compile(r"#[a-z]+[A-Z]")


def extract(text: str) -> List[str]:
    """Return hashtags in order of appearance, without the leading `#`, case preserved."""
    return TAG_RE.findall(text or "")


def analyze(text: str) -> Dict[str, Any]:
    tags = extract(text)
    lowered = [t.lower() for t in tags]
    unique = sorted(set(lowered))
    duplicates = sorted({t for t in lowered if lowered.count(t) > 1})
    words = WORD_RE.findall(text or "")
    word_count = len(words)
    density = round(len(tags) / word_count, 4) if word_count else None
    camel = CAMEL_RE.findall(text or "")
    return {
        "count": len(tags),
        "unique_count": len(unique),
        "duplicates": duplicates,
        "tags": tags,
        "unique_tags": unique,
        "word_count": word_count,
        "density": density,
        "avg_tag_length": round(sum(len(t) for t in tags) / len(tags), 1) if tags else None,
        "camel_case_count": len(camel),
        "longest_tag": max(tags, key=len) if tags else None,
    }


def stats_lines(a: Dict[str, Any]) -> List[str]:
    lines = [
        f"hashtags: {a['count']} ({a['unique_count']} unique)",
        f"density: {a['density']} tags/word" if a["density"] is not None else "density: not measured (no words)",
    ]
    if a["duplicates"]:
        lines.append("duplicates: " + ", ".join("#" + d for d in a["duplicates"]))
    if a["camel_case_count"]:
        lines.append(f"camelCase tags: {a['camel_case_count']} (screen-reader and parse risk)")
    return lines
