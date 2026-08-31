import importlib.util
import json
import sys
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CSPRO))
sys.path.insert(0, str(CSPRO / "F1"))

from cspro_helpers import _cap_text          # noqa: E402  (needs the sys.path above)

Q75_AUG21 = ("75. The maximum per capita rate amount for YAKAP/Konsulta is at Php 1,700 "
             "across private and public facilities (40% after first patient encounter, "
             "60% based on registered catchment population by December). "
             "Based on your practice, is this enough?")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _f1_items():
    gen = _load("f1_generate_dcf", CSPRO / "F1" / "generate_dcf.py")
    d = gen.build_dictionary()
    out = {}
    for lvl in d["levels"]:
        for rec in lvl["records"]:
            for it in rec["items"]:
                out[it["name"]] = it
    return out


def test_q75_label_matches_aug21_paper():
    it = _f1_items()["Q75_IS_1700_ENOUGH"]
    assert it["labels"][0]["text"] == Q75_AUG21
    assert len(Q75_AUG21) <= 255          # CSPro label cap (252 chars today)


def test_q75_value_set_codes_unchanged():
    it = _f1_items()["Q75_IS_1700_ENOUGH"]
    codes = [v["pairs"][0]["value"] for v in it["valueSets"][0]["values"]]
    assert codes == ["1", "2", "3"]       # Yes / No / I don't know — yes_no_dk


def test_capitation_regex_still_fires_on_aug21_stem():
    qsf = _load("f1_generate_qsf", CSPRO / "F1" / "generate_qsf.py")
    m = qsf._CAPITATION_RE.match(f"<p>{Q75_AUG21}</p>")
    assert m is not None
    assert m.group(2) == "Php 1,700"


F1_TR = CSPRO / "F1" / "translations"
OUT_AUG21 = CSPRO / "data" / "translations-official" / "out-aug21" / "F1"
LOCALES = ["fil", "bcl", "bis", "ceb", "war", "hil", "ilo"]
Q75_KEYS = ["item:Q75_IS_1700_ENOUGH", "vs:Q75_IS_1700_ENOUGH_VS1"]


def _map(loc):
    return json.loads((F1_TR / f"{loc}.json").read_text(encoding="utf-8"))


def _extracted(loc):
    return json.loads((OUT_AUG21 / f"{loc}.json").read_text(encoding="utf-8"))


def _flagged_keys(loc):
    rows = json.loads((OUT_AUG21 / f"{loc}_flagged.json").read_text(encoding="utf-8"))
    return {r["key"] for r in rows}


def test_f1_maps_carry_aug21_provenance():
    for loc in LOCALES:
        m = _map(loc)
        src = m["_meta"].get("sources", {}).get("aug21")
        assert src, f"{loc}: no _meta.sources.aug21 block"
        assert set(src) >= {"date", "file", "n_written", "n_replaced", "n_overridden"}


def test_f1_maps_name_scoped():
    for loc in LOCALES:
        assert all(":" in k for k in _map(loc) if k != "_meta"), f"{loc}: legacy key present"


def test_f1_q75_holds_the_aug21_value_or_is_flagged():
    """Aug-21 wins: for every locale the map value must equal what the Aug-21
    extractor emitted (clean), else the key must sit in the flagged worklist —
    a June-5 value surviving silently is the failure this catches."""
    for loc in LOCALES:
        m, ex, fl = _map(loc), _extracted(loc), _flagged_keys(loc)
        for k in Q75_KEYS:
            if k in ex:
                assert m.get(k) == ex[k], f"{loc} {k}: map != Aug-21 extract"
            else:
                assert k in fl, f"{loc} {k}: neither extracted clean nor flagged"


def test_versions_json_f1_is_at_least_4_1_0():
    """F1 carries the Aug-21 import build or a later patch of it, on the DEV channel.

    A floor rather than `== "4.1.0"` (controller ruling, post-Task 18): the next UAT patch
    bump must not turn a green suite red, while a rollback to a build that predates the
    Aug-21 import - or a premature flip to the `release` channel - still fails.
    """
    v = json.loads((CSPRO / "versions.json").read_text(encoding="utf-8"))
    assert tuple(int(n) for n in v["F1"]["version"].split(".")) >= (4, 1, 0), v["F1"]["version"]
    assert v["F1"]["channel"] == "dev"


