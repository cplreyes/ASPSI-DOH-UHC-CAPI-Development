"""F3 (wave 4) byte-verify tests: probes whose map value carries a source-side fill token.

Found on the 2026-08-27 v6.1.0 deploy. `item:Q66_SAME_AS_USUAL` is wave-changed in all
seven locales, which made it the natural gate probe -- but its map value contains the
literal `[facility_name_input]` placeholder, and generate_dcf.py's #714 pass rewrites that
token to a per-language neutral noun-phrase BEFORE the label reaches the package. The
literal bytes therefore can never be in the .pen, so the verifier reported MISS on a
package that was in fact correct: a false negative that would have sent an operator back
to re-publish a good build.

The verifier now renders such a probe through the instrument's OWN neutralisation pass
(imported from its generator, so the two cannot drift) and probes the rendered form.
"""
import json
import sys
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CSPRO = HERE.parent
sys.path.insert(0, str(HERE))

from byte_verify_aug21 import (  # noqa: E402
    LOCALES, _facility_renderer, main, sample_probes,
)

F3_MAPS = CSPRO / "F3" / "translations"

# A stand-in for an instrument generator, so the mechanism is tested without depending on
# F3's real wording. Same three names generate_dcf.py exports.
FAKE_GENERATOR = '''
import re
_FACILITY_PLACEHOLDER_RE = re.compile(r"\\[facility_name_input\\]")
_FACILITY_NEUTRAL = {"EN": "this facility", "FIL": "ang pasilidad na ito",
                     "BCL": "an pasilidad na ini", "BIS": "kini nga pasilidad",
                     "CEB": "kini nga pasilidad", "WAR": "ini nga pasilidad",
                     "HIL": "ini nga pasilidad", "ILO": "daytoy a pasilidad"}
_PLACEHOLDER_CLEANUPS = [(re.compile(r"\\bang ang\\b"), "ang")]
'''


def _instrument(tmp_path, with_generator=True):
    """A fake <INST>/ dir holding translations/ and (optionally) generate_dcf.py."""
    inst = tmp_path / "FX"
    (inst / "translations").mkdir(parents=True)
    if with_generator:
        (inst / "generate_dcf.py").write_text(FAKE_GENERATOR, encoding="utf-8")
    return inst


def _write_maps(d, values):
    for loc in LOCALES:
        (d / f"{loc}.json").write_text(json.dumps(values), encoding="utf-8")


def _pack(zip_path, terms):
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("App.pen", b"".join(t.encode("utf-16-le") for t in terms))


def test_placeholder_probe_matches_the_rendered_label(tmp_path):
    """The package carries the NEUTRALISED label; the probe must find it, not MISS."""
    inst = _instrument(tmp_path)
    maps = inst / "translations"
    base = tmp_path / "base"
    base.mkdir()
    _write_maps(maps, {"item:Q66": "Ang [facility_name_input] ba ang pasilidad?"})
    _write_maps(base, {"item:Q66": "june5 wording"})
    # exactly what generate_dcf writes: the placeholder replaced per language
    _pack(tmp_path / "App.zip",
          ["Ang ang pasilidad na ito ba ang pasilidad?",      # FIL, pre-cleanup form
           "Ang an pasilidad na ini ba ang pasilidad?",       # BCL
           "Ang kini nga pasilidad ba ang pasilidad?",        # BIS + CEB
           "Ang ini nga pasilidad ba ang pasilidad?",         # WAR + HIL
           "Ang daytoy a pasilidad ba ang pasilidad?",        # ILO
           "v1.0.0"])
    out = tmp_path / "bv.txt"
    with pytest.raises(SystemExit) as e:
        main(["F4", str(tmp_path / "App.zip"), str(maps), str(out),
              "--probe", "item:Q66", "--baseline", str(base), "--version", "v1.0.0"])
    text = out.read_text(encoding="utf-8")
    assert e.value.code == 0, text
    assert "MISS" not in text
    assert "[dcf-rendered]" in text, "a rendered probe must say so in the report"


def test_placeholder_probe_still_misses_a_package_without_the_label(tmp_path):
    """The rendering must not turn the probe into a rubber stamp."""
    inst = _instrument(tmp_path)
    maps = inst / "translations"
    _write_maps(maps, {"item:Q66": "Ang [facility_name_input] ba ang pasilidad?"})
    _pack(tmp_path / "App.zip", ["something else entirely"])
    out = tmp_path / "bv.txt"
    with pytest.raises(SystemExit) as e:
        main(["F4", str(tmp_path / "App.zip"), str(maps), str(out), "--probe", "item:Q66"])
    assert e.value.code == 1
    assert "MISS" in out.read_text(encoding="utf-8")


def test_instrument_without_the_pass_probes_literally(tmp_path):
    """F1/F4 have no #714 pass: no generator constants -> unchanged literal behaviour."""
    inst = _instrument(tmp_path, with_generator=False)
    maps = inst / "translations"
    _write_maps(maps, {"item:Q1": "Ano ang iyong pangalan?"})
    assert _facility_renderer(maps) is None
    rows = sample_probes(maps, ["item:Q1"])
    assert all(term == "Ano ang iyong pangalan?" for (_l, _lab, term, _c) in rows)
    assert all("[dcf-rendered]" not in lab for (_l, lab, _t, _c) in rows)


def test_values_without_a_placeholder_are_left_alone(tmp_path):
    inst = _instrument(tmp_path)
    maps = inst / "translations"
    _write_maps(maps, {"item:Q98": "Gingamit mo ba an bisan hain?"})
    rows = sample_probes(maps, ["item:Q98"], render=_facility_renderer(maps))
    assert all(term == "Gingamit mo ba an bisan hain?" for (_l, _lab, term, _c) in rows)
    assert all("[dcf-rendered]" not in lab for (_l, lab, _t, _c) in rows)


@pytest.mark.skipif(not F3_MAPS.exists(), reason="F3 maps not in this checkout")
def test_f3_q66_renders_through_the_real_generator():
    """Bind the mechanism to the shipped F3 pass, not just the stand-in."""
    render = _facility_renderer(F3_MAPS)
    assert render is not None, "F3/generate_dcf.py must expose the #714 constants"
    raw = json.loads((F3_MAPS / "hil.json").read_text(encoding="utf-8"))["item:Q66_SAME_AS_USUAL"]
    assert "[facility_name_input]" in raw
    out = render(raw, "HIL")
    assert "[facility_name_input]" not in out
    assert "ini nga pasilidad" in out
    # a value with no placeholder is reported as "nothing to render"
    assert render("plain text", "HIL") is None
