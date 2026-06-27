"""Structured, explainable feature scoring.

Every function returns a value in [0,1] (or a multiplicative penalty near 1.0).
These features encode what the JD *means*, and are what actually defeats the
keyword-stuffer and honeypot traps that pure semantic matching falls for.
"""
from __future__ import annotations
from typing import Dict, Any
from .text import norm, all_text_lower

PROF_W = {"beginner": 0.4, "intermediate": 0.7, "advanced": 1.0, "expert": 1.0}


def _contains_any(text: str, terms) -> bool:
    return any(t in text for t in terms)


def _count_terms(text: str, terms) -> int:
    return sum(1 for t in terms if t in text)


# --------------------------------------------------------------------------- #
# Title fit — the decisive anti-keyword-stuffer signal.
# --------------------------------------------------------------------------- #
def title_fit(c, spec) -> float:
    titles = [norm(c.get("profile", {}).get("current_title", ""))]
    for r in (c.get("career_history", []) or [])[:3]:
        titles.append(norm(r.get("title", "")))
    blob = " | ".join(titles)
    current = titles[0]

    neg = spec["negative_titles"]
    strong = spec["positive_titles"]["strong"]
    adj = spec["positive_titles"]["adjacent"]

    # Current title is a hard negative role (Marketing Manager, HR, Accountant...)
    if _contains_any(current, neg):
        # Even with AI skills listed, this is the trap. Heavily down-weight,
        # but allow a sliver if a past role was a strong engineering title.
        if _contains_any(blob, strong):
            return 0.30
        return 0.05

    if _contains_any(current, strong):
        return 1.0
    if _contains_any(blob, strong):       # strong title in recent history
        return 0.85
    if _contains_any(current, adj):       # software/data/backend engineer
        return 0.65
    if _contains_any(blob, adj):
        return 0.5
    if _contains_any(blob, neg):          # a negative role somewhere in history
        return 0.25
    return 0.35                            # unknown / ambiguous title


# --------------------------------------------------------------------------- #
# Skills fit, weighted by TRUST (endorsements + duration + assessment scores).
# Catches lazy keyword stuffing: a skill listed but never used / never endorsed
# / never assessment-verified counts for little.
# --------------------------------------------------------------------------- #
def _skill_trust(skill, assessment_scores) -> float:
    prof = PROF_W.get(str(skill.get("proficiency")), 0.5)
    dur = float(skill.get("duration_months", 0) or 0)
    end = float(skill.get("endorsements", 0) or 0)
    dur_f = min(dur / 24.0, 1.0)          # saturates at ~2 yrs of usage
    end_f = min(end / 20.0, 1.0)          # saturates at 20 endorsements
    name = norm(skill.get("name", ""))
    assess = assessment_scores.get(skill.get("name", ""))
    assess_f = (assess / 100.0) if isinstance(assess, (int, float)) else None
    # Trust = proficiency tempered by real-usage evidence.
    evidence = 0.5 * dur_f + 0.3 * end_f + (0.2 * assess_f if assess_f is not None else 0.0)
    if assess_f is None:
        evidence = evidence / 0.8         # renormalize when no assessment present
    # A skill claimed 'expert' with zero usage/endorsement -> evidence ~0 -> trust low.
    return prof * (0.35 + 0.65 * evidence)


def skills_fit(c, spec) -> float:
    must = spec["must_have_concepts"]
    nice = spec["nice_to_have_concepts"]
    assessment = (c.get("redrob_signals", {}) or {}).get("skill_assessment_scores", {}) or {}

    skills = c.get("skills", []) or []
    sk_index = {norm(s.get("name", "")): s for s in skills}
    blob = all_text_lower(c)

    def concept_score(concepts, cap):
        total_w = sum(v["weight"] for v in concepts.values()) or 1.0
        got = 0.0
        for v in concepts.values():
            w = v["weight"]
            terms = [t.lower() for t in v["terms"]]
            # Best trust among matching listed skills, else partial credit if the
            # concept appears in career/summary text (real usage in prose).
            best = 0.0
            for sname, s in sk_index.items():
                if any(t in sname for t in terms):
                    best = max(best, _skill_trust(s, assessment))
            if best == 0.0 and _contains_any(blob, terms):
                best = 0.45            # mentioned in experience prose, not as a skill
            got += w * min(best, 1.0)
        return min(got / total_w, 1.0)

    must_s = concept_score(must, 1.0)
    nice_s = concept_score(nice, 1.0)
    return min(0.8 * must_s + 0.2 * nice_s, 1.0)


# --------------------------------------------------------------------------- #
# Experience-years alignment with the 5-9 (ideal 6-8) band.
# --------------------------------------------------------------------------- #
def experience_fit(c, spec) -> float:
    e = spec["role"]["experience"]
    y = float(c.get("profile", {}).get("years_of_experience", 0) or 0)
    if e["ideal_min"] <= y <= e["ideal_max"]:
        return 1.0
    if e["min_years"] <= y <= e["max_years"]:
        return 0.85
    tol = e["soft_tolerance_years"]
    if e["min_years"] - tol <= y <= e["max_years"] + tol:
        return 0.55
    return 0.25


