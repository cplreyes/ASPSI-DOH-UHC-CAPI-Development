#!/usr/bin/env python3
"""build_hub_apps.py — Phase-2 C1 spike: login + role-menu shell generator.

Emits two minimal CSEntry apps plus the external login roster used by the
supervisor/enumerator login+menu shell (Phase-2 spike C1):

  UserRoster.dcf + .dat                 external login roster (key UR_USERNAME)
  LoginApp.{dcf,fmf,ent.apc,ent.qsf,ent.mgf,ent,pff}
  MenuApp.{dcf,fmf,ent.apc,ent.qsf,ent.mgf,ent,pff}

The shell proves three mechanisms on CSPro 8 + itel (see spikes/C1-login-menu-spike.md):
  * loadcase(USER_ROSTER_DICT, LOGIN_USERNAME)  — auth against an external dict (proven in-repo)
  * savesetting / loadsetting                    — role handoff between apps (grounded 2026-06-24)
  * execpff("<app>.pff", stop)                   — chain-launch (grounded 2026-06-24)

Iron rule: never hand-edit the generated .dcf/.fmf/.ent.qsf/.ent.apc/.ent/.pff/.dat —
edit THIS generator and rerun.

Run:  python build_hub_apps.py        # writes all artifacts into this folder
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))   # deliverables/CSPro  (for cspro_helpers)
from cspro_helpers import (             # noqa: E402
    alpha, select_one, record, build_dictionary, write_dcf, _truncate_long_labels,
)

# ----------------------------------------------------------------------------
# Seed roster (spike only — placeholder creds, rotate before any real use).
# ----------------------------------------------------------------------------
ROSTER_ROWS = [
    # (username, password, role, operator_id, cluster)
    ("se-004", "changeme04", "enumerator", "se-004", "01028"),
    ("se-011", "changeme11", "enumerator", "se-011", "01028"),
    ("fs-01",  "changeme-fs", "supervisor", "fs-01", "01028"),
]

# Role-filtered field-ops menus (spec ADDENDUM-2). Two value sets on MENU_CHOICE; the
# menu app swaps to the logged-in role's set in onfocus (setvalueset). Codes are DISJOINT
# across roles (supervisor 01-08, enumerator 11-18) so the postproc routes by code alone.
# Items whose backend is spike-gated (Assign EA / Receive / Map / collect / relay) show a
# precise "pending Phase-2B" message; the BUILT actions (open/conduct an instrument, log
# out, the per-role on-device report ENTRY POINT) work now.
SUPERVISOR_MENU = [
    ("Assign Enumeration Area",            "01"),
    ("Listing Data — view report",         "02"),
    ("Survey Interview — view report",     "03"),
    ("View EA on Map",                     "04"),
    ("Open F1 — Facility Head (review)",   "05"),
    ("Open F3 — Patient (review)",         "06"),
    ("Open F4 — Household (review)",       "07"),
    ("Log out",                            "08"),
]
ENUMERATOR_MENU = [
    ("Listing Exercise",                       "11"),
    ("Receive Assigned Data (Patient)",        "12"),
    ("Conduct F1 — Facility Head Interview",   "13"),
    ("Conduct F3 — Patient Interview",         "14"),
    ("Conduct F4 — Household Interview",       "15"),
    ("View EA on Map",                         "16"),
    ("View my report",                         "17"),
    ("Log out",                                "18"),
]

# B3 — EA / cluster assignment lookup (one assignment per EA-facility). Distributed
# supervisor->enumerator in N1 (B4, C2-gated); here it is the structural dict + seed.
ASSIGNMENT_ROWS = [
    # (ea_facility_code(9), enumerator_id, instrument, target_count, ea_name, cluster)
    ("040340002", "se-004", "F3", "30", "Binan RHU - Patient Survey",        "01028"),
    ("040340005", "se-011", "F4", "20", "Binan Brgy 5 - Household Survey",    "01028"),
    ("040340001", "fs-01",  "F1", "1",  "Binan City Health Office",          "01028"),
]

# ----------------------------------------------------------------------------
# .fmf form emitter — ported from SV/generate_fmf.py (single-record forms only,
# no roster, no off-form items). Mirrors the proven F1/F4/SV auto-layout that the
# CSPro 8 Designer accepts.
# ----------------------------------------------------------------------------
DEFAULT_FONT = ("DefaultTextFont=-013 0000 0000 0000 0700 0000 0000 0000 "
                "0000 0000 0000 0000 0000 Arial")
ENTRY_FONT = ("FieldEntryFont=0018 0000 0000 0000 0600 0000 0000 0000 "
              "0000 0000 0000 0000 0000 Courier New")
ROW_H = 30; TOP_Y = 27; LABEL_X = 50; LABEL_X2 = 330
FIELD_X = 350; FIELD_TEXTBOX_X2 = 760; FIELD_RADIO_X2 = 365
FIELD_H = 20; TEXT_H = 16; FORM_W = 806


def _form_height(n_items):
    return max(300, TOP_Y + n_items * ROW_H + 40)


def _emit_form(lines, num, label, item_names, height):
    lines += ["[Form]", f"Name=FORM{num:03d}", f"Label={label}", "Level=1",
              f"Size={FORM_W},{height}", "  "]
    for n in item_names:
        lines.append(f"Item={n}")
    lines += ["  ", "[EndForm]", "  "]


def _emit_group(lines, sym, label, form_one_based, item_objs, dict_name):
    lines += ["[Group]", "Required=Yes", f"Name={sym}", f"Label={label}",
              f"Form={form_one_based}", "Max=1"]
    if not item_objs:
        lines += ["[EndGroup]", "  "]
        return
    lines.append("  ")
    for i, it in enumerate(item_objs):
        y = TOP_Y + i * ROW_H
        coded = bool(it.get("valueSets"))
        is_alpha = it.get("contentType") == "alpha"
        x2 = FIELD_RADIO_X2 if coded else FIELD_TEXTBOX_X2
        capture = "RadioButton" if coded else "TextBox"
        text = (it["labels"][0]["text"] if it.get("labels") else it["name"]).replace("\n", " ").replace("\r", " ")
        lines += ["[Field]", f"Name={it['name']}",
                  f"Position={FIELD_X},{y},{x2},{y + FIELD_H}",
                  f"Item={it['name']},{dict_name}"]
        if not coded and is_alpha:
            lines.append("UseUnicodeTextBox=Yes")
        lines += [f"DataCaptureType={capture}", f"Form={form_one_based}", "  ",
                  "[Text]", f"Position={LABEL_X},{y + 3},{LABEL_X2},{y + 3 + TEXT_H}",
                  f"Text={text}", " ", "  "]
    lines += ["[EndGroup]", "  "]


def build_fmf(d, ff_name, dcf_rel, dict_label, form_plan):
    """form_plan: list of (form_label, record_name). FORM000 (id form) auto-prepended."""
    _truncate_long_labels(d)
    dict_name = d["name"]
    level = d["levels"][0]
    level_name = level["name"]
    recs = {r["name"]: r for r in level["records"]}
    id_objs = list(level["ids"]["items"])
    forms = [{"num": 0, "label": "Case Key", "sym": "IDS0_FORM",
              "names": [it["name"] for it in id_objs], "objs": id_objs}]
    for idx, (label, rn) in enumerate(form_plan, start=1):
        objs = list(recs[rn]["items"])
        forms.append({"num": idx, "label": label, "sym": f"{rn}_FORM",
                      "names": [it["name"] for it in objs], "objs": objs})
    lines = ["[FormFile]", "Version=CSPro 8.0", f"Name={ff_name}", f"Label={dict_label}",
             DEFAULT_FONT, ENTRY_FONT, "Type=SystemControlled", "  ",
             "[Dictionaries]", f"File={dcf_rel}", "  "]
    for f in forms:
        _emit_form(lines, f["num"], f["label"], f["names"], _form_height(len(f["objs"])))
    lines += ["[Level]", f"Name={level_name}", f"Label={dict_label} Level", "  "]
    for f in forms:
        _emit_group(lines, f["sym"], f["label"], f["num"] + 1, f["objs"], dict_name)
    return "\r\n".join(lines) + "\r\n"


# ----------------------------------------------------------------------------
# .ent.qsf question-text emitter — ported from SV/generate_qsf.py.
# ----------------------------------------------------------------------------
QSF_HEADER = """\
---
fileType: Question Text
version: CSPro 8.0
languages:
  - name: EN
    label: English
