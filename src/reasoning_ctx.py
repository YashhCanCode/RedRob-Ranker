"""Build the compact reasoning context for one candidate during the scoring pass."""
from __future__ import annotations
from .text import norm, all_text_lower


def matched_must_skills(c, spec, limit=3):
    must = spec["must_have_concepts"]
    terms = []
    for v in must.values():
        terms += [t.lower() for t in v["terms"]]
    seen, res = set(), []
    for s in c.get("skills", []) or []:
        nm = s.get("name", "")
        if any(t in norm(nm) for t in terms) and nm.lower() not in seen:
            seen.add(nm.lower()); res.append(nm)
        if len(res) >= limit:
            break
    return res


def _cv_speech_only(c, spec):
    blob = all_text_lower(c)
    has_caution = any(t.lower() in blob for t in spec["caution_domains"])
    has_nlp = any(t in blob for t in ["nlp", "natural language", "retrieval",
                                      "ranking", "search", "recommendation", "llm"])
    return has_caution and not has_nlp


def make_ctx(c, spec, result):
    p = c.get("profile", {}) or {}
    return {
        "cv_speech": _cv_speech_only(c, spec),
        "title": p.get("current_title", "professional"),
        "yoe": p.get("years_of_experience", None),
        "matched_skills": matched_must_skills(c, spec),
        "components": result["components"],
        "rf_hits": result["rf_hits"],
        "beh_notes": result["beh_notes"],
        "is_honeypot": result["is_honeypot"],
        "hp_reasons": result["hp_reasons"],
    }
