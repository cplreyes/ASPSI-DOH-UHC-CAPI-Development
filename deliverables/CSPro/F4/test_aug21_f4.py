"""Wave 3 (Aug-21 translations design): F4 English alignment + qsf gate notes.
Run from deliverables/CSPro/F4:  python -m pytest test_aug21_f4.py -q
"""
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # generate_dcf / generate_qsf
sys.path.insert(0, str(HERE.parent))   # cspro_helpers / notes_lookup / icf_content


def _sibling(name):
    """Load THIS directory's <name>.py, whichever instrument pytest collected first.

    F1/, F3/ and F4/ each carry a `generate_dcf.py`, a `generate_fmf.py` and a
    `generate_qsf.py`. A bare `import generate_dcf` off sys.path resolves to whichever one
    reached `sys.modules` first, so collecting two instruments in one run
    (`python -m pytest F3 F4 automation -q`) used to fail at collection with
    `ImportError: cannot import name 'build_f4_dictionary' from 'generate_dcf'`. Loading by
    explicit path and re-registering under the bare name makes the import order-independent
    - including for `generate_qsf.py`, which does `from generate_dcf import ...` and
    `from generate_fmf import ...` itself. No side effects: the generators write their
    output only under `if __name__ == "__main__"`.
    """
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # before exec, for the transitive bare imports
    spec.loader.exec_module(module)
    return module


_sibling("generate_dcf")
_sibling("generate_fmf")               # generate_qsf imports it by bare name
from generate_dcf import build_f4_dictionary, apply_dcf_short_labels   # noqa: E402
from cspro_helpers import CSPRO_LABEL_MAX, walk_labeled_nodes          # noqa: E402
qsf = _sibling("generate_qsf")
import json as _json   # noqa: E402  (module-level reads versions.json + cover_logos.png)

# Verbatim Aug-21 paper text, number prefix per the F4 label convention. Source:
# raw/Survey-Instruments-2026-08-21/English/
#   "F4-English_Household Survey Questionnaire_UHC Year 2_Aug21.pdf"
# (Q30 + Q35/Q36 in the Section C roster CODES columns, Q40 in C3, Q67 in Section G).
AUG21_F4_LABELS = {
    "Q30_NAME": "30. Name (Write the complete name of HH member)",
    "Q35_HAS_DISABILITY": "35. With disability?",
    "Q36_SPECIFY_DISABILITY": "36. Would the patient like to specify the type of disability?",
    "Q40_EDUCATION": "40. Highest level of education completed",
    # Q67 takes the paper's "for you to" correction ONLY. The paper's pharmacy definition
    # stays OUT of the dcf label: it is already INSTRUCTIONS[67] in generate_qsf.py, and
    # the dcf label feeds both the qsf question bar and the fmf field text, so inlining it
    # printed the definition twice (#1205 / F3 #1136-#1137). See test_q67_definition_*.
    "Q67_TRAVEL_HH": ("67. How much time does it take for you to reach the nearest pharmacy "
                      "from your home? — Hours"),
    "Q67_TRAVEL_MM": "67. Travel time to nearest pharmacy — Minutes",   # #1073: short 2nd component, unchanged
}

# The pharmacy definition, verbatim, as generate_qsf.INSTRUCTIONS[67] carries it.
Q67_PHARMACY_DEF = ("A Pharmacy is an ancillary primary care facility with a FDA LTO "
                    "where registered medicines can be bought.")


@pytest.fixture(scope="module")
def en_labels():
    d = build_f4_dictionary()
    return {key.split(":", 1)[1]: node["labels"][0]["text"]
            for key, node in walk_labeled_nodes(d) if key.startswith("item:")}


@pytest.mark.parametrize("name,expected", sorted(AUG21_F4_LABELS.items()))
def test_aug21_label_text(en_labels, name, expected):
    assert en_labels[name] == expected


def test_relabelled_items_keep_their_codes():
    d = build_f4_dictionary()
    vs = {key: [v["pairs"][0]["value"] for v in node["values"]]
          for key, node in walk_labeled_nodes(d) if key.startswith("vs:")}
    assert vs["vs:Q35_HAS_DISABILITY_VS1"] == ["0", "1"]          # YN_01
    assert vs["vs:Q36_SPECIFY_DISABILITY_VS1"] == ["0", "1"]
    # Q40_EDUCATION codes are 2-char zero-padded (generate_dcf.py:529-532: "01","02","03"...)
    assert vs["vs:Q40_EDUCATION_VS1"][:3] == ["01", "02", "03"]


