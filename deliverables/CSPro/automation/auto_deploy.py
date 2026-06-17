#!/usr/bin/env python
r"""Instrument-aware auto-deploy to CSWeb. Works when MULTIPLE 'CSPro Deploy Application'
dialogs are open at once (Carl keeps F1/F3/F4 dialogs all open for hands-off deploy).

Identification is SELF-VERIFYING: every deploy dialog carries a 'Package name' field
(FacilityHeadSurvey / PatientSurvey / HouseholdSurvey). This driver finds the dialog whose
Package name == the instrument I asked for, and REFUSES to touch any dialog that doesn't match
-- so it is structurally impossible to deploy one instrument's files into another's package.

It also restores the dialog if minimized (Carl's are parked minimized at -32000), which the
old screen-coord scripts could not handle.

Usage:
  py auto_deploy.py F3                # add the 8 PSGC files + screenshot; STOP (no deploy)
  py auto_deploy.py F3 --deploy       # ...then click Deploy and capture the result
  py auto_deploy.py F1 F3 F4 --deploy # several in sequence
Exit 0 = ok, 1 = a requested instrument's dialog was not found / package-name mismatch.
"""
import os, sys, time
from pathlib import Path
import win32gui, win32con
from pywinauto import Desktop, keyboard

ROOT = Path(r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro")
INSTRUMENTS = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
}
PSGC = [f"psgc_{lvl}.{ext}" for lvl in ("region", "province", "city", "barangay")
        for ext in ("dcf", "dat")]
EXPECTED_URL = "https://csweb.asiansocial.org/csweb/api"
OUT = Path(__file__).resolve().parent / "shots" / "deploy"


def deploy_dialogs():
    return [w for w in Desktop(backend="win32").windows()
            if (w.window_text() or "") == "CSPro Deploy Application"]


def package_name(dd):
    """Read the 'Package name' Edit value -> the app/instrument identity."""
    app_names = set(INSTRUMENTS.values())
    for c in dd.descendants():
        if c.friendly_class_name() == "Edit" and (c.window_text() or "").strip() in app_names:
            return c.window_text().strip()
    return None


def find_for(inst):
    want = INSTRUMENTS[inst]
    for dd in deploy_dialogs():
        if package_name(dd) == want:
            return dd, want
    return None, want


def btn(dd, text):
    for c in dd.descendants():
        if c.friendly_class_name() == "Button" and (c.window_text() or "").strip() == text:
            return c
    return None


def csweb_target_ok(dd):
    for c in dd.descendants():
        if c.friendly_class_name() == "Edit" and (c.window_text() or "").strip() == EXPECTED_URL:
            return True
    return False


def restore(dd):
    win32gui.ShowWindow(dd.handle, win32con.SW_RESTORE)
    time.sleep(0.5)
    try:
        dd.set_focus()
    except Exception:
        pass
    time.sleep(0.3)


def _get_picker():
    """The 'Add files to deployment package' modal, race-safe (windows can vanish
    mid-enumeration)."""
    try:
        for w in Desktop(backend="win32").windows():
            try:
                if w.is_visible() and (w.window_text() or "") == "Add files to deployment package":
                    return w
            except Exception:
                continue
    except Exception:
        return None
    return None


def _picker_filename_edit(pk):
    """The file-name Edit inside the open-file dialog (prefer the one in the combo)."""
    edits = [c for c in pk.descendants() if c.friendly_class_name() == "Edit"]
    for e in edits:
        try:
            if "Combo" in e.parent().friendly_class_name() and e.is_enabled():
                return e
        except Exception:
            pass
    for e in edits:
        try:
            if e.is_visible() and e.is_enabled():
                return e
        except Exception:
            pass
    return None


def add_files(dd, base):
    """Add the PSGC external dicts to the package. MESSAGE-based throughout (BM_CLICK +
    WM_SETTEXT), so it works even when another app (e.g. a Zoom meeting toolbar/overlay)
    sits over the dialog and swallows physical clicks — the failure mode that silently
    produced a PSGC-less package on 2026-06-17. Falls back to a coord click only if the
    button can't be resolved."""
    added = []
    for fn in PSGC:
        src = base / fn
        if not src.exists():
            print(f"   ! missing {src} -- skipped"); continue
        pk = _get_picker()
        if not pk:
            b = btn(dd, "Add files...")
            if not b:
                print("   ! no 'Add files...' button"); return added
            try:
                b.click()           # BM_CLICK message — overlay/focus-proof
            except Exception:
                b.click_input()     # last-resort physical
            time.sleep(1.4)
            pk = _get_picker()
        if not pk:
            print(f"   ! no file picker for {fn}"); return added
        e = _picker_filename_edit(pk)
        if not e:
            print(f"   ! no file-name field in picker for {fn}"); return added
        e.set_edit_text(str(src)); time.sleep(0.3)   # WM_SETTEXT
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
            print(f"   ! picker did not close for {fn}"); return added
        added.append(fn)
        print(f"   + {fn}")
        time.sleep(0.3)
    return added


