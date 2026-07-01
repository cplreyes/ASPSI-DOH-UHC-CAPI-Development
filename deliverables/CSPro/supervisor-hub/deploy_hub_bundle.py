#!/usr/bin/env python
r"""Deploy the C1 spike LOGIN+MENU bundle to CSWeb as ONE package.

The chain (LoginApp -execpff-> MenuApp -execpff-> instrument) needs every app's
files in ONE on-device folder so the relative .pff paths resolve. CSWeb installs a
package's added files alongside the app, so we add MenuApp's full file set + the
roster .dat to the open LoginApp deploy dialog, then Deploy.

PRECONDITION: open LoginApp in CSPro Designer and File > Publish and Deploy first,
so the 'CSPro Deploy Application' dialog with Package name 'LoginApp' is on screen
(the strict-publish compile must have passed — the dialog opening IS that proof).

Reuses automation/auto_deploy.py's proven file-picker automation (message-based,
overlay/focus-proof).

Usage:
  py deploy_hub_bundle.py            # add the bundle files + screenshot; STOP
  py deploy_hub_bundle.py --deploy   # ...then click Deploy and capture the result
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "automation"))
from auto_deploy import (  # proven helpers
    deploy_dialogs, btn, _get_picker, _picker_filename_edit, csweb_target_ok,
    restore, dismiss_result_popups, park, EXPECTED_URL,
)
from pywinauto import Desktop

HERE = Path(__file__).resolve().parent
PACKAGE = "LoginApp"
# MenuApp's full set + the roster data. LoginApp.{dcf,fmf,apc,qsf,mgf,ent,pff} and
# UserRoster.dcf ride along automatically (the .ent + its declared external);
# UserRoster.dat (data) and the entire MenuApp must be added explicitly.
BUNDLE = [
    "MenuApp.ent", "MenuApp.dcf", "MenuApp.fmf",
    "MenuApp.ent.apc", "MenuApp.ent.qsf", "MenuApp.ent.mgf", "MenuApp.pff",
    "UserRoster.dat",
    "survey-basemap.mbtiles",   # N3 offline base map (Map.setBaseMap reads it from the app folder)
    "report.html",              # C4b coverage report dialog (htmldialog reads it from the app folder; self-contained, no deps)
    # B4 (N1) assignment distribution: MenuApp.ent declares ASSIGNMENT_DICT external, so the
    # dict + data must ship. MyAssignment.dat = the local file the enumerator's syncfile GET
    # overwrites; the AS_<id>.dat per-enumerator files (added by glob below) are what the
    # supervisor serves over Bluetooth.
    "Assignment.dcf", "Assignment.dat", "MyAssignment.dat",
    # B6/B7 (case exchange): MenuApp.ent declares the F1/F3/F4 dicts EXTERNAL so syncdata can move
    # primary case data over Bluetooth. Only the PACKAGE's primary .ent (LoginApp) auto-rides its
    # externals, so MenuApp's snapshot instrument dcfs (build-time copies, ~2MB each) must ship
    # explicitly. Their DATA stays the separately-installed instrument's own .csdb
    # (..\\<App>\\<App>.csdb) — NOT shipped. ⚠ +~6MB on top of the 26MB mbtiles → a large upload;
    # the deploy "success" popup may outrun auto_deploy's watch window (re-check shots if so).
    "FacilityHeadSurvey.dcf", "PatientSurvey.dcf", "HouseholdSurvey.dcf",
]
OUT = Path(__file__).resolve().parent.parent / "automation" / "shots" / "deploy"


def find_login_dialog():
    for dd in deploy_dialogs():
        for c in dd.descendants():
            try:
                if c.friendly_class_name() == "Edit" and (c.window_text() or "").strip() == PACKAGE:
                    return dd
            except Exception:
                pass
    return None


def add_one(dd, src):
    pk = _get_picker()
    if not pk:
        b = btn(dd, "Add files...")
        if not b:
            print("   ! no 'Add files...' button"); return False
        try:
            b.click()
        except Exception:
            b.click_input()
        time.sleep(1.4)
        pk = _get_picker()
    if not pk:
        print(f"   ! no file picker for {src.name}"); return False
    e = _picker_filename_edit(pk)
    if not e:
        print(f"   ! no file-name field for {src.name}"); return False
    e.set_edit_text(str(src)); time.sleep(0.3)
    ob = None
    for c in pk.descendants():
        try:
            if c.friendly_class_name() == "Button" and (c.window_text() or "").strip().strip("&").lower() == "open":
                ob = c; break
        except Exception:
            pass
    try:
        (ob.click() if ob else e.type_keys("{ENTER}"))
    except Exception:
        e.type_keys("{ENTER}")
    for _ in range(14):
        if not _get_picker():
            break
        time.sleep(0.3)
    if _get_picker():
        print(f"   ! picker did not close for {src.name}"); return False
    print(f"   + {src.name}")
    time.sleep(0.3)
    return True


def shot(dd, name):
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        dd.capture_as_image().save(str(OUT / name))
        print(f"   shot -> shots/deploy/{name}")
    except Exception as e:
        print(f"   shot err: {e}")


def main():
    deploy_only = "--deploy-only" in sys.argv   # bundle already staged: just click Deploy
    do_deploy = "--deploy" in sys.argv or deploy_only
    dd = find_login_dialog()
    if not dd:
        print(f"NO deploy dialog with Package name '{PACKAGE}'. Open it in Designer first "
              f"(File > Publish and Deploy on LoginApp).")
        sys.exit(1)
    print(f"locked LoginApp deploy dialog hwnd={dd.handle}")
    restore(dd)
    if deploy_only:
        print("   deploy-only: bundle already staged; skipping Add files")
    else:
        # the per-enumerator assignment files track the roster -> glob so the bundle
        # can't drift when the roster changes (B4). Sorted for a stable order.
        files = list(BUNDLE) + sorted(p.name for p in HERE.glob("AS_*.dat"))
        for fn in files:
            src = HERE / fn
            if not src.exists():
                print(f"   ! missing {src} -- skipped"); continue
            add_one(dd, src)
        shot(dd, "hub_bundle_files.png")
    if not csweb_target_ok(dd):
        print(f"   ! WARNING: CSWeb target != {EXPECTED_URL}; not deploying")
        sys.exit(2)
    if not do_deploy:
        print("files added; STOP (no --deploy). Review the shot, then re-run with --deploy.")
        return
    db = btn(dd, "Deploy")
    if not db:
        print("   ! no Deploy button"); sys.exit(2)
    try:
        db.click()
    except Exception:
        db.click_input()
    print("   clicked Deploy; capturing ...")
    ok = False
    for i in range(6):
        time.sleep(4)
        shot(dd, f"hub_deploy_{i}.png")
        for w in Desktop(backend="win32").windows():
            try:
                if not w.is_visible():
                    continue
            except Exception:
                continue
            t = (w.window_text() or "")
            kids = " ".join((c.window_text() or "") for c in w.children()) if w.class_name() == "#32770" else ""
            if "successfully" in (t + " " + kids).lower():
                print("   result: deploy succeeded")
                dismiss_result_popups()
                ok = True
                break
        if ok:
            break
    park(dd)
    print("DONE" if ok else "deploy clicked; no success popup seen — check shots/deploy/hub_deploy_*.png")


if __name__ == "__main__":
    main()
