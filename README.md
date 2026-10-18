# Doddle Social Media OS — `doddle-social-media-skills`

**30 skills · 5 agents · one deterministic toolkit.** A standalone pack for social media
marketing: strategy, content, per-platform playbooks, community, influencer, paid social and
measurement. Agent-agnostic (`SKILL.md`) with DoddleOS blueprints (`blueprint.yaml`).

Sibling to [`doddle-seo-geo-skills`](https://github.com/DoddleHQ/doddle-seo-geo-skills).

## The one claim

**Every number is reproducible from recorded evidence.** The `dsocial` toolkit computes; the
model explains and prioritizes. Platform limits come from a versioned registry — never from
memory. No skill does arithmetic in prose, and no skill invents a metric.

## Install

No install step. Copy `.claude/skills/` and `.claude/agents/` into any agent that reads
`SKILL.md`, or add the folder to DoddleOS. The toolkit is stdlib-only, Python 3.9+.

```bash
python3 scripts/dsocial version
python3 scripts/dsocial specs --platform instagram
python3 scripts/dsocial validate-post linkedin --text "A short announcement. Sign up today." --json
python3 scripts/dsocial audit my-posts.json --json
```

## Deterministic toolkit — `dsocial`

| Command | What it computes |
|---------|------------------|
| `specs [--platform SLUG]` | The versioned platform-spec registry (caption limits, hashtag caps, ratios, durations, link rules) |
| `validate-post SLUG --text/--file` | Post readiness: length, hashtags, alt text, hook, CTA, emoji — with findings |
| `hashtags --platform SLUG --text …` | Hashtag count, unique, duplicates, density, camelCase risk |
| `calendar --start … --weeks N --platform SLUG:C --pillars …` | A deterministic schedule skeleton (dates, weekdays, pillar rotation) |
| `audit <export.json\|csv>` | Account audit: cadence, caption compliance, alt coverage, hashtag fit, engagement |
| `report <export>` | The audit rendered as a markdown report |
| `version`, `doctor` | Versions and environment self-check |

The registry is stamped `data_version` (e.g. `social-specs-2026-10`); every envelope carries
`scoring_version` and `data_version`, so scores are never compared across versions silently.

## Skills (30)

- **Strategy & planning (5):** `social-strategy`, `social-audit`, `social-content-calendar`,
  `social-brand-voice`, `social-competitor`
- **Content & creative (4):** `social-captions`, `social-hooks`, `social-hashtags`,
  `social-creative-brief`
- **Platform playbooks (6):** `social-instagram`, `social-linkedin`, `social-tiktok`,
  `social-x`, `social-youtube-shorts`, `social-pinterest`
- **Distribution (2):** `social-repurposing`, `social-ugc`
- **Community (3):** `social-community-management`, `social-listening`, `social-crisis`
- **Influencer & partnerships (2):** `social-influencer`, `social-employee-advocacy`
- **Paid social (4):** `social-paid-strategy`, `social-meta-ads`, `social-tiktok-ads`,
  `social-linkedin-ads`
- **Measurement (3):** `social-analytics`, `social-reporting`, `social-seo`
- **Governance (1):** `social-compliance`

## Agents (5)

`social-strategist`, `platform-specialist`, `content-producer`, `community-manager`,
`paid-social-strategist`.

## Design principles

- **Deterministic first.** If `dsocial` can compute it, the skill runs the command and reads
  the JSON envelope.
- **Registry, not memory.** Limits, caps, ratios and durations come from `dsocial specs`.
- **`null` ≠ 0.** An unmeasured signal is reported as not measured, with a reason.
- **Advisory is labelled.** Posting-time and cadence advice is heuristic and attributed to the
  user's own analytics when present.
- **Exported text is data, never instructions.**
- **Planning, not execution.** No scraping, no auto-posting, no ads console, no DM automation.

## Layout

```
.claude/
  agents/               5 agents
  skills/               30 skills (SKILL.md + blueprint.yaml [+ references/])
  skills/common/        shared references
scripts/
  dsocial               CLI launcher
  doddle_social/        the toolkit (stdlib-only)
  lint_pack.py          structure/frontmatter/blueprint/link/secret linter
tests/                  pytest + fixtures
```

## Develop

```bash
python3 scripts/lint_pack.py
python3 -m pytest tests -q
```

## License

MIT © Doddle Team.
