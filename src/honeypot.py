"""Honeypot / impossible-profile detection.

The dataset seeds ~80 honeypots with 'subtly impossible' profiles. Ranking any
of them in the top 100 hurts; >10% in the top 100 disqualifies the submission.
The spec's examples:
  * "8 years of experience at a company founded 3 years ago"
  * "'expert' proficiency in 10 skills with 0 years used"

We do NOT special-case known IDs. We detect impossibility from internal
consistency, which generalizes and is defensible at interview:

  1. Date arithmetic: a role's stated duration_months must roughly match the gap
     between start_date and end_date (or today, if current). A large mismatch is
     physically impossible.
  2. Tenure vs experience: total career tenure can't vastly exceed
     years_of_experience (you can't have worked more years than you've existed
     professionally).
  3. Proficiency vs usage: many 'advanced'/'expert' skills with duration_months
     == 0 means claimed mastery with zero usage — impossible.
  4. Skill usage vs career length: a skill used far longer than the whole career.

Each check contributes evidence; a candidate crossing the threshold is flagged
and pushed below all genuine candidates in the final ranking.
"""
from __future__ import annotations
from datetime import date
from typing import Dict, Any, Tuple

TODAY = date(2026, 6, 27)


def _parse_date(s):
    if not s:
        return None
    try:
        y, m, d = str(s)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _months_between(a: date, b: date) -> float:
    return (b.year - a.year) * 12 + (b.month - a.month) + (b.day - a.day) / 30.0


def honeypot_report(c: Dict[str, Any]) -> Tuple[bool, float, list]:
    """Return (is_honeypot, suspicion_score 0..1, reasons)."""
    reasons = []
    score = 0.0

    yoe = float(c.get("profile", {}).get("years_of_experience", 0) or 0)
    yoe_months = yoe * 12.0

    # --- 1. Date vs duration consistency per role ---
    total_tenure = 0.0
    for role in c.get("career_history", []) or []:
        dm = float(role.get("duration_months", 0) or 0)
        total_tenure += dm
        sd = _parse_date(role.get("start_date"))
        ed = _parse_date(role.get("end_date")) or (TODAY if role.get("is_current") else None)
        if sd and ed:
            actual = _months_between(sd, ed)
            if actual < -1:
                score += 0.6
                reasons.append("role end_date precedes start_date")
            elif dm - actual > 24:  # claims 2+ yrs more than the dates allow
                score += 0.5
                reasons.append(
                    f"role duration {int(dm)}mo exceeds its date span "
                    f"({int(max(actual,0))}mo) — impossible tenure")
        if sd and sd > TODAY:
            score += 0.5
            reasons.append("role start_date in the future")

    # --- 2. Total tenure vs declared experience ---
    if yoe_months > 0 and total_tenure - yoe_months > 36:
        score += 0.4
        reasons.append(
            f"career tenure {int(total_tenure)}mo far exceeds stated "
            f"{yoe:.0f}y experience")

    # --- 3. Proficiency vs usage on skills ---
    skills = c.get("skills", []) or []
    high = [s for s in skills if str(s.get("proficiency")) in ("advanced", "expert")]
    high_zero = [s for s in high if int(s.get("duration_months", 0) or 0) == 0]
    if len(high_zero) >= 3:
        score += 0.5
        reasons.append(
            f"{len(high_zero)} advanced/expert skills with 0 months of usage")
    elif len(high_zero) >= 1 and len(high) >= 5 and len(high_zero) / max(len(high), 1) > 0.5:
        score += 0.3
        reasons.append("majority of advanced skills have 0 months usage")

    # --- 4. Skill used longer than the entire career ---
    for s in skills:
        sdm = int(s.get("duration_months", 0) or 0)
        if yoe_months > 0 and sdm - yoe_months > 24:
            score += 0.3
            reasons.append("a skill is 'used' longer than the whole career")
            break

    score = min(score, 1.0)
    is_honeypot = score >= 0.5
    return is_honeypot, score, reasons
