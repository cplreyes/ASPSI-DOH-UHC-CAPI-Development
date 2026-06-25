#!/usr/bin/env python
r"""
CSPro Designer compile driver - one command for the whole IRON-RULE loop:
regenerate -> bind -> open -> compile -> read.

PROVEN on F1/F3/F4 (2026-06-08): each reads "Compile Successful" headlessly.

WHY THIS WORKS (after a lot of dead ends):
  - CSPro Designer's menus are OWNER-DRAWN -> win32 can't read menu labels, and
    UIA .descendants() tree walks HANG. So we drive it by KEYBOARD, not menus.
  - CSPro 8.0 Users Guide p.153/155:  Ctrl+L = Logic view, Ctrl+K = Compile,
    results land in the 'Compiler Output' tab as "Compile Successful" or an error list.
  - The compile RESULT is read by SCREENSHOTTING the window; a vision model reads
    the 'Compiler Output' tab (robust vs. the Scintilla editor + custom panes).
  - Launch with an app:  CSPro.exe <path-to.ent>  opens it directly in Designer.
  - Standard dialogs (#32770) ARE win32-readable/clickable; only menus are owner-drawn.

MODES
  py cspro_compile_driver.py F3              # open existing .ent, compile, screenshot
  py cspro_compile_driver.py F3 --build      # regenerate dcf/apc/fmf -> bind -> compile
  py cspro_compile_driver.py F3 --build --save   # + Ctrl+S to persist the .ent

--build performs the full generator->bindable pipeline (so a generator fix flows
straight to a compile):
  1. kill any running CSPro (avoid stale-in-memory / file locks)
  2. run generate_dcf.py, generate_apc.py, generate_fmf.py (whichever exist) in the dir
  3. copy <Base>.generated.fmf -> <Base>.fmf   (the .ent binds the plain .fmf)
  4. ensure <Base>.ent / .ent.qsf / .ent.mgf exist (templated from F1 boilerplate)
  5. run preflight_validate.py and report (warns, does not hard-block; compile is truth)

The caller (a vision model) reads <OUT>/<KEY>_compile.png: "Compile Successful" => clean;
otherwise the Compiler Output lists file/line/message for the next generator fix.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from pywinauto.application import Application
from pywinauto import keyboard

CSPRO_EXE = r"C:\Program Files (x86)\CSPro 8.0\CSPro.exe"
HERE = Path(__file__).resolve().parent          # deliverables/CSPro/automation
CSPRO_DIR = HERE.parent                          # deliverables/CSPro
OUT = HERE / "shots"
F1_QSF = CSPRO_DIR / "F1" / "FacilityHeadSurvey.ent.qsf"   # boilerplate question-text template

# CSWeb Simple Synchronization (an .ent app-property, NOT logic). Baked here from the
# block CSPro Designer wrote into FacilityHeadSurvey.ent after Options > Synchronization
# (Test Connection PASS 2026-06-09). Same CSWeb for all three instruments, so it is
# instrument-independent. direction "put" = device->server upload (covers the pilot
# round-trip: collect -> sync up -> verify in CSWeb). Switch to "both" to also pull cases down.
SYNC_SERVER = "https://csweb.asiansocial.org/csweb/api"
SYNC_DIRECTION = "put"

# base = file stem; ent_name = the .ent "name" (uppercase, no suffix).
SPECS = {
    "F1": {"dir": "F1", "base": "FacilityHeadSurvey", "ent_name": "FACILITYHEADSURVEY", "has_fmf_gen": False},
    "F3": {"dir": "F3", "base": "PatientSurvey",       "ent_name": "PATIENTSURVEY",      "has_fmf_gen": True},
    "F4": {"dir": "F4", "base": "HouseholdSurvey",     "ent_name": "HOUSEHOLDSURVEY",    "has_fmf_gen": True},
    "SV": {"dir": "SV", "base": "SupervisorApp",       "ent_name": "SUPERVISORAPP",      "has_fmf_gen": True},
    # Phase-2 C1 spike apps (supervisor-hub/). Pre-authored by build_hub_apps.py; compile-only
    # (NO --build — they have no generate_*.py and must NOT get the PSGC-external .ent template).
    "LOGIN": {"dir": "supervisor-hub", "base": "LoginApp", "ent_name": "LOGINAPP", "has_fmf_gen": False},
    "MENU":  {"dir": "supervisor-hub", "base": "MenuApp",  "ent_name": "MENUAPP",  "has_fmf_gen": False},
    # C7 map feasibility probe (throwaway; supervisor-hub/spikes/). Compile-only.
    "MAPSPIKE": {"dir": "supervisor-hub/spikes", "base": "MapSpike", "ent_name": "MAPSPIKE", "has_fmf_gen": False},
}


def _paths(key):
    s = SPECS[key]
    d = CSPRO_DIR / s["dir"]
    base = s["base"]
    return {
        "dir": d, "base": base, "ent_name": s["ent_name"], "has_fmf_gen": s["has_fmf_gen"],
        "ent": d / f"{base}.ent", "dcf": d / f"{base}.dcf", "fmf": d / f"{base}.fmf",
        "generated_fmf": d / f"{base}.generated.fmf", "apc": d / f"{base}.ent.apc",
        "qsf": d / f"{base}.ent.qsf", "mgf": d / f"{base}.ent.mgf",
    }


def _run(cmd, cwd):
    print(f"    $ {' '.join(str(c) for c in cmd)}  (cwd={cwd.name})")
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    for line in out.splitlines():
        if any(k in line for k in ("Wrote", "Capped", "WARNING", "orphan", "Error", "error", "ALL CLEAN", "FAIL")):
            print(f"      {line.strip()}")
    return r.returncode, out


def _ent_json(p):
    return json.dumps({
        "software": "CSPro", "version": 8.0, "fileType": "application", "type": "entry",
        "name": p["ent_name"], "label": p["base"],
        "dictionaries": [
            {"type": "input", "path": f"{p['base']}.dcf", "parent": f"{p['base']}.fmf"},
            {"type": "external", "path": "psgc_region.dcf"},
            {"type": "external", "path": "psgc_province.dcf"},
            {"type": "external", "path": "psgc_city.dcf"},
            {"type": "external", "path": "psgc_barangay.dcf"},
            # facility_lookup removed 2026-06-10: its text-repo indexing infinite-loops
            # Android CSEntry at app start (the auto-fill it served is gone in the
            # single-Questionnaire-Number redesign). See the redesign spec + blockers memo.
        ],
        "forms": [f"{p['base']}.fmf"],
        "questionText": [f"{p['base']}.ent.qsf"],
        "code": [{"type": "main", "path": f"{p['base']}.ent.apc"}],
        "messages": [f"{p['base']}.ent.mgf"],
        "logicSettings": {"version": 2.0, "caseSensitive": {"symbols": False},
                          "actionInvoker": {"accessFromExternalCaller": "promptIfNoValidAccessToken",
                                            "convertResultsForLogic": True}},
        "properties": {"askOperatorId": False, "autoAdvanceOnSelection": True, "caseTree": "mobileOnly",
                       "centerForms": False, "createListing": False, "createLog": False, "decimalMark": "dot",
                       "displayCodesAlongsideLabels": False, "notes": {"delete": "all", "edit": "all"},
                       "partialSave": {"operatorEnabled": True}, "showEndCaseMessage": True,
                       "showOnlyDiscreteValuesInComboBoxes": True, "showFieldLabels": True,
                       "showErrorMessageNumbers": False, "showQuestionText": True, "showRefusals": True,
                       "sync": {"server": SYNC_SERVER, "direction": SYNC_DIRECTION},
                       "verify": {"frequency": 1, "start": 1}, "htmlDialogs": True,
                       "paradata": {"collection": "all", "recordCoordinates": False,
                                    "recordInitialPropertyValues": False, "recordIteratorLoadCases": False,
                                    "recordValues": False, "deviceStateIntervalMinutes": 5},
                       "useHtmlComponentsInsteadOfNativeVersions": False},
    }, indent=2)


def _kill_cspro():
    subprocess.run(["taskkill", "/F", "/IM", "CSPro.exe"], capture_output=True, text=True)
    time.sleep(1.5)


def build_instrument(key):
    """Regenerate -> bind -> ensure app files -> preflight. Returns True if preflight clean."""
    p = _paths(key)
    print(f"[build {key}] regenerate -> bind")
    _kill_cspro()  # avoid stale-in-memory / file locks while regenerating

    # 1. run generators present in the instrument dir (dcf first; apc; then fmf)
    for gen in ("generate_dcf.py", "generate_apc.py", "generate_fmf.py"):
        if (p["dir"] / gen).exists():
            rc, _ = _run([sys.executable, gen], p["dir"])
            if rc != 0:
                print(f"    !! {gen} exited {rc}")

    # 2. bind: copy <Base>.generated.fmf -> <Base>.fmf, then re-apply the capture-type
    #    pass (DropDown >=7 / Date / CheckBox). The generators emit RadioButton/TextBox
    #    defaults, so a bare copy SHIPS A REGRESSION — the 2026-06-12 F4 sweep deploy
    #    lost 5 DropDowns + 2 date pickers this way. Promotion path is
    #    generate -> copy -> optimize (see log 2026-06-12).
    if p["has_fmf_gen"] and p["generated_fmf"].exists():
        p["fmf"].write_bytes(p["generated_fmf"].read_bytes())
        print(f"    copied {p['generated_fmf'].name} -> {p['fmf'].name}")
    # ... then re-apply capture types for EVERY instrument (idempotent; F1's
    # hand-maintained fmf needs it too — its 2 date fields carried a plain
    # 'Date' from old Designer hand-edits until 2026-06-12).
    rc, _ = _run([sys.executable, str(HERE / "optimize_capture_types.py"), key], HERE)
    if rc != 0:
        print(f"    !! optimize_capture_types.py exited {rc}")

    # 3. ensure .ent.qsf / .ent.mgf / .ent exist (templated boilerplate)
    if not p["qsf"].exists() and F1_QSF.exists():
        p["qsf"].write_bytes(F1_QSF.read_bytes())
        print(f"    templated {p['qsf'].name}")
    if not p["mgf"].exists():
        p["mgf"].write_bytes(("﻿{ Application '%s' message file generated by CSPro }\n" % p["base"]).encode("utf-8"))
        print(f"    templated {p['mgf'].name}")
    if not p["ent"].exists():
        p["ent"].write_text(_ent_json(p), encoding="utf-8")
        print(f"    templated {p['ent'].name}")
    else:
        # ensure required properties are present on a pre-existing .ent (idempotent;
        # surgical merge so we never clobber other Designer-set properties):
        #   - CSWeb sync block
        #   - operator partial save (stop mid-interview + resume; 2026-06-11)
        #   - auto-advance on selection (tap a choice -> next field, no extra Next tap; 2026-06-11)
        ent_obj = json.loads(p["ent"].read_text(encoding="utf-8"))
        props = ent_obj.setdefault("properties", {})
        changed = []
        want_sync = {"server": SYNC_SERVER, "direction": SYNC_DIRECTION}
        if props.get("sync") != want_sync:
            props["sync"] = want_sync
            changed.append("CSWeb sync")
        if props.get("partialSave", {}).get("operatorEnabled") is not True:
            props["partialSave"] = {"operatorEnabled": True}
            changed.append("operator partialSave")
        if props.get("autoAdvanceOnSelection") is not True:
            props["autoAdvanceOnSelection"] = True
            changed.append("autoAdvanceOnSelection")
        if changed:
            p["ent"].write_text(json.dumps(ent_obj, indent=2), encoding="utf-8")
            print(f"    set {' + '.join(changed)} in {p['ent'].name}")

    # 4. preflight (report; compile is the real gate)
    if (CSPRO_DIR / "preflight_validate.py").exists():
        rc, out = _run([sys.executable, "preflight_validate.py"], CSPRO_DIR)
        clean = "ALL CLEAN" in out
        print(f"    preflight: {'ALL CLEAN' if clean else 'NOT CLEAN (see compile output)'}")
        return clean
    return True


def _bring_to_front(main):
    """Force the CSPro window to the foreground before keystrokes/capture. On an active
    desktop Windows blocks focus-stealing, so a freshly-launched CSPro can sit BEHIND the
    user's editor -- then keystrokes go to the wrong app and the screenshot grabs the wrong
    window. Maximize + SetForegroundWindow, verify, fall back to a title-bar click."""
    import win32gui
    import win32con
    hwnd = main.handle
    for _ in range(5):
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            main.set_focus()
        except Exception:
            pass
        time.sleep(0.5)
        try:
            if win32gui.GetForegroundWindow() == hwnd:
                return True
        except Exception:
            pass
        try:  # simulated title-bar click reliably activates a window
            r = main.rectangle()
            main.click_input(coords=(min(200, max(40, r.width() // 2)), 10))
        except Exception:
            pass
        time.sleep(0.4)
    return False


def clear_known_dialogs(app, max_rounds=16):
    """Clear CSPro's standard #32770 dialogs on open. Unknown dialogs -> screenshot + stop.
    Every per-dialog interaction is guarded: F1's startup dialogs are TRANSIENT and can
    close themselves between enumeration and the next call (stale handle ->
    InvalidWindowHandle mid-round; seen 2026-06-12) — treat that as 'dialog gone, next'."""
    for _ in range(max_rounds):
        try:
            fg = app.top_window()
            if fg.class_name() != "#32770":
                return
            title = fg.window_text()
            btns = [b.window_text() for b in fg.children(class_name="Button")]
            fg.set_focus()
            time.sleep(0.2)
            if title == "Rename Item":            # F1 id-block re-sync; defaults are correct
                fg["OK"].click_input()
            elif title in ("CSPro Designer", "CSPro 8.0", "CSPro"):
                if "OK" in btns:
                    fg["OK"].click_input()
                elif "Cancel" in btns:
                    fg["Cancel"].click_input()
            else:
                OUT.mkdir(parents=True, exist_ok=True)
                shot = OUT / "UNEXPECTED_dialog.png"
                fg.capture_as_image().save(shot)
                print(f"  UNEXPECTED dialog {title!r} -> {shot}; stopping.")
                return
            time.sleep(0.9)
        except Exception:
            time.sleep(0.5)      # stale/transient dialog — re-enumerate next round
            continue


def compile_instrument(key, do_save=False):
    p = _paths(key)
    if not p["ent"].exists():
        print(f"NO-ENT: {p['ent']} missing. Run with --build first.")
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)

    try:
        app = Application(backend="win32").connect(title_re=r"CSPro 8\.0.*", timeout=3,
                                                   found_index=0)
        print("attached to running CSPro")
    except Exception:
        print(f"launching CSPro on {p['ent'].name} ...")
        proc = subprocess.Popen([CSPRO_EXE, str(p["ent"])])
        time.sleep(16)
        # connect by PID, not title: F1's open spawns several CSPro-titled
        # top-level windows incl. transient dialogs (title matching hit
        # ElementAmbiguousError, then InvalidWindowHandle as one vanished
        # mid-connect; seen 2026-06-12 — F4 only had one window).
        app = Application(backend="win32").connect(process=proc.pid, timeout=20)

    clear_known_dialogs(app)

    frames = [w for w in app.windows() if (w.window_text() or "").startswith("CSPro 8.0 - ")]
    main = max(frames, key=lambda w: (w.rectangle().width() * w.rectangle().height()))
    if not _bring_to_front(main):
        print("  WARNING: could not confirm CSPro is foreground; keystrokes may misfire.")
    time.sleep(0.4)
    keyboard.send_keys("^l")
    time.sleep(1.3)
    keyboard.send_keys("^k")
    print("compile sent; waiting ...")
    time.sleep(10)

    _bring_to_front(main)   # re-assert foreground so the screenshot captures CSPro, not an overlay
    time.sleep(0.4)
    shot = OUT / f"{key}_compile.png"
    main.capture_as_image().save(shot)
    print(f"COMPILE-SHOT {shot}")

    if do_save:
        _bring_to_front(main)
        time.sleep(0.3)
        keyboard.send_keys("^s")
        time.sleep(2.5)
        clear_known_dialogs(app)
        print("SAVED (Ctrl+S)")


def main():
    args = sys.argv[1:]
    key = next((a for a in args if a in SPECS), None)
    if not key:
        print("usage: py cspro_compile_driver.py {F1|F3|F4} [--build] [--save]")
        sys.exit(1)
    if "--build" in args:
        build_instrument(key)
    compile_instrument(key, do_save="--save" in args)


if __name__ == "__main__":
    main()
