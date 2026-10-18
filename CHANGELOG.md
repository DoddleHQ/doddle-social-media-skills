# Changelog

All notable changes to `doddle-social-media-skills` are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/); versioning follows
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-18

First release. Doddle Social Media OS — a standalone pack.

### Added

- **Deterministic toolkit** (`scripts/doddle_social/`, stdlib-only, Python 3.9+, CLI `dsocial`):
  - versioned **platform-spec registry** (Instagram, LinkedIn, TikTok, X, YouTube Shorts,
    Pinterest, Facebook, Threads) with sources and a `checked` date;
  - `validate-post` (post readiness), `hashtags`, `calendar` (deterministic schedule
    skeleton), `audit`/`report` (post-export audit), plus `specs`, `version`, `doctor`;
  - a shared JSON evidence envelope (`envelope.py`).
- **30 skills** (`.claude/skills/`), hybrid agent-agnostic `SKILL.md` + DoddleOS
  `blueprint.yaml`: 5 strategy, 4 content, 6 platform playbooks, 2 distribution, 3 community,
  2 influencer, 4 paid social, 3 measurement, 1 governance.
- **5 agents** (`.claude/agents/`): `social-strategist`, `platform-specialist`,
  `content-producer`, `community-manager`, `paid-social-strategist`.
- **Shared references** (`.claude/skills/common/`): `response-contract.md`,
  `data-reliability.md`, `fundamentals.md`, `scoring-methodology.md`, `platform-specs.md`,
  `mcp-integration-guide.md`.
- **Manifests**: `plugin.json`, `marketplace.json`, `package.json`.
- **Validation**: `scripts/lint_pack.py` and the pytest suite (toolkit + pack), plus CI.
- **Docs**: `README.md`, `skills-matrix.md`, `AGENTS.md`.

### Principles

- Deterministic first: the toolkit computes, skills narrate.
- Platform limits come from the registry, never from memory.
- `null` means not measured, never zero.
- No hardcoded market statistics (linter-enforced).
- Planning and analysis only — no scraping, auto-posting or ads-console actions.

[0.1.0]: https://github.com/DoddleHQ/doddle-social-media-skills/releases/tag/v0.1.0
