"""Wave 4a (Aug-21 English alignment) — F3 label re-sync is text-only.

Run from deliverables/CSPro:  python -m pytest F3/test_aug21_labels.py -q
"""
import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import pytest

CSPRO = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(CSPRO))
sys.path.insert(0, str(HERE))


def _sibling(name):
    """Load THIS directory's <name>.py, whichever instrument pytest collected first.

    F1/, F3/ and F4/ each carry a `generate_dcf.py`. A bare `import generate_dcf` off
    sys.path resolves to whichever one reached `sys.modules` first, so collecting two
    instruments in one run (`python -m pytest F3 F4 automation -q`) used to fail with
    `ImportError: cannot import name 'build_f4_dictionary' from 'generate_dcf'`. Loading by
    explicit path and re-registering under the bare name makes the import order-independent
    here and for any transitive bare import inside the module. No side effects: the
    generators write their dictionary only under `if __name__ == "__main__"`.
    """
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # before exec, for the transitive bare imports
    spec.loader.exec_module(module)
    return module


from cspro_helpers import TRANSLATION_LANGUAGES, walk_labeled_nodes, _value_pair_key  # noqa: E402
generate_dcf = _sibling("generate_dcf")

FIX = Path(__file__).parent / "test_fixtures" / "aug21_vs_codes_before.json"


def vs_code_map(dictionary):
    out = {}
    for key, node in walk_labeled_nodes(dictionary):
        if key.startswith("vs:"):
            out[key[3:]] = [_value_pair_key(v) for v in node.get("values", []) or []]
    return out


def en_labels(dictionary):
    out = {}
    for key, node in walk_labeled_nodes(dictionary):
        labs = node.get("labels") or []
        if labs:
            out[key] = labs[0].get("text", "")
    return out


@pytest.fixture(scope="module")
def d():
    return generate_dcf.build_f3_dictionary()


@pytest.fixture(scope="module")
def labels(d):
    return en_labels(d)


Q47_STEM = "47. Are you aware that there are PhilHealth packages for the following health services: — "
Q69_STEM = ("69. How long does it take you to travel from your house when going to the health "
            "facility that you usually go to?")
Q1141_STEM = ("115.1 Other than the expenses above (e.g. confinement, medicines, laboratory, etc.), "
              "which of the following were also included in the bill?")
Q1142_STEM = ("115.2 Did you pay for any other expenses during your confinement that were not "
              "included in the hospital bill?")


@pytest.mark.parametrize("name,service", [
    ("Q47_PHYSICIAN_CHECKUP", "Physician check-up"),
    ("Q47_DIAGNOSTIC_TESTS", "Diagnostic tests (e.g. laboratory tests and imaging)"),
    ("Q47_HOSPITAL_CONF", "Hospital confinement"),
    ("Q47_OUTPATIENT_DRUGS", "Outpatient drugs"),
])
def test_q47_single_stem(labels, name, service):
    assert labels[f"item:{name}"] == Q47_STEM + service


def test_q69_paper_stem(labels):
    assert labels["item:Q69_USUAL_TRAVEL_HH"] == Q69_STEM + " — Hours"
    assert labels["item:Q69_USUAL_TRAVEL_MM"] == Q69_STEM + " — Minutes"


def test_q94_q96_q98_stems(labels):
    assert labels["item:Q94_LAB_AMT"] == \
        "94. How much was the cost of [laboratory test]? (amount paid out-of-pocket, Pesos)"
    assert labels["item:Q96_SOURCES"] == "96. How much was spent for the prescribed medicines?"
    assert labels["item:Q98_SOURCES"] == \
        "98. Did you use any of the following to pay for medical costs? (select all that apply)"


def test_q972_paper_text(labels):
    assert labels["item:Q972_SOURCES"] == ("97.2 Did you pay for any other expenses during your "
                                           "OPD visit that were NOT included in the outpatient bill?")
    assert labels["val:Q972_SOURCES_VS1:90"] == "No, did not pay for any other expenses"