styles:
  - name: Normal
    className: normal
    css: |
      font-family: Arial;font-size: 16px;
  - name: Instruction
    className: instruction
    css: |
      font-family: Arial;font-size: 14px;color: #0000FF;
  - name: Heading 1
    className: heading1
    css: |
      font-family: Arial;font-size: 36px;
  - name: Heading 2
    className: heading2
    css: |
      font-family: Arial;font-size: 24px;
  - name: Heading 3
    className: heading3
    css: |
      font-family: Arial;font-size: 18px;
questions:"""


def _iter_items(d):
    level = d["levels"][0]
    for it in level["ids"]["items"]:
        yield it
    for rec in level["records"]:
        for it in rec["items"]:
            yield it


def build_qsf(d, dict_name):
    _truncate_long_labels(d)
    lines = [QSF_HEADER]
    for it in _iter_items(d):
        label = (it["labels"][0]["text"] if it.get("labels") else it["name"])
        label = label.replace("\n", " ").replace("\r", " ")
        lines += [f"  - name: {dict_name}.{it['name']}", "    conditions:",
                  "      - questionText:", "          EN: |", f"            <p>{label}</p>"]
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# .ent app-shell emitter (model: SV/SupervisorApp.ent, minus sync — these are
# utility apps that never sync to CSWeb).
# ----------------------------------------------------------------------------
def build_ent(app_name, label, dcf, fmf, qsf, apc, mgf, externals=None):
    dicts = [{"type": "input", "path": dcf, "parent": fmf}]
    for ext in (externals or []):
        dicts.append({"type": "external", "path": ext})
    return {
        "software": "CSPro", "version": 8.0, "fileType": "application", "type": "entry",
        "name": app_name, "label": label,
        "dictionaries": dicts,
        "forms": [fmf], "questionText": [qsf],
        "code": [{"type": "main", "path": apc}],
        "messages": [mgf],
        "logicSettings": {
            "version": 2.0, "caseSensitive": {"symbols": False},
            "actionInvoker": {"accessFromExternalCaller": "promptIfNoValidAccessToken",
                              "convertResultsForLogic": True},
        },
        "properties": {
            "askOperatorId": False, "autoAdvanceOnSelection": True, "caseTree": "mobileOnly",
            "centerForms": False, "createListing": False, "createLog": False, "decimalMark": "dot",
            "displayCodesAlongsideLabels": False, "notes": {"delete": "all", "edit": "all"},
            "partialSave": {"operatorEnabled": False},
            "showEndCaseMessage": False, "showOnlyDiscreteValuesInComboBoxes": True,
            "showFieldLabels": True, "showErrorMessageNumbers": False, "showQuestionText": True,
            "showRefusals": False, "htmlDialogs": True, "useHtmlComponentsInsteadOfNativeVersions": False,
        },
    }


def _pff(application, input_data, externals=None):
    lines = ["[Run Information]", "Version=CSPro 8.0", "AppType=Entry", "",
             "[Files]", f"Application=.\\{application}", f"InputData=.\\{input_data}", ""]
    if externals:
        lines.append("[ExternalFiles]")
        for dict_name, dat in externals.items():
            lines.append(f"{dict_name}=.\\{dat}")
        lines.append("")
    return "\r\n".join(lines)


def _mgf(app_label):
    return f"{{ Application '{app_label}' message file generated by build_hub_apps.py }}\n"


# ----------------------------------------------------------------------------
# Dictionaries
# ----------------------------------------------------------------------------
def build_user_roster_dict():
    """External login roster, modelled on the proven PSGC external-lookup shape
    (recordType start/length 0, relativePositions, alpha key) so loadcase() resolves
    exactly as the F1/F3/F4 PSGC dicts do."""
    return {
        "software": "CSPro", "version": 8.0, "fileType": "dictionary",
        "name": "USER_ROSTER_DICT",
        "labels": [{"text": "User Roster Lookup"}],
        "readOptimization": True,
        "recordType": {"start": 0, "length": 0},
        "defaults": {"decimalMark": True, "zeroFill": True},
        "relativePositions": True,
        "levels": [{
            "name": "USER_ROSTER_DICT_LEVEL",
            "labels": [{"text": "User Roster Lookup Level"}],
            "ids": {"items": [{
                "name": "UR_USERNAME", "labels": [{"text": "Username"}],
                "contentType": "alpha", "start": 1, "length": 20,
            }]},
            "records": [{
                "name": "UR_REC", "labels": [{"text": "User record"}],
                "occurrences": {"required": True, "maximum": 1},
                "items": [
                    {"name": "UR_PASSWORD", "labels": [{"text": "Password"}], "contentType": "alpha", "length": 20},
                    {"name": "UR_ROLE", "labels": [{"text": "Role"}], "contentType": "alpha", "length": 20},
                    {"name": "UR_OPERATOR_ID", "labels": [{"text": "Operator ID"}], "contentType": "alpha", "length": 20},
                    {"name": "UR_CLUSTER", "labels": [{"text": "Cluster"}], "contentType": "alpha", "length": 10},
                ],
            }],
        }],
    }


def write_user_roster_data(path):
    """Fixed-width: UR_USERNAME(20) UR_PASSWORD(20) UR_ROLE(20) UR_OPERATOR_ID(20) UR_CLUSTER(10)."""
    widths = [20, 20, 20, 20, 10]
    with Path(path).open("w", encoding="utf-8", newline="\n") as fh:
        for row in ROSTER_ROWS:
            fh.write("".join(v[:w].ljust(w) for v, w in zip(row, widths)) + "\n")


def build_login_dict():
    """Input dict: case key = username (alpha), one record holding the password."""
    id_items = [{
        "name": "LOGIN_USERNAME", "labels": [{"text": "Username"}],
        "contentType": "alpha", "start": 2, "length": 20,
    }]
    rec = record("LOGIN_REC", "Login record", "L", [
        alpha("LOGIN_PASSWORD", "Password", length=20),
    ])
    return build_dictionary("LOGINAPP_DICT", "LoginApp", records=[rec], id_items=id_items)


def _menu_choice_item():
    """MENU_CHOICE with TWO value sets (supervisor=VS1, enumerator=VS2); the menu .apc
    swaps to the role's set in onfocus. length 2 (codes 01-08 / 11-18), zero-filled."""
    def _vs(name, label, options):
        return {"name": name, "labels": [{"text": label}],
                "values": [{"labels": [{"text": t}], "pairs": [{"value": c}]} for t, c in options]}
    return {
        "name": "MENU_CHOICE", "labels": [{"text": "Choose an action"}],
        "contentType": "numeric", "length": 2, "zeroFill": True,
        "valueSets": [
            _vs("MENU_CHOICE_VS1", "Supervisor menu", SUPERVISOR_MENU),
            _vs("MENU_CHOICE_VS2", "Enumerator menu", ENUMERATOR_MENU),
        ],
    }


