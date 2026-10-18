"""The platform-spec registry.

Every figure a social skill quotes about a platform (caption limits, hashtag caps, media
ratios, durations) lives here, versioned and sourced. Skills read these values; they never
hardcode them. When a platform changes a limit, bump :data:`__init__.DATA_VERSION` and update
the entry — never the prose in a skill.

Values are the documented public limits as of the ``checked`` date. They are configuration,
not advice: a post that exceeds a hard limit cannot be published, so treat ``*_limit`` and
``hashtag_cap`` as hard constraints and ``hashtag_recommended`` as guidance only.

Sources are the platforms' own help centres. Verify with ``dsocial specs --platform <slug>``
before quoting a limit to a user; this file is the single source of truth for the pack.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Registry. One dict per platform. Missing/unknown values are ``None`` (not 0).
# ---------------------------------------------------------------------------
PLATFORMS: Dict[str, Dict[str, Any]] = {
    "instagram": {
        "name": "Instagram",
        "caption_limit": 2200,
        "title_limit": None,
        "hashtag_cap": 30,
        "hashtag_recommended": "3-5",
        "aspect_ratios": ["4:5", "1:1", "1.91:1", "9:16"],
        "image_recommended_px": "1080x1350",
        "video_max_seconds": 180,
        "link_in_caption": False,
        "link_notes": "In-feed captions are not clickable; use the link-in-bio or a Story link sticker.",
        "alt_text": True,
        "source": "https://help.instagram.com/",
    },
    "linkedin": {
        "name": "LinkedIn",
        "caption_limit": 3000,
        "title_limit": None,
        "hashtag_cap": None,
        "hashtag_recommended": "3-5",
        "aspect_ratios": ["1.91:1", "1:1", "4:5", "9:16"],
        "image_recommended_px": "1200x627",
        "video_max_seconds": 900,
        "link_in_caption": True,
        "link_notes": "Links work in the body; some reach models favour a link in the first comment.",
        "alt_text": True,
        "source": "https://www.linkedin.com/help/linkedin/",
    },
    "tiktok": {
        "name": "TikTok",
        "caption_limit": 2200,
        "title_limit": None,
        "hashtag_cap": None,
        "hashtag_recommended": "3-5",
        "aspect_ratios": ["9:16"],
        "image_recommended_px": "1080x1920",
        "video_max_seconds": 600,
        "link_in_caption": False,
        "link_notes": "Only verified/business accounts can add a clickable link in the caption.",
        "alt_text": True,
        "source": "https://support.tiktok.com/",
    },
    "x": {
        "name": "X",
        "caption_limit": 280,
        "title_limit": None,
        "hashtag_cap": None,
        "hashtag_recommended": "0-2",
        "aspect_ratios": ["16:9", "1:1", "4:5", "9:16"],
        "image_recommended_px": "1600x900",
        "video_max_seconds": 140,
        "link_in_caption": True,
        "link_notes": "A link suppresses reach on some models; consider a quote-post or reply link.",
        "alt_text": True,
        "source": "https://help.x.com/",
    },
    "youtube": {
        "name": "YouTube (Shorts)",
        "caption_limit": 5000,
        "title_limit": 100,
        "hashtag_cap": 15,
        "hashtag_recommended": "3",
        "aspect_ratios": ["9:16"],
        "image_recommended_px": "1080x1920",
        "video_max_seconds": 180,
        "link_in_caption": True,
        "link_notes": "First three hashtags show above the title; links live in the description.",
        "alt_text": False,
        "source": "https://support.google.com/youtube/",
    },
    "pinterest": {
        "name": "Pinterest",
        "caption_limit": 500,
        "title_limit": 100,
        "hashtag_cap": None,
        "hashtag_recommended": "2-5",
        "aspect_ratios": ["2:3", "1:1", "9:16"],
        "image_recommended_px": "1000x1500",
        "video_max_seconds": 900,
        "link_in_caption": True,
        "link_notes": "Every Pin carries a destination link; SEO-style keyworded copy performs best.",
        "alt_text": True,
        "source": "https://help.pinterest.com/",
    },
    "facebook": {
        "name": "Facebook",
        "caption_limit": 63206,
        "title_limit": None,
        "hashtag_cap": None,
        "hashtag_recommended": "0-2",
        "aspect_ratios": ["1.91:1", "4:5", "1:1", "9:16"],
        "image_recommended_px": "1200x630",
        "video_max_seconds": 14400,
        "link_in_caption": True,
        "link_notes": "Links work; keep the visible text above the fold short.",
        "alt_text": True,
        "source": "https://www.facebook.com/help/",
    },
    "threads": {
        "name": "Threads",
        "caption_limit": 500,
        "title_limit": None,
        "hashtag_cap": 1,
        "hashtag_recommended": "0-1",
        "aspect_ratios": ["4:5", "1:1", "9:16"],
        "image_recommended_px": "1080x1350",
        "video_max_seconds": 300,
        "link_in_caption": True,
        "link_notes": "One topic tag per post is the documented convention.",
        "alt_text": True,
        "source": "https://help.instagram.com/threads",
    },
}

CHECKED = "2026-10"
# One source-of-truth tag for the registry captured by __init__.DATA_VERSION.
REGISTRY_VERSION = "social-specs-2026-10"


def slugs() -> List[str]:
    return sorted(PLATFORMS)


def get(slug: str) -> Optional[Dict[str, Any]]:
    """Return a spec by slug (case-insensitive). ``None`` if unknown."""
    if not slug:
        return None
    key = slug.strip().lower().replace(" ", "-")
    aliases = {
        "ig": "instagram",
        "yt": "youtube",
        "youtube-shorts": "youtube",
        "shorts": "youtube",
        "twitter": "x",
        "fb": "facebook",
    }
    key = aliases.get(key, key)
    spec = PLATFORMS.get(key)
    return dict(spec, slug=key) if spec else None


def all_specs() -> List[Dict[str, Any]]:
    return [dict(spec, slug=slug) for slug, spec in sorted(PLATFORMS.items())]


def spec_summary(spec: Dict[str, Any]) -> str:
    cap = spec.get("caption_limit")
    hashtags = spec.get("hashtag_recommended")
    ratios = ", ".join(spec.get("aspect_ratios") or []) or "—"
    return (
        f"{spec.get('name')}: caption ≤{cap if cap is not None else '—'} chars, "
        f"hashtags {hashtags or '—'}, ratios {ratios}"
    )
