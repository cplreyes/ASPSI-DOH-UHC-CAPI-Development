#!/usr/bin/env python3
"""One-off: drive the open 'CSPro Deploy Application' dialog to a LOCAL ZIP.

Used for PILOT builds (proof-of-fix captures) that must NEVER go to CSWeb.
Selects the 'ZIP file' target, fills the output path, clicks Deploy, waits for
the result popup, dismisses it, and minimizes the dialog back.

Usage: python zip_deploy_once.py <out_zip_path>
"""
import sys
import time

from pywinauto import Application

out = sys.argv[1]
# Several parked deploy dialogs coexist (Carl keeps F1/F3/F4 minimized). The
# Deploy click packages CURRENT on-disk files, so the dialog just needs to be
# the right instrument — pass its hwnd (auto_deploy prints them when parking).
hwnd = int(sys.argv[2])
app = Application(backend="uia").connect(handle=hwnd)
dlg = app.window(handle=hwnd)
dlg.restore()
time.sleep(1)
dlg.set_focus()

dlg.child_window(title="ZIP file", control_type="RadioButton").select()
time.sleep(0.5)
# the ZIP path edit is the LAST enabled edit after selecting the radio
edits = dlg.descendants(control_type="Edit")
zip_edit = [e for e in edits if e.is_enabled()][-1]
zip_edit.set_edit_text(out)
time.sleep(0.5)
dlg.child_window(title="Deploy", control_type="Button").click_input()

for _ in range(60):
    time.sleep(2)
    try:
        oks = [b for w in app.windows() for b in w.descendants(control_type="Button")
               if (b.window_text() or "").strip() == "OK"]
        if oks:
            oks[0].click_input()
            time.sleep(1)
            break
    except Exception:
        pass

try:
    dlg.minimize()
except Exception:
    pass
print("zip deploy attempted ->", out)
