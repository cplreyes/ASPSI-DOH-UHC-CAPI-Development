#!/usr/bin/env python
r"""Minimal stepwise CSEntry driver for desk-test runtime checks.

CSEntry entry is GUI-only (no headless entry mode), so we drive it with
pywinauto (win32) and READ STATE BY SCREENSHOT -- the entry surface + HTML
validation modals are Chromium-rendered and not reliably win32-readable.

Each subcommand reconnects to the running CSEntry window by class
(CSProDEFrame), so state persists across separate invocations and a vision
model (the agent) can navigate step by step:

  launch <pff>      kill any CSEntry, start it on the pff, screenshot
  shot              screenshot the current window
  type <text>       type literal text into the focused field, then screenshot
  key <keys>        send pywinauto key syntax (e.g. {ENTER}, {F4}), screenshot
  click <x> <y>     left-click at client coords (for HTML modal OK buttons)

Shots go to automation/shots/csentry.png (overwritten each step).
"""
import subprocess
import sys
import time
from pathlib import Path

from pywinauto import Application, Desktop
from pywinauto import keyboard, mouse

CSENTRY_EXE = r"C:\Program Files (x86)\CSPro 8.0\CSEntry.exe"
HERE = Path(__file__).resolve().parent
OUT = HERE / "shots"
OUT.mkdir(exist_ok=True)
SHOT = OUT / "csentry.png"
WIN_CLASS = "CSProDEFrame"


def _win():
    """Connect to the running CSEntry main window."""
    for _ in range(20):
        try:
            d = Desktop(backend="win32")
            w = d.window(class_name=WIN_CLASS)
            if w.exists():
                return w
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit("ERROR: CSEntry window (CSProDEFrame) not found.")


def _shot(tag=""):
    w = _win()
    try:
        w.set_focus()
    except Exception:
        pass
    time.sleep(0.3)
    img = w.capture_as_image()
    img.save(SHOT)
    print(f"SHOT {SHOT}  size={img.size}  {tag}")


def cmd_launch(pff):
    subprocess.run(["taskkill", "/IM", "CSEntry.exe", "/F"],
                   capture_output=True)
    time.sleep(1.0)
    subprocess.Popen([CSENTRY_EXE, str(Path(pff).resolve())])
    time.sleep(6.0)
    _shot(f"launched {pff}")


def cmd_shot():
    _shot()


def cmd_type(text):
    _win().set_focus()
    time.sleep(0.2)
    keyboard.send_keys(text, with_spaces=True, pause=0.02)
    time.sleep(0.6)
    _shot(f"typed {text!r}")


def cmd_key(keys):
    _win().set_focus()
    time.sleep(0.2)
    keyboard.send_keys(keys, pause=0.05)
    time.sleep(0.8)
    _shot(f"key {keys}")


def cmd_click(x, y):
    w = _win()
    w.set_focus()
    r = w.rectangle()
    mouse.click(button="left", coords=(r.left + int(x), r.top + int(y)))
    time.sleep(0.6)
    _shot(f"click {x},{y}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    {
        "launch": lambda: cmd_launch(rest[0]),
        "shot": cmd_shot,
        "type": lambda: cmd_type(" ".join(rest)),
        "key": lambda: cmd_key(" ".join(rest)),
        "click": lambda: cmd_click(rest[0], rest[1]),
    }[cmd]()


if __name__ == "__main__":
    main()
