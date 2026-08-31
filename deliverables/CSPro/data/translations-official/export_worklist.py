#!/usr/bin/env python3
"""export_worklist.py - the translator worklist ASPSI gets after the Aug-21 import.

One row per (instrument, locale, key) that is still NOT carrying an Aug-21 translation,
plus the rows that carry one with a cosmetic residue, plus what the papers themselves have
to fix. Six sections, one sheet each in the workbook and one `status` value each in the CSV:

  worklist      every row of `out-aug21/<INST>/<loc>_flagged.json` - the extractor's own QA
                flags. `status` = `echo-english` when the paper reprints the English under
                the anchor, `flagged` otherwise. `unmatched` rows come from a
                `apply_aug21.py --unmatched` dry-run report: a dictionary anchor the paper
                was never found under.
  held          keys `aug21-overrides.json` says the import must NOT write - `keep: null`
                (never written, the map keeps whatever it had), `keep: ""` (renders
                English) and `remove: true` (the key is DELETED from the map, so the
                English label renders - those rows read `removed: <reason>`, never
                `held:`). Locale-scoped entries are expanded to one row per locale, so
                ASPSI sees exactly which papers a hold covers.
  accepted      the override rows that DO carry text: the value the wave kept or accepted,
                with the reason it was kept.
  residual      the CLEAN pairs - rows that were imported and never flagged, but still read
                with a stray glyph, an unbalanced bracket or a dangling tail. These never
                reach `_flagged.json`, which is why they need their own section.
  paper-defects defects in the printed questionnaires. Not fixable in CAPI - each row names
                the paper and what ASPSI has to correct.
  follow-ups    work already recorded against the next builds, so a translator does not
                re-report it.

An untranslated cell is NOT a build defect: the Aug-21 paper prints no translation under
that anchor, and nothing may be invented. That is what `empty` and `not-in-paper` mean, and
together they are most of the worklist.

    python export_worklist.py --xlsx ../../translator-worklist-aug21.xlsx \
                              --csv  ../../translator-worklist-aug21.csv
"""
import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSPRO = HERE.parents[1]
F2_MAPS = CSPRO.parent / "F2" / "PWA" / "app" / "spec" / "translations"
# The residual scan imports anchor_extract (which imports cspro_helpers from CSPro/), the
# same two-entry path setup every other tool in this folder does.
for _p in (str(CSPRO), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

COLS = ["instrument", "locale", "key", "english", "extracted", "flags", "status"]
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
CSPRO_INSTRUMENTS = ("F1", "F3", "F4")
DCF_FILE = {"F1": "FacilityHeadSurvey.dcf", "F3": "PatientSurvey.dcf",
            "F4": "HouseholdSurvey.dcf"}
SECTIONS = ["worklist", "held", "accepted", "residual", "paper-defects", "follow-ups"]

# `note:const:_READ_ONE:FIL` / `icf:2:1:WAR` carry their locale in the key itself, so they
# never need (and never have) an entry-level "locales" list.
NOTE_LOCALE_RE = re.compile(r"^(?:note|icf):.+:([A-Za-z]{3})$")

# ------------------------------------------------------------------ residual shapes --
# The three glyph families the four patch notes record, plus the truncation heuristic
# `_residual.py` used on F1. `anchor_extract.truncated_tail` (the Task-40 detector) is added
# on top when the English label is available.
_OPENERS = '"“‘([{'
_LEAD_JUNK = '"“”‘’()[]{}.,:;-–—/\\|'
_TERMINAL_OK = '.?!:…)]}"”’%'


def residual_defects(en, tr, tail_check=None):
    """Reason names for the cosmetic residue on a CLEAN (never-flagged) pair, or [].

    Two of the five shapes - `no-terminal-punct` and the `dangling-tail` the Task-40
    detector finds - can only be judged against the English, so they are silently skipped
    when `en` is empty. `collect_residual()` therefore fills the English from three
    sources before calling this and reports what it still could not fill.
    """
    out = []
    tr = (tr or "").strip()
    if not tr:
        return out
    if tr.count("(") != tr.count(")"):
        out.append("unbalanced-paren")
    if tr.count("[") != tr.count("]"):
        out.append("unbalanced-bracket")
    if tr[0] in _LEAD_JUNK:
        out.append("stray-leading-glyph")
    if tr[-1] in _OPENERS:
        out.append("stray-trailing-glyph")
    if en and en.strip()[-1:] in ".?!:" and tr[-1] not in _TERMINAL_OK:
        out.append("no-terminal-punct")
    if tail_check is not None:
        reason = tail_check(en or "", tr)
        if reason:
            out.append("dangling-tail (%s)" % reason)
    return out


# ------------------------------------------------------------------- paper defects --
# Each entry becomes one row per selected key (or a single narrative row when it selects
# nothing). `selects` kinds: ("keys", [...]), ("override", <key regex>) - override entries
# governing this locale, ("flagged", <key regex>) and ("flag", <flag name>) - rows of the
# `_flagged.json` files, ("f2-held", None) - the F2 overrides that are `keep: null`.
# Sources: the four Aug-21 patch notes and TRANSLATION-STATUS-2026-08-27.md.
PAPER_DEFECTS = (
    {"id": "hil-f1-option4-stutter", "instrument": "F1", "locale": "hil",
     "selects": [("override", r"^val:Q\d+_1_UHC_ATTRIB_VS1:4$"),
                 ("keys", ["val:Q10_1_UHC_ATTRIB_VS1:4"])],
     "defect": "the Hiligaynon paper prints option 4 of the UHC-attribution list as "
               "'... ginatuyo sa masunod sa masunod nga 1-2 ka tuig' - 'sa masunod' is "
               "stuttered on the option row itself (Q10.1-Q35.1, 20 rows)",
     "action": "correct the Hiligaynon questionnaire; the other six papers are correct on "
               "the same option, so 19 rows were held rather than imported and Q10.1 has "
               "carried the stutter since the June-5 pack"},
    {"id": "war-f4-question-number-offset", "instrument": "F4", "locale": "war",
     "selects": [("keys", ["item:Q27_REFRIGERATOR", "vs:Q27_REFRIGERATOR_VS1",
                           "item:Q28_TELEVISION", "vs:Q28_TELEVISION_VS1",
                           "item:Q29_WASHING_MACHINE", "vs:Q29_WASHING_MACHINE_VS1",
                           "val:ENUM_RESULT_FINAL_VISIT_PICK_VS1:4"])],
     "defect": "the Waray paper's question numbering runs one behind the CAPI's on "
               "Q27/Q28/Q29 (printed 26./27./28.) and it collapses the four-option "
               "result-of-visit grid into one label, so the printed text may answer a "
               "different question",
     "action": "confirm which question each Waray row belongs to; Waray shows English on "
               "screen until a translator rules, and accepting all seven is one line"},
    {"id": "paper-number-mismatch", "instrument": None, "locale": None,
     "selects": [("flag", "paper-number-mismatch")],
     "defect": "the dialect paper prints a question number that does not match the CAPI's",
     "action": "re-check the numbering on these rows before the text is reused"},
    {"id": "f2-paper-misprints", "instrument": "F2", "locale": None,
     "selects": [("f2-held", None)],
     "defect": "three Aug-21 F2 pages carry a misprint the extractor cannot work around - "
               "the Bicolano page prints the option as 'YesIyo' with no space, the Ilocano "
               "page prints the No-Balance-Billing option as 'Patient does not pay any "
               "hospital billn', and the Hiligaynon Q82 Likert row is printed with only "
               "the local scale labels and no English stem to anchor on",
     "action": "reprint those rows; each is held (never imported) until the page is fixed"},
    {"id": "f3-115x-english-only", "instrument": "F3", "locale": None,
     "selects": [("flagged", r"^(?:item|vs|val):Q114[12]")],
     "defect": "the 115.1 / 115.2 inpatient-and-outpatient cost matrix rows are printed "
               "only in the English column on all seven papers, so the row labels extract "
               "with no local text at all; the Bicolano Q1142_HAS_OTHER stem carries the "
               "outpatient noun inside the inpatient question, and the Cebuano and "
               "Hiligaynon papers print no 115.2 gate stem",
     "action": "add the 115.1 / 115.2 matrix row labels to every dialect paper"},
    {"id": "f1-tagalog-page1-wrong-paragraph", "instrument": "F1", "locale": "fil",
     "selects": [],
     "defect": "F1-Tagalog page 1, paragraph 2 prints F3's English coverage sentence above "
               "the correct F1 Tagalog",
     "action": "correct the English side of the Tagalog F1 cover page; the build is "
               "unaffected"},
    {"id": "f3-hiligaynon-consent-older-variant", "instrument": "F3", "locale": "hil",
     "selects": [],
     "defect": "the F3-Hiligaynon consent page carries an older English variant - an extra "
               "privacy clause, no Php 100 token-of-appreciation sentence, and the "
               "'Nothing bad will happen ...' paragraph missing",
     "action": "re-issue the Hiligaynon consent page against the current English; two "
               "paragraphs stay English on-device until then (HIL ICF 21/23)"},
    {"id": "f3-tagalog-header-date", "instrument": "F3", "locale": "fil",
     "selects": [],
     "defect": "the F3-Tagalog header still reads 06/05 - the one paper of the 21 whose "
               "header was not re-stamped in the Aug-21 pack",
     "action": "re-stamp the header; it is still part of the Aug-21 delivery and the CAPI "
               "clearance line already stamps 08/21/2026, so do NOT change the build"},
    {"id": "tagalog-papers-are-bilingual", "instrument": None, "locale": "fil",
     "selects": [],
     "defect": "the Aug-21 Tagalog F3 and F4 papers are bilingual (English line with the "
               "Filipino gloss in brackets after it) where the other six are monolingual",
     "action": "no paper change needed - recorded so the layout is not mistaken for a "
               "defect; the extractor now drops the bracket pair on import"},
    {"id": "f3-repeated-phrases", "instrument": "F3", "locale": None, "selects": [],
     "defect": "the Ilocano paper stutters on Q54/Q55/Q57 ('kangrunaan a kangrunaan a "
               "mangipapaay') and the Waray paper prints the whole of Q16 twice",
     "action": "correct both papers"},
    {"id": "f3-scale-wording-inconsistent", "instrument": "F3", "locale": None,
     "selects": [],
     "defect": "the Bicolano and Hiligaynon Q131-Q135 satisfaction scales are inconsistent "
               "on the paper itself ('Maray na maray' / 'Bako maray' beside 'Dai "
               "kontento'; Hiligaynon prints 'Kotento' for 'Kontento')",
     "action": "settle one scale wording per language; the build ships the text as printed, "
               "because Aug-21 wins"},
    {"id": "missing-terminal-punctuation", "instrument": None, "locale": None,
     "selects": [],
     "defect": "sentence-final punctuation is missing on F1-Bicolano (2 of 1), F4-Bicolano "
               "(2 of 1) and F3/F4-Ilocano (1 of 0); F1-Bicolano also stops short of the "
               "English",
     "action": "restore the punctuation on the affected rows"},
    {"id": "f2-tagalog-q2-english-only", "instrument": "F2", "locale": "fil",
     "selects": [],
     "defect": "F2 Section A Q2 ('What type of employment do you have at this health "
               "facility?') is followed straight by the ballot boxes on the Tagalog paper, "
               "with no Tagalog under it",
     "action": "add the Tagalog for Q2; nothing may be invented, so the screen stays "
               "English until the paper carries it"},
    {"id": "f1-ilocano-questions-in-english", "instrument": "F1", "locale": "ilo",
     "selects": [("keys", ["item:Q74_REGISTERED_PATIENTS", "item:Q91_BUCAS_SERVICES",
                           "vs:Q91_BUCAS_SERVICES_VS1"])],
     "defect": "the Ilocano F1 paper prints Q74 and Q91 in English, so the only "
               "'translation' on offer is the English itself",
     "action": "add the Ilocano for Q74 and Q91"},
)

# ---------------------------------------------------------------------- follow-ups --
# Already recorded against the next builds (TRANSLATION-STATUS-2026-08-27.md), so a
# translator reading the worklist does not re-report them.
FOLLOW_UPS = (
    ("F4", "f4-3.2.3-reimport",
     "F4 3.2.3 - re-import the 74 held rows the final extractor now clears", "build",
     "measured on the shipped v3.2.2 maps; the maps were not touched"),
    ("F1", "f1-4.1.1-reimport",
     "F1 4.1.1 - re-import the 68 rows the final extractor now changes: 7 x "
     "val:Q62_ENROLL_RESPONSIBILITY_VS1:02 (six recover 'Pasilidad') plus 61 orphan-glyph "
     "rows", "build",
     "F1 v4.1.0 shipped on the older extractor"),
    (None, "dangling-tail-values",
     "85 dangling-tail values are live in the F1 and F4 maps and 113 in F3", "build",
     "cleared by the same re-import; listed row by row in the residual section"),
    ("F3", "f3-115x-label-composition",
     "F3 115.x generator-side label composition (14 keys x 7 locales plus "
     "Q1142_HAS_OTHER x 3)", "build",
     "compose '<stem> - <option>' from the translated parts; no paper span can anchor the "
     "composite label"),
    ("F3", "q1141-other-txt-gate",
     "PROC Q1141_OTHER_TXT gates on row 1 instead of row 6 (errmsg 1177)", "UAT ticket",
     "pre-existing, found while aligning the Aug-21 English"),
    ("F3", "patient-type-fragments",
     "val:PATIENT_TYPE_VS1:1 / :2 carry neighbouring paper text in 6 of 7 locales and HIL "
     "item:Q7_SEX keeps an English anchor head", "UAT ticket",
     "pre-existing June-5 text on the case-start ROUTING field; fix is a locale-scoped "
     "hold plus an extractor rule"),
)


# ------------------------------------------------------------------------- loading --
def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _row(instrument, locale, key, english, extracted, flags, status, section):
    return {"instrument": instrument, "locale": locale, "key": key, "english": english,
            "extracted": extracted, "flags": flags, "status": status, "section": section}


def load_flagged(out_root):
    """{instrument: {locale: [flagged row, ...]}} from `out-aug21/<INST>/<loc>_flagged.json`.

    F1/F3/F4 rows carry a name-scoped `key`; F2 rows are keyed by their English string
    (the PWA store is flat English-keyed), so `key` falls back to `en`.
    """
    out = OrderedDict()
    root = Path(out_root)
    if not root.is_dir():
        return out
    for inst_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        per_locale = OrderedDict()
        for f in sorted(inst_dir.glob("*_flagged.json")):
            per_locale[f.name.split("_")[0]] = _read_json(f)
        if per_locale:
            out[inst_dir.name] = per_locale
    return out


def english_index(flagged):
    """{instrument: {key: English label}} harvested from the flagged rows.

    The overrides file records the key and the reason but never the English, and that is
    the one column a translator cannot work without.
    """
    idx = {}
    for inst, per_locale in flagged.items():
        seen = idx.setdefault(inst, {})
        for rows in per_locale.values():
            for r in rows:
                key = r.get("key") or r.get("en") or ""
                if key and key not in seen and r.get("en"):
                    seen[key] = r["en"]
    return idx


def dict_english(dcf_path):
    """{key: English label} for EVERY labels-bearing node of a written dcf.

    `anchor_extract.dcf_anchors()` keeps only the three ANCHOR_KINDS it can look for on
    paper (`item:` / `vs:` / `val:`), so `record:`, `level:` and `dict:` keys - which the
    translation maps DO carry - come back with no English at all. Same walker, same key
    contract, no kind filter: this is the second English source the residual section falls
    back to.
    """
    from cspro_helpers import walk_labeled_nodes   # local: needs CSPro/ on sys.path
    out = {}
    for key, node in walk_labeled_nodes(_read_json(dcf_path)):
        labels = node.get("labels") or []
        if not labels or labels[0].get("language") not in (None, "EN"):
            continue
        text = (labels[0].get("text") or "").strip()
        if text:
            out[key] = text
    return out


def merged_english(*sources):
    """One {key: English} from several indexes - the first non-empty value wins."""
    out = {}
    for source in sources:
        for key, text in (source or {}).items():
            if text and not out.get(key):
                out[key] = text
    return out


def _override_locales(key, entry):
    """The locales one override entry governs, as a list (["*"] = every locale)."""
    if entry.get("locales"):
        return list(entry["locales"])
    m = NOTE_LOCALE_RE.match(key)
    if m:
        return [m.group(1).lower()]
    return ["*"]


def _override_row(inst, loc, key, entry, english):
    keep = entry.get("keep")
    reason = entry.get("reason", "")
    if entry.get("remove"):             # deleted from the map - NOT the same as held
        flags, extracted, section = "removed: " + reason, "", "held"
    elif keep is None:
        flags, extracted, section = "held: " + reason, "", "held"
    elif keep == "":
        flags, extracted, section = "renders English: " + reason, "", "held"
    else:
        flags, extracted, section = reason, keep, "accepted"
    return _row(inst, loc, key, english, extracted, flags, "override", section)


# ------------------------------------------------------------- section collectors --
def collect_flagged(out_root, overrides_path, report_path=None):
    """The worklist / held / accepted sections: flagged rows, unmatched anchors, overrides."""
    flagged = load_flagged(out_root)
    ens = english_index(flagged)
    rows = []
    for inst, per_locale in flagged.items():
        for loc, entries in per_locale.items():
            for r in entries:
                flags = r.get("flags") or []
                rows.append(_row(
                    inst, loc, r.get("key") or r.get("en", ""), r.get("en", ""),
                    r.get("tr", ""), ",".join(flags),
                    "echo-english" if flags == ["echo-english"] else "flagged", "worklist"))

    if report_path and Path(report_path).exists():
        for inst, per_locale in _read_json(report_path).items():
            for loc, r in per_locale.items():
                for key in r.get("unmatched", []):
                    rows.append(_row(inst, loc, key, ens.get(inst, {}).get(key, ""), "",
                                     "no paper span found under this anchor", "unmatched",
                                     "worklist"))

    overrides = _read_json(overrides_path) if Path(overrides_path).exists() else {}
    for inst, block in overrides.items():
        if inst.startswith("_"):
            continue
        if inst == "F2":
            for loc, per_key in block.items():
                for key, entry in per_key.items():
                    rows.append(_override_row(inst, loc, key, entry, key))
        else:
            for key, entry in block.items():
                english = ens.get(inst, {}).get(key, "")
                for loc in _override_locales(key, entry):
                    rows.append(_override_row(inst, loc, key, entry, english))
    return rows


def collect_residual(out_root, cspro_root=CSPRO, f2_maps=F2_MAPS, warn=True):
    """The residual section: imported pairs that were never flagged but still read wrong.

    Truncations and stray-glyph rows are CLEAN pairs - `qa_flags()` passed them, so they are
    absent from every `_flagged.json` and would leave the worklist silent about them.
    `cspro_root=None` skips the F1/F3/F4 leg (which needs the built dictionaries for the
    English labels); `f2_maps=None` skips F2.

    The English is resolved from three indexes in order - the paper anchors, then every
    labelled node of the dcf (`record:` keys included), then the English the extractor
    already recorded on the flagged rows. A map key that survives all three no longer
    exists in the live dictionary (a stale key from an earlier numbering), so no English
    for it exists anywhere: those keys are COUNTED and reported, because two of the five
    residual shapes cannot run without the English and a silent skip is what hid them.
    `warn=False` keeps the count off stdout (tests).
    """
    flagged = load_flagged(out_root)
    from_flagged = english_index(flagged)
    rows, gaps = [], OrderedDict()
    if cspro_root is not None:
        import anchor_extract as ae            # local: needs deliverables/CSPro on sys.path
        root = Path(cspro_root)
        for inst in CSPRO_INSTRUMENTS:
            dcf = root / inst / DCF_FILE[inst]
            if not dcf.exists():
                continue
            ens = merged_english(ae.dcf_anchors(str(dcf)), dict_english(str(dcf)),
                                 from_flagged.get(inst, {}))
            missing = set()
            for loc in LOCALES:
                mp = root / inst / "translations" / (loc + ".json")
                if not mp.exists():
                    continue
                seen = {r.get("key") for r in flagged.get(inst, {}).get(loc, [])}
                rows += _residual_rows(inst, loc, _read_json(mp), ens, seen,
                                       ae.truncated_tail, missing)
            if missing:
                gaps[inst] = len(missing)
    if f2_maps is not None:
        maps = Path(f2_maps)
        missing = set()
        for loc in LOCALES:
            mp = maps / (loc + ".json")
            if not mp.exists():
                continue
            seen = {r.get("en") for r in flagged.get("F2", {}).get(loc, [])}
            # F2 keys ARE the English, so the map doubles as its own English index.
            store = _read_json(mp)
            rows += _residual_rows("F2", loc, store, {k: k for k in store}, seen, None,
                                   missing)
        if missing:
            gaps["F2"] = len(missing)
    if warn:
        for inst, n in gaps.items():
            print("%s: %d keys had no English label - punctuation/tail checks skipped"
                  % (inst, n))
    return rows


def _residual_rows(inst, loc, store, ens, already_flagged, tail_check, missing=None):
    """Rows for one (instrument, locale) map. `missing` collects the keys with no English."""
    rows = []
    for key, value in store.items():
        if key == "_meta" or key in already_flagged or not isinstance(value, str):
            continue
        english = ens.get(key, "")
        if not english and missing is not None:
            missing.add(key)
        reasons = residual_defects(english, value, tail_check)
        if reasons and not english:
            # Say so on the row: the blank English cell is a stale map key, not an
            # oversight, and the two English-dependent checks did not run on it.
            reasons.append("no-english-label")
        if reasons:
            rows.append(_row(inst, loc, key, english, value.strip(),
                             ",".join(reasons), "residual", "residual"))
    return rows


def collect_paper_defects(out_root, overrides_path, defects=PAPER_DEFECTS):
    """The paper-defects section: what ASPSI has to fix in the printed questionnaires."""
    flagged = load_flagged(out_root)
    ens = english_index(flagged)
    overrides = _read_json(overrides_path) if Path(overrides_path).exists() else {}
    rows = []
    for spec in defects:
        why = "%s: %s | ASPSI: %s" % (spec["id"], spec["defect"], spec["action"])
        hits = OrderedDict()          # (instrument, locale, key) -> paper text
        for kind, arg in spec["selects"]:
            for inst, loc, key, text in _select(kind, arg, spec, flagged, overrides):
                hits.setdefault((inst, loc, key), text)
        if not hits:
            rows.append(_row(spec["instrument"] or "*", spec["locale"] or "*", spec["id"],
                             "", "", why, "paper-defect", "paper-defects"))
            continue
        for (inst, loc, key), text in hits.items():
            rows.append(_row(inst, loc, key, ens.get(inst, {}).get(key, "") or
                             (key if inst == "F2" else ""), text, why, "paper-defect",
                             "paper-defects"))
    return rows


def _select(kind, arg, spec, flagged, overrides):
    """Yield (instrument, locale, key, paper text) for one select of one paper defect."""
    if kind == "f2-held":
        for loc, per_key in overrides.get("F2", {}).items():
            for key, entry in per_key.items():
                if entry.get("keep") is None:
                    yield "F2", loc, key, ""
        return
    insts = [spec["instrument"]] if spec["instrument"] else list(flagged)
    if kind == "override":
        rx = re.compile(arg)
        for inst in insts:
            if inst == "F2":
                continue
            for key, entry in overrides.get(inst, {}).items():
                if not rx.search(key):
                    continue
                for loc in _override_locales(key, entry):
                    if spec["locale"] and loc not in (spec["locale"], "*"):
                        continue
                    yield inst, spec["locale"] or loc, key, ""
        return
    if kind == "keys":
        # Emitted whether or not the key is flagged: a key held by an override never
        # reaches `_flagged.json`, and it is exactly the row ASPSI has to see.
        for inst in insts:
            locs = [spec["locale"]] if spec["locale"] else (list(flagged.get(inst, {}))
                                                            or ["*"])
            for loc in locs:
                text = {r.get("key") or r.get("en", ""): r.get("tr", "")
                        for r in flagged.get(inst, {}).get(loc, [])}
                for key in arg:
                    yield inst, loc, key, text.get(key, "")
        return
    for inst in insts:
        for loc, entries in flagged.get(inst, {}).items():
            if spec["locale"] and loc != spec["locale"]:
                continue
            for r in entries:
                key = r.get("key") or r.get("en", "")
                if kind == "flagged" and re.search(arg, key):
                    yield inst, loc, key, r.get("tr", "")
                elif kind == "flag" and arg in (r.get("flags") or []):
                    yield inst, loc, key, r.get("tr", "")


def collect_follow_ups(items=FOLLOW_UPS):
    return [_row(inst or "*", "*", slug, what, owner, note, "follow-up", "follow-ups")
            for inst, slug, what, owner, note in items]


def collect_all(out_root, overrides_path, report_path=None, cspro_root=CSPRO,
                f2_maps=F2_MAPS):
    rows = collect_flagged(out_root, overrides_path, report_path)
    rows += collect_residual(out_root, cspro_root, f2_maps)
    rows += collect_paper_defects(out_root, overrides_path)
    rows += collect_follow_ups()
    return rows


# ------------------------------------------------------------------------- output --
def write_csv(rows, path):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def _summary(rows):
    tally = Counter((r["instrument"], r["status"]) for r in rows)
    return [[inst, status, tally[(inst, status)]] for inst, status in sorted(tally)]


def write_xlsx(rows, path):
    """One sheet per section plus a `summary` sheet. False when openpyxl is missing."""
    try:
        from openpyxl import Workbook
    except ImportError:
        print("openpyxl not installed - csv only")
        return False
    wb = Workbook()
    ws = wb.active
    ws.title = "summary"
    ws.append(["instrument", "status", "rows"])
    for line in _summary(rows):
        ws.append(line)
    ws.append([])
    ws.append(["total", "", len(rows)])
    ws.freeze_panes = "A2"
    for section in SECTIONS:
        part = [r for r in rows if r.get("section") == section]
        if not part:
            continue
        sh = wb.create_sheet(section)
        sh.append(COLS)
        for r in part:
            sh.append([r.get(c, "") for c in COLS])
        sh.freeze_panes = "A2"
        sh.auto_filter.ref = sh.dimensions
    wb.save(path)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-root", default=str(HERE / "out-aug21"))
    ap.add_argument("--overrides", default=str(HERE / "aug21-overrides.json"))
    ap.add_argument("--report", default=str(HERE / "aug21_apply_diff.json"),
                    help="apply_aug21.py --unmatched dry-run report (unmatched anchors)")
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--csv", required=True)
    a = ap.parse_args(argv)

    rows = collect_all(a.out_root, a.overrides, a.report)
    write_csv(rows, a.csv)
    write_xlsx(rows, a.xlsx)
    for inst, status, n in _summary(rows):
        print("%-4s %-13s %5d" % (inst, status, n))
    print("%d rows -> %s / %s" % (len(rows), a.csv, a.xlsx))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(CSPRO))
    sys.path.insert(0, str(HERE))
    sys.exit(main())
