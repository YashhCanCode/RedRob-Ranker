"""Tests for the honeypot / impossible-profile detector."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.honeypot import honeypot_report


def _base():
    return {
        "candidate_id": "CAND_0000001",
        "profile": {"years_of_experience": 6},
        "career_history": [{
            "company": "Acme", "title": "ML Engineer",
            "start_date": "2020-01-01", "end_date": "2026-01-01",
            "duration_months": 72, "is_current": False,
            "industry": "Software", "company_size": "201-500", "description": "x",
        }],
        "skills": [{"name": "Python", "proficiency": "advanced",
                    "endorsements": 10, "duration_months": 40}],
    }


def test_clean_profile_not_honeypot():
    is_hp, score, reasons = honeypot_report(_base())
    assert not is_hp, reasons


def test_duration_exceeds_date_span():
    c = _base()
    # 96 months claimed but only ~36 months between dates -> impossible
    c["career_history"][0]["start_date"] = "2023-01-01"
    c["career_history"][0]["end_date"] = "2026-01-01"
    c["career_history"][0]["duration_months"] = 96
    is_hp, score, reasons = honeypot_report(c)
    assert is_hp, (score, reasons)


def test_expert_skills_zero_usage():
    c = _base()
    c["skills"] = [{"name": f"Skill{i}", "proficiency": "expert",
                    "endorsements": 0, "duration_months": 0} for i in range(5)]
    is_hp, score, reasons = honeypot_report(c)
    assert is_hp, (score, reasons)


if __name__ == "__main__":
    for fn in [test_clean_profile_not_honeypot, test_duration_exceeds_date_span,
               test_expert_skills_zero_usage]:
        fn(); print("PASS", fn.__name__)
