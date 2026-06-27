"""Load config.yaml and role_spec.yaml."""
from __future__ import annotations
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_config(path=None):
    return load_yaml(Path(path) if path else ROOT / "config.yaml")


def load_role_spec(path=None):
    return load_yaml(Path(path) if path else ROOT / "role_spec.yaml")
