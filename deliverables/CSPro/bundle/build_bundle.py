#!/usr/bin/env python
"""
Deployable-bundle assembler for the CAPI instruments (GOAL criterion #7).

Assembles, per instrument, the files CSWeb dictionary-upload + tablet deploy need:
the Designer-bound `.ent` + its `.dcf` / `.fmf` / `.ent.apc`, beside a `shared/`
folder holding the two #include'd helper `.apc`s and the 4 PSGC external dicts +
their `.dat` lookups. The layout preserves the `../shared/` relative #include so
the bundled `.ent.apc` resolves exactly as in the source tree.

WHY a script, not pre-copied files: the artifacts regenerate on every IRON-RULE
fix-loop and the `.ent` is re-bound on every Designer compile. A static copy would
go stale instantly; this assembles from the *current* artifacts on demand, so
"the bundle exists" is one command the moment each `.ent` is produced.

The `.ent` is the ONLY input this script cannot produce — Designer binds it (no
honest headless entry compile; verified runbook 2026-06-04). Until it exists for
an instrument, that bundle reports PENDING and is skipped by --assemble.

Usage:
  python build_bundle.py            # audit: per-instrument readiness, nothing written
  python build_bundle.py --assemble # copy current artifacts into dist/<INSTRUMENT>/ (+ dist/shared/)
"""
import shutil, sys
from pathlib import Path

CSPRO = Path(__file__).resolve().parent.parent          # deliverables/CSPro
SHARED = CSPRO / "shared"
DIST = Path(__file__).resolve().parent / "dist"

# Shared payload every instrument bundle needs (resolved via ../shared from the .ent.apc).
SHARED_FILES = [
    "Capture-Helpers.apc", "PSGC-Cascade.apc",
    "psgc_region.dcf", "psgc_province.dcf", "psgc_city.dcf", "psgc_barangay.dcf",
    "psgc_region.dat", "psgc_province.dat", "psgc_city.dat", "psgc_barangay.dat",
]

# Per-instrument files. `ent` is the Designer-bound app (PENDING until it exists).
# Components are exactly the files the .ent references (by filename) and that CSEntry
# loads at runtime: the input .dcf, the bound .fmf (the plain one — the .ent binds
# <stem>.fmf, NOT <stem>.generated.fmf), the logic .ent.apc, the multi-language
# question text .ent.qsf, and the messages .ent.mgf.
INSTRUMENTS = {
    "F1": {"dir": "F1", "stem": "FacilityHeadSurvey",
           "components": ["FacilityHeadSurvey.dcf", "FacilityHeadSurvey.fmf",
                          "FacilityHeadSurvey.ent.apc", "FacilityHeadSurvey.ent.qsf",
                          "FacilityHeadSurvey.ent.mgf"],
           "ent": "FacilityHeadSurvey.ent"},
    "F3": {"dir": "F3", "stem": "PatientSurvey",
           "components": ["PatientSurvey.dcf", "PatientSurvey.fmf",
                          "PatientSurvey.ent.apc", "PatientSurvey.ent.qsf",
                          "PatientSurvey.ent.mgf"],
           "ent": "PatientSurvey.ent"},
    "F4": {"dir": "F4", "stem": "HouseholdSurvey",
           "components": ["HouseholdSurvey.dcf", "HouseholdSurvey.fmf",
                          "HouseholdSurvey.ent.apc", "HouseholdSurvey.ent.qsf",
                          "HouseholdSurvey.ent.mgf"],
           "ent": "HouseholdSurvey.ent"},
}


def audit():
    print("=== Deployable-bundle readiness (GOAL criterion #7) ===\n")
    shared_ok = all((SHARED / f).exists() for f in SHARED_FILES)
    missing_shared = [f for f in SHARED_FILES if not (SHARED / f).exists()]
    print(f"shared/ payload: {'ALL PRESENT' if shared_ok else 'MISSING ' + ', '.join(missing_shared)}"
          f"  ({len(SHARED_FILES)} files)\n")
    ready = []
    for key, spec in INSTRUMENTS.items():
        idir = CSPRO / spec["dir"]
        comp_missing = [c for c in spec["components"] if not (idir / c).exists()]
        ent_path = idir / spec["ent"]
        ent_ok = ent_path.exists()
        # Freshness gate (content-based, NOT mtime): the .ent is a JSON manifest that
        # REFERENCES its files by name -- CSEntry reads the current files at load, so an
        # older .ent mtime is not staleness. What matters is that the .ent points at every
        # component + the 4 PSGC externals. (Verified 2026-06-08: all three load+run in
        # CSEntry from the current generator artifacts, no Designer re-bind needed.)
        ent_missing_refs = []
        if ent_ok and not comp_missing:
            ent_text = ent_path.read_text(encoding="utf-8-sig")
            expected_refs = list(spec["components"]) + [f"psgc_{x}.dcf" for x in ("region", "province", "city", "barangay")]
            ent_missing_refs = [r for r in expected_refs if r not in ent_text]
        ent_stale = bool(ent_missing_refs)
        comp_state = "all components present" if not comp_missing else f"MISSING {', '.join(comp_missing)}"
        if not ent_ok:
            ent_state = "PENDING (.ent not yet created)"
        elif ent_missing_refs:
            ent_state = "MISBOUND (.ent does not reference: " + ", ".join(ent_missing_refs) + ")"
        else:
            ent_state = "PRESENT & current (references all components + PSGC externals)"
        bundle_state = "READY" if (ent_ok and not ent_stale and not comp_missing and shared_ok) else "BLOCKED"
        if bundle_state == "READY":
            ready.append(key)
        print(f"[{key}] {spec['stem']}: bundle {bundle_state}")
        print(f"     components: {comp_state}")
        print(f"     .ent      : {ent_state}\n")
    summary = ", ".join(ready) if ready else "none -- each waits on its Designer-bound .ent"
    print(f"Ready to assemble now: {summary}")
    return ready


def assemble(ready):
    if not ready:
        print("Nothing to assemble — no instrument has its .ent yet.")
        return
    (DIST / "shared").mkdir(parents=True, exist_ok=True)
    for f in SHARED_FILES:
        shutil.copy2(SHARED / f, DIST / "shared" / f)
    for key in ready:
        spec = INSTRUMENTS[key]
        out = DIST / spec["dir"]
        out.mkdir(parents=True, exist_ok=True)
        idir = CSPRO / spec["dir"]
        for c in spec["components"] + [spec["ent"]]:
            shutil.copy2(idir / c, out / c)
        print(f"[{key}] assembled -> {out}")
    print(f"\nBundle written to {DIST}  (dist/shared + dist/<INSTRUMENT> per ready instrument).")


if __name__ == "__main__":
    ready = audit()
    if "--assemble" in sys.argv:
        print("\n--- assembling ---")
        assemble(ready)