def test_q1141_q1142_paper_text(labels):
    assert labels["item:Q1141_1"] == Q1141_STEM + " — Doctor's Professional Fee"
    assert labels["item:Q1141_3"] == Q1141_STEM + " — Non-medical expenses: (e.g. Hygiene kit)"
    assert labels["item:Q1141_6"] == Q1141_STEM + " — Other expenses:"
    assert labels["item:Q1141_3_AMT"] == \
        "115.1 How much were you charged or billed? — Non-medical expenses: (e.g. Hygiene kit) (Amount in Pesos)"
    assert labels["item:Q1141_NONE"] == Q1141_STEM + " — None"
    assert labels["item:Q1142_HAS_OTHER"] == Q1142_STEM
    assert labels["item:Q1142_2"] == Q1142_STEM + " — Payment made directly to doctor/s and their secretary"
    assert labels["item:Q1142_7_AMT"] == "115.2 Indicate the amount spent — Other (specify) (Amount in Pesos)"


def test_q66_q88_placeholders_untouched(labels):
    # The translated Aug-21 PDFs still carry [facility_name_input]; the regex only matches that form.
    assert "[facility_name_input]" in labels["item:Q66_SAME_AS_USUAL"]
    assert "[FACILITY_NAME_INPUT]" in labels["item:Q88_WHY_VISIT"]


def test_every_label_under_255(labels):
    long = {k: len(v) for k, v in labels.items() if len(v) > 255}
    assert long == {}


def test_value_set_codes_unchanged(d):
    before = json.loads(FIX.read_text(encoding="utf-8"))
    assert vs_code_map(d) == before


def test_checkbox_value_sets_ascend(d):
    for name in ("Q971_SOURCES_VS1", "Q972_SOURCES_VS1", "Q96_SOURCES_VS1", "Q98_SOURCES_VS1"):
        codes = vs_code_map(d)[name]
        assert codes == sorted(codes, key=int), name


def test_facility_neutral_covers_every_locale():
    want = {code for code, _disp, _f in TRANSLATION_LANGUAGES}
    assert set(generate_dcf._FACILITY_NEUTRAL) == want


def test_neutralise_touches_every_language():
    labs = [{"language": code, "text": "Is [facility_name_input] the one?"}
            for code, _d, _f in TRANSLATION_LANGUAGES]
    node = {"labels": labs}
    n = generate_dcf._neutralise_facility_placeholder(node)
    assert n == len(TRANSLATION_LANGUAGES)
    for lab in labs:
        assert "[facility_name_input]" not in lab["text"], lab
        # Non-English labels must NOT fall back to the English phrase (HIL/ILO gap).
        if lab["language"] != "EN":
            assert lab["text"] != "Is this facility the one?", lab


# ------------------------------------------------ Wave 4b (Aug-21 import) --
# Task 40 merges the Aug-21 F3 extract into the seven maps. These three tests are
# pinned at the ARTEFACT level (the maps + the extract that produced them), which
# is the one place a future wave, a different extractor and a hand edit all have
# to pass through.
F3_MAPS = CSPRO / "F3" / "translations"
OUT_F3 = CSPRO / "data" / "translations-official" / "out-aug21" / "F3"
LOCS = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
# keys whose English was reworded in Tasks 36-38: their June-5 values are stale and MUST
# be replaced by the Aug-21 cell (or sit in the flagged worklist) — never survive silently.
REWORDED = ["item:Q47_PHYSICIAN_CHECKUP", "item:Q69_USUAL_TRAVEL_HH", "item:Q96_SOURCES",
            "item:Q98_SOURCES", "item:Q972_SOURCES", "val:Q972_SOURCES_VS1:90",
            "item:Q1141_1", "item:Q1142_HAS_OTHER"]


@pytest.mark.parametrize("loc", LOCS)
def test_f3_map_carries_aug21_provenance(loc):
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    src = m["_meta"].get("sources", {}).get("aug21")
    assert src, f"{loc}: apply_aug21.py --apply has not run for F3"
    assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}


@pytest.mark.parametrize("loc", ["fil", "hil", "ilo"])
def test_f3_reworded_keys_hold_aug21_value_or_are_flagged(loc):
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    ex = json.loads((OUT_F3 / f"{loc}.json").read_text(encoding="utf-8"))
    fl = {r["key"] for r in json.loads((OUT_F3 / f"{loc}_flagged.json").read_text(encoding="utf-8"))}
    for k in REWORDED:
        if k in ex:
            assert m.get(k) == ex[k], f"{loc} {k}: map != Aug-21 extract"
        else:
            assert k in fl, f"{loc} {k}: neither extracted clean nor flagged"


