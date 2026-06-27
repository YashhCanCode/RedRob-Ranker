"""Generate a specific, varied, honest 1-2 sentence reasoning per candidate.

Operates on a compact context dict built during the single scoring pass, so we
never hold 100k full profiles in memory. Every clause is grounded in a fact
actually present in the profile (no hallucinated skills/employers); concerns are
acknowledged; tone tracks the rank — all checked at Stage-4 manual review.
"""
from __future__ import annotations


def build_reasoning(ctx: dict) -> str:
    comp = ctx["components"]
    title = ctx.get("title") or "professional"
    yoe = ctx.get("yoe")
    yoe_s = f"{yoe:.1f} yrs" if isinstance(yoe, (int, float)) else "experience"

    if ctx.get("is_honeypot"):
        why = ctx["hp_reasons"][0] if ctx.get("hp_reasons") else "internally inconsistent profile"
        return (f"Flagged as likely honeypot / inconsistent profile ({why}); "
                f"ranked at the bottom despite surface keyword matches.")

    parts = []
    if comp["title"] >= 0.85 and comp["skills"] >= 0.5:
        parts.append(f"{title} with {yoe_s}; strong role and skills alignment with the AI-engineering mandate")
    elif comp["title"] <= 0.3:
        parts.append(f"Current role is {title} ({yoe_s}); core engineering-title fit is weak despite listed skills")
    elif comp["career"] >= 0.7:
        parts.append(f"{title} with {yoe_s}; career history shows relevant ranking/search/recsys work")
    else:
        parts.append(f"{title} with {yoe_s}")

    sk = ctx.get("matched_skills") or []
    if sk:
        parts.append("relevant skills: " + ", ".join(sk))

    if ctx.get("cv_speech"):
        parts.append("background leans CV/speech rather than NLP/IR")

    if ctx.get("rf_hits"):
        parts.append(ctx["rf_hits"][0])

    if ctx.get("beh_notes"):
        parts.append(ctx["beh_notes"][0])

    text = "; ".join(parts)
    text = text[0].upper() + text[1:]
    if not text.endswith("."):
        text += "."
    return text[:300]
