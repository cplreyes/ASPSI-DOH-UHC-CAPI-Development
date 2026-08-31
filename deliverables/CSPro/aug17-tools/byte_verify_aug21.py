"""Byte-verify a CSWeb-served package against the translation maps (2026-08-14 method:
bz2-decompress the .pen, search each probe as UTF-16LE bytes with bytes.find — whole-blob
decode gives false negatives at odd offsets).
Usage: py byte_verify_aug21.py <INST> <App.zip> <INST/translations> <out.txt>
                                [--version vX.Y.Z] [--deploy-shot SRC.png DST.png]
                                [--count "<term>" <n>] [--probe <key>]
                                [--baseline <pre-wave maps dir>]
Used by every wave (F1 Task 19, F4 Task 32, F3 Task 42). Exit 1 on any MISS.

PROBE_KEYS holds *presence* probes only. A probe whose map value did not change in the
wave being deployed proves nothing about that wave: the previous package already carried
that byte string, so an OK on it is a survivor, not a discriminator. Pass --baseline with
the pre-wave maps (e.g. `git show HEAD:<INST>/translations/<loc>.json` dumped to a temp
dir) and the tool labels every row [wave-changed] / [unchanged-since-baseline] and FAILs
unless every locale has at least one OK on a wave-changed probe. Use --probe to add
wave-specific keys without editing PROBE_KEYS.

NOTE for Tasks 32/41 - PROBE_KEYS['F4'] / ['F3'] audited 2026-08-26 against the Aug-21
extracts then present in data/translations-official/out-aug21/:
  F4 (fil extracted only so far): all 5 keys are absent from the extract -> the apply will
     not touch them -> ZERO discriminators. Task 32 must add --probe keys.
  F3 (all 7 locales extracted): only item:Q972_SOURCES is changed by the extract; the other
     4 are absent from it. One discriminator per locale, so --baseline will pass, but Task 41
     should add a second --probe key rather than rely on a single row.
Re-audit at apply time - the extracts move as English alignment lands.

Superseded for F3 by the 2026-08-27 deploy: the fix-round-1 holds left item:Q972_SOURCES
absent in CEB and HIL, so Task 42 ran with --probe item:Q98_SOURCES and
--probe val:Q107_SOURCES_VS1:05 (both wave-changed in all 7). item:Q66_SAME_AS_USUAL is a
placeholder-carrying key - see _facility_renderer().
"""
import bz2
import importlib.util
import json
import shutil
import sys
import zipfile
from pathlib import Path

LOCALES = ("fil", "bcl", "bis", "ceb", "war", "hil", "ilo")

PROBE_KEYS = {
    # F1: the last two are Aug-21 wave discriminators (values that did not exist anywhere
    # in the pre-wave v4.0.0 maps, changed in all 7 locales).
    "F1": ["item:Q75_IS_1700_ENOUGH", "val:Q75_IS_1700_ENOUGH_VS1:3", "item:Q1_NAME",
           "item:Q20_EMR_USE", "item:Q123_NBB_ALL_PATIENTS"],
    "F4": ["item:Q30_NAME", "item:Q35_HAS_DISABILITY", "item:Q36_SPECIFY_DISABILITY",
           "item:Q40_EDUCATION", "item:Q67_TRAVEL_HH"],
    "F3": ["item:Q47_PHYSICIAN_CHECKUP", "item:Q972_SOURCES", "val:Q972_SOURCES_VS1:90",
           "item:Q1142_HAS_OTHER", "item:Q66_SAME_AS_USUAL"],
}


def pen_bytes_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        pen = next(n for n in z.namelist() if n.lower().endswith(".pen"))
        raw = z.read(pen)
    try:
        return bz2.decompress(raw)
    except OSError:
        return raw


def probe(blob, term):
    return blob.find(term.encode("utf-16-le")) >= 0


def count(blob, term):
    """How many times a term occurs as UTF-16LE bytes (overlaps not counted)."""
    return blob.count(term.encode("utf-16-le"))


def _load_map(maps_dir, loc):
    return json.loads((Path(maps_dir) / f"{loc}.json").read_text(encoding="utf-8"))


