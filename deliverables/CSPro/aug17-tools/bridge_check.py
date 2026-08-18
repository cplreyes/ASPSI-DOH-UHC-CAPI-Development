#!/usr/bin/env python3
"""
Aug-17 migration: locale-bridge sanity check + fixer.

The 2026-08-17 name-scoped translation migration (see each instrument's
translations/*.json `_meta`) bridged the legacy English-text-keyed archives
(translations/legacy-textkey-2026-08-17/<loc>.json) into item-name-scoped
files (translations/<loc>.json, `item:NAME` keys). This script re-derives
each item's canonical English label from the built .dcf (JSON) and checks it
against three failure modes found by hand during Task 0.1:

  Rule A (mismatch)   scoped `item:NAME` value differs from
                      legacy[en_label] even though a legacy entry exists.
                      NOT AUTO-FIXED. First implementation assumed legacy was
                      ground truth and auto-copied it over on any mismatch —
                      wrong. Of 50 real A-mismatches found across the fleet,
                      45 have the current scoped value ALREADY correct/
                      complete, with legacy carrying an extra glued-on tail
                      (the next question's stem, or a value-set option list,
                      bleeding in — a pre-cleanup artifact of the legacy
                      archive, not a defect in the current file). Copying
                      legacy over current in those cases would be a
                      regression. Only ~5 rows show the opposite: current
                      is genuinely truncated (cut off mid-sentence) and
                      legacy completes it — but even there, copying the
                      FULL legacy value risks reintroducing that same
                      glued-tail problem (observed directly on
                      F3/war/Q135_SAT_OVERALL_TIME). Properly trimming to
                      the correct sentence boundary is translation-content
                      repair work, out of scope for a Task-0.1 sanity pass.
                      Every A-mismatch is reported with a heuristic
                      `subtype` (prefix-truncated / suffix-truncated /
                      clean-extra-tail / ambiguous) for human triage.

  Rule B (admin-leak) FIELD_CONTROL is a CAPI-only administrative record
                      (enumerator/editor/visit-date housekeeping) present in
                      all three instruments with IDENTICAL English labels.
                      F3's legacy archive carries clean, sensible
                      translations for these fields (e.g. "Pangalan ng
                      Tagapagsiyasat" for Enumerator's Name); F1 and F4's
                      legacy archives carry leaked, out-of-place fragments
                      for the SAME field names ("Resulta" / "Resulta
                      aCodes: 1") that don't correspond to any real
                      translation. A pure length-ratio heuristic was tried
                      first and rejected: "Resulta aCodes: 1" (18 chars) is
                      LONGER than the correct concise "Sinuri ni" (9 chars),
                      so "shorter = corrupt" mis-detects here. Flags on
                      literal markers verified by hand against the actual
                      corruption: a SUBSTRING match on "resulta"
                      (case-insensitive — broadened after fix-round-1 review
                      found variants like "(Nagan ti Enumerator) Resulta" and
                      "Nagan ti Enumerator) Result(Resulta" that the original
                      exact-match `== "Resulta"` missed), or any value
                      containing "acodes:" (case-insensitive; an unambiguous
                      leaked ticket/governance annotation, never legitimate
                      target-language content). Scoped to the FIELD_CONTROL
                      record specifically — these are pure CAPI housekeeping
                      fields with no printed-paper equivalent, so a
                      substring match here carries much lower false-positive
                      risk than it would against ordinary content fields.
                      Fix: delete (fall back to English) — never borrow a
                      sibling instrument's unreviewed content across
                      instruments.

  Rule C (glued text) Two independently-justified sub-checks, combined with
                      OR (both delete on fire):
                      (a) contains a raw English cover-sheet field-label
                      fragment ("Email address", "Mobile Number",
                      "Questionnaire No", "Numero ng Telepono") — e.g.
                      RESP_POSITION in F1 fil.json: "Posisyon, Opisina
                      Email address _______ Mobile Number Numero ng
                      Telepono Questionnaire No". No length gate — these
                      phrases are specific enough on their own (verified: a
                      full sweep for these markers across the whole fleet
                      turns up nothing but genuine corruption, including the
                      44- and 76-char F1/ceb and F1/hil RESP_POSITION rows
                      the original `len > 100` gate was hiding). Deliberately
                      case-SENSITIVE, Title-Case only: an earlier attempt
                      made this case-insensitive and it produced a false
                      positive on F4/fil Q99_PHONE_ADVICE_CLOSED, a clean,
                      correct sentence that legitimately contains the
                      ordinary lowercase phrase "numero ng telepono" ("phone
                      number") as normal Filipino vocabulary, not a leaked
                      cover-sheet fragment — Title-Case is what actually
                      distinguishes the leaked-label pattern from ordinary
                      sentence content built from the same words.
                      (b) contains a 5+ underscore run AND is over 100
                      chars. The underscore run alone is NOT safe to flag —
                      "Month _________ Year__________" is a legitimate,
                      widely-used bilingual fill-in-the-blank convention for
                      date fields (confirmed clean at 78-89 chars across
                      several F3/F4 locales) — but every confirmed-corrupt
                      row carrying only an underscore run as its signal
                      (duplicated blank-fill labels, or a leaked English
                      question fragment bleeding in) was 103-186 chars, so
                      the length gate is kept here specifically as the
                      guard that separates the two, not dropped as a first
                      instinct might suggest.

  Rule D (orphaned    A value that (after stripping) STARTS with an
  tag fragment)       orphaned placeholder-tag close — `_input]` or
                      `_INPUT)` (case-insensitive) at position 0, with no
                      matching `[` opening bracket anywhere before it in the
                      string. Found on F3 FACILITY_NAME (Q88's prompt-fill
                      value) across all 7 locales, all with distinct garbage
                      tails ("_INPUT)? Days Minutes", "_input] the facility
                      you", "_INPUT) Days Adlaw Minutes Minutos") — a
                      truncated/mis-sliced templated tag, invisible to
                      Rules A-C (legacy carries the identical corruption, so
                      Rule A is silent too; it's not in FIELD_CONTROL, and
                      has none of Rule C's markers). IMPORTANT: this marker
                      is NOT safe as a general "contains an orphaned tag"
                      check — `[facility_name_input]` and similar bracketed
                      placeholders appear correctly, mid-sentence, in dozens
                      of OTHER legitimate items (Q66/Q88/Q143/Q144/Q162/Q172
                      all use it as an intentional prompt-fill). Anchoring
                      to "value literally starts with the orphaned closing
                      fragment" is what keeps this specific — verified
                      against the full fleet: exactly 7 hits, all
                      FACILITY_NAME, zero collisions with the ~30 legitimate
                      mid-sentence placeholder usages.

Rule-completeness caveat: these four rules were derived from the specific
corrupt examples found by hand plus one review round that independently
found 3 more variants the first pass missed. They are NOT proven exhaustive
— absence from this tool's report is not proof a row is clean. Treat "0
Rule-B/C/D defects" as "none of the KNOWN corruption patterns detected,"
not as a completeness guarantee, when Task 0.4 or later tasks build on this.

Usage:
    py bridge_check.py --check                  # report only, no writes
    py bridge_check.py --apply --out DIR         # write fixed <loc>.json
                                                  # per instrument into DIR
                                                  # (mirrors F{n}/translations/
                                                  # layout); does NOT touch
                                                  # MAIN directly.

Scope: `item:` keys only (per Task 0.1 Step 5 — vs:/val: keys are out of
scope for this pass).

Apply-mode implementation note: fixes are applied as a SURGICAL, line-level
text edit (find the `"item:NAME": "..."` line, delete it, fix a dangling
trailing comma if it was the last key) — never a full parse + `json.dump`
re-serialization. The translation files in this repo have inconsistent
indentation across locales (some 1-space, some 2-space) because they were
generated by different tools/passes at different times; a naive
load-then-json.dump round trip reformats the ENTIRE file to a uniform style,
producing a multi-thousand-line diff for a 2-row fix and burying the actual
change. First implementation of this script did exactly that and had to be
corrected after the fact (see `git log` on this file / Task 0.1 report).
"""
import argparse
import json
import re
from pathlib import Path