def test_built_dcf_carries_aug21_q75_values():
    """The regenerated dcf must carry the SAME values the maps now hold (i.e. the
    Aug-21 extract), not merely 'something non-English'."""
    d = json.loads((CSPRO / "F1" / "FacilityHeadSurvey.dcf").read_text(encoding="utf-8"))
    it = next(i for l in d["levels"] for r in l["records"] for i in r["items"]
              if i["name"] == "Q75_IS_1700_ENOUGH")
    by_lang = {l["language"]: l["text"] for l in it["labels"]}
    assert by_lang["EN"] == Q75_AUG21
    for loc in LOCALES:
        # write_dcf stores _cap_text(value): CSPro rejects any label over 255 chars, and
        # the Q75 translation runs 403-450 chars in fil/bcl/ceb/hil. Compare against the
        # same helper apply_translations keys off, never against a hand-copied truncation.
        expected = _cap_text(_map(loc).get("item:Q75_IS_1700_ENOUGH", Q75_AUG21))
        assert by_lang[loc.upper()] == expected, f"{loc}: dcf label != map value"


from byte_verify_aug21 import pen_bytes_from_zip, probe          # noqa: E402


def test_probe_finds_utf16le_terms():
    blob = ("xx".encode("utf-16-le") + "Ano ang iyong pangalan".encode("utf-16-le")
            + b"\x00\x00")
    assert probe(blob, "Ano ang iyong pangalan") is True
    assert probe(blob, "Batay sa inyong praktis") is False
    # odd-offset case: whole-blob decode would misalign, bytes.find must not
    assert probe(b"\x00" + blob, "Ano ang iyong pangalan") is True


import zipfile                                                   # noqa: E402
import pytest                                                    # noqa: E402
from byte_verify_aug21 import LOCALES, PROBE_KEYS, main, sample_probes   # noqa: E402


def _fake_maps(d, values):
    """values: {key: template}; '{loc}' in the template makes it per-locale."""
    d.mkdir(parents=True, exist_ok=True)
    for loc in LOCALES:
        body = {k: v.format(loc=loc) for k, v in values.items()}
        (d / f"{loc}.json").write_text(json.dumps(body), encoding="utf-8")


def _fake_pack(zip_path, terms):
    blob = b"".join(t.encode("utf-16-le") for t in terms)
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("App.pen", blob)      # stored raw: pen_bytes_from_zip falls back


def test_sample_probes_labels_wave_changed_rows(tmp_path):
    live, base = tmp_path / "live", tmp_path / "base"
    _fake_maps(live, {"item:FRESH": "aug21 {loc} text", "item:SURVIVOR": "june5 {loc} text"})
    _fake_maps(base, {"item:FRESH": "june5 {loc} text", "item:SURVIVOR": "june5 {loc} text"})
    rows = sample_probes(live, ["item:FRESH", "item:SURVIVOR"], base)
    flags = {(loc, key): changed
             for (loc, label, _t, changed) in rows
             for key in ["item:FRESH", "item:SURVIVOR"] if key in label}
    assert all(flags[(loc, "item:FRESH")] is True for loc in LOCALES)
    assert all(flags[(loc, "item:SURVIVOR")] is False for loc in LOCALES)
    assert "[wave-changed]" in next(l for (_lo, l, _t, c) in rows if c is True)
    # no baseline -> no verdict, and the old 2-tuple information is unchanged
    assert all(c is None for (_lo, _l, _t, c) in sample_probes(live, ["item:FRESH"]))


def test_main_fails_when_no_locale_has_a_wave_changed_probe(tmp_path):
    """The Task-19 review defect: every probe a survivor -> ALL PASS proves nothing."""
    live, base = tmp_path / "live", tmp_path / "base"
    survivors = {"item:SURVIVOR": "june5 {loc} text"}
    _fake_maps(live, survivors)
    _fake_maps(base, survivors)
    zp = tmp_path / "App.zip"
    _fake_pack(zp, [f"june5 {loc} text" for loc in LOCALES])
    out = tmp_path / "bv.txt"
    with pytest.raises(SystemExit) as e:
        main(["F4", str(zp), str(live), str(out), "--probe", "item:SURVIVOR",
              "--baseline", str(base)])
    assert e.value.code == 1
    text = out.read_text(encoding="utf-8")
    assert "MISS FIL has >=1 wave-changed" in text
    assert "RESULT: FAIL" in text
    assert "[unchanged-since-baseline]" in text


