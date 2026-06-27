# Redrob Candidate Ranker

A hybrid, **fully-offline** candidate ranking system for the Redrob *Intelligent
Candidate Discovery & Ranking Challenge*. It ranks the top 100 candidates from a
100,000-profile pool for the **Senior AI Engineer — Founding Team** job
description — the way a great recruiter would, by reasoning about role fit,
career evidence, and availability rather than counting keywords.

```bash
# the single reproduce command (no network, CPU only, ~1 min for 100k candidates)
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

> Compliant with the spec's compute constraints: **CPU-only, no GPU, no network /
> hosted-LLM calls during ranking, < 5 min, < 16 GB RAM.** The default semantic
> backend is TF-IDF, so the command needs nothing but the candidates file.

---

## Why this design

The JD is deliberately written to defeat keyword matching, and the dataset is
seeded with traps:

- **Keyword-stuffers** — e.g. a *Marketing Manager* whose skills list is full of
  "RAG", "Pinecone", "Embeddings". Perfect on keywords, wrong person.
- **Plain-language strong candidates** ("Tier-5") — built a recommendation system
  at a product company but never wrote "RAG" or "vector DB".
- **~80 honeypots** — subtly impossible profiles (8 years at a 3-year-old company;
  "expert" in 10 skills with 0 months of usage). Forced to relevance tier 0;
  ranking them in your top 100 is penalized and >10% disqualifies you.
- **Behavioral twins** — identical-on-paper candidates separated only by whether
  they are actually responsive and available.

A pure embedding / keyword system falls for all four. We instead combine an
explainable structured model with a semantic signal, then modulate by explicit
JD disqualifiers and real-world availability.

## Architecture

```
candidates.jsonl
      │  (single streaming pass)
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Structured feature scoring  (src/features.py)               │
│   title_fit · skills_fit(trust) · experience_fit · domain    │
│   career_evidence · location_fit                             │
└─────────────────────────────────────────────────────────────┘
      │                         │                         │
      ▼                         ▼                         ▼
 Semantic similarity      Red-flag penalty         Behavioral modifier
 TF-IDF JD↔profile        (disqualifiers,          (response rate, recency,
 (src/semantic.py)         multiplicative)          open-to-work, notice)
      │                         │                         │
      └──────────────┬──────────┴────────────┬───────────┘
                     ▼                        ▼
              Honeypot detector  ──►  Final score = merit · rf · behavioral
              (forces tier-0           (honeypots collapsed to the bottom)
               profiles down)                    │
                                                 ▼
                                    Top-100 ranked submission.csv
                                    + specific, honest reasoning per row
```

### The components (weights in `config.yaml`)

| Component | What it captures | Why it matters |
|---|---|---|
| **title_fit** | Is the current/recent title actually an ML/AI/SW engineer? | The decisive signal against keyword-stuffers — a *Marketing Manager* with AI skills scores ~0.05. |
| **skills_fit** | Must/nice-have skills weighted by **trust** = proficiency × (endorsements + duration + assessment score) | "Expert" in a skill with 0 endorsements / 0 months counts for almost nothing — kills lazy stuffing. |
| **career_evidence** | Product-company work + shipped ranking/search/recsys (from role *descriptions*) | Surfaces plain-language Tier-5s; down-weights services-only careers. |
| **semantic** | TF-IDF cosine between profile text and a JD-derived query | Catches strong candidates who don't use the buzzwords; non-dominant by design. |
| **experience_fit** | Alignment with the 5–9y band (ideal 6–8) | JD is explicit about the band, softly. |
| **domain_fit** | NLP/IR vs CV/speech/robotics | JD names CV/speech/robotics-without-NLP as a negative. |
| **location_fit** | Indian metros / willing-to-relocate | Noida/Pune-preferred, no visa sponsorship. |

### Modifiers (applied on top of the weighted merit)

- **Red-flag penalties** (multiplicative): services/consulting-only career,
  research-only without production, title-chasing (short avg tenure),
  CV/speech/robotics-only, stale "architect/manager" with no hands-on signal,
  LangChain-only.
- **Behavioral availability**: a perfect-on-paper candidate with a 5% recruiter
  response rate who hasn't logged in for 6 months is *not actually hireable* —
  down-weighted accordingly; responsive + recently-active + open-to-work get a
  small lift.
- **Honeypot collapse**: profiles failing internal-consistency checks (duration
  vs date span, total tenure vs declared experience, expert proficiency with 0
  months usage, skill used longer than the whole career) are forced beneath all
  genuine candidates. We do **not** special-case IDs — detection generalizes.

## "JD understanding" — `role_spec.yaml`

The structured reading of the job description (must/nice concepts, positive vs
negative titles, services vs product companies, disqualifiers, the ideal
"read-between-the-lines" profile) lives in `role_spec.yaml`. It is produced once,
offline (optionally LLM-assisted), then committed — so ranking is reproducible
and needs no network. Re-deriving it is the only place an LLM could be involved,
and even that is optional.

## Repository layout

```
rank.py                 # single reproduce command (offline)
precompute.py           # OPTIONAL dense-embedding pre-compute (allowed to use network)
config.yaml             # component weights
role_spec.yaml          # structured JD understanding
app.py                  # Streamlit sandbox demo (small-sample reproducibility)
validate_submission.py  # official format validator (bundled for convenience)
submission.csv          # the produced top-100 ranking
submission_metadata.yaml
src/
  data.py               # streaming jsonl/jsonl.gz loader
  text.py               # profile-text builder
  features.py           # structured feature scoring
  behavioral.py         # availability modifier
  honeypot.py           # impossible-profile detection
  semantic.py           # TF-IDF (default) + optional dense backend
  scoring.py            # component combiner
  reasoning.py          # specific, varied, honest reasoning generator
  pipeline.py           # orchestration
sample/                 # 50-candidate sample for the sandbox / tests
tests/                  # pytest-style unit + smoke tests
```

## Setup & run

```bash
pip install -r requirements.txt

# full submission (point at the unzipped or gzipped pool)
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
# or: --candidates ./candidates.jsonl.gz   (handled transparently)

# validate before uploading
python validate_submission.py submission.csv

# tests
python tests/test_honeypot.py && python tests/test_pipeline.py
```

### Optional: dense-embedding backend

For higher semantic quality you can precompute sentence-transformer embeddings
**offline** (this step may use the network and exceed 5 min), then rank against
them with zero network at ranking time:

```bash
pip install sentence-transformers
python precompute.py --candidates ./candidates.jsonl --out-dir ./artifacts
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --dense-dir ./artifacts
```

TF-IDF is the committed default because it needs no model download, is
deterministic, and is comfortably within budget — a deliberate latency/quality
tradeoff, which is exactly the kind of thinking the JD asks for.

## Results on the released pool (100,000 candidates)

- Runtime: **~1 min**, CPU-only, no network. Peak memory well under 16 GB.
- Top-100 composition: AI/ML/Applied-ML/NLP/Search/Recommendation engineers;
  **92/100 inside the 5–9y band** (mean 6.6y); **zero keyword-stuffer roles**
  (no Marketing Manager / HR / Accountant) and **zero honeypots** in the top 100.
- 43 honeypots detected and collapsed across the pool; none reached the shortlist.

## Reasoning column

Each row carries a 1–2 sentence justification built only from facts present in
that profile (named real skills, current title, years, signal values), it names
concerns honestly (short tenure, long notice, low response rate, CV/speech lean),
and its tone tracks the rank — designed for the Stage-4 manual review checks
(specificity, JD connection, honest concerns, no hallucination, variation).