MAIN = Path(r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development")
CSPRO = MAIN / "deliverables" / "CSPro"

INSTRUMENTS = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
}
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]

GLUED_FIELD_LABEL_MARKERS = re.compile(
    r"Email address|Mobile Number|Questionnaire No|Numero ng Telepono"
)  # deliberately case-SENSITIVE, Title-Case only — see docstring false-positive note
UNDERSCORE_RUN = re.compile(r"_{5,}")
ADMIN_LEAK_MARKERS = re.compile(r"resulta|acodes:", re.IGNORECASE)
ORPHANED_TAG_START = re.compile(r"^_input[\)\]]", re.IGNORECASE)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strip_item_keys(text, keys_to_remove):
    """Surgically remove `"item:NAME": ...` lines from raw JSON text, keeping
    every other byte of the file untouched (no reformatting). Returns
    (new_text, list_of_keys_actually_removed)."""
    if not keys_to_remove:
        return text, []
    patterns = [(k, re.compile(r'^\s*"item:' + re.escape(k) + r'"\s*:')) for k in keys_to_remove]
    lines = text.splitlines(keepends=True)
    kept, removed = [], []
    for line in lines:
        matched = next((k for k, p in patterns if p.match(line)), None)
        if matched:
            removed.append(matched)
            continue
        kept.append(line)
    new_text = "".join(kept)
    # Fix a dangling trailing comma if the removed row was the last key
    # before the closing brace.
    new_text = re.sub(r',(\s*\r?\n\s*\})', r'\1', new_text)
    return new_text, removed