def test_q67_pharmacy_definition_lives_in_the_qsf_note_not_the_dcf_label():
    """#1205 class of defect: the definition must render ONCE, on the blue line.

    One dcf label feeds BOTH the .qsf question bar and the .fmf field text, so a
    definition inlined into the label prints on top of the identical
    <p class="instruction"> note that generate_qsf already emits — the exact double
    that was removed from Q64_MEDICATIONS_LIST (#1205) and from F3 (#1136/#1137).
    F3 Q150 is the pattern: short stem in the dcf, definition in the qsf note.
    """
    from generate_qsf import question_extras                       # noqa: E402

    d = build_f4_dictionary()
    stem = {key.split(":", 1)[1]: node["labels"][0]["text"]
            for key, node in walk_labeled_nodes(d) if key.startswith("item:")}["Q67_TRAVEL_HH"]
    _intro, instr = question_extras("Q67_TRAVEL_HH", set())

    assert instr is not None and Q67_PHARMACY_DEF in instr, "the blue note must carry it"
    assert Q67_PHARMACY_DEF not in stem, "the dcf label must NOT repeat the blue note"


def test_no_dcf_label_inlines_its_own_qsf_instruction_note():
    """Generalisation of the test above — the #1205 rule, swept over every F4 item."""
    from generate_qsf import question_extras                       # noqa: E402

    d = build_f4_dictionary()
    doubled = {}
    for key, node in walk_labeled_nodes(d):
        if not key.startswith("item:") or not node.get("labels"):
            continue
        name = key.split(":", 1)[1]
        _intro, instr = question_extras(name, set())
        # instr may be a tuple since the aug21 gates (one paragraph per part) — check each
        hit = [p for p in _parts(instr) if p and p in node["labels"][0]["text"]]
        if hit:
            doubled[name] = hit
    assert doubled == {}


def test_no_label_hits_the_write_dcf_cap():
    """No label reaches write_dcf's last-resort 255-char truncation (#1177/#1182).

    The cap must be checked on the SHIPPED shape, i.e. after apply_dcf_short_labels() —
    exactly the order generate_dcf.main() uses. Before that swap, the 8 Section-N in-kind
    prompts are 269-290 chars by design (DCF_SHORT_LABELS exists precisely because of
    them, and generate_qsf must NOT apply it), so asserting on the raw dictionary would
    fail on pre-existing, intended text rather than on anything this wave changes.
    """
    d = build_f4_dictionary()
    apply_dcf_short_labels(d)
    over = {key: len(node["labels"][0]["text"])
            for key, node in walk_labeled_nodes(d)
            if node.get("labels") and len(node["labels"][0]["text"]) > CSPRO_LABEL_MAX}
    assert over == {}


# ------------------------------------------------------------------
# Aug-21 printed gates on Q117/Q118/Q131/Q135 — help text, never label text.
# ------------------------------------------------------------------
GATE_Q112 = "[Answer only “yes” in Q112]"
GATE_DOH = "[Ask only if they went to a DOH-retained hospital]"


def _parts(instr):
    return instr if isinstance(instr, tuple) else (instr,)


@pytest.mark.parametrize("name,gate", [
    ("Q117_SPECIALIST_FOLLOWUP", GATE_Q112),
    ("Q118_SAT_REFERRAL_PROCESS", GATE_Q112),
    ("Q131_NBB_OOP", GATE_DOH),
    ("Q135_ZBB_OOP", GATE_DOH),
])
def test_printed_gate_is_help_text_not_label(en_labels, name, gate):
    intro, instr = qsf.question_extras(name, set())
    assert instr is not None and _parts(instr)[0] == gate
    assert gate not in en_labels[name]                # dcf label = translation key, stays clean


def test_q118_keeps_read_one_as_a_separate_part():
    _, instr = qsf.question_extras("Q118_SAT_REFERRAL_PROCESS", set())
    assert instr == (GATE_Q112, qsf._READ_ONE)        # tuple: each part translated on its own


def test_gate_constants_have_no_digits_in_their_names():
    # convention kept even after extract_notes.py widened its scrape regex (Task 8)
    assert hasattr(qsf, "_GATE_ANSWER_ONLY_IF_YES") and hasattr(qsf, "_GATE_DOH_RETAINED")
    assert qsf._GATE_ANSWER_ONLY_IF_YES == GATE_Q112 and qsf._GATE_DOH_RETAINED == GATE_DOH


