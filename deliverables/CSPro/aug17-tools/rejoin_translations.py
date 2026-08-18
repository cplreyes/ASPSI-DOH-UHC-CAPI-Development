#!/usr/bin/env python3
r"""
Aug-17 migration: translation locale key mover + carryover reporter.

Three independent modes, one shared plan shape ({"kept", "moved", "fellback"}):

  1. CSPro rename mode (default) -- for instruments that get a hand-resolved
     item-rename map (F1, Task 2.1/2.5). Reads `maps/F{n}-renames.csv`
     (`old_name,new_name[,change_class,...]` -- extra columns tolerated) and
     moves every scoped key whose embedded item name matches a row:
       item:OLD -> item:NEW
       vs:OLD_VS1 -> vs:NEW_VS1
       val:OLD_VS1:3 -> val:NEW_VS1:3
     following the key grammar of cspro_helpers.walk_labeled_nodes (see
     `deliverables/CSPro/data/translations-official/migrate_maps_namekeys.py`
     for the reference migration that first produced this format):
       dict:<NAME> | level:<NAME> | record:<NAME> | item:<NAME>
       vs:<VALUE-SET-NAME> | val:<VALUE-SET-NAME>:<code[,code|lo..hi]>
     `vs:`/`val:` keys are matched by stripping a trailing `_VS<n>` suffix
     off the embedded value-set name -- this is a STRING convention (every
     value set observed in the fleet is named `<ITEM>_VS<n>`), not a DCF
     lookup; a value-set name that doesn't follow the convention simply
     never matches a rename row and stays untouched, which is the safe
     failure mode.

  2. --stale-from-tables mode -- for instruments WITHOUT a rename map (F3,
     F4). Reads the normalized paper/build tables produced by Task 0.2/0.3
     (`instruments-aug17-extract/normalized/F{n}-{paper,build}.csv`) and
     joins them with the EXACT SAME qnum-grouping / F4-paper-defect-rekey /
     build_unnumbered stem-matching logic as aug17_diff.diff_instrument
     (imported, not reimplemented -- see `join_paper_build_items`). Any item
     whose paper stem now differs from the build stem it used to match is
     "stem-changed"; any option whose paper label differs from the build
     label at the same code is "option-changed". Both get dropped (English
     fallback) rather than carried, and reported fell-back.

  3. --pwa mode -- the PWA store (`F2/PWA/app/spec/translations/*.json`) is
     still flat English-text-keyed (Task 3.3 has not re-keyed it to a
     name-scoped format). `maps/F2-english-rekey.csv`
     (`old_english,new_english`) renames the JSON key itself; the value
     (translation) carries verbatim. NOTE: unlike the two CSPro modes above,
     PWA mode has no drop/fallback step. A `--stale-from-tables`-equivalent
     for PWA would need its own old-English/new-English staleness signal
     that Task 3.3 hasn't defined yet -- deliberately left as a documented
     gap rather than guessed at here.

Decision 2 (why anything gets dropped at all): a name-scoped key survives a
bare rename or bare rewording -- but if the ENGLISH itself changed, showing
the OLD translation under the new/same key would silently display a
translation of superseded English. There is no cleared translation for the
new wording yet, so the correct behavior is to fall back to English (not
carry stale content) and list the item on the carryover report as work still
owed to the ASPSI translation team.

Apply-mode implementation note (same lesson as bridge_check.py): translation
files in this repo have INCONSISTENT indentation across locales/instruments
(1-space vs 2-space, fleet drift from different generation passes). A full
`json.load` + `json.dump` round trip reformats the entire file for a
handful of key changes, burying the real diff. `--apply` therefore uses a
SURGICAL, line-anchored text edit (`surgical_rejoin_scoped_text` /
`surgical_rejoin_text_keys`, adapted from bridge_check.py's
`strip_item_keys`): find each affected key's own line, rename or delete it
in place, repair a dangling trailing comma, then validate the whole result
with `json.loads` and a removed/renamed key-set equality check before
writing. Every untouched line is preserved byte-for-byte, INCLUDING its
original line-ending bytes.

Newline discipline (fix round 1, 2026-08-18 -- reviewer-caught): the real
MAIN locale files are LF-only. `Path.read_text`/`write_text` default to
universal-newline translation, which on Windows means a plain `write_text()`
silently turns every `\n` in the file into `\r\n` on write -- even for lines
this tool never touched -- flipping the whole file to CRLF (the documented
2026-07-13 F2 incident, recurring). Every read/write of a real locale file in
this module therefore passes `newline=""` (disables translation entirely: a
read returns line endings exactly as stored, a write emits exactly what's in
the string, no substitution either direction).

Atomicity (fix round 1): `--apply` is plan-then-write, not
plan-then-write-per-locale. All 7 locale files' plans, surgical texts, and
removed/renamed key-set equality checks are computed and validated FIRST
(`_prepare_cspro_write` / `_prepare_pwa_write`); only if every one of the 7
passes does the tool write any of them (`_commit_write`). A validation
failure on locale 5 of 7 aborts the whole instrument run with ZERO files
written -- never a half-applied instrument.

Usage:
    python rejoin_translations.py F1 --map maps/F1-renames.csv [--apply]
    python rejoin_translations.py F3 --stale-from-tables [--apply]
    python rejoin_translations.py F2 --pwa --map maps/F2-english-rekey.csv [--apply]

Dry-run (report only, no writes) is the default in every mode.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from aug17_diff import (
    DEFAULT_DATA_DIR,
    _group_by_qnum,
    _match_by_stem,
    _norm_build_stem,
    _norm_build_text,
    _norm_paper_text,
    _rekey_f4_paper_defect,
)
from rowspec import read_csv

SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_ROOT = Path(r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development")
MAIN_CSPRO = MAIN_ROOT / "deliverables" / "CSPro"
PWA_TRANSLATIONS_DEFAULT = (SCRIPT_DIR / ".." / ".." / "F2" / "PWA" / "app" / "spec" / "translations").resolve()

LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]


# --- name-scope guard --------------------------------------------------


def require_name_scoped(data: dict, label: str) -> None:
    """CSPro locale files must already be migrated to the 2026-08-17
    name-scoped format before this tool will touch them. A file still
    keyed on full English label text (the pre-migration shape) is refused
    outright -- silently "moving" text-keyed entries would just be
    re-implementing the fragile old apply_translations() lookup this
    migration replaced."""
    meta = data.get("_meta") if isinstance(data, dict) else None
    if not (isinstance(meta, dict) and meta.get("format") == "name-scoped-v2"):
        raise ValueError(
            f"{label}: not name-scoped (missing _meta.format == 'name-scoped-v2'). "
            "Run data/translations-official/migrate_maps_namekeys.py first."
        )


# --- CSPro name-scoped key grammar --------------------------------------

_VS_SUFFIX_RE = re.compile(r"^(.*)_VS(\d+)$")


def split_vs_suffix(name: str):
    """'FOO_VS1' -> ('FOO', '_VS1'); 'FOO' (no _VS<n> suffix) -> ('FOO', '')."""
    m = _VS_SUFFIX_RE.match(name)
    if m:
        return m.group(1), f"_VS{m.group(2)}"
    return name, ""


def plan_key_rename(key, rename_map, stem_changed_names, stale_val_codes):
    """Classify one raw key from a name-scoped CSPro locale file. Returns
    (action, detail):
      ("unmapped", None)     -- stays under its original key, byte-identical
      ("moved", new_key)     -- carries to new_key, value verbatim
      ("dropped", reason)    -- falls back to English (Decision 2)
    `stem_changed_names`: set of OLD item names whose English stem changed.
    `stale_val_codes`: set of (OLD value-set base name, code) whose option
    label changed.
    """
    if key.startswith("item:"):
        name = key[len("item:"):]
        new_name = rename_map.get(name)
        if new_name is None:
            return "unmapped", None
        if name in stem_changed_names:
            return "dropped", "renamed+reworded"
        return "moved", f"item:{new_name}"
    if key.startswith("vs:"):
        base, suffix = split_vs_suffix(key[len("vs:"):])
        new_name = rename_map.get(base)
        if new_name is None:
            return "unmapped", None
        return "moved", f"vs:{new_name}{suffix}"
    if key.startswith("val:"):
        rest = key[len("val:"):]
        vs_name, code = rest.rsplit(":", 1)
        base, suffix = split_vs_suffix(vs_name)
        new_name = rename_map.get(base)
        if new_name is None:
            return "unmapped", None
        if (base, code) in stale_val_codes:
            return "dropped", "renamed+reworded-option"
        return "moved", f"val:{new_name}{suffix}:{code}"
    if key.startswith("record:"):
        name = key[len("record:"):]
        new_name = rename_map.get(name)
        if new_name is None:
            return "unmapped", None
        return "moved", f"record:{new_name}"
    return "unmapped", None  # _meta, dict:, level: -- never touched by an item rename


def _check_collisions(kept: dict, moved: list) -> None:
    dest_seen = {}
    for old_key, new_key in moved:
        if new_key in kept:
            raise ValueError(
                f"rename collision: {old_key!r} -> {new_key!r} collides with an existing unmapped key"
            )
        if new_key in dest_seen:
            raise ValueError(
                f"rename collision: {dest_seen[new_key]!r} and {old_key!r} both map to {new_key!r}"
            )
        dest_seen[new_key] = old_key


def plan_rejoin(locale_data: dict, rename_map: dict, stem_changed_names: set, stale_val_codes: set) -> dict:
    """CSPro rename-mode plan for ONE locale file's already-parsed JSON.
    Returns {"kept": {key: value}, "moved": [(old_key, new_key)],
    "fellback": [(old_key, reason)]}."""
    kept, moved, fellback = {}, [], []
    if "_meta" in locale_data:
        kept["_meta"] = locale_data["_meta"]
    for key, value in locale_data.items():
        if key == "_meta":
            continue
        action, detail = plan_key_rename(key, rename_map, stem_changed_names, stale_val_codes)
        if action == "unmapped":
            kept[key] = value
        elif action == "dropped":
            fellback.append((key, detail))
        else:
            moved.append((key, detail))
    _check_collisions(kept, moved)
    return {"kept": kept, "moved": moved, "fellback": fellback}


def plan_stale_drop(locale_data: dict, stem_changed_names: set, option_changed: set) -> dict:
    """--stale-from-tables mode plan: pure drop, no renaming -- every
    item:/val: key whose (name)/(name, code) is in the stale sets is
    dropped (fell-back); everything else is kept untouched."""
    kept, fellback = {}, []
    if "_meta" in locale_data:
        kept["_meta"] = locale_data["_meta"]
    for key, value in locale_data.items():
        if key == "_meta":
            continue
        reason = None
        if key.startswith("item:") and key[len("item:"):] in stem_changed_names:
            reason = "stale-stem"
        elif key.startswith("val:"):
            rest = key[len("val:"):]
            vs_name, code = rest.rsplit(":", 1)
            base, _suffix = split_vs_suffix(vs_name)
            if (base, code) in option_changed:
                reason = "stale-option"
        if reason:
            fellback.append((key, reason))
        else:
            kept[key] = value
    return {"kept": kept, "moved": [], "fellback": fellback}


def load_rename_map(csv_path):
    """Load `old_name,new_name[,change_class,...]` (extra columns tolerated,
    including a future `stem_changed` column). Returns (rename: {old: new},
    stem_changed: {old names flagged stem_changed}). A duplicate old_name
    with a conflicting new_name is a hard error."""
    rename, stem_changed = {}, set()
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            old = (row.get("old_name") or "").strip()
            new = (row.get("new_name") or "").strip()
            if not old or not new:
                continue
            if old in rename and rename[old] != new:
                raise ValueError(f"{csv_path}: duplicate old_name {old!r} with conflicting new_name")
            rename[old] = new
            flag = (row.get("stem_changed") or "").strip().lower()
            if flag in ("1", "true", "yes", "y"):
                stem_changed.add(old)
    return rename, stem_changed


# --- --stale-from-tables: reuse the diff engine's exact join semantics ----


def join_paper_build_items(inst, paper_rows, build_rows):
    """Same qnum-grouping / F4-paper-defect-rekey / build_unnumbered
    stem-matching as aug17_diff.diff_instrument's join (imported helpers,
    not reimplemented). Returns a list of (qnum, paper_row, build_row) for
    matched pairs and (qnum, paper_row, None) for paper rows with no old
    build counterpart ("new" content -- see compute_stale_from_tables)."""
    paper_items = [r for r in paper_rows if r.kind == "item"]
    build_items = [r for r in build_rows if r.kind == "item"]
    if inst == "F4":
        _rekey_f4_paper_defect(paper_items)

    paper_g = _group_by_qnum(paper_items)
    build_g = _group_by_qnum(build_items)
    build_unnumbered = [r for r in build_items if not r.qnum]
    claimed = set()
    for r in build_unnumbered:
        target = _match_by_stem(r, paper_items, claimed)
        if target is not None:
            build_g.setdefault(target.qnum, []).append(r)

    pairs = []
    for q in sorted(set(paper_g) | set(build_g)):
        p_list, b_list = paper_g.get(q, []), build_g.get(q, [])
        n = min(len(p_list), len(b_list))
        for i in range(n):
            pairs.append((q, p_list[i], b_list[i]))
        for extra_p in p_list[n:]:
            pairs.append((q, extra_p, None))
    return pairs


def compute_stale_from_tables(inst, paper_rows, build_rows):
    """Returns (stem_changed: set[item_name], option_changed: set[(item_name,
    code)], new_rows: list[Row]) -- the item-name-scoped, locale-independent
    staleness signal that plan_stale_drop() consumes per locale file."""
    pairs = join_paper_build_items(inst, paper_rows, build_rows)
    stem_changed, option_changed, new_rows = set(), set(), []
    for _q, p, b in pairs:
        if b is None:
            new_rows.append(p)
            continue
        if not b.item_name:
            continue
        if _norm_paper_text(p.stem) != _norm_build_stem(b.stem):
            stem_changed.add(b.item_name)
        p_by_code = {o.get("code"): o.get("label", "") for o in p.options}
        for o in b.options:
            code = o.get("code")
            p_label = p_by_code.get(code)
            if p_label is None:
                continue  # no paper counterpart at this code -- can't judge staleness
            if _norm_paper_text(p_label) != _norm_build_text(o.get("label", "")):
                option_changed.add((b.item_name, code))
    return stem_changed, option_changed, new_rows


# --- PWA English-rekey mode ----------------------------------------------


def load_pwa_rekey_map(csv_path):
    """`old_english,new_english` -> {old: new}. Duplicate old_english with a
    conflicting new_english is a hard error."""
    mapping = {}
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            old = (row.get("old_english") or "").strip()
            new = (row.get("new_english") or "").strip()
            if not old or not new:
                continue
            if old in mapping and mapping[old] != new:
                raise ValueError(f"{csv_path}: duplicate old_english {old!r} with conflicting new_english")
            mapping[old] = new
    return mapping


def plan_pwa_rekey(locale_data: dict, rekey_map: dict) -> dict:
    """Flat English-text-keyed store: rename the key, carry the value
    verbatim. No drop/fallback step -- see module docstring."""
    kept, moved = {}, []
    for key, value in locale_data.items():
        new_key = rekey_map.get(key)
        if new_key is None:
            kept[key] = value
        else:
            moved.append((key, new_key))
    _check_collisions(kept, moved)
    return {"kept": kept, "moved": moved, "fellback": []}


# --- shared: logical rebuild (report/tests) + surgical apply (real files) --


def rebuild_locale_dict(locale_data: dict, plan: dict) -> dict:
    """Non-surgical reconstruction of the post-plan dict (kept + moved).
    Used for report generation and for testing plan correctness directly.
    Real file writes (`--apply`) go through the surgical text editors below
    instead, to avoid reformatting the whole file (see module docstring)."""
    out = dict(plan["kept"])
    for old_key, new_key in plan["moved"]:
        out[new_key] = locale_data[old_key]
    return out


_KEY_LINE_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"(\s*:\s*)')
_TRAILING_COMMA_RE = re.compile(r',(\s*\r?\n\s*\})')


def surgical_rejoin_scoped_text(text: str, moved: list, fellback: list):
    """Line-anchored rename/delete for a CSPro name-scoped locale file's raw
    text (adapted from bridge_check.py's strip_item_keys). Returns
    (new_text, applied_moves, applied_drops) -- the OLD keys actually found
    and edited, for the caller's equality check against the plan before
    writing."""
    move_map = dict(moved)
    drop_keys = {k for k, _ in fellback}
    applied_moves, applied_drops = [], []
    out_lines = []
    for line in text.splitlines(keepends=True):
        m = _KEY_LINE_RE.match(line)
        if m:
            key = json.loads('"' + m.group(2) + '"')
            if key in drop_keys:
                applied_drops.append(key)
                continue
            if key in move_map:
                new_key_enc = json.dumps(move_map[key], ensure_ascii=False)[1:-1]
                out_lines.append(m.group(1) + '"' + new_key_enc + '"' + m.group(3) + line[m.end():])
                applied_moves.append(key)
                continue
        out_lines.append(line)
    new_text = "".join(out_lines)
    new_text = _TRAILING_COMMA_RE.sub(r'\1', new_text)
    return new_text, applied_moves, applied_drops


def surgical_rejoin_text_keys(text: str, moved: list):
    """Same idea as surgical_rejoin_scoped_text but for the PWA flat
    English-text-keyed store: rename only, never deletes a line (PWA mode
    has no drop step), so no trailing-comma repair is needed."""
    move_map = dict(moved)
    applied = []
    out_lines = []
    for line in text.splitlines(keepends=True):
        m = _KEY_LINE_RE.match(line)
        if m:
            key = json.loads('"' + m.group(2) + '"')
            if key in move_map:
                new_key_enc = json.dumps(move_map[key], ensure_ascii=False)[1:-1]
                out_lines.append(m.group(1) + '"' + new_key_enc + '"' + m.group(3) + line[m.end():])
                applied.append(key)
                continue
        out_lines.append(line)
    return "".join(out_lines), applied


# --- report ----------------------------------------------------------------


def summarize_plan(plan: dict):
    """carried = every kept key that isn't the structural `_meta` marker,
    plus every moved key -- computed directly from the plan (fix round 1:
    a key-prefix heuristic here previously double-counted `_meta` as
    carried, ~+7 across the fleet, and undercounted any PWA English-text
    key that happens to contain a literal colon)."""
    carried = sum(1 for k in plan["kept"] if k != "_meta") + len(plan["moved"])
    return carried, len(plan["fellback"])


def write_report(inst, mode, per_locale_plans: dict, new_rows: list, out_path: Path, dry_run: bool = True):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {inst} — translation carryover report (mode: {mode})",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "DRY RUN — no files written" if dry_run else "APPLIED",
        "",
        "## Per-locale summary",
        "",
        "| locale | carried | fell-back |",
        "|---|---|---|",
    ]
    total_carried = total_fellback = 0
    fellback_union = {}
    for loc in LOCALES:
        plan = per_locale_plans.get(loc)
        if plan is None:
            lines.append(f"| {loc} | (file not found) | |")
            continue
        carried, fellback = summarize_plan(plan)
        total_carried += carried
        total_fellback += fellback
        lines.append(f"| {loc} | {carried} | {fellback} |")
        for key, reason in plan["fellback"]:
            fellback_union.setdefault(key, reason)
    lines += [
        "",
        f"**Totals:** carried {total_carried}, fell-back {total_fellback} "
        f"(summed across {len(LOCALES)} locale files), new {len(new_rows)}.",
        "",
        "## Fell-back (English shown now — needs re-translation; this is the ASPSI work order together with New below)",
        "",
    ]
    if fellback_union:
        for key, reason in sorted(fellback_union.items()):
            lines.append(f"- `{key}` — {reason}")
    else:
        lines.append("(none)")
    lines += ["", "## New (paper items with no old-build counterpart)", ""]
    if new_rows:
        for r in new_rows:
            lines.append(f"- qnum {r.qnum or '(none)'}: \"{r.stem[:120]}\"")
    else:
        lines.append("(none)")
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"carried": total_carried, "fellback": total_fellback, "new": len(new_rows), "fellback_keys": fellback_union}


# --- CLI ---------------------------------------------------------------


def _prepare_cspro_write(path: Path, plan: dict) -> str:
    """Compute + validate the post-plan surgical text for `path` WITHOUT
    writing it (plan-then-write: see module docstring "Atomicity"). Raises
    ValueError on any equality-gate mismatch or invalid JSON, so a caller
    driving all 7 locales can abort the whole instrument before any file is
    touched. `newline=""` disables newline translation on read (see module
    docstring "Newline discipline")."""
    text = path.read_text(encoding="utf-8", newline="")
    new_text, applied_moves, applied_drops = surgical_rejoin_scoped_text(text, plan["moved"], plan["fellback"])
    expected_moves = {k for k, _ in plan["moved"]}
    expected_drops = {k for k, _ in plan["fellback"]}
    if set(applied_moves) != expected_moves or set(applied_drops) != expected_drops:
        raise ValueError(
            f"{path}: surgical edit mismatch -- expected moves {expected_moves}, got {set(applied_moves)}; "
            f"expected drops {expected_drops}, got {set(applied_drops)}"
        )
    json.loads(new_text)  # validate before writing
    return new_text


def _prepare_pwa_write(path: Path, plan: dict) -> str:
    """Same idea as _prepare_cspro_write for the PWA flat store."""
    text = path.read_text(encoding="utf-8", newline="")
    new_text, applied = surgical_rejoin_text_keys(text, plan["moved"])
    expected = {k for k, _ in plan["moved"]}
    if set(applied) != expected:
        raise ValueError(f"{path}: surgical rename mismatch -- expected {expected}, applied {set(applied)}")
    json.loads(new_text)
    return new_text


def _commit_write(path: Path, new_text: str) -> None:
    """The only place this module writes a real locale file. `newline=""`
    disables write-side newline translation -- without it, Path.write_text
    on Windows silently turns every `\\n` into `\\r\\n`, flipping an
    LF-only fleet to CRLF even on lines this tool never touched (fix
    round 1, reviewer-caught -- see module docstring)."""
    path.write_text(new_text, encoding="utf-8", newline="")


def main():
    ap = argparse.ArgumentParser(description="Aug-17 migration: translation locale key mover + carryover reporter")
    ap.add_argument("instrument", choices=["F1", "F2", "F3", "F4"])
    ap.add_argument("--map", type=Path, default=None, help="rename/rekey CSV (required unless --stale-from-tables)")
    ap.add_argument("--pwa", action="store_true", help="PWA English-rekey mode (F2)")
    ap.add_argument("--stale-from-tables", action="store_true", help="derive drops from normalized paper/build tables (F3/F4)")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run/report only)")
    ap.add_argument("--cspro-dir", type=Path, default=MAIN_CSPRO, help="CSPro root for F{n}/translations/ (CSPro modes)")
    ap.add_argument("--pwa-dir", type=Path, default=PWA_TRANSLATIONS_DEFAULT, help="PWA translations dir (--pwa mode)")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="instruments-aug17-extract dir (--stale-from-tables)")
    ap.add_argument("--report", type=Path, default=None, help="override report output path")
    args = ap.parse_args()

    if args.pwa and args.stale_from_tables:
        raise SystemExit("--pwa and --stale-from-tables are mutually exclusive")

    try:
        if args.pwa:
            _run_pwa(args)
        elif args.stale_from_tables:
            _run_cspro(args, stale=True)
        else:
            _run_cspro(args, stale=False)
    except ValueError as e:
        raise SystemExit(str(e))


def _run_pwa(args):
    if args.map is None:
        raise SystemExit("--pwa mode requires --map maps/F2-english-rekey.csv")
    if not args.map.exists():
        raise SystemExit(
            f"--map {args.map} not found. Task 3.3 (F2 translations re-key + audit) has not produced this "
            "file yet -- pass a fixture map to exercise this mode meanwhile."
        )
    rekey_map = load_pwa_rekey_map(args.map)
    per_locale_plans = {}
    pending_writes = []  # [(path, new_text)] -- plan-then-write, see module docstring "Atomicity"
    for loc in LOCALES:
        path = args.pwa_dir / f"{loc}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        plan = plan_pwa_rekey(data, rekey_map)
        per_locale_plans[loc] = plan
        if args.apply:
            pending_writes.append((path, _prepare_pwa_write(path, plan)))

    if args.apply:
        for path, new_text in pending_writes:
            _commit_write(path, new_text)
            print(f"  wrote {path}")

    out_path = args.report or (args.data_dir / "reports" / f"{args.instrument}-translation-carryover.md")
    stats = write_report(args.instrument, "pwa-rekey", per_locale_plans, [], out_path, dry_run=not args.apply)
    print(f"{args.instrument} --pwa: carried {stats['carried']}, moved across {len(per_locale_plans)} locale file(s). report -> {out_path}")


def _run_cspro(args, stale: bool):
    new_rows = []
    if stale:
        paper_rows = read_csv(args.data_dir / "normalized" / f"{args.instrument}-paper.csv")
        build_rows = read_csv(args.data_dir / "normalized" / f"{args.instrument}-build.csv")
        stem_changed, option_changed, new_rows = compute_stale_from_tables(args.instrument, paper_rows, build_rows)
        rename_map = {}
        mode_label = "stale-from-tables"
    else:
        if args.map is None:
            raise SystemExit("CSPro rename mode requires --map maps/F{n}-renames.csv")
        if not args.map.exists():
            raise SystemExit(f"--map {args.map} not found.")
        rename_map, stem_changed = load_rename_map(args.map)
        option_changed = set()  # per-code drop for rename mode: see load_rename_map docstring (future extension)
        mode_label = "rename"

    per_locale_plans = {}
    pending_writes = []  # [(path, new_text)] -- plan-then-write, see module docstring "Atomicity"
    for loc in LOCALES:
        path = args.cspro_dir / args.instrument / "translations" / f"{loc}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        require_name_scoped(data, str(path))
        plan = plan_stale_drop(data, stem_changed, option_changed) if stale else plan_rejoin(data, rename_map, stem_changed, option_changed)
        per_locale_plans[loc] = plan
        if args.apply:
            pending_writes.append((path, _prepare_cspro_write(path, plan)))

    if args.apply:
        for path, new_text in pending_writes:
            _commit_write(path, new_text)
            print(f"  wrote {path}")

    out_path = args.report or (args.data_dir / "reports" / f"{args.instrument}-translation-carryover.md")
    stats = write_report(args.instrument, mode_label, per_locale_plans, new_rows, out_path, dry_run=not args.apply)
    print(
        f"{args.instrument} {mode_label}: carried {stats['carried']}, fell-back {stats['fellback']}, "
        f"new {stats['new']} across {len(per_locale_plans)} locale file(s). report -> {out_path}"
    )


if __name__ == "__main__":
    main()
