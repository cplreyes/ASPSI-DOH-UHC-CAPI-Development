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

# Resolve from THIS FILE, never a hardcoded checkout path (2026-08-14). The old
# absolute constant pointed at the main checkout, so a deploy driven from any other
# tree (a worktree, a release clone) pulled the .pen/.pff from that tree while these
# PSGC files still came from the main checkout. CSPro then makes every path relative
# to the two roots' COMMON ANCESTOR, and the package ships NESTED:
#     aspsi-reconcile-wt/deliverables/CSPro/F3/PatientSurvey.pen
#     ASPSI-DOH-CAPI-CSPro-Development/deliverables/CSPro/F3/psgc_region.dat
# instead of the flat layout CSEntry expects. Caught on the 2026-08-14 ICF deploy.
ROOT = Path(__file__).resolve().parent.parent      # .../deliverables/CSPro
INSTRUMENTS = {
    "F1": "FacilityHeadSurvey",
    "F3": "PatientSurvey",
    "F4": "HouseholdSurvey",
    "SV": "SupervisorApp",
    "HUB": "LoginApp",   # supervisor hub bundle (LoginApp+MenuApp); spec = supervisor-hub/LoginApp.csds
}
PSGC = [f"psgc_{lvl}.{ext}" for lvl in ("region", "province", "city", "barangay")
        for ext in ("dcf", "dat")]
# Extra files each package must carry, in add order. PER-INSTRUMENT on purpose
# (2026-08-27): the three questionnaires ship the PSGC external dicts, F4 also ships
# review.html, and the Supervisor App / Supervisor Hub ship NEITHER -- SV/ holds no
# psgc_* files and the HUB spec lives in supervisor-hub/, not HUB/. A blanket
# "everything needs PSGC" list made the completeness guard abort every SV/HUB deploy
# with a false 'incomplete package'. Anything unlisted defaults to no extra files.
EXTRA_FILES = {
    "F1": PSGC,
    "F3": PSGC,
    "F4": PSGC + ["review.html"],
    "SV": [],
    "HUB": [],
}
# 2026-08-08 migration: csweb.asiansocial.org is being retired; capi is the
# canonical sync endpoint. Both hosts still answer, so old installs keep
# working until every tablet has re-added the app.
EXPECTED_URL = "https://capi.asiansocial.org/csweb/api"
LEGACY_URLS = ("https://csweb.asiansocial.org/csweb/api",)
OUT = Path(__file__).resolve().parent / "shots" / "deploy"


def deploy_dialogs():
    # bare title = unsaved spec; "<PackageName> - CSPro Deploy Application" = loaded .csds
    # Desktop().windows() wraps EVERY top-level handle in one pass and raises
    # InvalidWindowHandle when any window dies mid-enumeration (a flickering
    # window makes that reproducible, seen 2026-08-17). Enumerate handles
    # ourselves and wrap individually, skipping the dead ones - same race-safe
    # stance as _get_picker().
    import win32gui
    from pywinauto.controls.hwndwrapper import HwndWrapper
    handles = []
    win32gui.EnumWindows(lambda h, _: (handles.append(h), True)[1], None)
    out = []
    for h in handles:
        try:
            if (win32gui.GetWindowText(h) or "").endswith("CSPro Deploy Application"):
                out.append(HwndWrapper(h))
        except Exception:
            continue
    return out


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


def _csweb_url_edit(dd):
    """The Deploy-To CSWeb edit: the only Edit whose value is an http(s) URL ending
    in /csweb/api. Matching on content rather than control order, which is not stable
    across dialog states."""
    for c in dd.descendants():
        if c.friendly_class_name() != "Edit":
            continue
        v = (c.window_text() or "").strip().rstrip("/")
        if v.startswith("http") and v.endswith("/csweb/api"):
            return c
    return None


def csweb_target_ok(dd):
    for c in dd.descendants():
        if c.friendly_class_name() == "Edit" and (c.window_text() or "").strip() == EXPECTED_URL:
            return True
    return False