def test_gate_renders_as_instruction_paragraph():
    pre, post = qsf.note_html(None, GATE_DOH, "EN")
    assert pre == "" and post == f'<p class="instruction">{GATE_DOH}</p>'


def test_tuple_instruction_renders_one_paragraph_per_part():
    pre, post = qsf.note_html(None, (GATE_Q112, qsf._READ_ONE), "EN")
    assert post == (f'<p class="instruction">{GATE_Q112}</p>'
                    f'<p class="instruction">{qsf._READ_ONE}</p>')


# ------------------------------------------------------------------
# Aug-21 notes layer for those gates (Task 29).
# ------------------------------------------------------------------
from notes_lookup import translate_note, coverage, _canon, _load  # noqa: E402

LOCALES = ("FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO")

# Non-regression floor, not a target (coverage() de-duplicates notes across instruments,
# so it is NOT F1 13 + F3 24 + F4 23). The JUNE-5 pre-wave numbers were
# FIL 51 / BCL 45 / CEB 28 / WAR 48 / HIL 45 / ILO 38 / BIS 45; two reductions since are
# deliberate and reviewed, and the floor below records the tree AFTER both:
#   CEB -1, WAR -1, HIL -1  Task 8 pruned F1's retired const:_PROBE rows (task-8-report.md
#                           "lost 6": stale rows nothing could render).
#   BIS -1                  Task 29 holds F4 note:intro:144:BIS, whose Aug-21 capture
#                           carries English reflow debris ("take- aways. Naa na kita ...").
#   FIL/BCL/CEB/WAR/HIL/ILO -1
#                           Task 29 fix round 1 widened that hold to all seven locales:
#                           fixing notes_lookup._canon() made intro:144 reachable and
#                           exposed captures 4-9% the length of the 865-char English (the
#                           six worst rows of 314; next worst 0.22). See the hold's reason
#                           in aug21-overrides.json. coverage() counts STORED values, so a
#                           deliberate hold shows here as a drop.
# Any FURTHER drop is a regression.
NOTES_FLOOR = {"FIL": 50, "BCL": 45, "CEB": 26, "WAR": 46, "HIL": 43, "ILO": 37, "BIS": 45}


@pytest.mark.xfail(strict=True, reason="Aug-21 papers print the dialect gate AFTER the "
                                       "English question, out of the anchor's reach; both "
                                       "gates are held at keep:'' and render English")
@pytest.mark.parametrize("const", ["_GATE_DOH_RETAINED", "_GATE_ANSWER_ONLY_IF_YES"])
def test_gate_note_translates_in_at_least_fil(const):
    # Both are digit-free module constants -> extract_notes emits const:<NAME> anchors.
    # strict xfail: the day find_translation() learns the Aug-21 layout this XPASSes and
    # fails the suite, which is the signal to delete the note:const:_GATE_* holds.
    en = getattr(qsf, const)
    assert translate_note(en, "FIL") != en


@pytest.mark.parametrize("const", ["_GATE_DOH_RETAINED", "_GATE_ANSWER_ONLY_IF_YES"])
def test_gate_note_is_never_an_english_question_bleed(const):
    """A gate renders either the English gate or a BRACKETED dialect gate — never prose.

    The Aug-21 papers reflow the gate inline, so the text following the English anchor is
    the English QUESTION, not the dialect gate (the dialect gate sits after that question).
    extract_notes' find_translation() takes what follows the anchor, so an unheld import
    writes "After you went to the specialist or special service, did they" into all seven
    locales — English prose on the blue line, in place of a routing gate. The paper prints
    the gate bracketed in every dialect, which is also what automation/aug21_check_gates.py
    counts, so this invariant still holds the day the extractor learns the new layout.
    """
    en = getattr(qsf, const)
    for lg in LOCALES:
        got = translate_note(en, lg)
        assert got == en or got.startswith("["), f"{const}/{lg}: bled {got!r}"


def test_notes_coverage_did_not_regress():
    cov = coverage()
    for lg, floor in NOTES_FLOOR.items():
        assert cov.get(lg, 0) >= floor, f"{lg}: {cov.get(lg)} < pre-wave floor {floor}"