def build_menu_dict():
    """Input dict: trivial numeric session key, a protected role display, and the
    role-filtered menu choice (two value sets — see _menu_choice_item)."""
    id_items = [{
        "name": "MENU_SESSION", "labels": [{"text": "Session"}],
        "contentType": "numeric", "start": 2, "length": 1, "zeroFill": True,
    }]
    rec = record("MENU_REC", "Menu record", "M", [
        alpha("ROLE_SHOWN", "Logged-in role", length=20),
        _menu_choice_item(),
    ])
    return build_dictionary("MENUAPP_DICT", "MenuApp", records=[rec], id_items=id_items)


def build_assignment_dict():
    """B3 — external EA-assignment lookup, modelled on the UserRoster shape (recordType
    start/length 0, alpha key, one record) so loadcase() resolves the same way. Keyed by
    the 9-digit EA-facility code; one assignment per EA. The patient pre-list (the listing
    output that becomes the enumerator's assigned interview targets) attaches in N2 (B5),
    where the listing flow is built."""
    return {
        "software": "CSPro", "version": 8.0, "fileType": "dictionary",
        "name": "ASSIGNMENT_DICT",
        "labels": [{"text": "EA Assignment Lookup"}],
        "readOptimization": True,
        "recordType": {"start": 0, "length": 0},
        "defaults": {"decimalMark": True, "zeroFill": True},
        "relativePositions": True,
        "levels": [{
            "name": "ASSIGNMENT_DICT_LEVEL",
            "labels": [{"text": "EA Assignment Lookup Level"}],
            "ids": {"items": [{
                "name": "AS_FACILITY_CODE", "labels": [{"text": "EA / Facility Code (9-digit RRPPMMMFF)"}],
                "contentType": "alpha", "start": 1, "length": 9,
            }]},
            "records": [{
                "name": "AS_REC", "labels": [{"text": "Assignment record"}],
                "occurrences": {"required": True, "maximum": 1},
                "items": [
                    {"name": "AS_ENUMERATOR_ID", "labels": [{"text": "Assigned Enumerator ID"}], "contentType": "alpha", "length": 20},
                    {"name": "AS_INSTRUMENT", "labels": [{"text": "Instrument (F1/F3/F4)"}], "contentType": "alpha", "length": 4},
                    {"name": "AS_TARGET_COUNT", "labels": [{"text": "Target case count"}], "contentType": "alpha", "length": 4},
                    {"name": "AS_EA_NAME", "labels": [{"text": "EA / Facility name"}], "contentType": "alpha", "length": 50},
                    {"name": "AS_CLUSTER", "labels": [{"text": "Cluster"}], "contentType": "alpha", "length": 10},
                ],
            }],
        }],
    }