# The 115.1/115.2 matrix rows are printed only in the English column of all seven Aug-21
# papers, so v6.1.0 ships their row labels in English. That is an ACCEPTED hold (patch note,
# "### Coverage hold ACCEPTED"), and the thing that makes it acceptable is that every gap is
# on the translator worklist. This pins that invariant, not the gap: it stays green when a
# later wave fills a key in, and fails only if a key goes missing SILENTLY - absent from the
# map and absent from the flagged corpus Task 45 exports.
Q115X_ROWS = (["Q1141_%d" % i for i in range(1, 7)] + ["Q1141_NONE"]
              + ["Q1142_%d" % i for i in range(1, 8)] + ["Q1142_HAS_OTHER"])


@pytest.mark.parametrize("loc", LOCS)
def test_115x_row_label_gaps_reach_the_task45_worklist(loc):
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    flagged = {r["key"]: r for r in
               json.loads((OUT_F3 / f"{loc}_flagged.json").read_text(encoding="utf-8"))}
    for name in Q115X_ROWS:
        key = "item:" + name
        if m.get(key, "").strip():
            continue  # translated - nothing to account for
        row = flagged.get(key)
        assert row is not None, f"{loc} {key}: no map value and no worklist row (silent drop)"
        assert row["flags"], f"{loc} {key}: worklist row carries no flag"


@pytest.mark.parametrize("loc", LOCS)
def test_115x_yes_no_value_sets_are_translated(loc):
    # The other half of the accepted hold: the rows render an English stem over a TRANSLATED
    # Yes/No value set. If these ever went missing the screens would be fully English and the
    # hold's reasoning ("half-translated by design") would no longer be true.
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    missing = [f"val:{n}_VS1:{code}" for n in Q115X_ROWS for code in (1, 2)
               if not m.get(f"val:{n}_VS1:{code}", "").strip()]
    assert not missing, f"{loc}: untranslated 115.x Yes/No codes {missing}"


def test_f3_hil_ilo_q66_no_longer_english():
    # Task 38 gave HIL/ILO a dialect fill; the import should also land the whole Q66 stem.
    for loc in ("hil", "ilo"):
        m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
        v = m.get("item:Q66_SAME_AS_USUAL", "")
        assert v and not v.startswith("66. Is "), f"{loc}: Q66 still English"


# ------------------------------------------------- Wave 4c (the built .qsf) --
# Task 11 wired the per-language consent into F3/generate_qsf.py; wave 4 is the first
# rebuild that actually runs that loop. These tests pin the ARTEFACT it produces, because
# the maps being right is not the same claim as the question text being WRITTEN per
# language: run them against the live v6.0.3 .qsf
# (`git show HEAD:deliverables/CSPro/F3/PatientSurvey.ent.qsf`) and both consent tests
# fail — that build serves the English consent to all eight languages, with no Aug-21
# stamp, while icf.json already held all seven translations.
QSF = CSPRO / "F3" / "PatientSurvey.ent.qsf"
QSF_LANGS = ["EN", "FIL", "BCL", "BIS", "CEB", "WAR", "HIL", "ILO"]


@lru_cache(maxsize=1)
def _qsf_text():
    return QSF.read_text(encoding="utf-8")


def qsf_question_text(item_name):
    """{LANG: first line of questionText} for one item, straight off the built .qsf.

    The .qsf is a YAML block-scalar file whose consent entries are ~124 KB single lines
    (an inline base64 logo), so it is read as text rather than parsed: a YAML load of the
    whole file costs seconds per test and buys nothing this assertion needs.
    """
    text = _qsf_text()
    start = text.index(f".{item_name}\n")
    end = text.find("\n  - name: ", start)
    block = text[start:end if end != -1 else len(text)]
    out = {}
    for lang in QSF_LANGS:
        m = re.search(r"\n +%s: \|\n +(.*)" % lang, block)
        if m:
            out[lang] = m.group(1)
    return out


@pytest.mark.parametrize("part", ["ICF_PART1", "ICF_PART2"])
def test_qsf_consent_is_rendered_per_language(part):
    q = qsf_question_text(part)
    assert set(q) == set(QSF_LANGS), f"{part}: missing languages {set(QSF_LANGS) - set(q)}"
    same = [lang for lang in QSF_LANGS[1:] if q[lang] == q["EN"]]
    assert not same, f"{part}: still English in {same} (generate_qsf.py consent loop)"


@pytest.mark.parametrize("part", ["ICF_PART1", "ICF_PART2"])
def test_qsf_consent_carries_aug21_stamp(part):
    # Task 9: every locale's consent footer states the Aug-21 questionnaire version,
    # including F3-Tagalog, whose PAPER header still says 06/05.
    q = qsf_question_text(part)
    missing = [lang for lang in QSF_LANGS if "08/21/2026" not in q[lang]]
    assert not missing, f"{part}: no 08/21/2026 stamp in {missing}"