def test_the_em_dash_intro_is_reachable_and_held():
    """SECTION_INTROS[144] is the only note in F1/F3/F4 authored with an em-dash.

    Two separate facts, and this pins both:

    1. REACHABLE. extract_notes.norm() folds en/em dashes before keying a note;
       notes_lookup._canon() did not, so this intro was stored under a key the runtime
       never built - the lookup could not miss more quietly. _canon now folds too, so the
       English resolves to a real row in the loaded map. Asserting on the map, not on the
       rendered text, is what keeps this test honest while the row is held.
    2. HELD. Every locale renders English on purpose. The captures the fix exposed are
       4-9% of the 865-character English script (one opening clause, no instructions), so
       all seven are held at keep:"" in aug21-overrides.json until find_translation() can
       span a multi-paragraph intro. Reading a fragment aloud is worse than reading the
       English, which is what the field sees today.

    Deleting the holds must flip this test, not slip past it.
    """
    en = qsf.SECTION_INTROS[144]
    assert "\u2014" in en, "fixture drifted: this intro no longer carries an em-dash"
    assert _canon(en) in _load(), "intro:144 is unreachable again - did _canon stop folding dashes?"
    for lg in LOCALES:
        assert translate_note(en, lg) == en, f"{lg}: intro:144 hold stopped firing"


def test_f4_version_is_at_least_3_2_0():
    """Both stamped surfaces carry the Wave-3 version or later, and neither drifts from
    versions.json.

    versions.json is the single source of truth; the .pff Description is what CSEntry's
    application list shows, so a tester can only tell a 3.2.2 tablet from a 3.2.1 one by
    this string. The full Description is asserted (not just the version) because the date
    and the [DEV] channel tag ride the same line and have gone stale on their own before.
    Task 32b patch: 3.2.0 shipped 154 Waray values carrying the paper's question number.
    Task 33b patch: 3.2.1 shipped 459 Filipino values wrapped in the paper's gloss brackets.
    The version is a floor rather than an equality (controller ruling, post-Task 18) so the
    next UAT patch bump cannot turn a green suite red; the floor is the wave's major.minor
    (3.2.0), and the drift check reads the SHIPPED version out of versions.json, so it keeps
    biting whatever that version is.
    """
    v = _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
    assert tuple(int(n) for n in v["version"].split(".")) >= (3, 2, 0), v["version"]
    assert v["channel"] == "dev"
    ver = v["version"]
    pff = (HERE / "HouseholdSurvey.pff").read_text(encoding="utf-8", errors="ignore")
    assert f"v{ver}" in pff and "[DEV]" in pff
    assert f"Description=Household Survey (F4) - v{ver} ({v['date']}) [DEV]" in pff


import re as _re   # noqa: E402


def _shipped_version():
    """versions.json is the single source of truth for which note is the shipped one.
    Task 49: three of these tests globbed a hard-coded version, so a patch bump pointed
    them at a superseded note instead of failing."""
    return _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]["version"]


def test_patch_note_exists_and_leads_with_remove_readd():
    """The #f4-uat note Carl posts: dated, named for the SHIPPED build, no placeholders.

    Controller rulings (post-32b, post-33b): the shipped build is v3.2.2 - 3.2.0 was
    superseded within the hour by the Waray question-number fix, and 3.2.1 by the Filipino
    bracket fix, all three on the same day - so the file is named for 3.2.2 and the brief's
    v3.2.0 assertions move with it. Three things this pins that a human eye slides over:

    * the file name carries a REAL date and it is versions.json's F4 date, so the note can
      never claim a build day the stamped .pff does not agree with;
    * `draft-` cannot satisfy it - sorted() puts a `draft-` name last and the ^-anchored
      regex then rejects it, so leaving the Task-32b draft in place fails this test;
    * the superseded v3.2.1 is named, because a tester who installed it this afternoon
      needs to know their build is one deploy stale.
    """
    v = _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
    ver = v["version"]
    notes = sorted((HERE.parent / "patch-notes").glob(f"*-f4-v{ver}-aug21-translations.md"))
    assert notes, f"no <EVDATE>-f4-v{ver}-aug21-translations.md under patch-notes/"
    p = notes[-1]
    assert _re.match(rf"\d{{4}}-\d{{2}}-\d{{2}}-f4-v{_re.escape(ver)}-aug21-translations\.md$",
                     p.name), p.name
    assert p.name.startswith(v["date"]), (p.name, v["date"])
    t = p.read_text(encoding="utf-8")
    assert f"v{ver}" in t and "remove" in t.lower() and "Add Application" in t
    assert "#608" in t and "completed" in t          # the Q40 reversal is stated
    maj, minr, pat = (int(n) for n in ver.split("."))
    prev = f"{maj}.{minr}.{pat - 1}"
    assert _re.search(r"\bv" + _re.escape(prev) + r"\b", t), \
        f"the superseded v{prev} build is not named"
    assert not _re.search(r"<\?>|<date>|<URL|<raw|<SHA|<EVDATE>|2026-08-2x", t)


