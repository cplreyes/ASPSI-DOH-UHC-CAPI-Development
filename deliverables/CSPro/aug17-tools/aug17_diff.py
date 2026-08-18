#!/usr/bin/env python3
r"""
Aug-17 migration: the Tier-1 countercheck engine.

Joins the paper-side and build-side normalized tables (rowspec.py Row
objects, produced by paper_tables.py / build_tables.py) on qnum, compares
every comparable field, and reports every divergence into one of a fixed
set of report categories. A divergence only "passes" if it is on record in
`aug17-approved-divergences.md` (the register) -- the exit code is 0 iff
every divergence found is registered, else 1. This is deliberately a
COUNTERCHECK, not a corrector: nothing here edits paper or build data, it
only classifies and reports.

Text normalization -- THREE sanctioned transforms, no others
--------------------------------------------------------------
1 + 2. `rowspec.normalize_text` -- whitespace collapse + smart-quote fold
   (shared with paper_tables.py/build_tables.py; see rowspec.py).
3. Pandoc double/triple-hyphen fold (PAPER SIDE ONLY, this module): the
   pandoc grid-table extracts render en/em dashes as `--`/`---` runs; the
   CAPI build always uses a plain single hyphen (no-em-dash device rule).
   `_norm_paper_text` applies this on top of `normalize_text` wherever
   paper-side text feeds a comparison, so the typographic artifact never
   surfaces as a false STEM_DIFF/OPTION_DIFF/etc. Build-side text is never
   run through this fold (it doesn't need it, and folding it too would risk
   masking a genuine build-authored double-hyphen).

Also applied (not a new transform, but easy to miss): rowspec.py's own
`strip_qnum=True` toggle, on the BUILD side only, for stem comparisons.
Build-side stems (CSPro qsf text, PWA label text) keep the printed "NN. "
question number as part of the on-screen prompt; paper_tables.py already
consumed that same prefix as the item-start marker while parsing, so paper
stems never carry it. Without this, nearly every item would false-positive
STEM_DIFF. See `_norm_build_stem`.

NOT sanctioned: case-folding (fix round 1, reviewer-caught). Every content
comparison (stem/option-label/section/skip/validation/messages) is
case-SENSITIVE -- "Refused to answer" vs "REFUSED TO ANSWER" is a real
OPTION_DIFF, not noise. `.casefold()` still appears in a few places in this
module, but only for REGISTER-KEY matching (finding which register row
covers a divergence, e.g. `_norm_key`, `find_structural_registered`'s
needle search) or for the deliberately-loose UNMATCHED_BUILD
stem-association / CONSENT_DIFF containment checks -- never for deciding
whether paper and build content are "the same" for reporting purposes.

Join mechanics
---------------
- Paper/build item rows are grouped by qnum (document order preserved).
  Rows sharing a qnum are paired positionally (paper's Nth occurrence vs
  build's Nth occurrence) -- a documented, deterministic tie-break for the
  real duplicate-qnum groups on both sides (roster fan-out, sub-fields,
  paper typesetting artifacts). Leftover paper rows -> MISSING_IN_BUILD;
  leftover build rows -> EXTRA_IN_BUILD.
- F4-only paper defect: the paper's second "1."-numbered item (document
  order) is actually item "2.1" mis-extracted as "1" -- rekeyed to "2.1"
  before grouping. See `_rekey_f4_paper_defect`.
- Build rows with qnum="" (F4 Section-N roster items, off-form system
  rows) are matched against paper item stems by normalized substring
  containment; unmatched ones are reported under UNMATCHED_BUILD, never
  silently dropped.
- kind="disposition" rows (ENUM_RESULT_*/BREAKOFF/CASE_DISPOSITION) are
  EXCLUDED from every ordinary category -- they are compared only via the
  dedicated DISPOSITION_DIFF rule (paper's parsed result-of-visit code list
  vs the build's ENUM_RESULT_FIRST_VISIT value set).
- kind="consent" rows are compared loosely (normalized-substring
  containment of each paper consent block's opening text inside the
  build's concatenated consent text) as CONSENT_DIFF. Per task-0.4 brief:
  full consent conformance is a Wave-1 task -- CONSENT_DIFF is reported but
  NEVER blocks this wave's exit code, registered or not.
- kind="note" paper rows have no build-side "note" kind at all (by
  build_tables.py design) -- every one is reported as NOTE_DIFF.

Register matching
-------------------
The register (`aug17-approved-divergences.md`) is human-authored prose, not
a machine key -- `_norm_key` extracts a comparable key from a "qnum/item"
cell (drop the parenthetical description, strip a leading "Q", casefold).
Ordinary per-item categories look up `(inst, norm_key(qnum))` against every
class in CLASS_ENUM (Tier A -- exact-ish key match). DISPOSITION_DIFF and
ORDER_DIFF are structural -- a single register row can cover an entire
instrument's disposition code-set divergence or a whole section-order
swap -- so a presence-only substring check isn't enough (fix round 1: it
would auto-stamp any FUTURE regression REGISTERED forever just because a
"FIELD CONTROL"/"order:X,Y" row happens to exist). Both are now
content-verified:
- DISPOSITION_DIFF: a matching "FIELD CONTROL" row (`find_structural_
  registered`, presence check) must ALSO carry a `(codes: 1=Label,...)`
  parenthetical in its `build_does` cell (`_parse_canonical_codes`) that
  EXACTLY equals the currently-computed build code set -- else the row is
  treated as not covering this run's content and the finding stays
  UNREGISTERED.
- ORDER_DIFF: `find_order_registered` parses both the finding's "order:X,Y"
  key and each candidate register row's `qnum/item` cell into a letter SET
  and requires exact set equality -- an "order:G,H" row does not cover an
  "order:G"-only move (nor an "order:G,H,I" move); it must name every
  moved section, no more, no less.
See task-0.4-report.md (including its "Fix round 1" section) for the
concrete matching rules and their known gaps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from rowspec import Row, normalize_text, read_csv

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (SCRIPT_DIR / ".." / "instruments-aug17-extract").resolve()

CLASS_ENUM = (
    "defect-fix", "capi-adaptation", "fill", "formatting",
    "cardinality-default", "system-item",
)

# Core categories per the task-0.4 brief, plus two join-mechanics extensions
# the brief's own point (b)/(d) require (UNMATCHED_BUILD, CONSENT_DIFF).
CATEGORIES = [
    "MISSING_IN_BUILD", "EXTRA_IN_BUILD", "STEM_DIFF", "OPTION_DIFF",
    "ORDER_DIFF", "SECTION_DIFF", "NOTE_DIFF", "CARDINALITY_DIFF",
    "SKIP_DIFF", "VALIDATION_DIFF", "MESSAGE_DIFF", "DISPOSITION_DIFF",
    "CONSENT_DIFF", "UNMATCHED_BUILD",
]

# Categories excluded from the exit-code gate this wave even when
# unregistered (brief join-mechanics point (d): full consent conformance
# is a Wave-1 task).
NON_BLOCKING_CATEGORIES = {"CONSENT_DIFF"}


# --- text normalization (transform #3; see module docstring) --------------

_PANDOC_DASH_RE = re.compile(r"-{2,}")


def _norm_paper_text(s: str, strip_qnum: bool = False) -> str:
    """normalize_text + pandoc double/triple-hyphen fold. PAPER SIDE ONLY."""
    return _PANDOC_DASH_RE.sub("-", normalize_text(s, strip_qnum=strip_qnum))


def _norm_build_text(s: str) -> str:
    return normalize_text(s)


def _norm_build_stem(s: str) -> str:
    """Build-side stems only: the CSPro qsf/PWA label text keeps the
    printed "NN. " question number as part of the on-screen prompt (the
    enumerator/respondent sees it); paper_tables.py's ITEM_START_RE already
    consumes that same prefix as the item-start marker, so paper stems
    never carry it. strip_qnum=True is rowspec.py's one sanctioned
    transform for exactly this asymmetry -- applied build-side, not
    paper-side, since the build is the side that still has the prefix."""
    return normalize_text(s, strip_qnum=True)


# --- register --------------------------------------------------------------


@dataclass
class RegisterRow:
    inst: str
    qnum_item: str
    cls: str
    paper_says: str
    build_does: str
    rationale: str


def _is_divider_cell(cell: str) -> bool:
    return bool(cell) and set(cell) <= {"-", ":"}


def parse_register_rows(text: str) -> list:
    """Markdown table -> list[RegisterRow]. Skips the title/prose, the
    header row, and the `|---|---|...|` divider row. Tolerant of a missing
    file (caller passes '' for that)."""
    rows = []
    for line in text.split("\n"):
        line = line.rstrip()
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            continue
        if cells[0].lower() == "inst":
            continue
        if _is_divider_cell(cells[0]):
            continue
        if not cells[0]:
            continue
        rows.append(RegisterRow(
            inst=cells[0], qnum_item=cells[1], cls=cells[2],
            paper_says=cells[3], build_does=cells[4], rationale=cells[5],
        ))
    return rows


_LEADING_Q_RE = re.compile(r"^[Qq](\d.*)$")


def _norm_key(text: str) -> str:
    """Normalize a register 'qnum/item' cell OR a Row.qnum into a
    comparable key: drop a parenthetical description, strip a leading Q
    immediately before a digit, casefold, collapse whitespace."""
    t = (text or "").strip()
    t = t.split("(", 1)[0].strip()
    m = _LEADING_Q_RE.match(t)
    if m:
        t = m.group(1)
    return re.sub(r"\s+", " ", t).strip().casefold()


def build_register_index(rows: list) -> dict:
    """list[RegisterRow] -> {(inst, norm_key(qnum_item), cls): RegisterRow}
    -- the interface literally specified by the task-0.4 brief."""
    reg = {}
    for r in rows:
        reg[(r.inst, _norm_key(r.qnum_item), r.cls)] = r
    return reg


def load_register(path) -> dict:
    p = Path(path)
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    return build_register_index(parse_register_rows(text))


def find_registered(register: dict, inst: str, qnum: str):
    """Tier A: exact-ish per-item key match, tried against every class."""
    key = _norm_key(qnum)
    if not key:
        return None
    for cls in CLASS_ENUM:
        row = register.get((inst, key, cls))
        if row:
            return row
    return None


def find_structural_registered(register: dict, inst: str, *needles: str):
    """Tier B: substring-containment scan for structural categories
    (DISPOSITION_DIFF, ORDER_DIFF) where one register row legitimately
    covers many items/qnums at once."""
    for row in register.values():
        if row.inst != inst:
            continue
        hay = row.qnum_item.casefold()
        if all(n.casefold() in hay for n in needles):
            return row
    return None


# --- findings ---------------------------------------------------------------


@dataclass
class Finding:
    category: str
    qnum: str
    detail: str
    registered: object = None  # RegisterRow | None, set by the registration pass
    context: dict = field(default_factory=dict)  # side-channel data the registration pass needs (e.g. build_codes for DISPOSITION_DIFF content verification)


def _qnum_sort_key(q: str):
    m = re.match(r"^(\d+)(?:\.(\d+))?", q or "")
    if m:
        major = int(m.group(1))
        minor = int(m.group(2)) if m.group(2) else 0
        return (0, major, minor, q)
    return (1, 0, 0, q or "")


def _opts_key(options: list, norm) -> tuple:
    """NOT case-folded -- case-insensitivity is not a sanctioned
    normalization (fix round 1). A pure-case option-label mismatch (e.g.
    paper "Refused to answer" vs build "REFUSED TO ANSWER") must surface as
    OPTION_DIFF, not be silently treated as identical."""
    return tuple(norm(o.get("label", "")) for o in options)


def _group_by_qnum(rows: list) -> dict:
    g: dict = {}
    for r in rows:
        if r.qnum:
            g.setdefault(r.qnum, []).append(r)
    return g


def _rekey_f4_paper_defect(paper_items: list) -> str:
    """F4-only documented paper defect: item '2.1' rides as the paper's
    SECOND '1.'-numbered item (document order). Rekeys that row's qnum in
    place. Returns a human note for the report header, or '' if the
    expected shape (>=2 rows at qnum '1') isn't present (defensive -- don't
    silently no-op without saying so)."""
    ones = [r for r in paper_items if r.qnum == "1"]
    if len(ones) < 2:
        return ""
    ones[1].qnum = "2.1"
    return (
        "F4 paper-defect rekey applied: the paper's 2nd document-order "
        "item numbered \"1.\" was rekeyed to qnum \"2.1\" (documented "
        "paper defect, not a real duplicate \"1\") before joining."
    )


def _match_by_stem(build_row: Row, paper_items: list, claimed: set):
    b_norm = _norm_build_stem(build_row.stem).casefold()
    if len(b_norm) < 15:
        return None
    for p in paper_items:
        if p.qnum in claimed:
            continue
        p_norm = _norm_paper_text(p.stem).casefold()
        if len(p_norm) < 15:
            continue
        if b_norm in p_norm or p_norm in b_norm:
            claimed.add(p.qnum)
            return p
    return None


def _compare_pair(q: str, p: Row, b: Row) -> list:
    out = []
    if _norm_paper_text(p.stem) != _norm_build_stem(b.stem):
        out.append(Finding("STEM_DIFF", q,
            f'paper: "{p.stem[:120]}" | build ({b.item_name}): "{b.stem[:120]}"'))

    if _opts_key(p.options, _norm_paper_text) != _opts_key(b.options, _norm_build_text):
        out.append(Finding("OPTION_DIFF", q,
            f"paper options={[o.get('label') for o in p.options]} | "
            f"build ({b.item_name}) options={[o.get('label') for o in b.options]}"))

    if p.cardinality != b.cardinality or p.qtype != b.qtype:
        out.append(Finding("CARDINALITY_DIFF", q,
            f"paper qtype/cardinality={p.qtype}/{p.cardinality} | "
            f"build ({b.item_name})={b.qtype}/{b.cardinality}"))

    if _norm_paper_text(p.skip) != _norm_build_text(b.skip):
        out.append(Finding("SKIP_DIFF", q,
            f'paper skip="{p.skip}" | build ({b.item_name}) skip="{b.skip}"'))

    if _norm_paper_text(p.validation) != _norm_build_text(b.validation):
        out.append(Finding("VALIDATION_DIFF", q,
            f'paper validation="{p.validation}" | build ({b.item_name}) validation="{b.validation}"'))

    if _norm_paper_text(p.messages) != _norm_build_text(b.messages):
        out.append(Finding("MESSAGE_DIFF", q,
            f'paper messages="{p.messages}" | build ({b.item_name}) messages="{b.messages}"'))

    if _norm_paper_text(p.section) != _norm_build_text(b.section):
        out.append(Finding("SECTION_DIFF", q,
            f'paper section="{p.section}" | build ({b.item_name}) section="{b.section}"'))

    return out


def _compare_consent(paper_rows: list, build_rows: list) -> list:
    findings = []
    paper_consent = [r for r in paper_rows if r.kind == "consent"]
    build_consent = [r for r in build_rows if r.kind == "consent"]
    if not paper_consent and not build_consent:
        return findings
    build_blob = " ".join(_norm_build_text(r.stem) for r in build_consent).casefold()
    for i, p in enumerate(paper_consent, start=1):
        probe = _norm_paper_text(p.stem).casefold()[:60]
        if probe and probe not in build_blob:
            findings.append(Finding("CONSENT_DIFF", f"consent:{i}",
                f'paper consent block #{i} ("{p.stem[:80]}...") not found (loose containment) '
                f"in build consent text -- non-blocking this wave"))
    return findings


_DISPOSITION_ITEM_RE = re.compile(
    r"(\d+)\s*[.\-]\s*([A-Za-z][^0-9]*?)(?=\s*\d+\s*[.\-]\s*[A-Za-z]|$)"
)


def _extract_paper_disposition(paper_rows: list) -> dict:
    in_window = False
    codes: dict = {}
    for r in paper_rows:
        if r.kind not in ("instruction", "section_header"):
            continue
        text = r.stem or ""
        if not in_window:
            if "field control" in text.lower():
                in_window = True
            continue
        if "total number of visits" in text.lower():
            break
        for m in _DISPOSITION_ITEM_RE.finditer(_norm_paper_text(text)):
            code, label = m.group(1), _norm_paper_text(m.group(2))
            if label:
                codes[code] = label
    return codes


def _extract_build_disposition(build_rows: list):
    for name in ("ENUM_RESULT_FIRST_VISIT", "ENUM_RESULT_FINAL_VISIT"):
        for r in build_rows:
            if r.kind == "disposition" and r.item_name == name:
                return {o["code"]: _norm_build_text(o["label"]) for o in r.options}
    return None


def _fmt_codes(codes: dict) -> str:
    def sort_key(kv):
        return int(kv[0]) if kv[0].isdigit() else 0
    return ", ".join(f"{k}-{v}" for k, v in sorted(codes.items(), key=sort_key))


def _compare_disposition(paper_rows: list, build_rows: list) -> list:
    paper_codes = _extract_paper_disposition(paper_rows)
    build_codes = _extract_build_disposition(build_rows)
    if not paper_codes and build_codes is None:
        return []
    if build_codes is None:
        build_codes = {}
    if paper_codes == build_codes:
        return []
    return [Finding("DISPOSITION_DIFF", "FIELD CONTROL",
        f"paper result-of-visit codes = {{{_fmt_codes(paper_codes)}}} | "
        f"build ENUM_RESULT = {{{_fmt_codes(build_codes)}}}",
        context={"build_codes": build_codes})]


_CANON_CODES_RE = re.compile(r"\(codes:\s*([^)]*)\)")


def _parse_canonical_codes(text: str) -> dict:
    """Parse a register row's `build_does` cell for a trailing
    '(codes: 1=Label,2=Label,...)' canonical code list -- the
    content-verification anchor for DISPOSITION_DIFF registration (fix
    round 1: presence of a "FIELD CONTROL" row alone is not enough, the
    row must name the EXACT code set it approves). Returns {} if absent,
    unparsable, or explicitly 'none' -- callers must then treat the row as
    NOT covering content (fail closed: an empty/missing canonical list only
    matches a build with zero disposition codes, e.g. F2)."""
    m = _CANON_CODES_RE.search(text or "")
    if not m:
        return {}
    out = {}
    for piece in m.group(1).split(","):
        piece = piece.strip()
        if "=" not in piece:
            continue
        code, label = piece.split("=", 1)
        out[code.strip()] = normalize_text(label.strip())
    return out


_SECTION_LETTER_RE = re.compile(r"^([A-Z])\b")


def _section_letter(section: str) -> str:
    m = _SECTION_LETTER_RE.match((section or "").strip())
    return m.group(1) if m else ""


def _first_appearance_order(items: list) -> list:
    seen = []
    for r in items:
        letter = _section_letter(r.section)
        if letter and letter not in seen:
            seen.append(letter)
    return seen


def _find_moved_block(paper_order: list, build_order: list):
    """If build_order is paper_order with exactly one contiguous run of
    letters relocated elsewhere (rest stays in the same relative order),
    return that run (paper order). Else None. A single transposition can
    always be described two ways (the small block that moved, or its large
    complement that "moved" the other direction around it) -- iterates
    block length ascending so the SMALLEST valid block wins; that's the
    minimal, meaningful description of what actually relocated."""
    n = len(paper_order)
    for length in range(1, n + 1):
        for i in range(0, n - length + 1):
            block = paper_order[i:i + length]
            rest = paper_order[:i] + paper_order[i + length:]
            build_rest = [x for x in build_order if x not in block]
            if build_rest == rest and any(x in block for x in build_order):
                return block
    return None


def _compare_order(inst: str, paper_items: list, build_items: list) -> list:
    paper_full = _first_appearance_order(paper_items)
    build_full = _first_appearance_order(build_items)
    common = [l for l in paper_full if l in build_full]
    common_build = [l for l in build_full if l in paper_full]
    if common == common_build:
        return []
    block = _find_moved_block(common, common_build)
    if block:
        key = "order:" + ",".join(block)
        detail = (f'section order: paper has {",".join(common)} | '
                   f'build relocates {",".join(block)} -> build order {",".join(common_build)}')
    else:
        key = "order:" + ",".join(common)
        detail = f'section order differs: paper={",".join(common)} | build={",".join(common_build)}'
    return [Finding("ORDER_DIFF", key, detail)]


_ORDER_KEY_RE = re.compile(r"^order:(.+)$", re.IGNORECASE)


def _parse_order_letters(key: str):
    """'order:G,H' -> frozenset({'G','H'}). None if the text isn't an
    order: key at all (register rows for other categories)."""
    m = _ORDER_KEY_RE.match((key or "").split("(", 1)[0].strip())
    if not m:
        return None
    return frozenset(x.strip().upper() for x in m.group(1).split(",") if x.strip())


def find_order_registered(register: dict, inst: str, order_key: str):
    """Content-verified ORDER_DIFF match (fix round 1): the register row
    must name EVERY moved section, exactly -- a "order:G,H" row does NOT
    cover a "order:G"-only move (and wouldn't cover a "order:G,H,I" move
    either). Set equality, not substring containment."""
    moved = _parse_order_letters(order_key)
    if not moved:
        return None
    for row in register.values():
        if row.inst != inst:
            continue
        row_letters = _parse_order_letters(row.qnum_item)
        if row_letters is not None and row_letters == moved:
            return row
    return None


# --- top-level diff ----------------------------------------------------------


def diff_instrument(inst: str, paper_rows: list, build_rows: list, register: dict):
    """Returns (findings: list[Finding], counts: dict[str,int],
    blocking_unregistered: int). `blocking_unregistered` > 0 means exit 1."""
    header_notes = []

    paper_items = [r for r in paper_rows if r.kind == "item"]
    build_items = [r for r in build_rows if r.kind == "item"]

    if inst == "F4":
        note = _rekey_f4_paper_defect(paper_items)
        if note:
            header_notes.append(note)

    findings: list = []

    paper_g = _group_by_qnum(paper_items)
    build_g = _group_by_qnum(build_items)
    build_unnumbered = [r for r in build_items if not r.qnum]

    claimed: set = set()
    unmatched_build = []
    for r in build_unnumbered:
        target = _match_by_stem(r, paper_items, claimed)
        if target is not None:
            build_g.setdefault(target.qnum, []).append(r)
        else:
            unmatched_build.append(r)

    all_qnums = sorted(set(paper_g) | set(build_g), key=_qnum_sort_key)
    for q in all_qnums:
        p_list = paper_g.get(q, [])
        b_list = build_g.get(q, [])
        n = min(len(p_list), len(b_list))
        for i in range(n):
            findings.extend(_compare_pair(q, p_list[i], b_list[i]))
        for idx, extra_p in enumerate(p_list[n:], start=n):
            findings.append(Finding("MISSING_IN_BUILD", q,
                f'paper {q} (occurrence #{idx + 1}): "{extra_p.stem[:100]}" has no build match'))
        for extra_b in b_list[n:]:
            findings.append(Finding("EXTRA_IN_BUILD", q,
                f'build {extra_b.item_name} (qnum {q}): "{extra_b.stem[:100]}" has no paper counterpart at this position'))

    for r in unmatched_build:
        findings.append(Finding("UNMATCHED_BUILD", "",
            f'{r.item_name}: "{r.stem[:100]}" -- no qnum, no stem match to any paper item'))

    for r in paper_rows:
        if r.kind == "note":
            findings.append(Finding("NOTE_DIFF", f"note:{r.section}",
                f'paper note ({r.section}): "{r.stem[:120]}" -- no build "note" counterpart (build never emits kind=note)'))

    findings.extend(_compare_consent(paper_rows, build_rows))
    findings.extend(_compare_disposition(paper_rows, build_rows))
    findings.extend(_compare_order(inst, paper_items, build_items))

    counts = {c: 0 for c in CATEGORIES}
    blocking_unregistered = 0
    registered_count = 0
    for f in findings:
        counts[f.category] = counts.get(f.category, 0) + 1
        reg_row = None
        if f.category == "DISPOSITION_DIFF":
            candidate = find_structural_registered(register, inst, "FIELD CONTROL")
            if candidate is not None:
                canon = _parse_canonical_codes(candidate.build_does)
                if canon == f.context.get("build_codes", {}):
                    reg_row = candidate
                # else: a FIELD CONTROL row exists but its canonical code
                # list doesn't match the CURRENT build -- content mismatch,
                # stays unregistered (fix round 1: presence alone isn't
                # enough, or any future disposition regression would be
                # auto-stamped REGISTERED forever).
        elif f.category == "ORDER_DIFF":
            reg_row = find_order_registered(register, inst, f.qnum)
        elif f.category == "CONSENT_DIFF":
            reg_row = find_structural_registered(register, inst, "consent")
        elif f.qnum:
            reg_row = find_registered(register, inst, f.qnum)
        f.registered = reg_row
        if reg_row:
            registered_count += 1
        elif f.category not in NON_BLOCKING_CATEGORIES:
            blocking_unregistered += 1

    counts["REGISTERED"] = registered_count
    diff_instrument.last_header_notes = header_notes  # type: ignore[attr-defined]
    return findings, counts, blocking_unregistered


# --- reporting ---------------------------------------------------------------


def write_report(inst: str, findings: list, counts: dict, blocking: int,
                  header_notes: list, out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {inst} — Aug-17 Tier-1 diff report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Result: {'PASS' if blocking == 0 else 'FAIL'} "
        f"({blocking} unregistered divergence(s) block the exit code)",
        "",
        "**Matching rules** (see aug17_diff.py module docstring for the full explanation):",
        "- Per-item categories (STEM_DIFF, OPTION_DIFF, CARDINALITY_DIFF, SKIP_DIFF, "
        "VALIDATION_DIFF, MESSAGE_DIFF, SECTION_DIFF, MISSING/EXTRA_IN_BUILD) register-match "
        "on a normalized qnum key against the register's `qnum/item` column.",
        "- DISPOSITION_DIFF and ORDER_DIFF register-match structurally AND "
        "content-verified: a 'FIELD CONTROL' row must ALSO carry a matching "
        "`(codes: 1=Label,...)` canonical list, and an 'order:X,Y' row must name "
        "EXACTLY the moved section letters -- presence of a plausible-looking row "
        "alone is not enough (fix round 1, 2026-08-18).",
        "- Every content comparison (stem/option/section/skip/validation/messages) is "
        "case-SENSITIVE -- case-insensitivity is not a sanctioned normalization "
        "(fix round 1, 2026-08-18).",
        "- CONSENT_DIFF is reported but NEVER blocks the exit code this wave "
        "(full consent conformance is a Wave-1 task per the task-0.4 brief).",
        "- Text comparisons use 3 sanctioned normalizations: whitespace collapse, "
        "smart-quote fold, and (paper side only) pandoc `--`/`---` -> `-` fold.",
    ]
    if header_notes:
        lines.append("")
        lines.append("**Instrument-specific notes:**")
        for n in header_notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---|")
    for c in CATEGORIES:
        lines.append(f"| {c} | {counts.get(c, 0)} |")
    lines.append(f"| REGISTERED | {counts.get('REGISTERED', 0)} |")
    lines.append("")

    for cat in CATEGORIES:
        cat_findings = [f for f in findings if f.category == cat]
        if not cat_findings:
            continue
        lines.append(f"## {cat} ({len(cat_findings)})")
        lines.append("")
        for f in cat_findings:
            tag = "REGISTERED" if f.registered else "UNREGISTERED"
            extra = ""
            if f.registered:
                extra = f" — {f.registered.cls}: {f.registered.rationale}"
            qnum_disp = f"[{f.qnum}] " if f.qnum else ""
            lines.append(f"- **{tag}** {qnum_disp}{f.detail}{extra}")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status(inst: str, counts: dict, ok: bool, out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tier1": "pass" if ok else "fail",
        "diff_counts": {k: v for k, v in counts.items()},
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --- CLI -----------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description="Aug-17 Tier-1 diff: paper vs build, register-aware")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()

    data_dir = (args.data_dir or DEFAULT_DATA_DIR).resolve()
    paper_rows = read_csv(data_dir / "normalized" / f"{args.instrument}-paper.csv")
    build_rows = read_csv(data_dir / "normalized" / f"{args.instrument}-build.csv")
    register = load_register(data_dir / "aug17-approved-divergences.md")

    findings, counts, blocking = diff_instrument(args.instrument, paper_rows, build_rows, register)
    header_notes = getattr(diff_instrument, "last_header_notes", [])
    ok = blocking == 0

    report_path = data_dir / "reports" / f"{args.instrument}-diff.md"
    status_path = data_dir / "status" / f"{args.instrument}-verify.json"
    write_report(args.instrument, findings, counts, blocking, header_notes, report_path)
    write_status(args.instrument, counts, ok, status_path)

    top = sorted(
        ((c, counts.get(c, 0)) for c in CATEGORIES if counts.get(c, 0)),
        key=lambda kv: -kv[1],
    )[:5]
    print(f"{args.instrument}: {'PASS' if ok else 'FAIL'} -- {blocking} unregistered divergence(s), "
          f"{counts.get('REGISTERED', 0)} registered. Top categories: {top}")
    print(f"  report -> {report_path}")
    print(f"  status -> {status_path}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
