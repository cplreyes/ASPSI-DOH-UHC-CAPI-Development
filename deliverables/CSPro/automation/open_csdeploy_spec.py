#!/usr/bin/env python
r"""Launch CSDeploy.exe and load a .csds deployment spec via Ctrl+O.

CSDeploy restores its LAST SESSION on launch (whatever package it deployed last), so the
only deterministic way to target an instrument is to load its spec file. After the load
the window retitles to "<PackageName> - CSPro Deploy Application" and auto_deploy.py
--deploy-only can take over (it verifies identity by the Package-name Edit regardless).

Usage: py open_csdeploy_spec.py <path-to-.csds>
Exit 0 = spec loaded (window title verified); 1 = failure (screenshot dumped).
"""
import sys, time, subprocess
from pathlib import Path
from pywinauto import Desktop

CSDEPLOY = r"C:\Program Files (x86)\CSPro 8.0\CSDeploy.exe"
SHOTS = Path(r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro\automation\shots\deploy")


def deploy_windows():
    return [w for w in Desktop(backend="win32").windows()
            if (w.window_text() or "").endswith("CSPro Deploy Application")]


def main():
    spec = Path(sys.argv[1]).resolve()
    want = spec.stem  # PackageName == spec filename for our specs
    before = {w.handle for w in deploy_windows()}

    subprocess.Popen([CSDEPLOY])
    new = None
    for _ in range(30):
        time.sleep(0.5)
        fresh = [w for w in deploy_windows() if w.handle not in before]
        if fresh:
            new = fresh[0]
            break
    if not new:
        print("! CSDeploy window never appeared"); sys.exit(1)
    time.sleep(1.5)                      # let last-session restore settle
    new.set_focus(); time.sleep(0.5)
    new.type_keys("^o"); time.sleep(1.5)

    # the Open file dialog: type the full path + Enter
    dlg = None
    for w in Desktop(backend="win32").windows():
        try:
            if w.is_visible() and w.class_name() == "#32770" and "open" in (w.window_text() or "").lower():
                dlg = w; break
        except Exception:
            continue
    if not dlg:
        print("! no Open dialog after Ctrl+O"); sys.exit(1)
    edit = None
    for c in dlg.descendants():
        try:
            if c.friendly_class_name() == "Edit" and c.is_enabled():
                edit = c; break
        except Exception:
            pass
    if not edit:
        print("! no filename Edit in Open dialog"); sys.exit(1)
    edit.set_edit_text(str(spec)); time.sleep(0.4)
    edit.type_keys("{ENTER}"); time.sleep(2.5)

    title = new.window_text() or ""
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        new.capture_as_image().save(str(SHOTS / f"spec_load_{want}.png"))
    except Exception:
        pass
    if title.startswith(want):
        print(f"loaded: '{title}' hwnd={new.handle}")
        sys.exit(0)
    print(f"! window title is '{title}' (expected to start with '{want}') — see shots/deploy/spec_load_{want}.png")
    sys.exit(1)


if __name__ == "__main__":
    main()