def test_qsf_q66_keeps_the_facility_fill_in_every_language():
    # The translated stems must keep ~~FACILITY_NAME~~ or the desk render shows the
    # dialect sentence with no facility piped into it.
    q = qsf_question_text("Q66_SAME_AS_USUAL")
    missing = [lang for lang in QSF_LANGS if "~~FACILITY_NAME~~" not in q[lang]]
    assert not missing, f"Q66: fill token lost in {missing}"


# --- Task 50 (v6.1.1): the row-inheritance repair -----------------------------------------
# Task 48 proved that the Aug-21 papers lay some option grids out in two columns, so one
# row's translation lands on its neighbour. The extractor now HOLDS those rows; what is
# already on disk is repaired here, on the restore-from-baseline path, by
# aug21-overrides.json. Three shapes, and one test each:
#   * `remove: true`  - the paper carries no distinct translation for the row, so the key is
#     deleted and CSEntry renders the English label (an English option beats a wrong one);
#   * a `keep` write where the paper's own text is an English proper noun (the seven CEB
#     `LGU/ Barangay` rows): the value IS written, and scan_waivers.json carries the reasoned,
#     value-pinned exemption that keeps run_aug21_gates.ps1 gate 1 from reading the write as a
#     new SELF_ECHO/IS_OTHER_EN (v6.1.1 deleted these keys instead - review finding 1);
#   * a released hold - `val:Q10_CIVIL_STATUS_VS1:5` was held for BCL on a wrong reason.
# The fourth test is the permanent gate itself, re-run over the maps on disk.

# (locale, key) -> the value v6.1.0 shipped, i.e. what must NOT be there any more.
REMOVED_ROWS = [
    ("bcl", "val:Q10_CIVIL_STATUS_VS1:6", "Hiwalay"),
    ("bis", "val:Q10_CIVIL_STATUS_VS1:6", "Separada/Separado"),
    ("ceb", "val:Q10_CIVIL_STATUS_VS1:6", "Bulag sa kapikas"),
    ("war", "val:Q10_CIVIL_STATUS_VS1:6", "Nagbulag"),
    ("war", "val:Q10_CIVIL_STATUS_VS1:2", "Minyo"),
    ("hil", "val:Q10_CIVIL_STATUS_VS1:2", "Kasado"),
    ("hil", "val:Q10_CIVIL_STATUS_VS1:4", "Balo"),
    ("bcl", "val:Q98_PAY_SRC_VS1:15", "Iba pa (ispecify)"),
    ("bcl", "val:Q113_PAY_SRC_VS1:13", "Iba pa (ispecify)"),
    ("fil", "val:Q38_2_WHY_NOT_REG_VS1:02", "[Mahirap magparehistro]"),
    ("fil", "val:Q38_2_WHY_NOT_REG_VS1:03", "[Mahirap magparehistro]"),
    ("ilo", "val:Q38_2_WHY_NOT_REG_VS1:08", "Awan ti oras nga agparehistro"),
    ("hil", "val:Q34_WHO_DECIDES_VS1:08", "Tatay sang Pasyente"),
    ("hil", "val:Q34_WHO_DECIDES_VS1:09", "Tatay sang Pasyente"),
    ("hil", "val:Q34_WHO_DECIDES_VS1:10", "Tatay sang Pasyente"),
    ("bcl", "val:Q2_RELATIONSHIP_VS1:02", "Aki"),
    ("bcl", "val:Q2_RELATIONSHIP_VS1:03", "Aki"),
    ("bcl", "val:Q2_RELATIONSHIP_VS1:08", "Apo"),
    ("bcl", "val:Q2_RELATIONSHIP_VS1:09", "Apo"),
    # Not override-driven: the pre-wave map never held these two, and the extractor now HOLDS
    # its `Pamangkin` candidate (Bikol has one word for nephew and niece), so v6.1.0's values
    # simply do not come back on the restore path. Pinned so a future extract cannot re-add
    # the pair silently.
    ("bcl", "val:Q2_RELATIONSHIP_VS1:16", "Pamangkin"),
    ("bcl", "val:Q2_RELATIONSHIP_VS1:17", "Pamangkin"),
]

