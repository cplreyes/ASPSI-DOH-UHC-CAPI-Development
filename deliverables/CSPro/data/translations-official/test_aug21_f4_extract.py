import json
import re
from pathlib import Path

import pytest

from textnorm import norm_for_match

OUT = Path(__file__).resolve().parent / "out-aug21" / "F4"
LOCS = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
# Hard-asserted: prose stems the seven papers print as full sentences, English row above
# local row, outside any roster grid.
ALIGNED_PROSE = ["item:Q1_IS_HH_HEAD", "item:Q115_HELPED_APPT"]
# Reported only: roster GRID captions and the suffix-stripped Q67 — the paper prints
# these as table headers / inside the roster `CODES` legend / with "Time (HH:MM)", so
# they usually land in _flagged.json.
#
# The Task-27 brief put Q40 and Q36 in ALIGNED_PROSE; the seven Aug-21 F4 papers
# disagree. Both are printed inside the household roster's `CODES` legend
# (`36. Would the patient like to specify the type of disability? 0-No 1-Yes`,
# `40. Highest level of education completed 1- Early Childhood Education …`) and the
# Tagalog paper prints no local half for either — grid captions exactly like Q35 beside
# them. They are REPORTED here rather than asserted; verified in
# text-aug21/F4_{FIL,CEB}.txt.
ALIGNED_GRID = ["item:Q30_NAME", "item:Q35_HAS_DISABILITY", "item:Q36_SPECIFY_DISABILITY",
                "item:Q40_EDUCATION", "item:Q67_TRAVEL_HH"]


@pytest.mark.parametrize("loc", LOCS)
def test_extract_exists_and_is_name_scoped(loc):
    p = OUT / f"{loc}.json"
    assert p.exists(), f"run anchor_extract.py for F4 first ({p})"
    m = json.loads(p.read_text(encoding="utf-8"))
    m.pop("_meta", None)
    assert m and all(":" in k for k in m), "legacy text-keyed output would SystemExit in apply_translations"
    assert all(isinstance(v, str) and v.strip() for v in m.values())


@pytest.mark.parametrize("loc", ["fil", "ceb"])
def test_aligned_prose_items_recovered(loc):
    m = json.loads((OUT / f"{loc}.json").read_text(encoding="utf-8"))
    missing = [k for k in ALIGNED_PROSE if k not in m]
    assert missing == [], f"{loc}: aligned prose items not recovered from the Aug-21 PDF: {missing}"


@pytest.mark.parametrize("loc", ["fil", "ceb"])
def test_aligned_grid_items_reported(loc):
    """Reports where each grid item landed (clean / flagged+flags) so the reviewer can
    hand-accept a flagged span that is a complete sentence — an accepted span becomes an
    override entry, never a hand-edit of the map (pre-flight ruling).

    It does not judge the clean/flagged SPLIT (that is the wave decision this report
    exists to inform), but it does assert the grid item is somewhere: `absent` means the
    extractor dropped an anchor silently instead of emitting a worklist row, which is a
    real defect the print alone would have hidden.
    """
    clean = json.loads((OUT / f"{loc}.json").read_text(encoding="utf-8"))
    flagged = {r["key"]: r for r in json.loads((OUT / f"{loc}_flagged.json").read_text(encoding="utf-8"))}
    absent = []
    for k in ALIGNED_GRID:
        where = ("clean" if k in clean else
                 f"flagged {flagged[k]['flags']} -> {flagged[k]['tr'][:80]!r}" if k in flagged else "absent")
        print(f"{loc} {k}: {where}")
        if k not in clean and k not in flagged:
            absent.append(k)
    assert absent == [], (
        f"{loc}: grid items in neither the clean map nor the worklist — silently dropped "
        f"by the extractor: {absent}")


F4_MAPS = Path(__file__).resolve().parents[2] / "F4" / "translations"