def ensure_csweb_target(dd):
    """Point the dialog at EXPECTED_URL. Returns (ok, note).

    This exists because the three deploy dialogs are parked long-term with whatever URL
    was last typed into them — during the 2026-08-08 csweb->capi migration that was the
    host being retired, so re-publishing without rewriting the field would have shipped
    packages still pointing at it."""
    if csweb_target_ok(dd):
        return True, "already " + EXPECTED_URL
    e = _csweb_url_edit(dd)
    if e is None:
        return False, "CSWeb URL edit not found - set it by hand before deploying"
    was = (e.window_text() or "").strip()
    try:
        e.set_focus()
        e.set_edit_text(EXPECTED_URL)
    except Exception as exc:
        return False, f"could not rewrite URL ({exc})"
    now = (e.window_text() or "").strip()
    if now != EXPECTED_URL:
        return False, f"URL rewrite did not stick (reads {now!r})"
    return True, f"rewrote {was} -> {EXPECTED_URL}"


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


def expected_files(base):
    """Every extra file this instrument's package must carry, in add order.

    Looked up per-instrument in EXTRA_FILES: F1/F3 = the 8 PSGC dicts, F4 = those plus
    review.html (Section N recap htmldialog reads it from the app folder), SV/HUB = none.
    An unknown folder name yields [] -- an unlisted app adds nothing and the completeness
    guard in deploy_one() has nothing to be short of."""
    return list(EXTRA_FILES.get(base.name, []))


def add_files(dd, base):
    """Add this instrument's extra files (expected_files(base) -- the PSGC external dicts
    for F1/F3/F4, plus review.html for F4; nothing for SV/HUB). MESSAGE-based throughout (BM_CLICK +
    WM_SETTEXT), so it works even when another app (e.g. a Zoom meeting toolbar/overlay)
    sits over the dialog and swallows physical clicks — the failure mode that silently
    produced a PSGC-less package on 2026-06-17. Falls back to a coord click only if the
    button can't be resolved.

    Returns the files actually added — SHORTER than expected_files(base) on every early
    return. deploy_one() treats a short list as a hard abort; never ignore it."""
    added = []
    for fn in expected_files(base):
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


# How long to wait for a deploy to reach a terminal state. The HUB bundle is ~35 MB;
# the old 6x4s window expired mid-upload and reported "no success popup seen".
DEPLOY_WAIT_S = int(os.environ.get("CSPRO_DEPLOY_WAIT", "900"))


def _is_login_prompt(w):
    """CSWeb credential prompt: a #32770 titled 'Login' with Username + Password edits.
    CSPro shows it when CSDeploy has no cached CSWeb credential — e.g. after the CSWeb
    user table is rebuilt. It MUST NOT be treated as a result popup (dismissing it
    aborts the deploy, which then hangs forever on 'Connecting to ...')."""
    if w.class_name() != "#32770":
        return False
    kids = " ".join((c.window_text() or "") for c in w.children()).lower()
    return "username" in kids and "password" in kids


def answer_login_prompt():
    """Fill the CSWeb Login prompt from the environment and click OK.

    Credentials come from CSPRO_ADMIN_USER + one of:
      CSPRO_ADMIN_PASS       — the password directly, or
      CSPRO_ADMIN_PASS_FILE  — a file containing it (preferred: keeps it off the
                               command line and out of any transcript).
    Returns True if a prompt was present AND answered."""
    for w in Desktop(backend="win32").windows():
        if not w.is_visible() or not _is_login_prompt(w):
            continue
        user = os.environ.get("CSPRO_ADMIN_USER")
        pw = os.environ.get("CSPRO_ADMIN_PASS")
        pw_file = os.environ.get("CSPRO_ADMIN_PASS_FILE")
        if not pw and pw_file and Path(pw_file).exists():
            pw = Path(pw_file).read_text(encoding="utf-8").strip()
        if not (user and pw):
            print("   ! CSWeb Login prompt is open, but CSPRO_ADMIN_USER / "
                  "CSPRO_ADMIN_PASS(_FILE) are not set -- type it by hand, then re-poll.")
            return False
        edits = [c for c in w.descendants() if c.friendly_class_name() == "Edit"]
        if len(edits) < 2:
            print("   ! Login prompt has no Username/Password edits -- typing by hand needed")
            return False
        edits[0].set_edit_text(user)
        edits[1].set_edit_text(pw)
        for c in w.descendants():
            if c.friendly_class_name() == "Button" and (c.window_text() or "").strip().strip("&") == "OK":
                c.click_input()
                print(f"   answered CSWeb Login prompt as '{user}'")
                time.sleep(1.0)
                return True
    return False


def dismiss_result_popups():
    """Click OK/Close on any 'Application Deployed Successfully' (or error) confirmation
    that CSPro pops after Deploy. These are #32770 dialogs; the result text lives in a
    child Static and the button is 'OK'. Returns count dismissed.

    NEVER touches the Login prompt -- see _is_login_prompt()."""
    n = 0
    for w in Desktop(backend="win32").windows():
        if not w.is_visible() or w.class_name() != "#32770":
            continue
        if _is_login_prompt(w):
            continue                      # the credential prompt is NOT a result popup
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


