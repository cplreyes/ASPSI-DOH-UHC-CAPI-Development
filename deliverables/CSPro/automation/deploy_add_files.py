#!/usr/bin/env python
r"""Add files to the open 'CSPro Deploy Application' dialog, one at a time (reliable;
multi-select via typed paths only grabbed the first). Usage:
  py deploy_add_files.py psgc_province.dcf psgc_province.dat ...
Files are resolved relative to the F1 app folder.
"""
import os, sys, time
from pathlib import Path
from pywinauto import Desktop, keyboard

# Folder the file names resolve against. Override with env CSPRO_ADDFILES_DIR
# (e.g. ...\deliverables\CSPro\F3) to deploy F3/F4; defaults to F1.
BASE = os.environ.get(
    "CSPRO_ADDFILES_DIR",
    r"C:\Users\analy\Documents\analytiflow\1_Projects\ASPSI-DOH-CAPI-CSPro-Development\deliverables\CSPro\F1")
OUT = Path(__file__).resolve().parent / "shots" / "deploy"


def deploy_dlg():
    d = [w for w in Desktop(backend="win32").windows()
         if (w.window_text() or "") == "CSPro Deploy Application"]
    return d[0] if d else None


def main():
    for fn in sys.argv[1:]:
        dd = deploy_dlg()
        if not dd:
            print("no deploy dialog"); return
        dd.set_focus(); time.sleep(0.3)
        dd.click_input(coords=(482, 162))   # Add files...
        time.sleep(1.5)
        pk = [w for w in Desktop(backend="win32").windows()
              if (w.window_text() or "") == "Add files to deployment package"]
        if not pk:
            print("no picker for", fn); return
        p = pk[0]; p.set_focus(); time.sleep(0.3)
        p.click_input(coords=(550, 578))     # File name field
        time.sleep(0.2)
        keyboard.send_keys("^a{BACKSPACE}")
        keyboard.send_keys(BASE + "\\" + fn, with_spaces=True, pause=0.0)
        time.sleep(0.3)
        keyboard.send_keys("{ENTER}")
        time.sleep(1.5)
        print("added", fn)
    OUT.mkdir(parents=True, exist_ok=True)
    dd = deploy_dlg()
    if dd:
        dd.capture_as_image().save(str(OUT / "60_files.png"))
        print("shot 60_files.png")


if __name__ == "__main__":
    main()