# The seven CEB `*_SOURCE_VS1:06` rows the review flagged: v6.1.0 shipped code 02's
# `Balaod` (= "Legislation") on the "LGU/ Barangay" option of all seven questions. v6.1.2
# WRITES the paper's own text on them (controller ruling 2026-08-27 06:30 (b)).
CEB_SOURCE_06 = ["val:Q36_UHC_SOURCE_VS1:06", "val:Q75_KON_SOURCE_VS1:06",
                 "val:Q100_BUCAS_SOURCE_VS1:06", "val:Q117_NBB_SOURCE_VS1:06",
                 "val:Q120_ZBB_SOURCE_VS1:06", "val:Q125_MAIFIP_SOURCE_VS1:06",
                 "val:Q153_GAMOT_SOURCE_VS1:06"]


@pytest.mark.parametrize("loc,key,shipped", REMOVED_ROWS,
                         ids=[f"{l}-{k}" for l, k, _ in REMOVED_ROWS])
def test_the_row_inheritance_rows_are_deleted_from_the_f3_maps(loc, key, shipped):
    # ABSENCE, not emptiness: an empty string is still a label as far as the .dcf is
    # concerned, and it would render a blank option instead of the English one.
    m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
    assert key not in m, (f"{loc} {key}: still in the map as {m[key]!r}, so it still renders "
                          f"instead of the English label (v6.1.0 shipped {shipped!r})")


@pytest.mark.parametrize("key", CEB_SOURCE_06)
def test_ceb_source_option_06_reads_lgu_barangay_not_the_legislation_row(key):
    # F3_CEB.txt prints `☐ Legislation / Balaod / ☐ LGU/ Barangay / LGU/Barangay` as one
    # two-column block (1096-1099 for Q36, six more through 5654-5657), and v6.1.0 shipped code
    # 02's `Balaod` on code 06 of all seven questions. The paper's own Cebuano for this option
    # is the untranslated proper noun, and that is what the tablet must show.
    m = json.loads((F3_MAPS / "ceb.json").read_text(encoding="utf-8"))
    assert m.get(key) == "LGU/Barangay", f"ceb {key}: {m.get(key)!r}"


@pytest.mark.parametrize("key", CEB_SOURCE_06)
def test_each_written_ceb_source_row_is_covered_by_a_value_pinned_scan_waiver(key):
    # The write only survives the gate because scan_waivers.json exempts it, and the waiver is
    # pinned to the value - so the two files must agree. If someone edits one, this fails.
    m = json.loads((F3_MAPS / "ceb.json").read_text(encoding="utf-8"))
    waivers = json.loads((CSPRO / "data" / "translations-official" / "scan_waivers.json")
                         .read_text(encoding="utf-8"))
    ent = waivers["F3"]["ceb"][key]
    assert ent["value"] == m[key], f"{key}: waiver pins {ent['value']!r}, map holds {m[key]!r}"
    assert set(ent["reasons"]) <= {"SELF_ECHO", "IS_OTHER_EN"}


def test_bcl_q10_common_law_holds_the_papers_live_in():
    # The released hold. F3_BCL.txt line 377 reads `☐ Common law / Live-in Live-in`, so the
    # Aug-21 value IS `Live-in`; holding it left code 5 on June-5's `Diborsyado`, which is
    # code 2's translation - the direct cause of a RED duplicate-label row.
    m = json.loads((F3_MAPS / "bcl.json").read_text(encoding="utf-8"))
    assert m.get("val:Q10_CIVIL_STATUS_VS1:5") == "Live-in"


def test_no_f3_value_set_ships_two_codes_with_the_same_label():
    # The permanent Task-48 gate, re-run over the seven maps ON DISK - i.e. over the values
    # that are about to be built into the .dcf - so it fails on ANY future duplicate, not
    # just the ones this task repaired. It carries the gate's own two exemptions (identical
    # English, keys the dictionary no longer defines).
    sys.path.insert(0, str(CSPRO / "data" / "translations-official"))
    import apply_aug21

    english = apply_aug21.dcf_english("F3")
    bad = []
    for loc in LOCS:
        m = json.loads((F3_MAPS / f"{loc}.json").read_text(encoding="utf-8"))
        for row in apply_aug21.duplicate_label_rows(m, english):
            bad.append(f"{loc} {row['value_set']} codes {','.join(row['codes'])} "
                       f"both read {row['value']!r}")
    assert not bad, "duplicate option labels live in F3:\n    " + "\n    ".join(bad)