def write_assignment_data(path):
    """Fixed-width: AS_FACILITY_CODE(9) AS_ENUMERATOR_ID(20) AS_INSTRUMENT(4)
    AS_TARGET_COUNT(4) AS_EA_NAME(50) AS_CLUSTER(10)."""
    widths = [9, 20, 4, 4, 50, 10]
    with Path(path).open("w", encoding="utf-8", newline="\n") as fh:
        for row in ASSIGNMENT_ROWS:
            fh.write("".join(v[:w].ljust(w) for v, w in zip(row, widths)) + "\n")


# ----------------------------------------------------------------------------
# Logic (.ent.apc)
# ----------------------------------------------------------------------------
LOGIN_APC = """\
{ ============================================================================
  LoginApp — Phase-2 C1 spike: login + role handoff   (AUTOGENERATED)
  Do NOT hand-edit: edit build_hub_apps.py and rerun.  Spec:
  docs/superpowers/specs/2026-06-21-supervisor-app-phase2-bluetooth-design.md
  ============================================================================ }

PROC GLOBAL

PROC LOGIN_PASSWORD
postproc
  { Authenticate against the UserRoster external dict (loadcase by the case-key
    username), then hand the role to MenuApp via savesetting + chain-launch.
    loadcase()/<> 0 is the proven in-repo idiom (F1/F3/F4 PSGC cascades). }
  if loadcase(USER_ROSTER_DICT, LOGIN_USERNAME) <> 0 then
    if strip(UR_PASSWORD) = strip(LOGIN_PASSWORD) then
      savesetting("hub_role", strip(UR_ROLE));
      savesetting("hub_operator_id", strip(UR_OPERATOR_ID));
      savesetting("hub_cluster", strip(UR_CLUSTER));
      execpff("MenuApp.pff", stop);   { stop = end LoginApp, launch the menu }
    else
      errmsg("Incorrect password.");
      reenter;
    endif;
  else
    errmsg("Unknown username.");
    reenter;
  endif;
"""

