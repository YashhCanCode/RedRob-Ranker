"""Behavioral / availability modifier from redrob_signals.

A perfect-on-paper candidate who hasn't logged in for months and ignores
recruiters is, for hiring purposes, not actually available. This produces a
multiplier (roughly 0.6..1.1) applied to the merit score, plus human-readable
notes used in the reasoning column.
"""
from __future__ import annotations
from datetime import date

TODAY = date(2026, 6, 27)


def _parse_date(s):
    try:
        y, m, d = str(s)[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def behavioral_modifier(c, spec):
    s = c.get("redrob_signals", {}) or {}
    b = spec["behavioral"]
    mult = 1.0
    notes = []

    # Recruiter responsiveness — the strongest availability signal.
    rr = s.get("recruiter_response_rate")
    if isinstance(rr, (int, float)):
        if rr < 0.1:
            mult *= 0.70; notes.append(f"very low recruiter response rate ({rr:.0%})")
        elif rr < 0.3:
            mult *= 0.85; notes.append(f"low recruiter response rate ({rr:.0%})")
        elif rr >= b["good_response_rate"]:
            mult *= 1.06; notes.append(f"responsive to recruiters ({rr:.0%})")

    # Recency of activity.
    la = _parse_date(s.get("last_active_date"))
    if la:
        days = (TODAY - la).days
        if days > 2 * b["stale_days"]:
            mult *= 0.75; notes.append(f"inactive ~{days}d")
        elif days > b["stale_days"]:
            mult *= 0.88; notes.append(f"not active in {days}d")
        elif days <= 14:
            mult *= 1.04; notes.append("recently active")

    # Open to work.
    if s.get("open_to_work_flag") is True:
        mult *= 1.05; notes.append("open to work")
    elif s.get("open_to_work_flag") is False:
        mult *= 0.92

    # Interview reliability.
    ic = s.get("interview_completion_rate")
    if isinstance(ic, (int, float)) and ic < 0.4:
        mult *= 0.92; notes.append(f"low interview completion ({ic:.0%})")

    # Notice period (soft).
    np_ = s.get("notice_period_days")
    if isinstance(np_, (int, float)):
        if np_ <= b["notice_period_soft_cap_days"]:
            mult *= 1.03
        elif np_ >= 90:
            mult *= 0.95; notes.append(f"long notice ({int(np_)}d)")

    # Verification / completeness (minor trust).
    if s.get("verified_email") and s.get("linkedin_connected"):
        mult *= 1.02

    # Clamp.
    mult = float(min(max(mult, 0.55), 1.15))
    return mult, notes
