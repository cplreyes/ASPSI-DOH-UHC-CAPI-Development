#!/usr/bin/env python3
r"""
Aug-17 migration: paper-side normalized tables.

Parses the pandoc grid-table extracts (`instruments-aug17-extract/F{n}-
extract.md`) into `Row` objects (see rowspec.py) and writes one CSV per
instrument to `instruments-aug17-extract/normalized/F{n}-paper.csv`. Root
tool of the countercheck chain — every later diff/crosswalk tool consumes
this output; nothing upstream of it.

Parsing approach — line-scan, not a real table parser
-------------------------------------------------------
The extracts are pandoc grid tables, but column widths vary per table and
cell text wraps across physical lines mid-word. Rather than track column
character offsets (fragile — widths differ row-group to row-group), this
parser strips border/pipe syntax and classifies each *logical cell* (a
`|`-delimited, non-empty stripped segment) independently:

  - a cell containing "☐" is an OPTION cell — one or more checkbox options,
    possibly carrying an inline `<proceed to Q..>` skip fragment;
  - a lone cell matching `^\d+[a-z]?(\.\d+)?\.\s*\**` is an ITEM START —
    opens a new item accumulator (paper prints item numbers two ways:
    "38. **stem**" and "**38.1. stem**"; the regex accepts either);
  - a lone cell matching `^([A-Z])\.\s*\*\*` or `^#\s*\*\*` is a SECTION
    HEADER (the first section in each instrument uses the "#" form with no
    letter — see each F{n}-inventory.md §1; letters are assigned by a
    rolling counter reset whenever an explicit letter is seen);
  - a lone cell that is a short bold ALL-CAPS run (letters only, no digits)
    is treated as an unlettered heading (PART I/II banners, consent
    headers) — tagged kind=consent if it mentions "consent", else
    kind=section_header;
  - any other lone cell is either stem continuation (if the currently open
    item has no options yet — i.e. we're still inside its stem) or a
    standalone note/instruction row (once the open item already has
    options, later stray text is very unlikely to be more of its stem —
    e.g. inter-item lead-in scripts, roster sub-item labels);
  - a multi-cell row with NO checkbox (FIELD CONTROL grids, coding-list
    blocks, roster amount/date sub-rows) resists this scheme entirely and
    is silently skipped, counted in `unparsed_count` — the Step-5 spot
    check + item-count assertions are the safety net for this bucket, per
    brief guidance.

Paper defects (broken cross-refs, duplicate/renumbered item numbers, e.g.
the two "1."/"2." Word-renumbering artifacts in F3 Sections G/H) are parsed
AS PRINTED — this tool does not try to detect or fix them, the divergence
register (Task 0.4) does.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from rowspec import Row, normalize_text, write_csv

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (SCRIPT_DIR / ".." / "instruments-aug17-extract").resolve()

CHECKBOX = "☐"

DIVIDER_RE = re.compile(r"^[+\-:=\s]+$")

ITEM_START_RE = re.compile(r"^\*{0,2}\s*(\d+[a-z]?(?:\.\d+)?)\.\s*\*{0,2}\s*(.*)$")
SECTION_LETTER_RE = re.compile(r"^([A-Z])\.\s*\*\*\s*(.*)$")
SECTION_HASH_RE = re.compile(r"^#\s*\*\*\s*(.*)$")

SKIP_RE = re.compile(r"<\s*(proceed to|skip to|end of survey)([^>]*)>", re.IGNORECASE)
NOTE_RE = re.compile(r"note to enumerator|enumerator note|note for capi version", re.IGNORECASE)
MULTI_SELECT_RE = re.compile(r"select all that apply", re.IGNORECASE)
SINGLE_SELECT_RE = re.compile(r"select one answer only", re.IGNORECASE)

DIRECTIVE_BANNER_RE = re.compile(
    r"^(READ OPTIONS|DO NOT READ|SELECT (ALL|ONE)|CODING FOR QUESTION|CODES\b|"
    r"BASED ON|ONLY FOR|ONLY ANSWER|ASK IF|SKIP (TO|IF)|FOR (BOTH|INPATIENT|OUTPATIENT)|"
    r"PLEASE LIST DOWN)",
    re.IGNORECASE,
)
MARK_SPAN_RE = re.compile(r"\[([^\]]*)\]\{\.mark\}")
SUPERSCRIPT_RE = re.compile(r"\^([A-Za-z0-9]+)\^")
BLOCKQUOTE_PREFIX_RE = re.compile(r"^>\s*")


def _prep_cell(cell: str) -> str:
    """Unwrap a `[...]{.mark}` span and strip a leading `> ` blockquote
    marker before classification. Both are common on Year-2 `{.mark}`
    additions (e.g. F1 Q10.1/Q11.1), where pandoc emits `> **[10.1. ...]
    {.mark}**` or `> [**11.1. ...** *...*]{.mark}` — the digit prefix ends
    up hidden behind either wrapper, or both at once, so ITEM_START_RE /
    SECTION_*_RE never see it without this pre-pass. Idempotent against
    plain cells (no-op if neither wrapper is present)."""
    cell = MARK_SPAN_RE.sub(r"\1", cell)
    cell = BLOCKQUOTE_PREFIX_RE.sub("", cell)
    return cell


def _strip_md(text: str) -> str:
    """Remove pandoc markdown decoration, leaving plain text.

    Order matters: unwrap [..]{.mark} spans before stripping ** / * (the
    span's brackets survive intact, but bold/italic runs may cross the span
    boundary), then drop bold/italic markers, then un-escape pandoc's
    backslash-escaped punctuation (\\<, \\>, \\[, \\], \\-, \\.) and fold
    superscripts (^a^ -> a).
    """
    text = MARK_SPAN_RE.sub(r"\1", text)
    text = text.replace("**", "").replace("*", "")
    text = SUPERSCRIPT_RE.sub(r"\1", text)
    for esc, plain in (("\\<", "<"), ("\\>", ">"), ("\\[", "["), ("\\]", "]"), ("\\-", "-"), ("\\.", ".")):
        text = text.replace(esc, plain)
    return text


def _is_divider(line: str) -> bool:
    """True for a pandoc grid-table border line. Handles the plain case
    (`+---+---+`) and the mid-row case where an uneven column split makes a
    divider start with a leading `|` (e.g. one cell's box continues past
    where its neighbors already closed) — stripping `|` before the
    divider-charset check catches both; without it, the `|`-led form falls
    through as ordinary content and its `+---+` border junk gets glued
    onto whatever item is open."""
    stripped = line.strip()
    if not stripped:
        return False
    without_pipes = stripped.replace("|", "")
    return bool(without_pipes) and bool(DIVIDER_RE.match(without_pipes))


def _split_cells(line: str) -> list:
    """Split a `|`-delimited table row into non-empty, stripped cells."""
    parts = line.strip().split("|")
    return [p.strip() for p in parts if p.strip()]


def _looks_like_glossary_entry(text: str) -> bool:
    """True for definitional-legend lines that happen to share the item-
    start print shape "N. **Term**: elaboration..." (or the colon just
    inside the bold run, "N. **Term:** elaboration"). Observed in F2 after
    Q2 ("employment type"): a 7-entry glossary numbered 1-7, restarting the
    paper's own numbering, immediately followed by the real Q3. Every real
    survey item in these instruments is phrased as a question, an
    imperative, or a bare field label — never "term: definition" on its
    first line — so "has an early colon but no early question mark" is a
    precise enough discriminator without a global qnum-monotonicity rule
    (which would also wrongly swallow F3's genuine "1."/"2." renumbering
    artifacts elsewhere in the document)."""
    head = text[:70]
    return ":" in head and "?" not in head


def _is_allcaps_heading(text: str) -> bool:
    """True for a genuine unlettered document heading (PART I/II banners,
    CERTIFICATE OF CONSENT, INFORMED CONSENT FORM). Requires a letter-led,
    multi-word all-caps run — excludes bracket/paren/digit-led fragments
    ("[ITEM]?", "(BASED ON...", "14) HMO") and single-word acronym
    fragments ("PWD", "CODES") that share the all-caps look but are legend/
    piped-fill noise bleeding out of a roster cell, not a heading."""
    text = text.strip()
    if not text or not text[0].isalpha():
        return False
    if " " not in text:
        return False
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def _extract_options(cells: list) -> tuple:
    """Pull (label, skip_fragment_or_None) pairs out of a checkbox row's
    cells. A cell may hold more than one "☐ label" run (rare, but the
    fixture's grid layout puts two per physical line)."""
    opts = []
    for raw_cell in cells:
        if CHECKBOX not in raw_cell:
            continue
        cell = _strip_md(raw_cell)
        for chunk in cell.split(CHECKBOX)[1:]:
            chunk = chunk.strip()
            if not chunk:
                continue
            m = SKIP_RE.search(chunk)
            frag = None
            if m:
                frag = chunk[m.start():m.end()]
                chunk = chunk[: m.start()] + chunk[m.end():]
            label = normalize_text(chunk)
            if not label:
                continue
            opts.append((label, frag))
    return opts


def _new_item(inst: str, section: str, qnum: str, stem_start: str) -> dict:
    return {
        "inst": inst,
        "section": section,
        "qnum": qnum,
        "stem_parts": [stem_start] if stem_start.strip() else [],
        "options": [],
        "skip_fragments": [],
    }


def _finalize_item(cur: dict) -> Row:
    stem_raw = " ".join(_strip_md(p) for p in cur["stem_parts"] if p.strip())
    stem = normalize_text(stem_raw)
    text_for_type = stem_raw
    options = []
    for idx, (label, _frag) in enumerate(cur["options"], start=1):
        options.append({"code": str(idx), "label": label})
        text_for_type += " " + label
    if MULTI_SELECT_RE.search(text_for_type):
        qtype = "multi"
        cardinality = "multi"
    elif options:
        qtype = "single"
        cardinality = "single"
    elif re.search(r"pesos|amount|\bage\b|years|days|minutes|number of", stem, re.IGNORECASE):
        qtype = "number"
        cardinality = "single"
    elif re.search(r"\btime\s*\(hh:mm\)|date of|month and year", stem, re.IGNORECASE):
        qtype = "date"
        cardinality = "single"
    else:
        qtype = "text"
        cardinality = "single"
    skip = "; ".join(
        f"IF {label} GOTO {normalize_text(_strip_md(frag))}"
        for label, frag in cur["options"]
        if frag
    )
    # question-level skip fragments captured off the stem itself (rare, but
    # some banners live inside a stem/instruction line rather than tied to
    # a specific option)
    for extra in cur.get("stem_skip_fragments", []):
        piece = f"IF <stem> GOTO {normalize_text(_strip_md(extra))}"
        skip = f"{skip}; {piece}" if skip else piece
    return Row(
        inst=cur["inst"],
        qnum=cur["qnum"],
        section=cur["section"],
        kind="item",
        stem=stem,
        options=options,
        qtype=qtype,
        cardinality=cardinality,
        skip=skip,
    )


def _merge_split_grid_items(rows: list) -> list:
    """Collapse a bare-column-number roster placeholder (e.g. a household-
    roster header row printing consecutive bare numbers with no stem text
    yet) into the same qnum's later, content-bearing row from that block's
    CODES/legend restatement (same number, now paired with its real field
    label). Both are the SAME paper item printed twice for typesetting
    reasons, not a genuine duplicate/renumbering artifact (those keep
    distinct printed content on each occurrence and are left alone — see
    F3-inventory.md's renumbering-artifact rows)."""
    by_qnum: dict = {}
    for i, r in enumerate(rows):
        if r.kind == "item":
            by_qnum.setdefault(r.qnum, []).append(i)
    to_drop = set()
    for idxs in by_qnum.values():
        if len(idxs) < 2:
            continue
        empties = [i for i in idxs if not rows[i].stem and not rows[i].options]
        non_empties = [i for i in idxs if i not in empties]
        if empties and non_empties:
            to_drop.update(empties)
    return [r for i, r in enumerate(rows) if i not in to_drop]


def parse_extract(md_text: str, inst: str) -> list:
    rows: list = []
    section = ""
    section_letter_ord = ord("A")
    cur = None
    unparsed_row_count = 0

    def close_current():
        nonlocal cur
        if cur is not None:
            rows.append(_finalize_item(cur))
            cur = None

    for raw_line in md_text.split("\n"):
        line = raw_line.rstrip("\r")
        if not line.strip():
            continue
        if _is_divider(line):
            continue

        if not line.lstrip().startswith("|"):
            # Rare: standalone paragraph text outside any grid table box.
            text = normalize_text(_strip_md(line))
            if text:
                kind = "note" if NOTE_RE.search(text) else "instruction"
                rows.append(Row(inst=inst, kind=kind, section=section, stem=text))
            continue

        cells = _split_cells(line)
        if not cells:
            continue

        # Cell-level dispatch, not line-level: some rows pack a plain
        # (non-bold) item number into one cell and its Yes/No checkboxes
        # into the very next cell on the SAME physical line (F4's Section N
        # income-source roster does this for a run of items), and
        # household-roster matrices (F1/F4 "C3/C4..." blocks) print a bare
        # column-number header row (consecutive numbers, e.g. three cells
        # in a row) where each cell is its own item start with no stem text
        # yet. A single whole-line classifier missed both; cells are now
        # classified independently, in order.
        row_matched_something = False
        for raw_cell in cells:
            if CHECKBOX in raw_cell:
                opts = _extract_options([raw_cell])
                if cur is not None:
                    cur["options"].extend(opts)
                    row_matched_something = True
                # An orphan option cell (no open item) has nowhere
                # principled to go; drop it rather than fabricate an item.
                continue

            cell = _prep_cell(raw_cell)

            m_item = ITEM_START_RE.match(cell)
            if m_item:
                stem_start = m_item.group(2)
                # NOTE: tried widening this to "cur is not None" (drop the
                # "not cur['options']" requirement) so it would also catch
                # F2's Q2 employment-type glossary, which sits in a "Note:"
                # block AFTER Q2's own checkboxes (so cur.options is
                # already non-empty by the time its first numbered
                # definitional entry appears) — that leaves ONE residual
                # duplicate qnum in F2 (see spot-check report). The widened
                # version was reverted: it also suppresses a genuine
                # colon-shaped F1
                # item elsewhere (186 -> 180), a much worse trade.
                if cur is not None and not cur["options"] and _looks_like_glossary_entry(stem_start):
                    cur["stem_parts"].append(cell)
                else:
                    close_current()
                    qnum = m_item.group(1)
                    cur = _new_item(inst, section, qnum, stem_start)
                row_matched_something = True
                continue

            m_letter = SECTION_LETTER_RE.match(cell)
            m_hash = SECTION_HASH_RE.match(cell)
            if m_letter or m_hash:
                close_current()
                if m_letter:
                    letter = m_letter.group(1)
                    title = m_letter.group(2)
                    section_letter_ord = ord(letter) + 1
                else:
                    letter = chr(section_letter_ord)
                    title = m_hash.group(1)
                    section_letter_ord += 1
                title_clean = normalize_text(_strip_md(title))
                section = f"{letter} {title_clean}".strip()
                rows.append(Row(inst=inst, kind="section_header", section=section, stem=title_clean))
                row_matched_something = True
                continue

            text = normalize_text(_strip_md(cell))
            if not text:
                continue

            if _is_allcaps_heading(text):
                if DIRECTIVE_BANNER_RE.match(text):
                    # A loud read/skip/select-mode directive banner or a
                    # back-coding legend header (see DIRECTIVE_BANNER_RE),
                    # not a new section — leave `section`/`cur` untouched
                    # so it doesn't relabel every later item until the
                    # next real section header.
                    rows.append(Row(inst=inst, kind="instruction", section=section, stem=text))
                else:
                    close_current()
                    kind = "consent" if "consent" in text.lower() else "section_header"
                    if kind == "section_header":
                        section = text
                    rows.append(Row(inst=inst, kind=kind, section=section, stem=text))
                row_matched_something = True
                continue

            if cur is not None and not cur["options"]:
                cur["stem_parts"].append(cell)
                continue

            kind = "note" if NOTE_RE.search(text) else "instruction"
            rows.append(Row(inst=inst, kind=kind, section=section, stem=text))

        if len(cells) > 1 and not row_matched_something:
            # Multi-cell row where no cell resolved to an item/section start
            # or a checkbox option: FIELD CONTROL grids, hyphenated coding-
            # list legends, roster label/date sub-rows. Content isn't lost
            # (each cell still became stem-continuation or a note/
            # instruction row above) but nothing new was structurally
            # recognized here — counted for the spot-check report.
            unparsed_row_count += 1

    close_current()
    rows = _merge_split_grid_items(rows)
    parse_extract.last_unparsed_count = unparsed_row_count  # type: ignore[attr-defined]
    return rows


def main():
    ap = argparse.ArgumentParser(description="Parse an Aug-17 paper extract into normalized/F{n}-paper.csv")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="instruments-aug17-extract dir (default: ../instruments-aug17-extract relative to this script)",
    )
    args = ap.parse_args()

    data_dir = (args.data_dir or DEFAULT_DATA_DIR).resolve()
    extract_path = data_dir / f"{args.instrument}-extract.md"
    text = extract_path.read_text(encoding="utf-8")

    rows = parse_extract(text, args.instrument)

    out_path = data_dir / "normalized" / f"{args.instrument}-paper.csv"
    write_csv(rows, out_path)

    items = [r for r in rows if r.kind == "item"]
    kinds = {}
    for r in rows:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
    unparsed = getattr(parse_extract, "last_unparsed_count", 0)
    print(f"{args.instrument}: {len(rows)} rows -> {out_path}")
    print(f"  items={len(items)}  kinds={kinds}  unparsed_multicell_rows={unparsed}")


if __name__ == "__main__":
    main()
