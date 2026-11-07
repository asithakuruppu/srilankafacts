"""Minimal catalogue check until F02 adds full schemas.

Today it confirms the catalogue folders exist and that every YAML file parses. F02 adds schema,
referential-integrity, rights, spatial and footprint rules.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CATALOG_DIRS = ("sources", "datasets", "indicators", "geographies", "spaces")


def validate_catalog(root: Path) -> list[str]:
    problems: list[str] = []
    if not root.is_dir():
        return [f"catalogue folder not found: {root}"]
    for name in CATALOG_DIRS:
        if not (root / name).is_dir():
            problems.append(f"missing folder: {root / name}")
    for path in sorted(root.rglob("*.y*ml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            problems.append(f"{path}: invalid YAML ({exc})")
    return problems
