"""build_all.py — orchestrate generators across all UHC instruments + emit a
compile manifest for the human-driven `.ent` -> `.pen` step.

Why a human step? CSPro 8.0 has no documented CLI for compiling `.ent` to `.pen`.
The compile is done by CSPro Designer's *File -> Publish Entry Application (F7)*.
See docs/superpowers/runbooks/cspro-publish-entry-runbook.md for the manual SOP.

Usage:
    python build_all.py --env=dev               # generate all sources for dev env
    python build_all.py --env=dev --only=F1     # iterate on F1 alone
    python build_all.py --env=uat               # generate for UAT (LAN IP)
    python build_all.py --env=prod              # post-VPS, when ready

After this script runs successfully, you open each emitted `.ent` in CSPro
Designer and press F7 to produce the `.pen`. The script prints the file list
at the end as a checklist.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from shared.env_loader import load_env, splice_user_settings


WORKSPACE = Path(__file__).resolve().parent

# (numeric_prefix, short_name, dir_name, ent_filename)
# Phase 1 builds F1 + F3LIST + F3 + F4 (all quartet-complete as of
# 2026-05-12). Login + menu parked at 101_login/ and 106_menu/ (on-disk
# but not built); reactivated in Phase 2 alongside the chain rebuild.
# F3LIST = the 110_F3_listing patient listing CAPI app; its compiled .pen
# is consumed by the listing-side menu launch entry (Phase 2 menu rebuild)
# and its output PATIENTLISTING_DICT is consumed by F3/F4 entry apps as
# an EXTERNAL dictionary.
# F3 = the 111_F3 Patient Survey CAPI app (2026-05-12 quartet build); it
# declares PATIENTLISTING_DICT as an EXTERNAL dictionary so the case-open
# patient-pick PROC can query the listing roster and write F3_STATUS back
# at case-open / case-save / refusal. F3 follows F3LIST in INSTRUMENTS so
# the listing DCF is generated before F3's ENT references it.
# F4 = the 115_F4 Household Survey CAPI app (2026-05-12 quartet build);
# it declares F4LISTING_DICT (../113_F4_listing/F4Listing.dcf) as an
# EXTERNAL dictionary for the household-pick PROC. Until the 113_F4_listing
# app lands (task #7 of the F4 rebuild plan), the household-pick PROC is
# stubbed -- PickHousehold() returns 0 and the enumerator enters
# HH_LISTING_NO manually in FIELD_CONTROL. F4_PARENT_F3_CASE_SEQ defaults
# to 999 (NA per F-series convention) on the barangay-listing sampling
# path. CSPro Designer F7 publish on F4 will fail until F4Listing.dcf
# exists; this is the expected state for the interim phase.
INSTRUMENTS = [
    ("107", "F1",     "107_F1",         "FacilityHeadSurvey"),
    ("110", "F3LIST", "110_F3_listing", "PatientListing"),
    ("111", "F3",     "111_F3",         "PatientSurvey"),
    ("115", "F4",     "115_F4",         "HouseholdSurvey"),
]


def run_generators(inst_dir: Path) -> None:
    """Run every generate_*.py in the instrument's folder, in alphabetical order
    (dcf → ent → fmf → apc puts the dictionary first, which the others depend on)."""
    for gen in sorted(inst_dir.glob("generate_*.py")):
        print(f"  -> {gen.name}")
        result = subprocess.run(
            [sys.executable, str(gen)], cwd=inst_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            raise RuntimeError(f"{gen.name} failed (exit {result.returncode})")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_one(inst, env_config):
    """Run generators for one instrument and splice env config into its .ent.

    Returns the absolute .ent path so main() can list all emitted files at the
    end as the F7-checklist for the human compile step. When an instrument
    is partially built (DCF-only -- e.g. F4 during the core DCF rebuild
    before the quartet ENT/FMF/APC generators land), the .ent will not
    exist; we skip the splice and return None as the ent_path so the
    caller's listing logic can flag the instrument as "DCF-only".
    """
    prefix, short, dir_name, ent_name = inst
    inst_dir = WORKSPACE / dir_name
    ent_path = inst_dir / f"{ent_name}.ent"

    print(f"[{prefix}_{short}] generating sources ...")
    run_generators(inst_dir)

    if not ent_path.exists():
        print(f"[{prefix}_{short}] DCF-only build (no .ent yet -- skipping "
              f"env-config splice). This is expected for instruments still in "
              f"the core-DCF rebuild phase; the .ent generator lands in a "
              f"later commit series.")
        print(f"[{prefix}_{short}] OK (sources at {inst_dir.relative_to(WORKSPACE)})")
        return prefix, short, None

    print(f"[{prefix}_{short}] splicing env config into {ent_path.name}")
    splice_user_settings(ent_path, {
        "csweb_url": env_config["csweb_url"],
        "expiration_days": env_config["expiration_days"],
    })

    print(f"[{prefix}_{short}] OK (sources at {inst_dir.relative_to(WORKSPACE)})")
    return prefix, short, ent_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env", required=True, choices=["dev", "uat", "prod"])
    p.add_argument("--only", help="short name to build only (e.g. F1, login, menu)")
    args = p.parse_args()

    env_config = load_env(args.env, WORKSPACE / "urls.yaml")

    targets = INSTRUMENTS
    if args.only:
        targets = [i for i in INSTRUMENTS if i[1] == args.only]
        if not targets:
            sys.exit(f"--only={args.only} matched no instrument; have {[i[1] for i in INSTRUMENTS]}")

    built = [build_one(inst, env_config) for inst in targets]

    print()
    print(f"Generated sources for {len(built)} instrument(s), env={args.env}.")
    print()
    print("=" * 72)
    print("NEXT STEP — manual compile in CSPro Designer:")
    print("=" * 72)
    print("CSPro 8.0 has no headless `.ent` -> `.pen` CLI. Open each .ent below")
    print("in CSPro Designer and press F7 (File -> Publish Entry Application).")
    print("Save the resulting .pen alongside the .ent.")
    print()
    print("See docs/superpowers/runbooks/cspro-publish-entry-runbook.md for SOP.")
    print()
    print(f"{'#':>4}  {'name':<8}  ent path")
    print(f"{'-' * 4}  {'-' * 8}  {'-' * 60}")
    for prefix, short, ent_path in built:
        if ent_path is None:
            print(f"{prefix:>4}  {short:<8}  (DCF-only build -- no .ent yet, "
                  f"skip F7)")
        else:
            print(f"{prefix:>4}  {short:<8}  {ent_path.relative_to(WORKSPACE)}")
    print()


if __name__ == "__main__":
    main()
