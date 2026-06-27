"""Smoke test: the pipeline runs on the bundled sample and emits a valid CSV."""
import sys, os, csv, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import run


def test_runs_and_emits_valid_topn():
    sample = os.path.join(ROOT, "sample", "sample_candidates.jsonl")
    out = os.path.join(tempfile.gettempdir(), "smoke_sub.csv")
    rows = run(sample, out, top_n=10, log=lambda *a, **k: None)
    assert len(rows) == 10
    with open(out) as f:
        r = list(csv.DictReader(f))
    assert [c.strip() for c in r[0].keys()] == ["candidate_id", "rank", "score", "reasoning"]
    ranks = [int(x["rank"]) for x in r]
    assert ranks == list(range(1, 11))
    scores = [float(x["score"]) for x in r]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)), "non-increasing"
    assert all(x["reasoning"].strip() for x in r), "reasoning non-empty"
    assert len(set(x["reasoning"] for x in r)) > 1, "reasoning varied"


if __name__ == "__main__":
    test_runs_and_emits_valid_topn(); print("PASS test_pipeline")