MENU_APC = """\
{ ============================================================================
  MenuApp — Phase-2 field-ops role menu   (AUTOGENERATED)
  Do NOT hand-edit: edit build_hub_apps.py and rerun.
  Restructured 2026-06-25 (B1) to the spec ADDENDUM-2 Supervisor/Enumerator menus.
  BUILT actions: open/conduct an instrument (PFF chain-launch, OnExit back to menu),
  log out (execpff back to LoginApp), and the per-role on-device report ENTRY POINT.
  PENDING (spike-gated, shown as a precise message): Assign EA / Receive assigned /
  Listing exchange (C2 Bluetooth spike); View EA on Map (C7 map spike).
  REPORT NOTE (B2/N4): the on-device report uses errmsg text (proven). A rich HTML
  report via view() is NOT yet feasibility-confirmed — Phase-3 view() displays a photo
  IMAGE, not generated HTML — so the HTML/live-coverage version is a flagged follow-up
  (needs a small view()-HTML spike + the C2-collected data).
  ============================================================================ }

PROC GLOBAL
string m_role;
Pff instr_pff;

function launch_instrument(string pffPath)
  { Launch a SEPARATELY-INSTALLED instrument and RETURN to this menu on exit. Load the
    instrument's OWN .pff (inherits its data file + externals UNCHANGED — no data split),
    and add only an OnExit back to the menu. CSEntry installs each app at a sibling folder
    .../csentry/<App>/; the running menu lives in .../csentry/LoginApp/, so the instrument
    is "../<App>/<App>.pff" and OnExit back is "../LoginApp/MenuApp.pff". (C1-proven; the
    instruments are launched UNMODIFIED — D6.) }
  instr_pff.load(pffPath);
  instr_pff.setProperty("OnExit", "../LoginApp/MenuApp.pff");
  instr_pff.exec();
end;

function show_ea_map()
  { N3 "View EA on Map" - offline EA/case map (C7 = PASS). setBaseMap loads the bundled
    offline MBTiles (renders with NO signal); returns 0 if the file isn't on the device.
    Markers are fixed Laguna/Binan EA reference points for now - the real EA + captured-case
    markers wire in with a facility-coords lookup / the C2-collected case GPS. }
  numeric ok;
  Map ea_map;
  ok = ea_map.setBaseMap("survey-basemap.mbtiles");
  if ok = 0 then
    errmsg("Offline base map not found on this device. Remove + re-add LoginApp from the server to install it.");
  else
    ea_map.addMarker(14.3400, 121.0800);   { test facility area - Binan, Laguna }
    ea_map.addMarker(14.2840, 121.0680);   { EA reference point }
    ea_map.zoomTo(14.3100, 121.0700, 12);  { CENTER the view on the EA / offline-tile coverage -
                                             without this the map opens at the device GPS / world view
                                             (outside the mbtiles bbox) and renders blank offline. }
    ea_map.show();
  endif;
end;

PROC MENUAPP_LEVEL
preproc
  { Read the role handed over by LoginApp (loadsetting persists across apps). }
  m_role = loadsetting("hub_role");

PROC MENU_SESSION
preproc
  { Single-case menu: auto-key the session, surface the role read-only, skip entry.
    ROLE_SHOWN is set + protected here (a visited, non-protected field's preproc),
    NOT in its own preproc (CSEntry skips a protected field's preproc — #617). }
  MENU_SESSION = 1;
  ROLE_SHOWN = m_role;
  protect(ROLE_SHOWN, true);
  noinput;

PROC MENU_CHOICE
onfocus
  { Role-filtered menu: show the logged-in role's value set (supervisor=VS1, enumerator=VS2).
    onfocus (not preproc) so reverse navigation re-applies the filter. }
  if strip(m_role) = "supervisor" then
    setvalueset(MENU_CHOICE, MENU_CHOICE_VS1);
  else
    setvalueset(MENU_CHOICE, MENU_CHOICE_VS2);
  endif;

postproc
  if strip(m_role) = "supervisor" then
    { Supervisor menu (codes 01-08) }
    if MENU_CHOICE = 1 then
      errmsg("Assign Enumeration Area - pending Phase-2B: needs the C2 Bluetooth spike (push the EA assignment to the enumerator).");
      reenter;
    elseif MENU_CHOICE = 2 then
      errmsg("LISTING DATA report - on-device entry point is live. Assigned-vs-collected coverage populates after assignment distribution + Bluetooth collection (Phase-2B). A rich HTML report is a flagged follow-up.");
      reenter;
    elseif MENU_CHOICE = 3 then
      errmsg("SURVEY INTERVIEW report - on-device entry point is live. Captured-vs-target coverage populates after Bluetooth collection (Phase-2B). A rich HTML report is a flagged follow-up.");
      reenter;
    elseif MENU_CHOICE = 4 then
      show_ea_map();
      reenter;
    elseif MENU_CHOICE = 5 then
      launch_instrument("../FacilityHeadSurvey/FacilityHeadSurvey.pff");
    elseif MENU_CHOICE = 6 then
      launch_instrument("../PatientSurvey/PatientSurvey.pff");
    elseif MENU_CHOICE = 7 then
      launch_instrument("../HouseholdSurvey/HouseholdSurvey.pff");
    elseif MENU_CHOICE = 8 then
      execpff("LoginApp.pff", stop);
    endif;
  elseif strip(m_role) = "enumerator" then
    { Enumerator menu (codes 11-18) }
    if MENU_CHOICE = 11 then
      errmsg("Listing Exercise - pending Phase-2B: needs the listing app + C2 send-to-supervisor.");
      reenter;
    elseif MENU_CHOICE = 12 then
      errmsg("Receive Assigned Data (Patient) - pending Phase-2B: needs the C2 Bluetooth spike (assignment distribution).");
      reenter;
    elseif MENU_CHOICE = 13 then
      launch_instrument("../FacilityHeadSurvey/FacilityHeadSurvey.pff");
    elseif MENU_CHOICE = 14 then
      launch_instrument("../PatientSurvey/PatientSurvey.pff");
    elseif MENU_CHOICE = 15 then
      launch_instrument("../HouseholdSurvey/HouseholdSurvey.pff");
    elseif MENU_CHOICE = 16 then
      show_ea_map();
      reenter;
    elseif MENU_CHOICE = 17 then
      errmsg("MY INTERVIEWS report - on-device entry point is live. Your captured-vs-target coverage populates as you complete interviews (Phase-2B reporting). A rich HTML report is a flagged follow-up.");
      reenter;
    elseif MENU_CHOICE = 18 then
      execpff("LoginApp.pff", stop);
    endif;
  else
    errmsg("No role found from login. Close and sign in again via LoginApp.");
  endif;
"""


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------
def _write(path, text, *, bom=False):
    Path(path).write_text(("﻿" if bom else "") + text, encoding="utf-8")
    print(f"Wrote {path}")


