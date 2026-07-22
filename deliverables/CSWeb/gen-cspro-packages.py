#!/usr/bin/env python3
r"""Package the F1/F3/F4 CSPro CAPI applications + data dictionaries for the
Responses Data Room, so other CSPro users can download a local copy and run
the instruments themselves (Carl's request, 2026-07-21).

Output (to --out-dir, then scp to /opt/app/lamp/www/docs/data/ on the box):
  f{1,3,4}-cspro-app.zip           complete entry application per instrument:
                                   compiled .pen + versioned .pff + Designer
                                   source (.ent/.apc/.mgf/.qsf/.dcf/.fmf) +
                                   PSGC lookup dictionaries/data (+ F1's
                                   facility lookup) + README. Extracts into
                                   one folder; double-click the .pff with
                                   CSPro 8.0 installed and it runs with an
                                   EMPTY local case file — no sync, no
                                   credentials anywhere in the package
                                   (verified: the field apps hold no
                                   syncconnect URLs or secrets).
  FacilityHeadSurvey.dcf etc.      the 3 instrument dictionaries served
                                   individually (for data users).
  uhc-year2-cspro-dictionaries.zip the 3 dictionaries + README in one zip.
  cspro-manifest.json              versions (from versions.json, the build
                                   SSOT) + filenames — the data-room index
                                   and the dashboard Downloads band render
                                   their CSPro rows from this.

STRICT include list (never a directory sweep): the CSPro folders also hold
desk-test .csdb DATA, backups and generator tooling that must never ship.
Any expected file missing -> loud failure listing it (so a gitignore-thinned
worktree copy can't produce a silently broken package — psgc_*.dat live only
in the MAIN checkout; point --cspro-dir there).

These packages are STATIC (they change only when Carl redeploys an
instrument): re-run this + re-scp on each instrument redeploy, ideally in the
same breath as the /opt/spss-meta codebook refresh.

  py deliverables/CSWeb/gen-cspro-packages.py \
     --cspro-dir <MAIN-checkout>/deliverables/CSPro --out-dir <stage>
  scp <stage>/* root@207.148.65.115:/opt/app/lamp/www/docs/data/

F2 has no CSPro package: it is the Healthcare-Worker PWA (browser app).
"""
import argparse, json, os, sys, zipfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSPRO = os.path.abspath(os.path.join(HERE, "..", "CSPro"))

BASE = {"f1": ("F1", "FacilityHeadSurvey"),
        "f3": ("F3", "PatientSurvey"),
        "f4": ("F4", "HouseholdSurvey")}
NAMES = {"f1": "F1 - Facility Head", "f3": "F3 - Patient", "f4": "F4 - Household"}
PSGC = ["psgc_region", "psgc_province", "psgc_city", "psgc_barangay"]
LOOKUP_EXT = [".dcf", ".dat", ".dat.csidx"]
APP_EXT = [".ent", ".ent.apc", ".ent.mgf", ".ent.qsf", ".dcf", ".fmf", ".pen", ".pff"]
DICT_ZIP = "uhc-year2-cspro-dictionaries.zip"


def instrument_files(inst, cspro_dir):
    """Ordered [(abs path, arc name)] for one instrument — the strict include list."""
    folder, base = BASE[inst]
    d = os.path.join(cspro_dir, folder)
    files = [os.path.join(d, base + e) for e in APP_EXT]
    for lk in PSGC + (["facility_lookup"] if inst == "f1" else []):
        files += [os.path.join(d, lk + e) for e in LOOKUP_EXT]
    return [(p, os.path.basename(p)) for p in files]


def readme(inst, ver, stamp, nl):
    folder, base = BASE[inst]
    return nl.join([
        "%s — CSPro CAPI application package" % NAMES[inst],
        "App: %s   Version: %s (%s)" % (ver.get("app", base), ver.get("version", "?"),
                                        ver.get("date", "?")),
        "Packaged %s UTC from the UHC Survey Year 2 build tree." % stamp,
        "",
        "TO RUN (data entry):",
        "  1. Install CSPro 8.0 or newer (free): https://www.census.gov/data/software/cspro.html",
        "  2. Extract this zip anywhere and double-click %s.pff" % base,
        "  3. CSEntry opens with an EMPTY local case file (%s.csdb is created" % base,
        "     on first run). Cases you enter stay on your machine — this package",
        "     contains no sync configuration and no credentials.",
        "",
        "TO INSPECT / MODIFY (CSPro Designer):",
        "  Open %s.ent in CSPro Designer. Everything the app needs is here:" % base,
        "  the questionnaire dictionary (%s.dcf), forms (.fmf), logic (.ent.apc)," % base,
        "  question text (.ent.qsf), messages (.ent.mgf) and the PSGC geographic",
        "  lookup dictionaries%s." % (" plus the facility lookup" if inst == "f1" else ""),
        "  %s.pen is the same app compiled for CSEntry (incl. Android sideload)." % base,
        "",
        "NOTE: F2 (Healthcare Worker) is a PWA (browser app) — no CSPro package.",
        ""])


