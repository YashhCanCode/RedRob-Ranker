#!/usr/bin/env python3
"""OPTIONAL pre-computation step (allowed to use network + exceed 5 min).

Generates dense sentence-transformer embeddings for the candidate pool and the
role query, saved to disk so the ranking step (rank.py --dense-dir ...) stays
fully offline. This is the only place a model download / heavier compute happens.

    python precompute.py --candidates ./candidates.jsonl --out-dir ./artifacts \
        --model sentence-transformers/all-MiniLM-L6-v2

Skip this entirely to use the default TF-IDF backend.
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.data import iter_candidates
from src.text import candidate_text
from src.config import load_role_spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out-dir", default="artifacts")
    ap.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--batch-size", type=int, default=256)
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    os.makedirs(args.out_dir, exist_ok=True)
    model = SentenceTransformer(args.model)

    ids, texts = [], []
    for c in iter_candidates(args.candidates):
        ids.append(c.get("candidate_id"))
        texts.append(candidate_text(c))

    emb = model.encode(texts, batch_size=args.batch_size, show_progress_bar=True,
                       normalize_embeddings=True)
    np.save(os.path.join(args.out_dir, "candidate_emb.npy"), emb.astype(np.float32))
    with open(os.path.join(args.out_dir, "candidate_ids.txt"), "w") as f:
        f.write("\n".join(ids))

    spec = load_role_spec()
    q = model.encode([spec["semantic_query"]], normalize_embeddings=True)[0]
    np.save(os.path.join(args.out_dir, "query_emb.npy"), q.astype(np.float32))
    print(f"Saved embeddings for {len(ids)} candidates to {args.out_dir}")


if __name__ == "__main__":
    main()
