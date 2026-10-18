# Platform Specs — how to read the registry

The single source of truth for every platform fact in this pack is
`scripts/doddle_social/platforms.py`. Skills must **never** hardcode a caption limit, hashtag
cap, aspect ratio or duration. Query the registry instead.

## Reading it

```bash
dsocial specs                 # every platform, JSON
dsocial specs --platform x    # one platform
```

Each entry carries: `caption_limit`, `title_limit`, `hashtag_cap`, `hashtag_recommended`,
`aspect_ratios`, `image_recommended_px`, `video_max_seconds`, `link_in_caption`, `link_notes`,
`alt_text`, `source`, and the registry `checked` date.

## Registered platforms

`instagram`, `linkedin`, `tiktok`, `x`, `youtube` (Shorts), `pinterest`, `facebook`, `threads`.
Aliases accepted: `ig`, `yt`, `shorts`, `twitter`, `fb`.

## Hard constraint vs guidance

| Field | Type | Rule |
|-------|------|------|
| `caption_limit`, `title_limit` | hard | exceeding it blocks publication — report as a blocker |
| `hashtag_cap` | hard (when set) | exceeding it is a violation on the platforms that enforce it |
| `hashtag_recommended` | soft | a starting range, not a rule — never present as one |
| `aspect_ratios`, `*_px`, `video_max_seconds` | hard | production constraints for the creative |
| `link_in_caption` / `link_notes` | convention | explain the behaviour; do not assert reach effects |
| `alt_text` | capability | if the platform supports it and media lacks it, that is a gap |

A `null` is **not measured / not documented** for that platform — not zero. Say so.

## Versioning

The registry is stamped by `data_version` (e.g. `social-specs-2026-10`) and a `checked` date.
When a platform changes a limit, edit `platforms.py`, bump `DATA_VERSION` in
`scripts/doddle_social/__init__.py`, and note it in `CHANGELOG.md`. Every report then states
the new `data_version`, and old scores are correctly marked non-comparable.