def build_login_app():
    d = build_login_dict()
    write_dcf(d, HERE / "LoginApp.dcf")
    _write(HERE / "LoginApp.fmf",
           build_fmf(d, "LOGINAPP_FF", r".\LoginApp.dcf", "LoginApp",
                     [("Login", "LOGIN_REC")]))
    _write(HERE / "LoginApp.ent.qsf", build_qsf(d, "LOGINAPP_DICT"), bom=True)
    _write(HERE / "LoginApp.ent.apc", LOGIN_APC)
    _write(HERE / "LoginApp.ent.mgf", _mgf("LoginApp"))
    ent = build_ent("LOGINAPP", "LoginApp", "LoginApp.dcf", "LoginApp.fmf",
                    "LoginApp.ent.qsf", "LoginApp.ent.apc", "LoginApp.ent.mgf",
                    externals=["UserRoster.dcf"])
    _write(HERE / "LoginApp.ent", json.dumps(ent, indent=2))
    _write(HERE / "LoginApp.pff",
           _pff("LoginApp.ent", "LoginApp.csdb",
                externals={"USER_ROSTER_DICT": "UserRoster.dat"}))


def build_menu_app():
    d = build_menu_dict()
    write_dcf(d, HERE / "MenuApp.dcf")
    _write(HERE / "MenuApp.fmf",
           build_fmf(d, "MENUAPP_FF", r".\MenuApp.dcf", "MenuApp",
                     [("Menu", "MENU_REC")]))
    _write(HERE / "MenuApp.ent.qsf", build_qsf(d, "MENUAPP_DICT"), bom=True)
    _write(HERE / "MenuApp.ent.apc", MENU_APC)
    _write(HERE / "MenuApp.ent.mgf", _mgf("MenuApp"))
    ent = build_ent("MENUAPP", "MenuApp", "MenuApp.dcf", "MenuApp.fmf",
                    "MenuApp.ent.qsf", "MenuApp.ent.apc", "MenuApp.ent.mgf")
    _write(HERE / "MenuApp.ent", json.dumps(ent, indent=2))
    _write(HERE / "MenuApp.pff", _pff("MenuApp.ent", "MenuApp.csdb"))


def build_roster():
    d = build_user_roster_dict()
    _truncate_long_labels(d)
    _write(HERE / "UserRoster.dcf", json.dumps(d, indent=2))
    write_user_roster_data(HERE / "UserRoster.dat")
    print(f"  Roster rows: {len(ROSTER_ROWS)}")


def build_assignment():
    d = build_assignment_dict()
    _truncate_long_labels(d)
    _write(HERE / "Assignment.dcf", json.dumps(d, indent=2))
    write_assignment_data(HERE / "Assignment.dat")
    print(f"  Assignment rows: {len(ASSIGNMENT_ROWS)}")


def main():
    build_roster()
    build_assignment()
    build_login_app()
    build_menu_app()
    print("\nHub apps generated in", HERE)


if __name__ == "__main__":
    main()
