"""Pack structure: every skill complete, lint clean, blueprints valid."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, ".claude", "skills")
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import lint_pack  # noqa: E402

EXPECTED = {
    # strategy & planning
    "social-strategy", "social-audit", "social-content-calendar", "social-brand-voice",
    "social-competitor",
    # content & creative
    "social-captions", "social-hooks", "social-hashtags", "social-creative-brief",
    # platform playbooks
    "social-instagram", "social-linkedin", "social-tiktok", "social-x",
    "social-youtube-shorts", "social-pinterest",
    # distribution
    "social-repurposing", "social-ugc",
    # community
    "social-community-management", "social-listening", "social-crisis",
    # influencer & partnerships
    "social-influencer", "social-employee-advocacy",
    # paid social
    "social-paid-strategy", "social-meta-ads", "social-tiktok-ads", "social-linkedin-ads",
    # measurement
    "social-analytics", "social-reporting", "social-seo",
    # governance
    "social-compliance",
}
AGENTS = {"social-strategist", "platform-specialist", "content-producer",
          "community-manager", "paid-social-strategist"}
REQUIRED_SECTIONS = ("## Response Contract", "## Related Skills", "## Inputs", "## Outputs")


def _skill_names():
    return {
        d for d in os.listdir(SKILLS)
        if os.path.isdir(os.path.join(SKILLS, d)) and d != "common"
    }


def test_all_expected_skills_present():
    assert _skill_names() == EXPECTED
    assert len(EXPECTED) == 30


def test_lint_pack_is_clean():
    lint = lint_pack.Lint()
    lint_pack.run(lint)
    assert lint.errors == [], lint.errors


def test_frontmatter_matches_dirname():
    for name in sorted(_skill_names()):
        text = open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8").read()
        fm = lint_pack.parse_frontmatter(text)
        assert fm.get("name") == name, name
        assert fm.get("id") == f"doddle.social.{name}", name
        assert fm.get("blueprint") == "./blueprint.yaml", name
        assert len(fm.get("description", "")) >= 30, name


def test_required_sections_present():
    for name in sorted(_skill_names()):
        text = open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8").read()
        for section in REQUIRED_SECTIONS:
            assert section in text, f"{name}: missing {section}"


def test_blueprints_have_kind_and_id():
    for name in sorted(_skill_names()):
        bp = open(os.path.join(SKILLS, name, "blueprint.yaml"), encoding="utf-8").read()
        assert "kind: skill" in bp, name
        assert f"id: doddle.social.{name}" in bp, name


def test_agents_present():
    agents_dir = os.path.join(ROOT, ".claude", "agents")
    agents = {f[:-3] for f in os.listdir(agents_dir) if f.endswith(".md")}
    assert agents == AGENTS


def test_toolkit_cli_runs():
    proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "dsocial"), "version", "--json"],
                          capture_output=True, text=True)
    assert proc.returncode == 0
    assert "toolkit_version" in proc.stdout