def main():
    ap = argparse.ArgumentParser(description="Package CSPro apps + dictionaries for the data room.")
    ap.add_argument("--cspro-dir", default=DEFAULT_CSPRO,
                    help="deliverables/CSPro of the MAIN checkout (worktrees lack the "
                         "gitignored psgc_*/facility lookup .dat files); default: %(default)s")
    ap.add_argument("--out-dir", required=True, help="staging dir for the zips + manifest")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    vpath = os.path.join(a.cspro_dir, "versions.json")
    versions = json.load(open(vpath, encoding="utf-8")) if os.path.exists(vpath) else {}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    NL = chr(10)

    missing = [p for inst in BASE for p, _ in instrument_files(inst, a.cspro_dir)
               if not os.path.exists(p)]
    if missing:
        sys.exit("REFUSING to package — %d expected file(s) missing (a worktree copy "
                 "lacks the gitignored lookup .dat files; point --cspro-dir at the MAIN "
                 "checkout):%s  %s" % (len(missing), NL, (NL + "  ").join(missing)))

    manifest = {"generated": stamp + " UTC", "dictionaries_zip": DICT_ZIP,
                "instruments": {}}
    for inst in BASE:
        folder, base = BASE[inst]
        ver = versions.get(folder, {})
        files = instrument_files(inst, a.cspro_dir)
        assert not any(n.endswith(".csdb") for _, n in files), "case data must never ship"
        zname = "%s-cspro-app.zip" % inst
        arcdir = "%s-%s" % (folder, base)                 # extracts into one clean folder
        with zipfile.ZipFile(os.path.join(a.out_dir, zname), "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(arcdir + "/README.txt", readme(inst, ver, stamp, NL))
            for p, n in files:
                z.write(p, arcdir + "/" + n)
        manifest["instruments"][inst] = {
            "zip": zname, "app": ver.get("app", base), "version": ver.get("version", ""),
            "date": ver.get("date", ""), "dcf": base + ".dcf", "files": len(files) + 1}
        # the instrument dictionary, served individually for data users
        with open(os.path.join(a.cspro_dir, folder, base + ".dcf"), "rb") as src, \
             open(os.path.join(a.out_dir, base + ".dcf"), "wb") as dst:
            dst.write(src.read())
        # drift guard: the pff Description is stamped from versions.json — warn on mismatch
        pff = open(os.path.join(a.cspro_dir, folder, base + ".pff"),
                   encoding="utf-8-sig").read()
        if ver.get("version") and ("v" + ver["version"]) not in pff:
            print("WARN: %s .pff Description does not carry v%s — check stamp_version.py"
                  % (folder, ver["version"]))

    with zipfile.ZipFile(os.path.join(a.out_dir, DICT_ZIP), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", NL.join([
            "UHC Survey Year 2 — CSPro data dictionaries (CSPro 8.0 JSON .dcf)",
            "Packaged %s UTC. One dictionary per CAPI instrument:" % stamp] + [
            "  %s.dcf  %s (v%s)" % (BASE[i][1], NAMES[i],
                                    versions.get(BASE[i][0], {}).get("version", "?"))
            for i in BASE] + [
            "",
            "The PSGC / facility lookup dictionaries ship inside the per-instrument",
            "application packages. F2 (Healthcare Worker) is a PWA — no CSPro dictionary;",
            "its codebook is f2_codebook.csv in the data room.",
            ""]))
        for inst in BASE:
            folder, base = BASE[inst]
            z.write(os.path.join(a.cspro_dir, folder, base + ".dcf"), base + ".dcf")

    with open(os.path.join(a.out_dir, "cspro-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print("CSPro packages -> %s" % a.out_dir)
    for inst, m in manifest["instruments"].items():
        print("  %-4s %s v%s (%s): %s, %d files + %s"
              % (inst, m["app"], m["version"], m["date"], m["zip"], m["files"], m["dcf"]))


if __name__ == "__main__":
    main()