# --------------------------------------------------------------------------- #
# Domain fit — reward NLP/IR/search/recsys; caution CV/speech/robotics w/o NLP.
# --------------------------------------------------------------------------- #
def domain_fit(c, spec) -> float:
    blob = all_text_lower(c)
    pos = _count_terms(blob, [t.lower() for t in spec["positive_domains"]])
    caution = _count_terms(blob, [t.lower() for t in spec["caution_domains"]])
    has_nlp = _contains_any(blob, ["nlp", "natural language", "information retrieval",
                                   "search", "ranking", "recommendation", "llm"])
    score = min(pos / 3.0, 1.0)
    if caution > 0 and not has_nlp:
        score = min(score, 0.35)        # CV/speech/robotics only -> JD negative
    return max(score, 0.1)


# --------------------------------------------------------------------------- #
# Career evidence — product-company work and shipped ranking/search/recsys.
# --------------------------------------------------------------------------- #
def career_evidence(c, spec) -> float:
    hist = c.get("career_history", []) or []
    blob = all_text_lower(c)
    services = [s.lower() for s in spec["services_companies"]]
    product = [p.lower() for p in spec["product_companies"]]

    companies = [norm(r.get("company", "")) for r in hist]
    n = max(len(companies), 1)
    services_n = sum(1 for cc in companies if _contains_any(cc, services))
    product_n = sum(1 for cc in companies if _contains_any(cc, product))

    score = 0.5
    # Built the kind of system the role owns.
    if _contains_any(blob, ["ranking", "search", "recommend", "retrieval",
                            "matching system", "relevance"]):
        score += 0.25
    if _contains_any(blob, ["embedding", "vector", "faiss", "semantic search",
                            "learning to rank"]):
        score += 0.1
    if product_n > 0:
        score += 0.15
    # Entirely services/consulting career -> negative (handled more in red_flags).
    if services_n == n and product_n == 0:
        score -= 0.25
    return float(min(max(score, 0.0), 1.0))


# --------------------------------------------------------------------------- #
# Location fit — Indian metros preferred; relocation willingness compensates.
# --------------------------------------------------------------------------- #
def location_fit(c, spec) -> float:
    p = c.get("profile", {})
    loc = norm(p.get("location", "")) + " " + norm(p.get("country", ""))
    sig = c.get("redrob_signals", {}) or {}
    pref = [x.lower() for x in spec["preferred_locations"]]
    in_pref = _contains_any(loc, pref)
    if in_pref:
        return 1.0
    if sig.get("willing_to_relocate"):
        return 0.8
    if "india" in loc:
        return 0.7
    return 0.4    # outside India, not relocating -> visa/logistics friction


# --------------------------------------------------------------------------- #
# Red-flag penalty (multiplicative, <=1.0) for explicit JD disqualifiers.
# --------------------------------------------------------------------------- #
def red_flag_penalty(c, spec):
    blob = all_text_lower(c)
    rf = spec["red_flags"]
    penalty = 1.0
    hits = []
    hist = c.get("career_history", []) or []
    companies = [norm(r.get("company", "")) for r in hist]
    services = [s.lower() for s in spec["services_companies"]]
    product = [p.lower() for p in spec["product_companies"]]

    # Consulting-only career (no product-company stint anywhere).
    if companies and all(_contains_any(cc, services) for cc in companies) \
            and not any(_contains_any(cc, product) for cc in companies):
        penalty *= (1 - rf["consulting_only"]["penalty"])
        hits.append("services/consulting-only career")

    # Research-only without production language.
    if _contains_any(blob, [t.lower() for t in rf["research_only"]["terms"]]) \
            and not _contains_any(blob, ["production", "deployed", "users", "shipped",
                                         "real-time", "scale"]):
        penalty *= (1 - rf["research_only"]["penalty"])
        hits.append("research-only, no production signal")

    # CV/speech/robotics only, no NLP/IR.
    if _contains_any(blob, [t.lower() for t in spec["caution_domains"]]) \
            and not _contains_any(blob, ["nlp", "natural language", "retrieval",
                                         "ranking", "search", "recommendation"]):
        penalty *= (1 - rf["cv_speech_robotics_only"]["penalty"])
        hits.append("CV/speech/robotics without NLP/IR")

    # Title-chaser: short average tenure.
    durs = [float(r.get("duration_months", 0) or 0) for r in hist if r.get("duration_months")]
    if len(durs) >= 3:
        avg = sum(durs) / len(durs)
        if avg < rf["title_chaser"]["max_avg_tenure_months"]:
            penalty *= (1 - rf["title_chaser"]["penalty"])
            hits.append(f"short avg tenure ({avg:.0f}mo) — possible title-chaser")

    # Stale IC: current title is a manager/architect with no IC/coding signal.
    cur = norm(c.get("profile", {}).get("current_title", ""))
    if _contains_any(cur, [t.lower() for t in rf["stale_ic"]["terms"]]) \
            and not _contains_any(blob, ["built", "implemented", "wrote", "developed",
                                         "coded", "python", "shipped"]):
        penalty *= (1 - rf["stale_ic"]["penalty"])
        hits.append("management/architect title, weak hands-on signal")

    return penalty, hits
