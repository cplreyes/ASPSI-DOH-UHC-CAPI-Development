#!/usr/bin/env python3
r"""
Aug-17 migration: F1 rename proposer (Task 2.1).

F1 is renumbered AND restructured -- unlike F3/F4 (numbering stable, patch-
scale) or F2 (a hand-authored continuous re-key, Task 3.1), F1's old build
items and the new paper's items don't share qnums at all, so there is no
qnum-based join to lean on. This tool instead joins OLD (build, kind="item")
rows to NEW (paper, kind="item") rows by normalized STEM CONTENT -- exact
match first, difflib fuzzy match second -- and proposes the mechanical
item-name rekey (`Q<old-qnum>_<suffix>` -> `Q<new-qnum>_<suffix>`) that
Task 2.2's dictionary rebuild and Task 2.5's translation re-join both
consume.

Join mechanics
---------------
Per the plan brief (Task 2.1, Step 1/2): join on
`rowspec.normalize_text(stem, strip_qnum=True)`. Layered UNDER that exact
key, this module reuses the paper/build stem folds `aug17_diff.py` already
established (pandoc dash fold, escape-apostrophe fold, trailing SELECT/
bracket-directive strip, build "NN. " prefix strip) -- not reimplemented,
imported -- so real-world artifacts (a stem ending in "SELECT ALL THAT
APPLY.", a paper double-hyphen) don't manufacture false REWORDED/unresolved
noise. For this task's own invented-content unit tests (NDU: no verbatim
questionnaire text in committed code/tests/fixtures), the two normalizations
are equivalent -- none of the fixture stems carry those artifacts.

- **Exact pass**: paper items are grouped by normalized key; each build item
  claims one UNCLAIMED paper item sharing its exact key, in paper document
  order. `change_class` is "unchanged" if the qnum ALSO matches (nothing
  moved at all), else "renumbered-only" (same content, different position).
- **Fuzzy pass** (over what's left after the exact pass): each remaining old
  item is scored against every remaining new item with
  `difflib.SequenceMatcher.ratio()`, using a FIXED snapshot of the post-
  exact-pass remainder computed once up front (not recomputed as later
  items claim candidates -- deterministic and order-independent). Commits
  are then applied in DESCENDING best-ratio order (the most confident
  guesses claim contested candidates first). A match commits only when the
  best score is >= 0.85 AND strictly greater than the second-best score for
  that same old item -- a genuine tie, or a best-candidate some earlier
  (higher-ratio) commit already claimed, both leave the item unresolved
  rather than guess. `change_class="reworded"`.
- Anything left on either side after both passes is NOT in the map --
  it's hand-resolution territory (Step 3): every leftover old item needs a
  citation-backed unchanged/removed call against `F1-inventory.md`; every
  leftover new item is `change_class="new"` by definition (no old partner
  to carry).

Only `kind="item"` rows are ever candidates for this join. Build-side
kind="consent"/"disposition" rows and off-form system items (no printed
paper "item" analog at all -- FIELD CONTROL tracking fields, the consent
flow, the Secondary-Data dcf record stubs which don't even produce a Row,
being empty records) are OUT OF SCOPE for automated matching by design; Step
3 hand-adds them to the map explicitly (see task-2.1-report.md).

Item-name rekey convention
---------------------------
Decision 6 (migration design doc): dictionary/item names follow
`Q<qnum>_<STEM>` (decimal subs `Q10_1_<STEM>`, letter subs `Q71A_<STEM>`).
`qnum_to_name_prefix`/`rekey_item_name` below are the literal INVERSE of
`build_tables.derive_qnum` (which recovers a qnum FROM an item name) --
same regex shape, opposite direction. A matched pair's proposed new_name is
just the old item_name's own suffix (whatever follows its own qnum-derived
prefix) re-attached to the NEW qnum's prefix; the survey-content SUFFIX
itself is never touched by this tool, only the numeric part.

Map format contract (this brief, consumed by Tasks 2.2/2.4/2.5 and
`crosswalk.py`): `old_name,new_name,change_class` plus tolerated extra
columns (`load_rename_map` in `rejoin_translations.py` already reads an
optional `stem_changed` column; this tool emits it, set for every REWORDED
row, so Task 2.5's translation re-join can drop those to English fallback
immediately without a second pass). `change_class` values match
crosswalk.py's Task-0.5 enum: unchanged / renumbered-only / reworded /
removed / new.

Usage:
    python propose_renames.py F1 [--data-dir DIR]
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from aug17_diff import _norm_build_stem, _norm_paper_stem
from rowspec import read_csv

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (SCRIPT_DIR / ".." / "instruments-aug17-extract").resolve()

FUZZY_THRESHOLD = 0.85

MAP_FIELDS = [
    "old_name", "new_name", "change_class",
    "old_qnum", "new_qnum", "stem_changed", "ratio", "note",
]


# --- item-name rekey convention (inverse of build_tables.derive_qnum) -----

_QNUM_PARSE_RE = re.compile(r"^(\d+)([a-z]?)(?:\.(\d+))?$", re.IGNORECASE)


def qnum_to_name_prefix(qnum: str) -> str:
    """Inverse of build_tables.derive_qnum's `Q<N><LETTER>[_<SUB>]` naming
    convention (Decision 6): '5' -> 'Q5_'; '10.1' -> 'Q10_1_'; '71a' ->
    'Q71A_'. Returns '' if qnum doesn't parse (e.g. empty/off-form)."""
    m = _QNUM_PARSE_RE.match((qnum or "").strip())
    if not m:
        return ""
    num, letter, sub = m.groups()
    prefix = "Q" + num + (letter.upper() if letter else "")
    if sub:
        prefix += "_" + sub
    return prefix + "_"


