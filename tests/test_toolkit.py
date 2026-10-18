"""Toolkit behaviour: specs, post validation, hashtags, calendar, export audit. Determinism."""

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from doddle_social import hashtags, planner, platforms, posts  # noqa: E402
from doddle_social.audit import audit_export  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "posts.json")


def test_registry_has_expected_platforms():
    assert set(platforms.slugs()) == {
        "instagram", "linkedin", "tiktok", "x", "youtube", "pinterest", "facebook", "threads"
    }
    for slug in platforms.slugs():
        spec = platforms.get(slug)
        assert spec["name"]
        assert spec["source"].startswith("http")


def test_platform_aliases():
    assert platforms.get("IG")["slug"] == "instagram"
    assert platforms.get("twitter")["slug"] == "x"
    assert platforms.get("youtube-shorts")["slug"] == "youtube"
    assert platforms.get("nope") is None


def test_validate_post_within_limit_scores_higher():
    short = posts.validate("A clear one-line hook that earns the stop. Learn more.", "x")
    long_text = "word " * 200
    over = posts.validate(long_text, "x")
    assert short.ok and over.ok
    assert short.composite > over.composite
    length = {s.id: s for s in over.signals}["post.length"]
    assert length.value < length.max
    assert any(f.id == "post.length" for f in over.findings)


def test_validate_post_hashtag_cap_is_a_hard_finding():
    text = "hello " + " ".join(f"#tag{i}" for i in range(31))
    report = posts.validate(text, "instagram")
    sig = {s.id: s for s in report.signals}["post.hashtags"]
    assert sig.value == 0.0
    assert any(f.id == "post.hashtags" and f.severity == "high" for f in report.findings)


def test_validate_post_alt_text_gap():
    report = posts.validate("A post with media. Sign up today.", "instagram",
                            has_media=True, has_alt_text=False)
    sig = {s.id: s for s in report.signals}["post.media_alt"]
    assert sig.value == 0.0
    assert any(f.id == "post.media_alt" for f in report.findings)


def test_validate_post_is_deterministic():
    text = "Stop guessing. Here is the fix. #growth #marketing #social"
    a = posts.validate(text, "instagram", has_media=True, has_alt_text=True)
    b = posts.validate(text, "instagram", has_media=True, has_alt_text=True)
    assert a.composite == b.composite
    assert [s.to_dict() for s in a.signals] == [s.to_dict() for s in b.signals]


def test_unknown_platform_fails_cleanly():
    report = posts.validate("hi", "myspace")
    assert report.ok is False
    assert report.missing


def test_hashtag_analysis():
    a = hashtags.analyze("great #launch #growth #launch")
    assert a["count"] == 3
    assert a["unique_count"] == 2
    assert a["duplicates"] == ["launch"]
    assert a["density"] is not None


def test_calendar_is_deterministic_and_counts_match():
    a = planner.plan("2026-11-02", 2, [{"platform": "instagram", "cadence": 3},
                                       {"platform": "linkedin", "cadence": 2}],
                     ["educate", "story", "offer"])
    b = planner.plan("2026-11-02", 2, [{"platform": "instagram", "cadence": 3},
                                       {"platform": "linkedin", "cadence": 2}],
                     ["educate", "story", "offer"])
    assert a["slots"] == b["slots"]
    assert a["by_platform"] == {"instagram": 6, "linkedin": 4}
    assert a["slot_count"] == 10


def test_calendar_rejects_bad_cadence():
    result = planner.plan("2026-11-02", 1, [{"platform": "x", "cadence": 9}], None)
    assert result["ok"] is True
    assert result["errors"]
    assert result["slot_count"] == 0


def test_audit_fixture_runs_and_has_envelope_shape():
    env = audit_export(FIXTURE)
    assert env["ok"] is True
    assert env["scores"]["composite"] is not None
    assert env["evidence"]["stamp"] == "CURRENT"
    assert env["completeness"]["signals"] == "5/5"
    ids = {s["id"] for s in env["signals"]}
    assert {"audit.cadence", "audit.caption_compliance", "audit.alt_coverage"} <= ids


def test_audit_missing_engagement_is_null_not_zero():
    env = audit_export(os.path.join(ROOT, "tests", "fixtures", "no_impressions.json"))
    eng = {s["id"]: s for s in env["signals"]}["audit.engagement"]
    assert eng["value"] is None
    assert eng["skipped_reason"]


def test_audit_handles_missing_file():
    env = audit_export(os.path.join(ROOT, "tests", "fixtures", "does-not-exist.json"))
    assert env["ok"] is False
    assert env["error"]["hint"]


def test_cli_validate_post_json():
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "dsocial"),
         "validate-post", "linkedin", "--text", "A clear announcement. Sign up today.", "--json"],
        capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["command"] == "validate-post"
    assert payload["scores"]["composite"] > 0


def test_cli_specs_and_calendar():
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "dsocial"),
         "calendar", "--start", "2026-11-02", "--weeks", "1", "--platform", "x:2", "--json"],
        capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["calendar"]["slot_count"] == 2