def shot(dd, name):
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        dd.capture_as_image().save(str(OUT / name))
        print(f"   shot -> shots/deploy/{name}")
    except Exception as e:
        print(f"   shot err: {e}")


def dismiss_result_popups():
    """Click OK/Close on any 'Application Deployed Successfully' (or error) confirmation
    that CSPro pops after Deploy. These are #32770 dialogs; the result text lives in a
    child Static and the button is 'OK'. Returns count dismissed."""
    n = 0
    for w in Desktop(backend="win32").windows():
        if not w.is_visible() or w.class_name() != "#32770":
            continue
        kids = " ".join((c.window_text() or "") for c in w.children())
        # the deploy dialog itself is 'CSPro Deploy Application' (not #32770), so this only
        # matches the small confirmation popups it spawns
        if not any(k in kids.lower() for k in ("deployed", "success", "error", "fail")):
            continue
        for c in w.descendants():
            if c.friendly_class_name() == "Button" and (c.window_text() or "").strip().strip("&") in ("OK", "Close"):
                try:
                    c.click_input(); n += 1; time.sleep(0.4)
                except Exception:
                    pass
                break
    return n


def park(dd):
    """Return the deploy dialog to Carl's parked (minimized) state for the next hands-off run."""
    try:
        win32gui.ShowWindow(dd.handle, win32con.SW_MINIMIZE)
        print(f"   parked (minimized) deploy dialog hwnd={dd.handle}")
    except Exception as e:
        print(f"   park err: {e}")


def cleanup_after_deploy(dd):
    """Post-deploy tidy: dismiss the success/error popup, then re-minimize the dialog.
    NEVER closes the deploy dialog (Carl keeps the 3 open for hands-off deploys)."""
    d = dismiss_result_popups()
    print(f"   dismissed {d} result popup(s)")
    park(dd)


def deploy_one(inst, do_deploy, skip_add=False):
    dd, want = find_for(inst)
    if not dd:
        print(f"[{inst}] NO dialog with Package name '{want}' -- skipping (open it in Designer first)")
        return False
    print(f"[{inst}] locked dialog hwnd={dd.handle}  Package name='{want}'  (verified)")
    restore(dd)
    if not csweb_target_ok(dd):
        print(f"   ! WARNING: CSWeb target URL != {EXPECTED_URL} -- not auto-deploying; check the dialog")
        do_deploy = False
    base = ROOT / inst
    if skip_add:
        print(f"   skip-add: files already prepared in this dialog; clicking Deploy only")
    else:
        add_files(dd, base)
        shot(dd, f"auto_{inst}_files.png")
    if not do_deploy:
        print(f"[{inst}] files added; STOP (no --deploy). Review the shot, then re-run with --deploy.")
        return True
    db = btn(dd, "Deploy")
    if not db:
        print("   ! no Deploy button"); return False
    try:
        db.click()            # BM_CLICK message — overlay/focus-proof (Zoom-overlay safe)
    except Exception:
        db.click_input()      # last-resort physical
    print("   clicked Deploy; capturing result ...")
    for i in range(6):
        time.sleep(4)
        shot(dd, f"auto_{inst}_deploy_{i}.png")
        # surface any credential / result dialog (popup text or its child Static)
        for w in Desktop(backend="win32").windows():
            if not w.is_visible():
                continue
            t = (w.window_text() or "")
            kids = " ".join((c.window_text() or "") for c in w.children()) if w.class_name() == "#32770" else ""
            if "successfully" in (t + " " + kids).lower():
                print(f"   result: deploy succeeded")
                cleanup_after_deploy(dd)          # dismiss popup + re-minimize dialog
                return True
    print(f"[{inst}] deploy clicked but no success popup seen; see shots/deploy/auto_{inst}_deploy_*.png")
    cleanup_after_deploy(dd)                       # tidy anyway (dismiss stray popup, re-park)
    return True


def check_one(inst):
    """Dry verify: which dialog maps to this instrument + is the CSWeb target right.
    Touches nothing (no restore, no add, no deploy)."""
    dd, want = find_for(inst)
    if not dd:
        print(f"[{inst}] NO dialog with Package name '{want}'  (open it in Designer)")
        return False
    url = csweb_target_ok(dd)
    print(f"[{inst}] dialog hwnd={dd.handle}  Package name='{want}' (verified)  "
          f"CSWeb target {'OK' if url else 'MISMATCH'}")
    return True


def main():
    args = [a for a in sys.argv[1:]]
    deploy_only = "--deploy-only" in args            # click Deploy on an already-prepared dialog
    do_deploy = "--deploy" in args or deploy_only
    do_check = "--check" in args
    insts = [a.upper() for a in args if a.upper() in INSTRUMENTS]
    if do_check:
        insts = insts or list(INSTRUMENTS)   # default: check all three
        ok = all([check_one(i) for i in insts])
        sys.exit(0 if ok else 1)
    if not insts:
        print("usage: py auto_deploy.py F1|F3|F4 [...] [--deploy | --deploy-only] | --check"); sys.exit(1)
    ok = True
    for inst in insts:
        ok = deploy_one(inst, do_deploy, skip_add=deploy_only) and ok
        print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