def test_main_passes_when_every_locale_has_a_wave_changed_probe(tmp_path):
    live, base = tmp_path / "live", tmp_path / "base"
    _fake_maps(live, {"item:FRESH": "aug21 {loc} text"})
    _fake_maps(base, {"item:FRESH": "june5 {loc} text"})
    zp = tmp_path / "App.zip"
    _fake_pack(zp, [f"aug21 {loc} text" for loc in LOCALES] + ["v9.9.9"])
    out = tmp_path / "bv.txt"
    with pytest.raises(SystemExit) as e:
        main(["F4", str(zp), str(live), str(out), "--probe", "item:FRESH",
              "--baseline", str(base), "--version", "v9.9.9"])
    assert e.value.code == 0
    text = out.read_text(encoding="utf-8")
    assert "RESULT: ALL PASS" in text
    assert all(f"OK   {loc.upper()} has >=1 wave-changed" in text for loc in LOCALES)


def test_f1_probe_keys_give_every_locale_a_real_map_value(tmp_path):
    """Guards the other half of the defect: a locale whose probes all SKIP is unverified."""
    for loc in LOCALES:
        m = _map(loc)
        hits = [k for k in PROBE_KEYS["F1"] if isinstance(m.get(k), str)]
        assert len(hits) >= 2, f"{loc}: only {hits} of PROBE_KEYS['F1'] resolve"
# --- Task 49b: F1 v4.1.1, the confirmed row-inheritance instances -------------------------
#
# Two F1 option rows shipped in v4.1.0 carrying a NEIGHBOURING row's translation
# (Task 48 §5, "Real, mechanism 1/2"). The Aug-21 paper prints no distinct text for
# either, so the honest outcome is to delete the map row and let English render -
# expressed as a `remove: true` entry in aug21-overrides.json, never by hand-editing a
# map. The third row (bcl Q83 code 02) IS translated on the paper; its clean span is
# accepted with a `keep: "<text>"` override so the restore-from-baseline path cannot
# hand it back the June-5 value with the English tail glued on.

F1_REMOVED_ROWS = {
    "bcl": {"val:Q83_NOT_RECEIVED_REASONS_VS1:03"},   # was code 02's "Pagka-antala sa tracking ..."
    "fil": {"val:Q45_PERF_INDICATORS_VS1:04"},        # was code 03's "... antibiotics ..."
}
BCL_Q83_02 = "Pagka-antala sa tracking kan patient enrollment"


def test_the_row_inheritance_rows_are_deleted_from_the_f1_maps():
    """A removed row must be ABSENT, not blanked: an empty string is still a label."""
    for loc, keys in F1_REMOVED_ROWS.items():
        m = _map(loc)
        for k in keys:
            assert k not in m, f"{loc} {k}: still in the map, so it still renders"


def test_bcl_q83_code_02_keeps_the_clean_span_not_the_glued_june5_value():
    v = _map("bcl").get("val:Q83_NOT_RECEIVED_REASONS_VS1:02")
    assert v == BCL_Q83_02, repr(v)


def test_no_f1_value_set_ships_two_codes_with_the_same_label():
    """The permanent gate (apply_aug21.duplicate_label_rows) re-run over the LIVE maps.

    The apply gate judges the map an apply would leave behind; this judges the map that
    is actually on disk and therefore about to be built into the .dcf. Exemptions are the
    gate's own two: identical English, and a key the dictionary no longer defines.
    """
    sys.path.insert(0, str(CSPRO / "data" / "translations-official"))
    from apply_aug21 import dcf_english, duplicate_label_rows   # noqa: E402

    english = dcf_english("F1")
    bad = []
    for loc in LOCALES:
        for row in duplicate_label_rows(_map(loc), english):
            bad.append(f"{loc} {row['value_set']} codes {','.join(row['codes'])} "
                       f"both read {row['value']!r}")
    assert not bad, "duplicate option labels live in F1:\n  " + "\n  ".join(bad)