def rekey_item_name(old_name: str, old_qnum: str, new_qnum: str) -> str:
    """Old item_name's Q<old-qnum>_ prefix replaced by Q<new-qnum>_, the
    suffix preserved verbatim -- the mechanical rename Task 2.2's rebuild
    applies. Falls back to the bare new prefix (no suffix) if old_name
    doesn't actually start with the prefix its OWN qnum implies -- this
    shouldn't happen (build_tables.derive_qnum derives old_qnum FROM
    old_name in the first place), but a mismatch never silently
    mis-renames; it degrades to the least-wrong guess instead."""
    old_prefix = qnum_to_name_prefix(old_qnum)
    new_prefix = qnum_to_name_prefix(new_qnum)
    if old_prefix and old_name.upper().startswith(old_prefix):
        return new_prefix + old_name[len(old_prefix):]
    return new_prefix.rstrip("_")


# --- stem join keys (see module docstring "Join mechanics") ----------------


def _paper_key(stem: str) -> str:
    return _norm_paper_stem(stem)


def _build_key(stem: str) -> str:
    return _norm_build_stem(stem)


# --- matching ----------------------------------------------------------------


@dataclass
class Match:
    old: object  # Row
    new: object  # Row
    change_class: str
    ratio: float


def match_by_stem(build_items: list, paper_items: list):
    """Join OLD (build) items to NEW (paper) items by normalized stem --
    see module docstring "Join mechanics" for the exact/fuzzy algorithm.
    Returns (matches: list[Match], unresolved_old: list[Row],
    unresolved_new: list[Row])."""
    paper_by_key: dict = {}
    for p in paper_items:
        paper_by_key.setdefault(_paper_key(p.stem), []).append(p)

    matches: list = []
    claimed_paper: set = set()
    unresolved_old: list = []
    for b in build_items:
        bucket = paper_by_key.get(_build_key(b.stem), [])
        p = next((cand for cand in bucket if id(cand) not in claimed_paper), None)
        if p is None:
            unresolved_old.append(b)
            continue
        claimed_paper.add(id(p))
        cls = "unchanged" if p.qnum == b.qnum else "renumbered-only"
        matches.append(Match(old=b, new=p, change_class=cls, ratio=1.0))

    # Fuzzy pass: fixed snapshot of what's left after the exact pass.
    remaining_paper = [p for p in paper_items if id(p) not in claimed_paper]
    scored = []  # (b, best_ratio, second_ratio, best_p)
    for b in unresolved_old:
        bkey = _build_key(b.stem)
        ranked = sorted(
            ((difflib.SequenceMatcher(None, bkey, _paper_key(p.stem)).ratio(), p)
             for p in remaining_paper),
            key=lambda t: -t[0],
        )
        best_ratio = ranked[0][0] if ranked else 0.0
        second_ratio = ranked[1][0] if len(ranked) > 1 else -1.0
        best_p = ranked[0][1] if ranked else None
        scored.append((b, best_ratio, second_ratio, best_p))

    still_unresolved_old: list = []
    for b, best_ratio, second_ratio, best_p in sorted(scored, key=lambda t: -t[1]):
        if (
            best_p is not None
            and best_ratio >= FUZZY_THRESHOLD
            and best_ratio > second_ratio
            and id(best_p) not in claimed_paper
        ):
            claimed_paper.add(id(best_p))
            matches.append(Match(old=b, new=best_p, change_class="reworded", ratio=best_ratio))
        else:
            still_unresolved_old.append(b)

    # Preserve original build-item order for the two "still unresolved" /
    # "matches" outputs -- the sort above is a processing order, not the
    # result order.
    still_unresolved_set = {id(b) for b in still_unresolved_old}
    unresolved_old_ordered = [b for b in unresolved_old if id(b) in still_unresolved_set]
    old_order = {id(b): i for i, b in enumerate(build_items)}
    matches_ordered = sorted(matches, key=lambda m: old_order.get(id(m.old), 0))

    unresolved_new = [p for p in paper_items if id(p) not in claimed_paper]
    return matches_ordered, unresolved_old_ordered, unresolved_new


