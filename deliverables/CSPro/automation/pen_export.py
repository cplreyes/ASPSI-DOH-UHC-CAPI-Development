#!/usr/bin/env python
r"""Drive the CSPro Designer window (by EXACT title, bypassing the ambiguous
"CSPro.*" attach that the 4 parked CSDeploy dialogs break) to export a LOCAL .pen
package for sideloading to a device. No CSWeb involved.

  py pen_export.py filemenu          # focus Designer, Alt+F, screenshot File menu
  py pen_export.py keys "<seq>"      # send a pywinauto key sequence to Designer, screenshot
  py pen_export.py shot              # screenshot frontmost CSPro-ish window
"""
import sys, time
from pathlib import Path
import win32gui, win32con
from pywinauto import keyboard

TITLE = "CSPro 8.0 - [HouseholdSurvey]"
OUT = Path(__file__).resolve().parent / "shots" / "deploy"


def _find(title):
    h = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == title:
            h.append(hwnd)
        return True
    win32gui.EnumWindows(cb, None)
    return h[0] if h else None


def _focus(hwnd):
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    for _ in range(6):
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.3)
        if win32gui.GetForegroundWindow() == hwnd:
            return True
    return win32gui.GetForegroundWindow() == hwnd


def _shot(name):
    OUT.mkdir(parents=True, exist_ok=True)
    from PIL import ImageGrab
    p = OUT / f"{name}.png"
    ImageGrab.grab().save(p)
    print(f"SHOT {p}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "shot"
    hwnd = _find(TITLE)
    if not hwnd:
        print(f"ERROR: Designer window {TITLE!r} not found")
        sys.exit(1)
    ok = _focus(hwnd)
    print(f"focus={ok} hwnd={hwnd}")
    if arg == "filemenu":
        keyboard.send_keys("%f")
        time.sleep(1.0)
        _shot("pen_10_filemenu")
    elif arg == "keys":
        keyboard.send_keys(sys.argv[2], pause=0.08)
        time.sleep(1.2)
        _shot("pen_keys")
    else:
        _shot("pen_shot")


if __name__ == "__main__":
    main()