@pytest.mark.parametrize("loc", LOCS)
def test_f4_map_carries_aug21_provenance(loc):
    m = json.loads((F4_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    src = m["_meta"].get("sources", {}).get("aug21")
    assert src, f"{loc}: apply_aug21.py --apply has not run for F4"
    assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}
    assert src["file"] == f"{loc}.json"


def test_f4_q40_no_longer_carries_the_attended_translation():
    # FIL June-5 value for the #608 wording must have been REPLACED by the Aug-21 cell.
    ext = json.loads((OUT / "fil.json").read_text(encoding="utf-8"))
    if "item:Q40_EDUCATION" not in ext:
        pytest.skip("item:Q40_EDUCATION not in the clean FIL extract - see _flagged.json / wave log")
    m = json.loads((F4_MAPS / "fil.json").read_text(encoding="utf-8"))
    assert m["item:Q40_EDUCATION"] == ext["item:Q40_EDUCATION"]


def test_no_override_keeps_a_placeholder():
    """No override may carry an unfilled `keep` placeholder.

    The pre-flight ruling widens the brief's F4-only guard to F1 and F3 as well: a
    `keep` that still reads `<current text>` would be written into a live map verbatim
    (or, on an existing key, silently fail the apply's `WARN override 'keep' != current
    map value` line into a value nobody pasted).
    """
    p = Path(__file__).resolve().parent / "aug21-overrides.json"
    if not p.exists():
        pytest.skip("no overrides file yet")
    data = json.loads(p.read_text(encoding="utf-8"))
    for inst in ("F1", "F3", "F4"):
        for key, ent in data.get(inst, {}).items():
            keep = ent.get("keep")     # Task 49: a `remove: true` entry carries no `keep`
            if keep is None:
                continue        # `keep: null` = never write; there is no text to check
            if isinstance(keep, dict):            # 2026-08-27: locale-keyed keep
                keep = " ".join(v for v in keep.values() if isinstance(v, str))
            assert not keep.startswith("<"), (
                f"{inst}/{key}: 'keep' is a placeholder, paste the real map value")
# --------------------------------------------------------------------------------------
# Fix round 1 (2026-08-26, review finding 1/2): NOTE-LAYER English must never reach a map.
#
# The note layer (`notes.json[<INST>]["english"]`) is what the paper prints AROUND a
# question - `intro:` section paragraphs and `const:` enumerator directives. It is not a
# labelled .dcf node, so every English-furniture detector built from `walk_labeled_nodes`
# is structurally blind to it, and `anchor_extract.has_directive()` does not match it
# either. That gap let the Aug-21 ILO span for Q72 open with
# `Applicable only to respondents in areas with GAMOT facility (...)` -
# note:const:_GAMOT_FAC glued in front of the Ilocano question - and ship into the .dcf
# and the .qsf, so the ILO Q72 prompt opened in English on the tablet.
#
# These two tests pin the class at the ARTEFACT level (the maps themselves), which is the
# only place a future wave, a different extractor or a hand edit all have to pass through.
# Matching runs on the `norm_for_match` projection and on NOTE_WINDOW-char runs, because
# the leak is never a byte-exact copy: the page break drops the note's full stop, glues a
# paren on, or (FIL Q38) swallows three words out of the middle.
#
# Known and deliberately NOT covered: `val:Q88_DIFF_PAYING_VS1:04` carries a TRAILING
# `intro:89` fragment in all seven live maps. It predates this wave (it is already in the
# pre-wave baseline), the Aug-21 extract offers no clean replacement, and repairing it
# would be a hand edit outside the apply path - so it is on the worklist, not in a test
# that would then fail for a defect nobody here introduced. `test_..._never_open_with_...`
# is scoped to a LEADING note and `test_..._no_enumerator_directive_...` to `const:`
# notes; both shapes are clean today and both FAIL on the pre-fix maps.
# --------------------------------------------------------------------------------------

NOTES_JSON = Path(__file__).resolve().parent / "notes.json"
NOTE_PREFIX = re.compile(r"^\s*Enumerator(?:\s+Instruction)?\s*(?:\([^)]*\))?\s*:\s*",
                         re.IGNORECASE)
NOTE_WINDOW = 40      # chars of NORMALISED note text that must appear verbatim
NOTE_MIN = 15         # shorter than this is not distinctive enough to blame on the note


def _note_corpus(inst="F4", only_const=False):
    """[(note key, normalised English)] for the instrument's note layer.

    Both forms of a directive go in - with and without its `Enumerator:` /
    `Enumerator Instruction (DO NOT READ ALOUD):` label - because the extractor's span may
    start before or after the label.
    """
    block = json.loads(NOTES_JSON.read_text(encoding="utf-8"))[inst]["english"]
    out = []
    for key, text in block.items():
        if only_const and not key.startswith("const:"):
            continue
        text = (text or "").strip()
        if not text or text.startswith("~~"):      # `~~strip(Q30_NAME)~~` is a fill
            continue
        for form in (text, NOTE_PREFIX.sub("", text)):
            n = norm_for_match(form)
            if len(n) >= NOTE_MIN:
                out.append((key, n))
    return sorted(set(out), key=lambda r: -len(r[1]))


def _note_run_in(nv, corpus):
    """The note key whose English (whole, or a NOTE_WINDOW-char run of it) is inside the
    normalised value `nv`, or None."""
    for key, n in corpus:
        if n in nv:
            return key
        if len(n) > NOTE_WINDOW and any(n[i:i + NOTE_WINDOW] in nv
                                        for i in range(len(n) - NOTE_WINDOW + 1)):
            return key
    return None


def _map_values(loc):
    m = json.loads((F4_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    m.pop("_meta", None)
    return [(k, v) for k, v in m.items() if isinstance(v, str) and v.strip()]


@pytest.mark.parametrize("loc", LOCS)
def test_f4_map_values_never_open_with_note_layer_english(loc):
    corpus = _note_corpus()
    assert corpus, "note corpus is empty - notes.json moved and the guard became a no-op"
    bad = []
    for k, v in _map_values(loc):
        nv = norm_for_match(v)
        key = next((nk for nk, n in corpus if nv.startswith(n)), None)
        if key:
            bad.append((k, v[:80], key))
    assert bad == [], (
        f"{loc}: value OPENS with note-layer English - the note rode into the span in "
        f"front of the translation: {bad}")


@pytest.mark.parametrize("loc", LOCS)
def test_f4_map_values_carry_no_enumerator_directive_note_text(loc):
    """A `const:` note is an enumerator directive; it is never any question's text."""
    corpus = _note_corpus(only_const=True)
    assert corpus, "no const: notes in notes.json[F4] - the guard became a no-op"
    bad = []
    for k, v in _map_values(loc):
        key = _note_run_in(norm_for_match(v), corpus)
        if key:
            bad.append((k, v[:80], key))
    assert bad == [], (
        f"{loc}: enumerator-directive note text inside a translation value: {bad}")