def _facility_renderer(maps_dir):
    """Return render(text, LOC) -> rendered text, or None when there is nothing to render.

    Some map values hold a SOURCE-side fill token -- F3's `[facility_name_input]` and its
    dialect spellings -- which generate_dcf.py's #714 pass rewrites to a per-language
    neutral noun-phrase before the label ever reaches the package. Probing the literal map
    value for those keys is a guaranteed false MISS (2026-08-27, F3 v6.1.0: five OK rows
    and seven MISSes on `item:Q66_SAME_AS_USUAL`, on a package that was correct).

    The pass is imported from the instrument's OWN generator rather than restated here, so
    the verifier cannot drift from the build. Instruments with no such pass (F1, F4) have
    none of these names and get None -- literal probing, unchanged.
    """
    gen = Path(maps_dir).resolve().parent / "generate_dcf.py"
    if not gen.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"_bv_gen_{gen.parent.name}", gen)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(gen.parent))          # the generator imports its own siblings
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                     # a generator we cannot load must not
        print(f"  (facility renderer unavailable: {exc})")   # break the verify run
        return None
    finally:
        sys.path.remove(str(gen.parent))
    rx = getattr(mod, "_FACILITY_PLACEHOLDER_RE", None)
    neutral = getattr(mod, "_FACILITY_NEUTRAL", None)
    if rx is None or not neutral:
        return None
    cleanups = getattr(mod, "_PLACEHOLDER_CLEANUPS", [])

    def render(text, loc):
        if not rx.search(text):
            return None
        out = rx.sub(neutral.get(loc, neutral.get("EN", "this facility")), text)
        for pat, sub in cleanups:
            out = pat.sub(sub, out)
        return out

    return render


def sample_probes(maps_dir, keys, baseline_dir=None, render=None):
    """(locale, label, term-or-None, changed-or-None) per locale x key.

    `changed` is None when no baseline was given, True when the map value differs from
    the baseline (pre-wave) value for that key, False when it is a survivor. It is always
    decided on the RAW map value -- rendering changes what bytes to look for, never
    whether the wave touched the key.
    """
    out = []
    for loc in LOCALES:
        m = _load_map(maps_dir, loc)
        base = _load_map(baseline_dir, loc) if baseline_dir else None
        for k in keys:
            v = m.get(k)
            if not isinstance(v, str):
                out.append((loc, f"{loc.upper()} {k} (no map value - English fallback)",
                            None, None))
                continue
            changed = None
            tag = ""
            if base is not None:
                changed = base.get(k) != v
                tag = " [wave-changed]" if changed else " [unchanged-since-baseline]"
            term = v
            if render is not None:
                rendered = render(v, loc.upper())
                if rendered is not None:
                    term, tag = rendered, tag + " [dcf-rendered]"
            out.append((loc, f"{loc.upper()} {k}{tag}", term[:60], changed))
    return out


def main(argv):
    inst, zip_path, maps_dir, out = argv[:4]
    rest = argv[4:]
    version = rest[rest.index("--version") + 1] if "--version" in rest else None
    baseline = rest[rest.index("--baseline") + 1] if "--baseline" in rest else None
    counts = []
    i = 0
    while True:
        try:
            i = rest.index("--count", i)
        except ValueError:
            break
        counts.append((rest[i + 1], int(rest[i + 2])))
        i += 3
    extra = []
    i = 0
    while True:
        try:
            i = rest.index("--probe", i)
        except ValueError:
            break
        extra.append(rest[i + 1])
        i += 2
    if "--deploy-shot" in rest:
        i = rest.index("--deploy-shot")
        shutil.copyfile(rest[i + 1], rest[i + 2])
    blob = pen_bytes_from_zip(zip_path)
    lines = [f"--- {inst} byte-verify {zip_path} ---", f"pen bytes: {len(blob)}"]
    if baseline:
        lines.append(f"baseline (pre-wave) maps: {baseline}")
    ok_all = True
    keys = PROBE_KEYS[inst] + extra
    rows = sample_probes(maps_dir, keys, baseline, render=_facility_renderer(maps_dir))
    changed_ok = {loc: False for loc in LOCALES}
    for loc, label, term, changed in rows:
        if term is None:
            lines.append(f"SKIP {label}")
            continue
        ok = probe(blob, term)
        ok_all &= ok
        if ok and changed:
            changed_ok[loc] = True
        lines.append(f"{'OK  ' if ok else 'MISS'} {label}: {term!r}")
    if version:
        ok = probe(blob, version)
        ok_all &= ok
        lines.append(f"{'OK  ' if ok else 'MISS'} footer version "
                     f"(non-truncation signal): {version!r}")
    for term, want in counts:
        got = count(blob, term)
        ok = got == want
        ok_all &= ok
        lines.append(f"{'OK  ' if ok else 'MISS'} occurs {got}x (want {want}x): {term!r}")
    if baseline:
        for loc in LOCALES:
            ok = changed_ok[loc]
            ok_all &= ok
            lines.append(f"{'OK  ' if ok else 'MISS'} {loc.upper()} has >=1 wave-changed "
                         f"probe present in the served pack")
    lines.append("RESULT: " + ("ALL PASS" if ok_all else "FAIL"))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