def _deploy_result(dd, inst):
    """One scan of the visible windows for a TERMINAL deploy state.
    Returns 'success', 'failed', or None (still running -- keep polling)."""
    for w in Desktop(backend="win32").windows():
        if not w.is_visible():
            continue
        t = (w.window_text() or "")
        kids = " ".join((c.window_text() or "") for c in w.children()) if w.class_name() == "#32770" else ""
        blob = (t + " " + kids).lower()
        if "successfully" in blob:
            return "success"
        if any(k in blob for k in ("error", "failed", "unable", "denied")):
            shot(dd, f"auto_{inst}_deploy_ERR.png")
            print(f"   result: deploy FAILED -- {kids.strip()[:90] or t.strip()[:90]}")
            return "failed"
    return None


def deploy_one(inst, do_deploy, skip_add=False):
    dd, want = find_for(inst)
    if not dd:
        print(f"[{inst}] NO dialog with Package name '{want}' -- skipping (open it in Designer first)")
        return False
    print(f"[{inst}] locked dialog hwnd={dd.handle}  Package name='{want}'  (verified)")
    restore(dd)
    # 2026-08-08 csweb->capi migration: the parked dialogs still held the retired host,
    # so CHECKING alone would have blocked every re-publish. Rewrite it, then re-verify;
    # only refuse to deploy if the rewrite could not be made to stick.
    ok, note = ensure_csweb_target(dd)
    print(f"   CSWeb target: {note}")
    if not ok:
        print(f"   ! WARNING: CSWeb target URL != {EXPECTED_URL} -- not auto-deploying; check the dialog")
        do_deploy = False
    base = ROOT / inst
    if skip_add:
        print(f"   skip-add: files already prepared in this dialog; clicking Deploy only")
    else:
        added = add_files(dd, base)
        shot(dd, f"auto_{inst}_files.png")
        # add_files() returns early on a missing button / picker / file-name field, and
        # skips a file whose source is absent. Before this guard (2026-08-27) deploy_one()
        # ignored that and clicked Deploy anyway, shipping a package short of its external
        # dicts -- the silent 2026-06-17 defect. A short list is now a hard abort.
        missing = [f for f in expected_files(base) if f not in added]
        if missing:
            print(f"[{inst}] ABORT: only {len(added)}/{len(expected_files(base))} files were added "
                  f"to the package -- missing: {', '.join(missing)}. Deploy NOT clicked; "
                  f"fix the dialog and re-run (see shots/deploy/auto_{inst}_files.png).")
            return False
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
    # The HUB bundle is ~35 MB — the upload far outruns a 24 s watch window, and a
    # deploy that needs credentials sits on the Login prompt indefinitely. So: poll
    # long, answer the Login prompt, and only give up on a real terminal state.
    handled_login = False
    deadline = time.time() + DEPLOY_WAIT_S
    i = 0
    while time.time() < deadline:
        time.sleep(4)
        if i < 6:
            shot(dd, f"auto_{inst}_deploy_{i}.png")
        i += 1

        # CSWeb Login prompt -> answer it (never let cleanup eat it).
        if not handled_login and answer_login_prompt():
            handled_login = True
            deadline = time.time() + DEPLOY_WAIT_S   # upload starts now; restart the clock
            continue

        res = _deploy_result(dd, inst)
        if res == "success":
            print("   result: deploy succeeded")
            cleanup_after_deploy(dd)              # dismiss popup + re-minimize dialog
            return True
        if res == "failed":
            cleanup_after_deploy(dd)
            return False

    print(f"[{inst}] deploy still running after {DEPLOY_WAIT_S}s -- NOT confirmed. "
          f"Do NOT re-click Deploy; poll for the popup. shots/deploy/auto_{inst}_deploy_*.png")
    return False                                   # never report success on the click alone


def check_one(inst):
    """Dry verify: which dialog maps to this instrument + is the CSWeb target right.
    Touches nothing (no restore, no add, no deploy)."""
    dd, want = find_for(inst)
    if not dd:
        print(f"[{inst}] NO dialog with Package name '{want}'  (open it in Designer)")
        return False
    url, url_note = ensure_csweb_target(dd)
    print(f"   CSWeb target: {url_note}")
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
