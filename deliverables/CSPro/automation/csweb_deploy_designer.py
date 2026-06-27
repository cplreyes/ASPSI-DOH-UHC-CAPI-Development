#!/usr/bin/env python
r"""Drive CSPro Designer to deploy an instrument to CSWeb (the reference packaging
that correctly rewrites external-dict paths). Owner-drawn menus can't be read by
win32, but they RENDER, so we navigate by screenshot+vision + standard #32770 dialogs.

This produces the FIRST F1 CSWeb package as ground truth; afterwards F3/F4 deploy
headless via the API (automation/csweb_deploy.py, built from the package this creates).

Steps (run with a step name so a vision model can read each screenshot and guide):
  py csweb_deploy_designer.py open        # launch Designer on F1, screenshot baseline
  py csweb_deploy_designer.py filemenu    # Alt+F, screenshot the File menu
  py csweb_deploy_designer.py shot         # just screenshot current state
  py csweb_deploy_designer.py keys "<seq>" # send a pywinauto key sequence, then screenshot
"""
import os
import subprocess
import sys
import time
from pathlib import Path

from pywinauto import keyboard, mouse
from pywinauto import Desktop

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cspro_compile_driver import (  # reuse hardened helpers
    CSPRO_EXE, _paths, _kill_cspro, _bring_to_front, clear_known_dialogs,
)
from pywinauto.application import Application

OUT = Path(__file__).resolve().parent / "shots" / "deploy"
KEY = os.environ.get("DEPLOY_KEY", "F1")


def _attach():
    app = Application(backend="win32").connect(title_re=r"CSPro 8\.0 - \[.*\]", timeout=20)
    frames = [w for w in app.windows() if (w.window_text() or "").startswith("CSPro 8.0 - ")]
    main = max(frames, key=lambda w: (w.rectangle().width() * w.rectangle().height()))
    return app, main


def _shot(main, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.png"
    main.capture_as_image().save(p)
    print(f"SHOT {p}")


def cmd_open():
    p = _paths(KEY)
    _kill_cspro()
    print(f"launching Designer on {p['ent'].name} ...")
    subprocess.Popen([CSPRO_EXE, str(p["ent"])])
    time.sleep(16)
    app, main = _attach()
    clear_known_dialogs(app)
    _bring_to_front(main)
    time.sleep(0.5)
    _shot(main, "00_open")


def cmd_filemenu():
    app, main = _attach()
    _bring_to_front(main)
    time.sleep(0.4)
    keyboard.send_keys("%f")   # Alt+F -> File menu (mnemonic works even on owner-drawn)
    time.sleep(1.0)
    _shot(main, "10_filemenu")


def cmd_shot():
    app, main = _attach()
    _shot(main, "shot")


def cmd_keys(seq):
    app, main = _attach()
    _bring_to_front(main)
    time.sleep(0.3)
    keyboard.send_keys(seq, pause=0.08)
    time.sleep(1.0)
    _shot(main, "keys")


def _shot_any(name):
    """Screenshot the frontmost relevant window (prefer a CSPro dialog), robust to
    multiple top-level CSPro windows being open."""
    OUT.mkdir(parents=True, exist_ok=True)
    wins = [w for w in Desktop(backend="win32").windows()
            if (w.window_text() or "").startswith("CSPro") and w.is_visible()]
    # prefer a dialog (not the main 'CSPro 8.0 - [..]' frame) if one is open
    dialogs = [w for w in wins if not (w.window_text() or "").startswith("CSPro 8.0 - ")]
    target = dialogs[0] if dialogs else (wins[0] if wins else Desktop(backend="win32"))
    p = OUT / f"{name}.png"
    target.capture_as_image().save(p)
    print(f"SHOT {p}  (window: {target.window_text()!r})")


def cmd_click(x, y, name="click"):
    """Absolute screen click (main window is maximized at origin, so window coords
    == screen coords). Robust to extra CSPro dialog windows."""
    mouse.click(button="left", coords=(int(x), int(y)))
    time.sleep(1.5)
    _shot_any(name)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "shot"
    if arg == "click":
        cmd_click(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "click")
    else:
        {"open": cmd_open, "filemenu": cmd_filemenu, "shot": cmd_shot}.get(
            arg, lambda: cmd_keys(sys.argv[2] if len(sys.argv) > 2 else "{ENTER}")
        )()
