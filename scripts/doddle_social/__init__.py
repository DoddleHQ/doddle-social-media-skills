"""Doddle Social Media deterministic toolkit.

Every number a skill reports is computed here from recorded evidence. The toolkit is
stdlib-only so it runs anywhere Python 3.9+ runs, with no install step and no network
requirement for scoring a saved post or an account export.

Public entry points:
    - :mod:`doddle_social.platforms` — the versioned platform-spec registry
    - :mod:`doddle_social.posts`     — validate one post against a platform spec
    - :mod:`doddle_social.audit`     — audit an account/post export
    - :mod:`doddle_social.cli`       — the ``dsocial`` command line
"""

from __future__ import annotations

TOOLKIT_VERSION = "0.1.0"
SCORING_VERSION = "social-1"
DATA_VERSION = "social-specs-2026-10"

__all__ = ["TOOLKIT_VERSION", "SCORING_VERSION", "DATA_VERSION"]
