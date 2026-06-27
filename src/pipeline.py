"""End-to-end ranking pipeline (offline, CPU, no network).

Single streaming pass to build text + structured scores, then a TF-IDF semantic
pass, then combine, rank, and emit the top-100 submission CSV that satisfies the
official validator (exactly 100 rows; unique ranks; score non-increasing;
ties broken by candidate_id ascending).

`run()` does it all in one process (the real reproduce command). `phase1`/`phase2`
expose the same logic in two steps via a checkpoint — used only to fit inside the
short per-call limit of the dev sandbox; they are NOT needed for reproduction.
"""
from __future__ import annotations
import csv
import pickle
import time
import numpy as np

from .config import load_config, load_role_spec
from .data import iter_candidates
from .text import candidate_text
from . import features as F
from .behavioral import behavioral_modifier
from .honeypot import honeypot_report
from .semantic import TfidfSemantic, DensePrecomputed, minmax
from .reasoning import build_reasoning
from .reasoning_ctx import make_ctx


def _norm_weights(cfg):
    weights = dict(cfg["scoring"]["weights"])
    wsum = sum(weights.values()) or 1.0
    return {k: v / wsum for k, v in weights.items()}


def _components_no_semantic(c, spec):
    return {
        "semantic": 0.0,
        "title": F.title_fit(c, spec),
        "skills": F.skills_fit(c, spec),
        "experience": F.experience_fit(c, spec),
        "domain": F.domain_fit(c, spec),
        "career": F.career_evidence(c, spec),
        "location": F.location_fit(c, spec),
    }


def structured_pass(candidates_path, spec, weights, log=print):
    t0 = time.time()
    texts, records = [], []
    n = 0
    for c in iter_candidates(candidates_path):
        cid = c.get("candidate_id")
        if not cid:
            continue
        comp = _components_no_semantic(c, spec)
        rf_mult, rf_hits = F.red_flag_penalty(c, spec)
        beh_mult, beh_notes = behavioral_modifier(c, spec)
        is_hp, hp_score, hp_reasons = honeypot_report(c)
        result = {"components": comp, "rf_mult": rf_mult, "rf_hits": rf_hits,
                  "beh_mult": beh_mult, "beh_notes": beh_notes,
                  "is_honeypot": is_hp, "hp_reasons": hp_reasons}
        merit_wo = sum(weights[k] * comp[k] for k in weights if k != "semantic")
        records.append({"id": cid, "comp": comp, "merit_wo": merit_wo,
                        "rf_mult": rf_mult, "beh_mult": beh_mult, "is_hp": is_hp,
                        "ctx": make_ctx(c, spec, result)})
        texts.append(candidate_text(c))
        n += 1
        if n % 20000 == 0:
            log(f"  scored {n} candidates ({time.time()-t0:.1f}s)")
    log(f"Structured scoring done: {n} candidates ({time.time()-t0:.1f}s)")
    return texts, records


def semantic_and_rank(texts, records, spec, weights, out_path, dense_dir=None,
                      top_n=100, log=print):
    t0 = time.time()
    n = len(records)
    if dense_dir:
        import os
        sem = DensePrecomputed(os.path.join(dense_dir, "candidate_emb.npy"),
                               os.path.join(dense_dir, "query_emb.npy"))
        sims = sem.query_similarity()
    else:
        sem = TfidfSemantic()
        sem.fit_transform(texts)
        sims = sem.query_similarity(spec["semantic_query"])
    sims = minmax(sims)
    log(f"Semantic similarity done ({time.time()-t0:.1f}s)")

    wsem = weights["semantic"]
    for i, r in enumerate(records):
        merit = r["merit_wo"] + wsem * sims[i]
        final = merit * r["rf_mult"] * r["beh_mult"]
        if r["is_hp"]:
            final *= 0.05
        r["final"] = final
        r["comp"]["semantic"] = float(sims[i])

    order = sorted(range(n), key=lambda i: (-records[i]["final"], records[i]["id"]))
    top = order[:top_n]
    rows = [{"candidate_id": records[i]["id"], "rank": rank,
             "score": records[i]["final"],
             "reasoning": build_reasoning(records[i]["ctx"])}
            for rank, i in enumerate(top, start=1)]
    rows = _normalize_scores(rows)
    _write_csv(rows, out_path)
    n_hp = sum(1 for i in top if records[i]["is_hp"])
    log(f"Wrote {len(rows)} rows -> {out_path}. Honeypots in top {top_n}: "
        f"{n_hp} ({n_hp/top_n:.1%}) ({time.time()-t0:.1f}s)")
    return rows


def run(candidates_path, out_path, config_path=None, role_spec_path=None,
        dense_dir=None, top_n=100, log=print):
    cfg = load_config(config_path)
    spec = load_role_spec(role_spec_path)
    weights = _norm_weights(cfg)
    texts, records = structured_pass(candidates_path, spec, weights, log=log)
    return semantic_and_rank(texts, records, spec, weights, out_path,
                             dense_dir=dense_dir, top_n=top_n, log=log)


# --- checkpoint helpers (dev-sandbox only) ---
def phase1(candidates_path, ckpt_path, config_path=None, role_spec_path=None, log=print):
    cfg = load_config(config_path)
    spec = load_role_spec(role_spec_path)
    weights = _norm_weights(cfg)
    texts, records = structured_pass(candidates_path, spec, weights, log=log)
    with open(ckpt_path, "wb") as f:
        pickle.dump({"texts": texts, "records": records}, f, protocol=pickle.HIGHEST_PROTOCOL)
    log(f"Checkpoint saved: {ckpt_path}")


def phase2(ckpt_path, out_path, config_path=None, role_spec_path=None,
           dense_dir=None, top_n=100, log=print):
    cfg = load_config(config_path)
    spec = load_role_spec(role_spec_path)
    weights = _norm_weights(cfg)
    with open(ckpt_path, "rb") as f:
        d = pickle.load(f)
    return semantic_and_rank(d["texts"], d["records"], spec, weights, out_path,
                             dense_dir=dense_dir, top_n=top_n, log=log)


def _normalize_scores(rows):
    raw = [r["score"] for r in rows]
    lo, hi = min(raw), max(raw)
    rng = (hi - lo) or 1.0
    for r in rows:
        r["score"] = round(0.30 + 0.69 * (r["score"] - lo) / rng, 4)
    for k in range(1, len(rows)):
        if rows[k]["score"] > rows[k - 1]["score"]:
            rows[k]["score"] = rows[k - 1]["score"]
    return rows


def _write_csv(rows, out_path):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in rows:
            w.writerow([r["candidate_id"], r["rank"], f"{r['score']:.4f}", r["reasoning"]])