def test_patch_note_waray_fix_example_is_actually_shipped():
    """The Waray question-number fix must be illustrated with a row the pack SHIPS.

    v3.2.0's regression prefixed 154 WAR values with the paper's question number; v3.2.1
    strips it. But seven WAR rows (Q27/Q28/Q29 + one result-of-visit label) are held
    `keep: null` and fall back to English on screen - so naming one of THEM as the "now
    reads ..." example points a Waray tester at a screen that is in English, and they file
    a false bug or conclude the re-add failed. This pins the example to the shipped set:
    every straight-double-quoted Waray span on the supersede bullet that does not open
    with the stripped question number must be a real prefix of a value in war.json.
    """
    notes = sorted((HERE.parent / "patch-notes").glob(f"*-f4-v{_shipped_version()}-aug21-translations.md"))
    assert notes, "no patch note to check"
    lines = notes[-1].read_text(encoding="utf-8").splitlines()
    bullet = [ln for ln in lines if "supersedes v3.2.0" in ln]
    assert len(bullet) == 1, "expected exactly one 'supersedes v3.2.0' bullet"
    war = _json.loads(
        (HERE / "translations" / "war.json").read_text(encoding="utf-8")
    )
    war.pop("_meta", None)          # name-scoped-v2 provenance, not a translation
    values = list(war.values())

    quoted = _re.findall(r'"([^"]+)"', bullet[0])
    assert quoted, "the supersede bullet quotes no example at all"
    shipped = [q for q in quoted if not _re.match(r"\s*\d+\.", q)]
    assert shipped, "the bullet shows no post-fix (un-numbered) example"
    for q in shipped:
        stem = q.rstrip("\u2026. ")
        assert any(v.startswith(stem) for v in values), (
            f"patch note cites {q!r} as the fixed Waray text, but no war.json value "
            f"starts with it - that key is held (English on screen)"
        )


def test_patch_note_filipino_fix_example_is_actually_shipped():
    """The v3.2.2 bullet's Filipino examples must be values the pack SHIPS.

    Same trap as the Waray bullet one line up: quoting a string that is held (or that
    the strip did not actually produce) points a Filipino tester at a screen that does
    not match the note, and they file a false bug. Every straight-double-quoted span on
    the v3.2.2 supersede bullet that does NOT still carry a bracket must be a real value
    in fil.json.
    """
    notes = sorted((HERE.parent / "patch-notes").glob(f"*-f4-v{_shipped_version()}-aug21-translations.md"))
    assert notes, "no patch note to check"
    lines = notes[-1].read_text(encoding="utf-8").splitlines()
    bullet = [ln for ln in lines if "supersedes v3.2.1" in ln]
    assert len(bullet) == 1, "expected exactly one 'supersedes v3.2.1' bullet"
    fil = _json.loads((HERE / "translations" / "fil.json").read_text(encoding="utf-8"))
    fil.pop("_meta", None)
    values = set(fil.values())
    quoted = _re.findall(r'"([^"]+)"', bullet[0])
    shipped = [q for q in quoted if "[" not in q]
    assert shipped, "the bullet shows no post-fix (un-bracketed) example"
    for q in shipped:
        assert q in values, (
            f"patch note cites {q!r} as the fixed Filipino text, but no fil.json value "
            f"is exactly that string"
        )
    # and the pre-fix shapes it quotes must be gone from the shipped map
    for q in [q for q in quoted if "[" in q]:
        assert q not in values, f"{q!r} is still in fil.json"


