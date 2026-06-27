"""Build the searchable text blob for a candidate and small text utilities."""
from __future__ import annotations
from typing import Dict, Any


def norm(s) -> str:
    return (s or "").strip().lower()


def candidate_text(c: Dict[str, Any]) -> str:
    """Concatenate the human-readable, semantically meaningful parts of a profile.

    We deliberately weight career-history *descriptions* and the summary, because
    that is where 'plain-language Tier-5' candidates reveal real experience
    (e.g. 'built a recommendation system') without using the buzzwords. The skills
    list is included but it is NOT the dominant signal — that is by design, so the
    semantic component is not fooled by keyword stuffing.
    """
    p = c.get("profile", {}) or {}
    parts = [
        p.get("headline", ""),
        p.get("summary", ""),
        p.get("current_title", ""),
        p.get("current_industry", ""),
    ]
    for role in c.get("career_history", []) or []:
        parts.append(role.get("title", ""))
        parts.append(role.get("industry", ""))
        # Description is the richest signal; include it fully.
        parts.append(role.get("description", ""))
    for ed in c.get("education", []) or []:
        parts.append(ed.get("field_of_study", ""))
        parts.append(ed.get("degree", ""))
    # Skills appended once (not repeated) so they inform but don't dominate.
    skills = [s.get("name", "") for s in c.get("skills", []) or []]
    parts.append(" ".join(skills))
    return "\n".join(x for x in parts if x)


def all_text_lower(c: Dict[str, Any]) -> str:
    """Lowercased blob used for keyword/term presence checks in feature scoring."""
    return candidate_text(c).lower()
