#!/usr/bin/env python
r"""Click the Deploy button in the open 'CSPro Deploy Application' dialog and capture
the result (and any credential prompt). Authorized auto-deploy. Usage: py deploy_click.py
"""
import os, sys, time
from pathlib import Path
from pywinauto import Desktop, keyboard

OUT = Path(__file__).resolve().parent / "shots" / "deploy"
# CSWeb deploy normally uses creds cached by CSPro from the prior session, so no prompt
# appears. If a credential dialog ever does appear, supply creds via env (never hardcode):
#   set CSPRO_ADMIN_USER / CSPRO_ADMIN_PASS  (or read from the server's root-only creds file).
ADMIN_USER = os.environ.get("CSPRO_ADMIN_USER", "")
ADMIN_PASS = os.environ.get("CSPRO_ADMIN_PASS", "")


def win(title_pred):
    for w in Desktop(backend="win32").windows():
        if w.is_visible() and title_pred(w.window_text() or ""):
            return w
    return None


def main():
    dlg = win(lambda t: t == "CSPro Deploy Application")
    if not dlg:
        print("no deploy dialog"); return
    dlg.set_focus(); time.sleep(0.3)
    dlg.click_input(coords=(505, 588))    # Deploy button (window-relative)
    print("clicked Deploy; waiting for upload ...")
    time.sleep(6)
    OUT.mkdir(parents=True, exist_ok=True)
    # capture whatever is frontmost (progress, credential prompt, or result)
    for i in range(6):
        time.sleep(4)
        top = [w for w in Desktop(backend="win32").windows()
               if w.is_visible() and (w.window_text() or "") and "CSPro" in (w.window_text() or "")]
        # credential prompt?
        cred = next((w for w in top if w.class_name() == "#32770"
                     and any("ass" in (c.window_text() or "") or "ser" in (c.window_text() or "")
                             for c in w.children())), None)
        tgt = top[0] if top else Desktop(backend="win32")
        tgt.capture_as_image().save(str(OUT / f"90_deploy_{i}.png"))
        print(f"  [{i}] front: {tgt.window_text()[:60]!r}")
        if "successfully" in (tgt.window_text() or "").lower():
            break
    print("done; see shots/deploy/90_deploy_*.png")


if __name__ == "__main__":
    main()