def test_patch_note_cites_the_shipped_builds_artifacts():
    """The note must present the SHIPPED build's numbers and evidence, not a superseded one's.

    v3.2.2 folds two earlier notes (3.2.0 -> 3.2.1 -> 3.2.2 all on one day), and the way a
    fold goes wrong is that the prose gets the new version while a table row or an evidence
    filename keeps the old one. A tester who opens `byte-verify-3.2.1.txt` from the Slack
    post is reading the verification of a build that is no longer served, and a reviewer
    reading a coverage row headed "shipped (3.2.1)" cannot tell whether the counts were
    re-measured after the 3.2.2 maps were rewritten. Both are pinned here:

    * every `byte-verify-*.txt` the note names is the shipped version's file, and it exists
      in this wave's evidence folder;
    * the coverage table's shipped row is labelled with the shipped version.
    """
    v = _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
    ver = v["version"]
    notes = sorted((HERE.parent / "patch-notes").glob(f"*-f4-v{ver}-aug21-translations.md"))
    assert notes, "no patch note to check"
    t = notes[-1].read_text(encoding="utf-8")

    cited = set(_re.findall(r"byte-verify-[\d.]+\.txt", t))
    assert cited, "the note names no byte-verify file at all"
    assert cited == {f"byte-verify-{ver}.txt"}, (
        f"note cites {sorted(cited)}; the shipped build is {ver}"
    )
    ev = (HERE.parents[2] / "docs" / "uat-fix-evidence"
          / "2026-08-26-aug21-translations" / "F4" / f"byte-verify-{ver}.txt")
    assert ev.exists(), f"{ev} is not in the evidence folder"

    shipped_row = [ln for ln in t.splitlines() if ln.lstrip("| ").startswith("**shipped")]
    assert len(shipped_row) == 1, "expected exactly one 'shipped' coverage row"
    assert ver in shipped_row[0], (
        f"coverage table's shipped row reads {shipped_row[0]!r}, not the shipped {ver}"
    )


# --------------------------------------------------------------------------------------
# Task 49 (v3.2.3): the row-inheritance repair.
#
# Some option rows inherited a NEIGHBOURING row's translation - well formed, right
# language, wrong meaning, so no extractor flag could fire on the value alone. Where the
# Aug-21 paper carries no distinct translation for such a row the honest outcome is to
# DELETE the map entry and let the English label render (`remove: true` in
# aug21-overrides.json). Two ways that goes wrong and a human eye slides over both:
# a note that lists a row the map still holds, and a map row nobody told the testers about.

def test_v3_2_3_removed_rows_are_named_in_the_note_and_gone_from_the_maps():
    v = _json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
    assert tuple(int(n) for n in v["version"].split(".")) >= (3, 2, 3), v["version"]
    ov = _json.loads((HERE.parent / "data" / "translations-official" / "aug21-overrides.json")
                     .read_text(encoding="utf-8"))["F4"]
    want = {(k, loc) for k, e in ov.items() if e.get("remove") for loc in e["locales"]}
    assert want, "no F4 `remove: true` override at all - the v3.2.3 repair is not in the file"

    for key, loc in sorted(want):
        m = _json.loads((HERE / "translations" / f"{loc}.json").read_text(encoding="utf-8"))
        assert key not in m, f"{loc}.json still holds {key}, which is overridden `remove: true`"

    notes = sorted((HERE.parent / "patch-notes").glob(f"*-f4-v{v['version']}-aug21-translations.md"))
    assert notes, "no patch note to check"
    body = notes[-1].read_text(encoding="utf-8").split("## v3.2.3", 1)
    assert len(body) == 2, "the note carries no `## v3.2.3` section"
    body = body[1].split("\n## ")[0]
    listed = set(_re.findall(r"`(val:[A-Z0-9_]+:\d+)` \((fil|bcl|bis|ceb|war|hil|ilo)\)", body))
    assert listed == want, (f"the v3.2.3 section lists {sorted(listed - want)} that are not "
                            f"removed and misses {sorted(want - listed)}")


def test_v3_2_3_every_kept_sibling_still_reads_differently_from_its_neighbours():
    """The point of the repair: no two codes of one F4 value set may share a label.

    This is the shipped-artefact half of apply_aug21.duplicate_label_rows() - it reads the
    maps that are on disk, so it keeps biting after any future apply, not only this one.
    """
    import sys as _sys
    _sys.path.insert(0, str(HERE.parent / "data" / "translations-official"))
    from apply_aug21 import duplicate_label_rows, dcf_english          # noqa: E402
    en = dcf_english("F4")
    for loc in LOCALES:
        m = _json.loads((HERE / "translations" / f"{loc.lower()}.json").read_text(encoding="utf-8"))
        m.pop("_meta", None)
        rows = duplicate_label_rows(m, en)
        assert rows == [], (
            f"{loc}: " + "; ".join(f"{r['value_set']} codes {','.join(r['codes'])} "
                                   f"both read {r['value']!r}" for r in rows))