def dcf_item_map(instrument):
    """Return {item_name: (en_label, record_name)} for every item in the dcf,
    walking every level's records and id-items."""
    dcf_path = CSPRO / instrument / f"{INSTRUMENTS[instrument]}.dcf"
    d = load_json(dcf_path)
    out = {}
    for lvl in d.get("levels", []):
        ids = lvl.get("ids", {})
        for it in ids.get("items", []):
            en = next((l["text"] for l in it["labels"] if l["language"] == "EN"), None)
            out[it["name"]] = (en, "IDS")
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                en = next((l["text"] for l in it["labels"] if l["language"] == "EN"), None)
                out[it["name"]] = (en, rec["name"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only (default)")
    ap.add_argument("--apply", action="store_true", help="write fixed files")
    ap.add_argument("--out", type=Path, help="output dir for --apply (mirrors F{n}/translations/<loc>.json)")
    args = ap.parse_args()
    apply_mode = args.apply
    if apply_mode and not args.out:
        raise SystemExit("--apply requires --out DIR")

    # Pass 1: build per-instrument item maps + collect FIELD_CONTROL legacy
    # values across instruments/locales for the Rule-B cross-instrument check.
    item_maps = {ins: dcf_item_map(ins) for ins in INSTRUMENTS}
    fc_legacy_by_item_locale = {}  # (item_name, locale) -> {instrument: value}
    legacy_cache = {}  # (instrument, locale) -> dict
    for ins in INSTRUMENTS:
        for loc in LOCALES:
            legacy_path = CSPRO / ins / "translations" / "legacy-textkey-2026-08-17" / f"{loc}.json"
            legacy_cache[(ins, loc)] = load_json(legacy_path) if legacy_path.exists() else {}
    for ins, imap in item_maps.items():
        for name, (en, rec) in imap.items():
            if rec != "FIELD_CONTROL" or en is None:
                continue
            for loc in LOCALES:
                val = legacy_cache[(ins, loc)].get(en)
                if val is not None:
                    fc_legacy_by_item_locale.setdefault((name, loc), {})[ins] = val

    defects = []  # dicts: instrument, locale, item, en, rule, current, legacy, sibling_note
    delete_keys = {}  # (instrument, locale) -> [item names to surgically delete]

    for ins in INSTRUMENTS:
        imap = item_maps[ins]
        for loc in LOCALES:
            scoped_path = CSPRO / ins / "translations" / f"{loc}.json"
            scoped = load_json(scoped_path)
            legacy = legacy_cache[(ins, loc)]
            to_delete = []

            item_keys = [k for k in scoped.keys() if k.startswith("item:")]
            for key in item_keys:
                name = key[len("item:"):]
                current = scoped[key]
                en, rec = imap.get(name, (None, None))
                if en is None:
                    continue  # item not found in current dcf (renamed/removed) — out of scope here
                legacy_val = legacy.get(en)

                fired = None
                fix_value = None  # None => delete
                auto_apply = False

                # Rule A: mismatch against same-instrument legacy value. NOT
                # auto-applied (see module docstring "Rule A" note below) —
                # empirically the legacy archive is usually the MESSIER side
                # (extra glued-on tail from the next question/value-set, a
                # pre-cleanup artifact), not a clean ground truth. Blindly
                # copying it over would regress already-correct current
                # values. Reported with a heuristic subtype for triage only.
                if legacy_val is not None and legacy_val != current:
                    fired = "A-mismatch"
                    fix_value = legacy_val  # recorded for the report; NOT applied
                    auto_apply = False

                # Rule B: FIELD_CONTROL admin-leak — substring match (see
                # module docstring for why exact-match was too narrow).
                if fired is None and rec == "FIELD_CONTROL" and isinstance(current, str):
                    if ADMIN_LEAK_MARKERS.search(current):
                        fired = "B-admin-leak"
                        fix_value = None  # delete, do not borrow cross-instrument
                        auto_apply = True

                # Rule C: two independently-justified sub-checks (see
                # module docstring — the underscore-run sub-check keeps its
                # length gate on purpose; the field-label sub-check doesn't
                # need one).
                if fired is None and isinstance(current, str):
                    field_label_leak = GLUED_FIELD_LABEL_MARKERS.search(current)
                    underscore_leak = len(current) > 100 and UNDERSCORE_RUN.search(current)
                    if field_label_leak or underscore_leak:
                        fired = "C-glued-fragments"
                        fix_value = None
                        auto_apply = True

                # Rule D: orphaned placeholder-tag fragment (value starts
                # with an unmatched closing tag — see module docstring for
                # why this is anchored to the START of the value rather than
                # a bare "contains" check).
                if fired is None and isinstance(current, str) \
                        and ORPHANED_TAG_START.match(current.strip()):
                    fired = "D-orphaned-tag"
                    fix_value = None
                    auto_apply = True

                if fired:
                    note = ""
                    subtype = ""
                    if fired == "B-admin-leak":
                        sib_desc = "; ".join(f"{k}={v!r}" for k, v in fc_legacy_by_item_locale[(name, loc)].items())
                        note = f"siblings: {sib_desc}"
                    if fired == "A-mismatch":
                        cur_s, leg_s = current.strip(), legacy_val.strip()
                        ends_ok = cur_s.endswith(("?", ".", ")"))
                        if not ends_ok and leg_s.startswith(cur_s):
                            subtype = "prefix-truncated (current cut off mid-sentence; legacy completes it — candidate for hand-trim fix)"
                        elif leg_s.endswith(cur_s) and not leg_s.startswith(cur_s):
                            subtype = "suffix-truncated (current missing its opening clause; legacy has it — candidate for hand-trim fix)"
                        elif ends_ok and leg_s.startswith(cur_s):
                            subtype = "clean-extra-tail (current already correct/complete; legacy carries a pre-cleanup glued tail — NO ACTION)"
                        else:
                            subtype = "ambiguous (neither a clean prefix nor suffix relationship — needs eyeball review)"
                    defects.append({
                        "instrument": ins, "locale": loc, "item": name, "en_label": en,
                        "rule": fired, "current": current, "legacy": legacy_val,
                        "fix": ("auto-delete" if (auto_apply and fix_value is None)
                                else "not-auto-applied" if fired == "A-mismatch"
                                else "legacy-value"),
                        "subtype": subtype,
                        "note": note,
                    })
                    if apply_mode and auto_apply and fix_value is None:
                        to_delete.append(name)
                    # Note: no Rule currently sets auto_apply=True with a
                    # non-None fix_value (B/C/D are always deletions). If
                    # that ever changes, this surgical approach would need a
                    # value-replace mode too — not implemented, by design:
                    # see the Rule-A docstring on why "copy legacy value" is
                    # unsafe to automate.

            if apply_mode and to_delete:
                delete_keys[(ins, loc)] = to_delete

    fixed_files = {}  # (instrument, locale) -> new raw text
    if apply_mode:
        for (ins, loc), keys in delete_keys.items():
            scoped_path = CSPRO / ins / "translations" / f"{loc}.json"
            text = scoped_path.read_text(encoding="utf-8")
            new_text, removed = strip_item_keys(text, keys)
            if set(removed) != set(keys):
                raise SystemExit(f"surgical removal mismatch for {ins}/{loc}: "
                                  f"expected {keys}, removed {removed}")
            json.loads(new_text)  # validate before writing
            fixed_files[(ins, loc)] = new_text

    # Report
    print(f"Scanned {len(INSTRUMENTS)} instruments x {len(LOCALES)} locales.")
    print(f"Total defects found: {len(defects)}")
    by_ins_loc = {}
    for d in defects:
        by_ins_loc.setdefault((d["instrument"], d["locale"]), 0)
        by_ins_loc[(d["instrument"], d["locale"])] += 1
    for (ins, loc), n in sorted(by_ins_loc.items()):
        print(f"  {ins}/{loc}.json: {n} defect(s)")

    if apply_mode:
        for (ins, loc), new_text in fixed_files.items():
            out_path = args.out / ins / "translations" / f"{loc}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(new_text.encode("utf-8"))
        print(f"Wrote {len(fixed_files)} fixed file(s) under {args.out} "
              f"(only files with an actual deletion — untouched files are not rewritten)")

    return defects


if __name__ == "__main__":
    main()
