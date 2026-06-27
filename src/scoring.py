"""Combine all signals into a final fit score for one candidate."""
from __future__ import annotations
from . import features as F
from .behavioral import behavioral_modifier
from .honeypot import honeypot_report


def score_candidate(c, spec, semantic_sim, weights):
    """Return a dict with the final score and all component scores / notes.

    semantic_sim: precomputed, min-max normalized semantic similarity for this
                  candidate (0..1).
    """
    comp = {
        "semantic": float(semantic_sim),
        "title": F.title_fit(c, spec),
        "skills": F.skills_fit(c, spec),
        "experience": F.experience_fit(c, spec),
        "domain": F.domain_fit(c, spec),
        "career": F.career_evidence(c, spec),
        "location": F.location_fit(c, spec),
    }

    # Weighted merit (weights normalized upstream).
    merit = sum(weights[k] * comp[k] for k in weights)

    # Red-flag multiplicative penalties (explicit JD disqualifiers).
    rf_mult, rf_hits = F.red_flag_penalty(c, spec)

    # Behavioral availability modifier.
    beh_mult, beh_notes = behavioral_modifier(c, spec)

    # Honeypot: force to the bottom band so it cannot reach the top 100.
    is_hp, hp_score, hp_reasons = honeypot_report(c)

    final = merit * rf_mult * beh_mult
    if is_hp:
        final = final * 0.05          # collapse honeypots beneath all real fits

    return {
        "candidate_id": c.get("candidate_id"),
        "final": float(final),
        "merit": float(merit),
        "components": comp,
        "rf_mult": rf_mult,
        "rf_hits": rf_hits,
        "beh_mult": beh_mult,
        "beh_notes": beh_notes,
        "is_honeypot": is_hp,
        "hp_reasons": hp_reasons,
    }