# --- map rows / I-O ----------------------------------------------------------


def build_map_rows(matches: list) -> list:
    """Match objects -> MAP_FIELDS dicts ready for `write_map`."""
    rows = []
    for m in matches:
        new_name = rekey_item_name(m.old.item_name, m.old.qnum, m.new.qnum)
        rows.append({
            "old_name": m.old.item_name,
            "new_name": new_name,
            "change_class": m.change_class,
            "old_qnum": m.old.qnum,
            "new_qnum": m.new.qnum,
            "stem_changed": "1" if m.change_class == "reworded" else "",
            "ratio": f"{m.ratio:.4f}" if m.change_class == "reworded" else "",
            "note": "",
        })
    return rows


def write_map(rows: list, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MAP_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in MAP_FIELDS})


def write_unresolved_report(inst: str, reworded_matches: list, unresolved_old: list,
                             unresolved_new: list, out_path) -> None:
    """Human review report (Step 2): the leftovers after the automated
    exact/fuzzy join, PLUS every fuzzy (reworded) match -- a machine guess,
    however confident, still gets a line here so a human can sanity-check
    it before it's trusted (Step 3 hand-resolution consumes this)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {inst} -- rename proposal: unresolved + needs-review",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"## Reworded matches flagged for review ({len(reworded_matches)})",
        "",
        "Fuzzy stem match (ratio >= 0.85, unique best) -- confirm the pairing "
        "and the proposed new_name before trusting it.",
        "",
    ]
    if reworded_matches:
        for m in reworded_matches:
            lines.append(
                f"- `{m.old.item_name}` (old Q{m.old.qnum}) -> Q{m.new.qnum} "
                f"(ratio {m.ratio:.4f}): old=\"{m.old.stem[:100]}\" | new=\"{m.new.stem[:100]}\""
            )
    else:
        lines.append("(none)")
    lines += ["", f"## Old items with no confident match ({len(unresolved_old)})", "",
              "Hand-resolve against F1-inventory.md: moved/merged/removed, or "
              "retained-unchanged (system/consent/off-form -- see task-2.1-report.md).", ""]
    if unresolved_old:
        for b in unresolved_old:
            lines.append(f"- `{b.item_name}` (Q{b.qnum or '(none)'}, kind={b.kind}): \"{b.stem[:120]}\"")
    else:
        lines.append("(none)")
    lines += ["", f"## New paper items with no old partner ({len(unresolved_new)})", "",
              "change_class=new by definition -- no old item to carry.", ""]
    if unresolved_new:
        for p in unresolved_new:
            lines.append(f"- Q{p.qnum or '(none)'}: \"{p.stem[:120]}\"")
    else:
        lines.append("(none)")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- CLI -----------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Aug-17 migration: propose an old->new item rename map by stem match")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()

    data_dir = (args.data_dir or DEFAULT_DATA_DIR).resolve()
    paper_rows = read_csv(data_dir / "normalized" / f"{args.instrument}-paper.csv")
    build_rows = read_csv(data_dir / "normalized" / f"{args.instrument}-build.csv")

    paper_items = [r for r in paper_rows if r.kind == "item"]
    build_items = [r for r in build_rows if r.kind == "item"]

    matches, unresolved_old, unresolved_new = match_by_stem(build_items, paper_items)
    reworded = [m for m in matches if m.change_class == "reworded"]

    map_rows = build_map_rows(matches)
    map_path = data_dir / "maps" / f"{args.instrument}-renames.csv"
    write_map(map_rows, map_path)

    report_path = data_dir / "reports" / f"{args.instrument}-rename-unresolved.md"
    write_unresolved_report(args.instrument, reworded, unresolved_old, unresolved_new, report_path)

    counts = {}
    for r in map_rows:
        counts[r["change_class"]] = counts.get(r["change_class"], 0) + 1
    print(
        f"{args.instrument}: {len(map_rows)} matched ({counts}), "
        f"{len(unresolved_old)} old unresolved, {len(unresolved_new)} new unresolved"
    )
    print(f"  map -> {map_path}")
    print(f"  report -> {report_path}")


if __name__ == "__main__":
    main()
