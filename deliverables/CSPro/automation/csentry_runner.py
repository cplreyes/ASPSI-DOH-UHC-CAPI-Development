#!/usr/bin/env python
r"""CSEntry scenario runner — scripts a runtime data-entry path so deep-form
validations become repeatable with one command.

WHY: CSEntry entry is GUI-only and HTML modals are Chromium-rendered (not
win32-readable), so reaching a validation buried in Section B/G/H meant driving
it field-by-field by hand. This runner executes a scenario file in ONE process
(no per-step reconnect) and saves a NUMBERED screenshot after every step into
shots/<scenario>/, so a reviewer (or a vision model) confirms each validation
fired from the visual trail. The runner produces EVIDENCE; it does not assert.

Scenario DSL (one step per line; blank lines and `#` comments ignored):
  rmdata <csdb>      delete a .csdb so the next launch opens in Add mode (empty)
  launch <pff>       kill CSEntry, launch on the pff (path relative to this file)
  casekey A B C ...  type each id at full zero-pad width (auto-advances on fill)
  type <text>        type literal text (spaces ok) into the focused field
  key <keys>         pywinauto keys, e.g. {ENTER}  {ESC}  {ENTER 3}
  click <x> <y>      left-click at window-relative coords (picker rows, modal OK/Yes)
  wait <secs>        sleep
  shot <label>       labelled screenshot (one is auto-taken after every step anyway)
  note <text>        log-only; use to record the EXPECTED outcome of the next step

Usage:  py csentry_runner.py <scenario.txt> [--keep]
  --keep   leave CSEntry open at the end (default: kill it)
Exit 0 if all steps ran; non-zero on a step error (the shot trail shows where).
"""
import subprocess
import sys
import time
from pathlib import Path

import win32con
import win32gui
from pywinauto import Desktop, keyboard, mouse

CSENTRY_EXE = r"C:\Program Files (x86)\CSPro 8.0\CSEntry.exe"
HERE = Path(__file__).resolve().parent
WIN_CLASS = "CSProDEFrame"


class Runner:
    def __init__(self, scenario_path):
        self.scenario = Path(scenario_path)
        self.outdir = HERE / "shots" / self.scenario.stem
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.outdir / "run.log"
        self.n = 0
        self.win = None
        self.loglines = []

    def log(self, msg):
        print(msg, flush=True)
        self.loglines.append(msg)

    def _connect(self, tries=20):
        for _ in range(tries):
            try:
                w = Desktop(backend="win32").window(class_name=WIN_CLASS)
                if w.exists():
                    self.win = w
                    return w
            except Exception:
                pass
            time.sleep(0.5)
        raise SystemExit("ERROR: CSEntry window (CSProDEFrame) not found.")

    def _focus(self):
        """Force CSEntry to the foreground and CONFIRM it. On an active desktop
        Windows blocks focus-stealing, so a freshly-launched CSEntry can sit BEHIND
        the editor -- then send_keys leaks into the wrong app and capture grabs the
        wrong window. Maximize + SetForegroundWindow + verify; title-bar-click
        fallback. Raises if it cannot confirm foreground -> NEVER type into the
        wrong window (the bug that leaked keystrokes into VS Code on 2026-06-09)."""
        hwnd = self.win.handle
        for _ in range(6):
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                self.win.set_focus()
            except Exception:
                pass
            time.sleep(0.4)
            try:
                if win32gui.GetForegroundWindow() == hwnd:
                    return
            except Exception:
                pass
            try:  # simulated title-bar click reliably activates a window
                r = self.win.rectangle()
                self.win.click_input(coords=(min(200, max(40, r.width() // 2)), 10))
            except Exception:
                pass
            time.sleep(0.3)
        raise RuntimeError("could not bring CSEntry to the foreground "
                           "(refusing to send keystrokes to the wrong window)")

    def shot(self, label):
        self.n += 1
        path = self.outdir / f"{self.n:03d}_{label}.png"
        self._focus()
        time.sleep(0.3)
        self.win.capture_as_image().save(path)
        self.log(f"  [{self.n:03d}] {label} -> {path.name}")

    # ---- step ops -------------------------------------------------------
    def op_rmdata(self, args):
        p = (HERE / args[0]).resolve()
        try:
            p.unlink()
            self.log(f"rmdata: deleted {p.name}")
        except FileNotFoundError:
            self.log(f"rmdata: {p.name} already absent")

    def op_launch(self, args):
        pff = (HERE / args[0]).resolve()
        subprocess.run(["taskkill", "/IM", "CSEntry.exe", "/F"], capture_output=True)
        time.sleep(1.0)
        subprocess.Popen([CSENTRY_EXE, str(pff)])
        time.sleep(6.0)
        self._connect()
        self.shot("launch")

    def op_casekey(self, args):
        for a in args:
            self._focus()
            keyboard.send_keys(a, with_spaces=False, pause=0.03)
            time.sleep(0.5)
        self.shot("casekey")

    def op_type(self, args):
        text = " ".join(args)
        self._focus()
        keyboard.send_keys(text, with_spaces=True, pause=0.03)
        time.sleep(0.6)
        self.shot(f"type_{text[:16]}")

    def op_key(self, args):
        keys = " ".join(args)
        self._focus()
        keyboard.send_keys(keys, pause=0.05)
        time.sleep(0.8)
        self.shot(f"key_{keys.strip('{}').replace(' ', '')[:12]}")

    def op_click(self, args):
        x, y = int(args[0]), int(args[1])
        self._focus()
        r = self.win.rectangle()
        mouse.click(button="left", coords=(r.left + x, r.top + y))
        time.sleep(0.6)
        self.shot(f"click_{x}_{y}")

    def op_wait(self, args):
        time.sleep(float(args[0]))
        self.shot("wait")

    def op_shot(self, args):
        self.shot(args[0] if args else "shot")

    def op_note(self, args):
        self.log(f"  NOTE: {' '.join(args)}")

    OPS = {"rmdata", "launch", "casekey", "type", "key", "click", "wait", "shot", "note"}

    def run(self):
        lines = self.scenario.read_text(encoding="utf-8").splitlines()
        self.log(f"=== scenario {self.scenario.name} -> {self.outdir} ===")
        try:
            for raw in lines:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                op, args = parts[0], parts[1:]
                if op not in self.OPS:
                    self.log(f"!! unknown op: {op}")
                    continue
                self.log(f"> {line}")
                getattr(self, f"op_{op}")(args)
            self.log("=== scenario complete ===")
            return 0
        except Exception as e:
            self.log(f"!! step failed: {e}")
            try:
                self.shot("ERROR")
            except Exception:
                pass
            return 1
        finally:
            self.log_path.write_text("\n".join(self.loglines), encoding="utf-8")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keep = "--keep" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    rc = Runner(args[0]).run()
    if not keep:
        subprocess.run(["taskkill", "/IM", "CSEntry.exe", "/F"], capture_output=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
