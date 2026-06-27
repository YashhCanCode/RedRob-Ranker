#!/usr/bin/env python3
"""Redrob candidate ranker — single reproduce command.

    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs fully offline on CPU (no GPU, no network/API calls), well within the
5-minute / 16 GB budget for the 100k pool. Optionally consumes precomputed dense
embeddings via --dense-dir (see precompute.py); by default uses a self-contained
TF-IDF semantic backend so the command needs nothing but the candidates file.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.pipeline import run


def main():
    ap = argparse.ArgumentParser(description="Rank candidates for the Redrob JD.")
    ap.add_argument("--candidates", required=True,
                    help="Path to candidates.jsonl or candidates.jsonl.gz")
    ap.add_argument("--out", default="submission.csv", help="Output CSV path")
    ap.add_argument("--config", default=None, help="Path to config.yaml")
    ap.add_argument("--role-spec", default=None, help="Path to role_spec.yaml")
    ap.add_argument("--dense-dir", default=None,
                    help="Optional dir with precomputed candidate_emb.npy + query_emb.npy")
    ap.add_argument("--top-n", type=int, default=100)
    args = ap.parse_args()

    run(args.candidates, args.out, config_path=args.config,
        role_spec_path=args.role_spec, dense_dir=args.dense_dir, top_n=args.top_n)


if __name__ == "__main__":
    main()
