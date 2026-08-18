#!/usr/bin/env python3
"""
Aug-17 migration: the shared normalized-row schema.

`Row` is the single CSV contract every countercheck tool in this chain reads
or writes (paper_tables.py, build_tables.py, aug17_diff.py, crosswalk.py).
Keeping the dataclass + normalization logic in one module means every tool
compares apples to apples: same columns, same whitespace/quote folding, same
qnum-prefix stripping rule.

See `.superpowers/sdd/2026-08-18-aug17-capi-migration/task-0.2-brief.md` for
the schema definition this implements verbatim.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- text normalization -----------------------------------------------

_WS_RE = re.compile(r"\s+")
_SMART_SINGLE_RE = re.compile(r"[‘’]")
_SMART_DOUBLE_RE = re.compile(r"[“”]")
_QNUM_PREFIX_RE = re.compile(r"^\d+[a-z]?(\.\d+)?\.\s+")


def normalize_text(s: str, strip_qnum: bool = False) -> str:
    """Collapse whitespace, fold smart quotes/apostrophes to ASCII, and
    (when strip_qnum=True) strip a leading 'NN. ' paper-number prefix.

    This is the ONLY tolerated text transform between paper and build sides
    per the migration contract — everything else must byte-match or carry a
    register row (see brief).
    """
    if not s:
        return ""
    text = _SMART_SINGLE_RE.sub("'", s)
    text = _SMART_DOUBLE_RE.sub('"', text)
    text = _WS_RE.sub(" ", text).strip()
    if strip_qnum:
        text = _QNUM_PREFIX_RE.sub("", text)
    return text


# --- Row -----------------------------------------------------------------

ROW_FIELDS = [
    "inst",
    "qnum",
    "item_name",
    "section",
    "kind",
    "stem",
    "options",
    "qtype",
    "cardinality",
    "skip",
    "validation",
    "messages",
    "instructions",
]

KINDS = {"item", "section_header", "note", "consent", "instruction", "disposition"}


@dataclass
class Row:
    inst: str
    qnum: str = ""
    item_name: str = ""
    section: str = ""
    kind: str = "item"
    stem: str = ""
    options: list = field(default_factory=list)
    qtype: str = ""
    cardinality: str = ""
    skip: str = ""
    validation: str = ""
    messages: str = ""
    # R19 (rev-1.4 close-out finding): build-only. build_tables.py's
    # load_qsf_text severs any enumerator-instruction / section-intro
    # paragraph baked into the SAME questionText HTML block as the item's
    # own stem (see build_tables.py module docstring) -- the severed text
    # lands here instead of being silently concatenated into `stem`.
    # Paper-side rows never set this (paper's own instruction/note text
    # already gets its own separate kind="instruction"/"note" Row).
    instructions: str = ""

    def to_csv_row(self) -> dict:
        """Flatten to a dict of strings suitable for csv.DictWriter."""
        out: dict[str, Any] = {}
        for f in ROW_FIELDS:
            v = getattr(self, f)
            if f == "options":
                out[f] = json.dumps(v, ensure_ascii=False)
            else:
                out[f] = v
        return out

    @classmethod
    def from_csv_row(cls, d: dict) -> "Row":
        """Inverse of to_csv_row(). `options` is parsed back from JSON."""
        kwargs = {f: d.get(f, "") for f in ROW_FIELDS if f != "options"}
        raw_opts = d.get("options") or "[]"
        kwargs["options"] = json.loads(raw_opts) if raw_opts.strip() else []
        return cls(**kwargs)


def write_csv(rows: list, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r.to_csv_row())


def read_csv(path: Path) -> list:
    path = Path(path)
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [Row.from_csv_row(d) for d in reader]
