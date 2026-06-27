"""Streaming loader for the candidate pool (.jsonl or .jsonl.gz)."""
from __future__ import annotations
import gzip
import json
from pathlib import Path
from typing import Iterator, Dict, Any


def _open(path):
    path = str(path)
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")


def iter_candidates(path) -> Iterator[Dict[str, Any]]:
    """Yield one candidate dict per non-empty line. Memory-light."""
    with _open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def count_lines(path) -> int:
    n = 0
    with _open(path) as f:
        for line in f:
            if line.strip():
                n += 1
    return n
