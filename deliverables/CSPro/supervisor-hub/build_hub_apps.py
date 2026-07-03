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
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Hub build version (versioning extended to the hub 2026-07-02; SemVer like the instruments).
# ../versions.json is the single source of truth — bump via `py ../automation/stamp_version.py
# bump HUB`, which re-runs this build. The version lands on the generated .pff Descriptions
# (CSEntry app list; these pffs are GENERATOR-owned, unlike the instruments') and in the
# role-menu JSON, which menu.html renders as a footer line.
_BUILD = json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["HUB"]
HUB_VERSION = f"v{_BUILD['version']} ({_BUILD['date']})"
sys.path.insert(0, str(HERE.parent))   # deliverables/CSPro  (for cspro_helpers)
from cspro_helpers import (             # noqa: E402
    alpha, select_one, record, build_dictionary, write_dcf, _truncate_long_labels,
)

# ----------------------------------------------------------------------------
# Data sources (externalized 2026-07-03 — the data/ layer; see ../data/*/README).
# The hub build stays the SINGLE WRITER of the deployed artifacts; only the row
# data moved out of this file.
# ----------------------------------------------------------------------------
DATA_DIR = HERE.parent / "data"


def _load_csv_rows(csv_path, n_cols, what):
    """Load an n-column CSV (header row required) into a list of str tuples,
    preserving file order. Hard-stop with a helpful message if missing."""
    import csv as _csv
    if not csv_path.exists():
        sys.exit(
            f"MISSING {what} source: {csv_path}\n"
            f"  (gitignored data source — copy the *.template.csv alongside it to "
            f"{csv_path.name} and fill in real rows)")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = [tuple((v or "").strip() for v in r) for r in _csv.reader(fh)]
    header, rows = rows[0], rows[1:]
    if len(header) != n_cols:
        sys.exit(f"{csv_path}: expected {n_cols} columns, found {len(header)} ({header})")
    bad = [r for r in rows if len(r) != n_cols]
    if bad:
        sys.exit(f"{csv_path}: rows with wrong column count: {bad[:3]}")
    return rows


# Login roster — (username, password, role, operator_id, cluster, supervisor_id).
# C5 — supervisor_id models the enumerator->supervisor hierarchy ("who reports to me");
# Khurshid's UsernamePassword.dcf carries this. Enumerators point at their supervisor; the
# supervisor's own supervisor_id is blank (top of this chain). Encryption + device-bound
# login stay ASPSI-gated (real names/creds) — not built here.
# Hub login is a LOCAL plaintext gate (UserRoster.dat ships in the app) — typeable test
# passwords in the source CSV; the REAL security is each tester's CSWeb account (strong
# pw), see config/UAT-R6-tester-credentials.md + config/uat-r6-csweb-users.csv.
# Source of truth: ../data/roster/roster-source.csv (GITIGNORED — carries credentials;
# currently the UAT Round 6 tester roster, 2 teams covering F1/F3/F4).
ROSTER_ROWS = _load_csv_rows(DATA_DIR / "roster" / "roster-source.csv", 6, "roster")

# C3a — GROUPED field-ops menus, Khurshid 101-apps "accept()" interface (replaced the flat
# value-set radio field 2026-06-27). Each role = [(SECTION_HEADER, [(item_label, action_key), ...])].
# The CSPro accept() option list AND the index routing are GENERATED from this by
# _accept_menu_block() — headers + indented "+" items flatten to 1-based accept positions with no
# drift: item positions route to MENU_ACTIONS[key]; a header/blank/cancel pick hits the guard.
# Use plain "-" (not em-dash) in labels: these become CSPro string literals in the .apc logic.
# LISTING still descoped (Carl 2026-06-25): PatientListing never built (§3a unauthored, ASPSI's call).
SUPERVISOR_MENU_GROUPED = [
    ("ASSIGNMENTS", [
        ("Assign Enumeration Area", "assign"),
    ]),
    ("COLLECT & RELAY", [
        ("Collect Interviews from Enumerators", "collect"),
        ("Relay Collected Interviews to CSWeb", "relay"),
    ]),
    ("REVIEW & REPORTS", [
        ("Survey Interview - view report", "report_sup"),
        ("View EA on Map", "map"),
        ("Open F1 - Facility Head (review)", "open_f1"),
        ("Open F3 - Patient (review)", "open_f3"),
        ("Open F4 - Household (review)", "open_f4"),
    ]),
    ("SESSION", [
        ("Log out", "logout"),
    ]),
]
ENUMERATOR_MENU_GROUPED = [
    ("ASSIGNMENT", [
        ("Receive Assigned Data", "receive"),
    ]),
    ("INTERVIEWS", [
        ("Conduct F1 - Facility Head Interview", "open_f1"),
        ("Conduct F3 - Patient Interview", "open_f3"),
        ("Conduct F4 - Household Interview", "open_f4"),
        ("Send My Interviews to Supervisor", "send"),
    ]),
    ("REPORTS", [
        ("View EA on Map", "map"),
        ("View my report", "report_enum"),
    ]),
    ("SESSION", [
        ("Log out", "logout"),
    ]),
]
# action_key -> the CSPro statement(s) run for that menu item inside MENU_PICK preproc.
# "stay" actions end with `move to MENU_SESSION` (re-runs the id -> flows back to MENU_PICK ->
# re-shows the menu; reenter can't be used in a preproc and forces field entry). "leave" actions
# launch an instrument (Pff OnExit chains back here) or execpff back to LoginApp (control transfers).
MENU_ACTIONS = {
    "assign":  "assign_ea();\n      move to MENU_SESSION;",
    "collect": "collect_interviews();\n      move to MENU_SESSION;",
    "relay":   "relay_to_csweb();\n      move to MENU_SESSION;",
    "receive": "receive_assignment();\n      move to MENU_SESSION;",
    "send":    "send_to_supervisor();\n      move to MENU_SESSION;",
    "map":     "show_ea_map();\n      move to MENU_SESSION;",
    "report_sup":  ('show_coverage_report("SURVEY COVERAGE - interviews collected at this hub");'
                    '\n      move to MENU_SESSION;'),
    "report_enum": ('show_coverage_report("MY INTERVIEW COVERAGE");'
                    '\n      move to MENU_SESSION;'),
    "open_f1": 'launch_instrument("../FacilityHeadSurvey/FacilityHeadSurvey.pff");',
    "open_f3": 'launch_instrument("../PatientSurvey/PatientSurvey.pff");',
    "open_f4": 'launch_instrument("../HouseholdSurvey/HouseholdSurvey.pff");',
    "logout":  'execpff("LoginApp.pff", stop);',
}

# B3 — EA / cluster assignment lookup (one assignment per EA-facility). Distributed
# supervisor->enumerator in N1 (B4, C2-gated); here it is the structural dict + seed.
# Columns: (ea_facility_code(9), enumerator_id, instrument, target_count, ea_name, cluster).
# Source of truth: ../data/assignments/assignments-source.csv (tracked — R6 fixtures today;
# ASPSI's real EA plan replaces the rows there, this build stays the writer).
ASSIGNMENT_ROWS = _load_csv_rows(DATA_DIR / "assignments" / "assignments-source.csv", 6, "assignments")

# B6/B7 — the F1/F3/F4 instrument dicts are declared EXTERNAL in MenuApp so the Bluetooth case
# exchange (syncdata) can move PRIMARY case data device-to-device (the C2-DEVICE-PROVEN path).
# syncdata requires the synced dict to be external OR the running app's main dict; MenuApp's main
# dict is MENUAPP_DICT, so each instrument dict rides as an EXTERNAL whose DATA file is the
# SEPARATELY-INSTALLED instrument's own .csdb (../<App>/<App>.csdb). The dcf (STRUCTURE) is snapshot
# into this folder at build time (copy_instrument_dcfs) so it cannot silently drift from THIS build —
# BUT it is a build-time snapshot: if an instrument is redeployed during UAT, REBUILD + REDEPLOY the
# hub so the shipped dcf still matches the device's .csdb schema (a syncdata schema mismatch is the
# main risk of this instrument coupling). Tuple: (instrument_label, dcf_filename, dict_name, app_folder);
# csdb on device = <app_folder>/<app_folder>.csdb; dcf source = ../<instrument_label>/<dcf_filename>.
INSTRUMENTS = [
    ("F1", "FacilityHeadSurvey.dcf", "FACILITYHEADSURVEY_DICT", "FacilityHeadSurvey"),
    ("F3", "PatientSurvey.dcf",      "PATIENTSURVEY_DICT",      "PatientSurvey"),
    ("F4", "HouseholdSurvey.dcf",    "HOUSEHOLDSURVEY_DICT",    "HouseholdSurvey"),
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
# Action-Invoker access token: registered in every hub .ent (logicSettings.actionInvoker.accessTokens,
# per zAppO/LogicSettings.cpp + csprousers.org/help/CSPro/logic_settings.html) and presented by
# menu.html/report.html via `new CSProActionInvoker(<token>)`. CSEntry 8.1+ REMOVED the deprecated
# CSPro.* web-view interface (blank-menu bug, Samsung A23 8.1.1-20260622, 2026-07-02), so on 8.1 the
# dialogs authenticate to CS.UI with this token instead - a caller with a REGISTERED token gets NO
# "Allow Access?" prompt while accessFromExternalCaller stays the secure promptIfNoValidAccessToken
# (consent still gates any caller WITHOUT the token). 8.0.1 devices keep using CSPro.* untouched.
HUB_ACCESS_TOKEN = "2c9e4f71-a6d3-4b8f-9e02-d5c1b7a83e46"


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
                              "accessTokens": [HUB_ACCESS_TOKEN],
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


def _pff(application, input_data, externals=None, html_dialogs=None, description=None):
    # C2 (|type=None): Login/Menu carry NO case data — open straight to the form/menu (no "0 Cases"
    # list, no "+" tap). A "|type=None" value is written verbatim; a real filename gets the ".\" prefix.
    # CSEntry 8.0.1 bypassed the case list implicitly for a type=None input, but 8.1 shows an empty
    # "0 Cases" list first — [DataEntryInit] StartMode=Add + Lock=CaseListing makes the bypass explicit
    # ("On mobile CSEntry, the Case Listing screen will be bypassed", run_production_data_entry help),
    # so both CSEntry generations behave the same.
    input_line = input_data if input_data.startswith("|") else f".\\{input_data}"
    lines = ["[Run Information]", "Version=CSPro 8.0", "AppType=Entry"]
    if description:
        # CSEntry's app-list display name (PFF.cpp APPDESCRIPTION) — carries the hub build version
        lines.append(f"Description={description}")
    lines.append("")
    if input_data.startswith("|"):
        lines += ["[DataEntryInit]", "StartMode=Add", "Lock=CaseListing", ""]
    lines += (["[Files]", f"Application=.\\{application}", f"InputData={input_line}"]
              + ([f"HtmlDialogs={html_dialogs}"] if html_dialogs else []) + [""])
    if externals:
        lines.append("[ExternalFiles]")
        for dict_name, dat in externals.items():
            # value is the verbatim relative path (so instrument .csdb externals can use ..\\<App>\\…)
            lines.append(f"{dict_name}={dat}")
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
                    {"name": "UR_SUPERVISOR_ID", "labels": [{"text": "Supervisor ID"}], "contentType": "alpha", "length": 20},
                ],
            }],
        }],
    }


def write_user_roster_data(path):
    """Fixed-width: UR_USERNAME(20) UR_PASSWORD(20) UR_ROLE(20) UR_OPERATOR_ID(20) UR_CLUSTER(10)
    UR_SUPERVISOR_ID(20)."""
    widths = [20, 20, 20, 20, 10, 20]
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


def _menu_pick_item():
    """C3a — MENU_PICK is just the host field for the accept() menu (shown in its preproc); it
    stores nothing (noinput). No value set — the grouped option list is built by accept() in logic."""
    return {
        "name": "MENU_PICK", "labels": [{"text": "Menu"}],
        "contentType": "numeric", "length": 1, "zeroFill": True,
    }


def build_menu_dict():
    """Input dict: trivial numeric session key + the MENU_PICK host field for the accept() menu.
    (ROLE_SHOWN dropped — the role is shown in the accept() title; no value-set field — the grouped
    menu is built in logic. C3a.)"""
    id_items = [{
        "name": "MENU_SESSION", "labels": [{"text": "Session"}],
        "contentType": "numeric", "start": 2, "length": 1, "zeroFill": True,
    }]
    rec = record("MENU_REC", "Menu record", "M", [
        _menu_pick_item(),
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
        # readOptimization MUST be False: B4 overwrites MyAssignment.dat MID-SESSION (the syncfile
        # GET in receive_assignment), then setfile+forcase to read it. With read-optimization ON,
        # CSPro caches the dict's index at app start (when MyAssignment.dat is empty), so the
        # mid-session forcase sees STALE empty data and the "Assignment received…" display never
        # fires (device-confirmed 2026-06-27: the file transferred but the in-session display was
        # blank). Off = forcase reads fresh from disk each time. The file is tiny, so no perf cost.
        "readOptimization": False,
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


_ASSIGNMENT_WIDTHS = [9, 20, 4, 4, 50, 10]


def _assignment_line(row):
    """Fixed-width: AS_FACILITY_CODE(9) AS_ENUMERATOR_ID(20) AS_INSTRUMENT(4)
    AS_TARGET_COUNT(4) AS_EA_NAME(50) AS_CLUSTER(10)."""
    return "".join(v[:w].ljust(w) for v, w in zip(row, _ASSIGNMENT_WIDTHS)) + "\n"


def write_assignment_data(path):
    """Master assignment file (all EAs) — the supervisor's reference copy."""
    with Path(path).open("w", encoding="utf-8", newline="\n") as fh:
        for row in ASSIGNMENT_ROWS:
            fh.write(_assignment_line(row))


def write_per_enumerator_assignments(folder):
    """B4 (N1) — one AS_<operator_id>.dat per enumerator: the file each enumerator PULLS
    from the supervisor over Bluetooth (syncfile GET) in "Receive Assigned Data". The
    supervisor ships+serves them from its syncserver(Bluetooth) root (the app folder); the
    enumerator GETs theirs by operator_id, so no cross-enumerator scan or known-EA-key is
    needed. Also writes an empty MyAssignment.dat — the local file ASSIGNMENT_DICT is mapped
    to (MenuApp.pff), which the received file overwrites on-device. Ships empty so the
    external dict opens cleanly before the first receive."""
    folder = Path(folder)
    by_op = {}
    for row in ASSIGNMENT_ROWS:
        by_op.setdefault(row[1], []).append(row)
    for opid, rows in by_op.items():
        with (folder / f"AS_{opid}.dat").open("w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(_assignment_line(row))
    (folder / "MyAssignment.dat").write_text("", encoding="utf-8")
    print(f"  Per-enumerator assignment files: {len(by_op)} (+ empty MyAssignment.dat)")


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
  C3a 2026-06-27: the value-set radio field is REPLACED by Khurshid's grouped accept() menu
  (section headers + indented + items, generated from *_MENU_GROUPED; routed by accept position).
  C2 2026-06-27: Login + Menu use InputData=|type=None (no case store, no "tap +").
  BUILT actions: open/conduct an instrument (PFF chain-launch, OnExit back to menu),
  log out (execpff back to LoginApp), the per-role on-device report ENTRY POINT,
  View EA on Map (C7=PASS, offline MBTiles); B4 (N1), 2026-06-25 — Assign EA /
  Receive Assigned Data over Bluetooth (syncserver/syncconnect+syncfile); and B6/B7,
  2026-06-27 — the survey CASE EXCHANGE over Bluetooth: enumerator "Send My Interviews"
  (syncconnect+syncdata PUT of the assigned instrument, declared EXTERNAL), supervisor
  "Collect Interviews" (syncserver host loop), and "Relay to CSWeb" (syncconnect(CSWeb)+
  syncdata(PUT) of the collected F1/F3/F4 dicts under supervisor-qa — Khurshid 101-apps
  pattern, grounded in csprousers.org; relay logic wired 2026-06-27). Bluetooth case data
  moves on the C2-DEVICE-PROVEN syncdata path (B6/B7 collect/send DEVICE-CONFIRMED 2026-06-27);
  the CSWeb relay is build-valid, its on-our-server credential prompt device-verify pending.
  DESCOPED FROM v1 (Carl, 2026-06-25): the LISTING leg — the PatientListing app it would
  chain-launch was never built (§3a unauthored, ASPSI's call); its codes now carry collect/send.
  REPORT NOTE (B2/N4/C4/C4b): the on-device report (show_coverage_report) computes REAL
  per-instrument coverage by iterating the F1/F3/F4 external dicts with forcase + the received
  AS_TARGET_COUNT, and renders it as an HTML TABLE via the CSPro 8 htmldialog() function against a
  self-contained report.html (C4b, 2026-06-30). Falls back to the proven one-line errmsg if
  htmldialog returns != "ok". Compiles clean; the OFFLINE on-CSEntry render is the device-verify gate.
  ============================================================================ }

PROC GLOBAL
string m_role;
string m_op;
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

function receive_assignment()
  { B4 (N1) — pull THIS enumerator's EA assignment from the supervisor over Bluetooth.
    Transport = the C2-DEVICE-PROVEN syncconnect(Bluetooth) session, but with syncfile (the
    assignment is a fixed-width TEXT lookup, NOT a CSPro DB, so syncdata does not apply -
    syncfile moves any file type, GET/PUT, after syncconnect). The supervisor's "Assign EA"
    runs syncserver(Bluetooth) and serves AS_<operator_id>.dat from its app folder; we GET
    ours into MyAssignment.dat (the file ASSIGNMENT_DICT is mapped to in MenuApp.pff), reload
    it with setfile, and show the assigned EA + target.
    DEVICE-UNCONFIRMED bits (verify on the 2-tablet rig): syncfile over Bluetooth (C2 proved
    syncdata; syncfile rides the same session per docs but is not yet device-run here), the
    syncserver default file root, and the setfile reload of a just-overwritten external file. }
  string opid;
  string fromfile;
  opid = loadsetting("hub_operator_id");
  fromfile = "AS_" + strip(opid) + ".dat";
  if syncconnect(Bluetooth) then
    if syncfile(GET, fromfile, "MyAssignment.dat") then
      syncdisconnect();
      setfile(ASSIGNMENT_DICT, "MyAssignment.dat");   { reload the freshly-received file }
      forcase ASSIGNMENT_DICT do
        errmsg("Assignment received - EA " + strip(AS_FACILITY_CODE) + " (" + strip(AS_EA_NAME)
               + "): instrument " + strip(AS_INSTRUMENT) + ", target " + strip(AS_TARGET_COUNT)
               + ". Open it from the menu.");
      enddo;
    else
      syncdisconnect();
      errmsg("Connected to the supervisor, but no assignment file (" + fromfile
               + ") was published for you. Ask the supervisor to run 'Assign Enumeration Area' first.");
    endif;
  else
    errmsg("Couldn't connect over Bluetooth. Check: (1) Bluetooth is ON on BOTH tablets, and "
             + "(2) the supervisor has started 'Assign Enumeration Area' - then retry.");
  endif;
end;

function collect_interviews()
  { B7 (collect) - become a passive Bluetooth host so each enumerator can PUT their interviews
    into this hub's matching instrument .csdb (syncdata). The SAME syncserver(Bluetooth) call as
    'Assign EA': syncserver is passive - it serves files AND receives case data, responding to
    whatever the connected client requests. Handles ONE enumerator per call; re-select for the
    next (one-host-from-many = the C2-proven loop). Collected cases accumulate by the 12-digit
    key into this hub's own ../<App>/<App>.csdb (the F1/F3/F4 dicts declared EXTERNAL here), ready
    to relay to CSWeb. DEVICE-UNCONFIRMED: receiving syncdata into a sibling app's live .csdb. }
  errmsg("COLLECT: starting the Bluetooth server to receive interviews. Make sure Bluetooth is ON "
           + "on both tablets. Keep this screen open; each enumerator now runs 'Send My Interviews to "
           + "Supervisor'. Receives one enumerator per connection - re-select this item for the next enumerator.");
  syncserver(Bluetooth);
  errmsg("COLLECT: an enumerator connected and synced their interviews to this hub.");
end;

function send_to_supervisor()
  { B6 - push THIS enumerator's captured cases to the supervisor over Bluetooth. Transport = the
    C2-DEVICE-PROVEN syncconnect(Bluetooth)+syncdata(PUT)+syncdisconnect (the exact SyncSpike shape:
    syncconnect tested in an if, syncdata as a statement).
    #829 (2026-07-03): sends ALL THREE instrument dicts unconditionally. The old send routed by
    the RECEIVED assignment (MyAssignment.dat) and silently defaulted to F3 when none was loaded -
    on the R6 rig se-001 conducted an F1 interview, the hub PUT the empty F3 dict, reported
    "Sent your F3 interviews", and the F1 case never left the tablet. Sending all three closes
    both gaps (wrong default + interviews conducted off-assignment): PUT of an empty dict syncs
    nothing, PUT is non-destructive - the enumerator keeps their copies (proven in C2). The cases
    live in each instrument's OWN separately-installed .csdb (../<App>/<App>.csdb), declared
    EXTERNAL here. Per-dict forcase counts (the report-proven idiom) make the confirmation state
    exactly what was sent. }
  numeric sn1; numeric sn3; numeric sn4;
  sn1 = 0; sn3 = 0; sn4 = 0;
  forcase FACILITYHEADSURVEY_DICT do sn1 = sn1 + 1; enddo;
  forcase PATIENTSURVEY_DICT do sn3 = sn3 + 1; enddo;
  forcase HOUSEHOLDSURVEY_DICT do sn4 = sn4 + 1; enddo;
  if syncconnect(Bluetooth) then
    syncdata(PUT, FACILITYHEADSURVEY_DICT);
    syncdata(PUT, PATIENTSURVEY_DICT);
    syncdata(PUT, HOUSEHOLDSURVEY_DICT);
    syncdisconnect();
    errmsg(maketext("Sent your interviews to the supervisor over Bluetooth - F1: %d, F3: %d, "
             + "F4: %d. Your own copies are unchanged (non-destructive).", sn1, sn3, sn4));
  else
    errmsg("Couldn't connect over Bluetooth. Check: (1) Bluetooth is ON on BOTH tablets, and "
             + "(2) the supervisor has started 'Collect Interviews from Enumerators' - then retry.");
  endif;
end;

function relay_to_csweb()
  { B7 (relay) - push the hub's COLLECTED F1/F3/F4 cases to CSWeb under the supervisor-qa account.
    Grounded in the official CSPro API (syncconnect(CSWeb, url [, user, pass]) + syncdata(PUT, dict),
    csprousers.org) + Khurshid's senddataontheserver pattern. Credentials are OMITTED, so CSEntry
    prompts the supervisor ONCE for the supervisor-qa login then caches it (subsequent relays one-tap).
    syncdata(PUT) requires the dict to be uploaded to CSWeb already - F1/F3/F4 are (they are deployed
    there). The cases sit in this hub's OWN ../<App>/<App>.csdb (the same EXTERNAL dicts the Bluetooth
    collect writes into); CSWeb upserts by the 12-digit key, so hub-relayed + direct-synced copies never
    conflict. Dual-path: direct enumerator->CSWeb stays the default; this is the no-signal safety net.
    Shape = syncconnect tested in an if, syncdata as statements (the C2/Khurshid-proven form).
    DEVICE-UNCONFIRMED: syncconnect(CSWeb)-from-logic + the supervisor-qa credential prompt on OUR server. }
  string csweb_url;
  csweb_url = "https://csweb.asiansocial.org/csweb/api";
  if syncconnect(CSWeb, csweb_url) then
    syncdata(PUT, FACILITYHEADSURVEY_DICT);
    syncdata(PUT, PATIENTSURVEY_DICT);
    syncdata(PUT, HOUSEHOLDSURVEY_DICT);
    syncdisconnect();
    errmsg("Relayed the hub's collected F1/F3/F4 interviews to CSWeb (supervisor-qa). Cases upsert "
             + "by the 12-digit key, so direct-synced and hub-relayed copies never conflict.");
  else
    errmsg("CSWeb connect failed - no internet, or sign-in was cancelled. This hub relay is the "
             + "no-signal safety net; retry on signal. Sign in as the supervisor-qa account when prompted.");
  endif;
end;

function assign_ea()
  { B4 (N1) - publish EA assignments: become a passive Bluetooth host so each enumerator can pull
    their AS_<id>.dat (syncfile GET). syncserver handles ONE client per call; re-select for the next
    enumerator (one-host-from-many). The AS_*.dat files ship in the app folder = the syncserver root. }
  errmsg("ASSIGN EA: starting the Bluetooth server to publish assignments. Make sure Bluetooth is "
           + "ON on both tablets. Keep this screen open; the enumerator now runs 'Receive Assigned "
           + "Data'. Serves one enumerator per connection - re-select this item for the next enumerator.");
  syncserver(Bluetooth);
  errmsg("ASSIGN EA: an enumerator connected and pulled their assignment.");
end;

function show_coverage_report(string scope)
  { C4b - on-device coverage report as an HTML TABLE (replaced the one-line errmsg 2026-06-30). Counts
    the F1/F3/F4 cases stored on THIS device (each dict declared EXTERNAL here -> ../<App>/<App>.csdb)
    with forcase - the proven idiom the Bluetooth functions use. Reads the received assignment
    (MyAssignment.dat) for captured-vs-target, then renders it with the CSPro 8 htmldialog() function
    against a SELF-CONTAINED report.html (inline CSS + vanilla JS, no jQuery/Bootstrap/Mustache -> no
    dependency to bundle, renders offline). Role meaning: supervisor = cases collected into this hub;
    enumerator = own captured interviews. FALLS BACK to the proven one-line errmsg if htmldialog returns
    anything but "ok" (older CSEntry / report.html missing). htmldialog grounded at
    csprousers.org/help/CSPro/htmldialog_function.html: htmldialog(file, inputData:=, displayOptions:=)
    returns the string the HTML passes to UI.close(). NOTE: htmldialog compiles clean, but the OFFLINE
    on-CSEntry render is the device-verify gate (the C8 spike). }
  numeric n1; numeric n3; numeric n4;
  string aInstr; string aTgt; string aEA; string j; string dopt; string res;
  n1 = 0; n3 = 0; n4 = 0;
  forcase FACILITYHEADSURVEY_DICT do n1 = n1 + 1; enddo;
  forcase PATIENTSURVEY_DICT do n3 = n3 + 1; enddo;
  forcase HOUSEHOLDSURVEY_DICT do n4 = n4 + 1; enddo;
  aInstr = ""; aTgt = ""; aEA = "";
  setfile(ASSIGNMENT_DICT, "MyAssignment.dat");
  forcase ASSIGNMENT_DICT do
    aInstr = strip(AS_INSTRUMENT); aTgt = strip(AS_TARGET_COUNT); aEA = strip(AS_EA_NAME);
  enddo;
  { JSON for report.html - single-quoted format so the inner double-quotes are literal (proven in the
    htmldialog doc example). EA names in this round have no quotes, so no escaping needed. }
  j = maketext('{"scope":"%s","f1":%d,"f3":%d,"f4":%d,"instr":"%s","target":"%s","ea":"%s"}',
               scope, n1, n3, n4, aInstr, aTgt, aEA);
  dopt = '{"width":380,"height":340,"resizable":false,"keyboard":0}';
  { htmldialog renders report.html (device-confirmed on CSEntry itel_P10001L 2026-07-01 with
    the real forcase counts + assignment). NO errmsg fallback: this CSEntry's htmldialog return
    value is not a stable "ok" sentinel (it uses the deprecated CSPro.returnData path, which does
    not round-trip a plain "ok"), so an `if res <> "ok"` guard fires a SECOND dialog every time.
    The dialog is reliable here; keep the single clean dialog. res is captured but unused. }
  res = htmldialog("report.html", inputData := j, displayOptions := dopt);
end;

PROC MENUAPP_LEVEL
preproc
  { Read the role + operator id handed over by LoginApp (loadsetting persists across apps).
    m_op titles the accept() menu; m_role picks the role's option list. Auto-key + PROTECT the
    session id HERE (level preproc): the menu's `move to MENU_SESSION` loop must land on a PROTECTED
    field so it auto-skips forward to MENU_PICK. A noinput field is still ENTERED on move-to
    (device-confirmed 2026-06-27 — landed on the id in entry mode); protect is the fix. Set it in the
    level preproc because #617: a protected field's OWN preproc is skipped, so MENU_SESSION has none. }
  m_role = loadsetting("hub_role");
  m_op = loadsetting("hub_operator_id");
  MENU_SESSION = 1;
  protect(MENU_SESSION, true);

PROC MENU_PICK
preproc
  { HTMLDIALOG role menu - prompt-free + secure on BOTH CSEntry generations: 8.0.1 renders menu.html
    through the deprecated CSPro.* interface (no Action-Invoker consent gate), while 8.1+ (CSPro.*
    REMOVED - blank-menu bug, Samsung A23 2026-07-02) authenticates to CS.UI with the hub access
    token registered in this .ent (accessTokens) - still no per-show prompt, and
    accessFromExternalCaller stays the secure promptIfNoValidAccessToken. Menu content = a static JSON per role (from *_MENU_GROUPED via
    _menu_json_expr); the tapped item returns its action wrapped as "<<action>>", and pos() routing
    survives whatever encoding the htmldialog return comes back in. Loops via `move to MENU_SESSION`;
    "leave" actions launch an instrument (Pff OnExit chains back) or execpff to LoginApp. }
  string res;
  string menuJson;
  string dopt;
  dopt = '{"width":380,"height":600,"resizable":false,"keyboard":0}';
  if strip(m_role) = "supervisor" then
    menuJson = __SUPERVISOR_MENU_JSON__;
    res = htmldialog("menu.html", inputData := menuJson, displayOptions := dopt);
  elseif strip(m_role) = "enumerator" then
    menuJson = __ENUMERATOR_MENU_JSON__;
    res = htmldialog("menu.html", inputData := menuJson, displayOptions := dopt);
  else
    errmsg("No role found from login. Close and sign in again via LoginApp.");
    execpff("LoginApp.pff", stop);
  endif;
__MENU_ROUTING__
  noinput;
"""


def _menu_json_expr(role_label, grouped):
    """CSPro expression building the htmldialog inputData JSON for one role's menu, injecting the live
    operator id. Chunked into <=180-char concat() args so no single string literal is over-long;
    labels/headers carry no single-quotes, so the single-quoted CSPro literals are safe."""
    groups = [{"header": h, "items": [{"label": l, "action": a} for (l, a) in items]}
              for (h, items) in grouped]
    gjson = json.dumps(groups, separators=(",", ":"))
    # "ver" -> menu.html's footer line; the hub build version rides every role menu
    tail = ' - ' + role_label + '","ver":"Hub ' + HUB_VERSION + '","groups":' + gjson + '}'
    chunks = [tail[i:i + 180] for i in range(0, len(tail), 180)]
    q = chr(39)
    parts = [q + '{"title":"' + q, 'strip(m_op)'] + [q + c + q for c in chunks]
    return 'concat(' + ', '.join(parts) + ')'


def _routing_block():
    """Shared pos()-routing over ALL MENU_ACTIONS keys. menu.html wraps the return "<<key>>" so pos()
    finds it whatever the htmldialog return encoding; keys are distinct (none a substring of another).
    The else re-shows the menu silently (cancel/back or an unexpected return just loops)."""
    lines = []
    for i, (key, body) in enumerate(MENU_ACTIONS.items()):
        kw = "if" if i == 0 else "elseif"
        lines.append('  %s pos("<<%s>>", res) > 0 then' % (kw, key))
        for stmt in body.split("\n"):
            s = stmt.strip()
            lines.append(("    " + s) if s else "")
    lines += ['  else',
              '    move to MENU_SESSION;',
              '  endif;']
    return "\n".join(lines)


def build_menu_apc():
    """Fill MENU_APC with the per-role htmldialog menu JSON + the shared pos() routing."""
    return (MENU_APC
            .replace("__SUPERVISOR_MENU_JSON__", _menu_json_expr("Supervisor", SUPERVISOR_MENU_GROUPED))
            .replace("__ENUMERATOR_MENU_JSON__", _menu_json_expr("Enumerator", ENUMERATOR_MENU_GROUPED))
            .replace("__MENU_ROUTING__", _routing_block()))


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
           _pff("LoginApp.ent", "|type=None",   # C2 — no case store; opens straight to the username field
                externals={"USER_ROSTER_DICT": r".\UserRoster.dat"},
                description=f"Supervisor Hub (HUB) - {HUB_VERSION}"))


def build_menu_app():
    d = build_menu_dict()
    write_dcf(d, HERE / "MenuApp.dcf")
    _write(HERE / "MenuApp.fmf",
           build_fmf(d, "MENUAPP_FF", r".\MenuApp.dcf", "MenuApp",
                     [("Menu", "MENU_REC")]))
    _write(HERE / "MenuApp.ent.qsf", build_qsf(d, "MENUAPP_DICT"), bom=True)
    _write(HERE / "MenuApp.ent.apc", build_menu_apc())   # C3a — grouped accept() menu generated from *_MENU_GROUPED
    _write(HERE / "MenuApp.ent.mgf", _mgf("MenuApp"))
    # Externals: (1) B4 — Assignment.dcf, the enumerator's pulled AS_<id>.dat (mapped to
    # MyAssignment.dat); (2) B6/B7 — the F1/F3/F4 instrument dicts, so syncdata can move primary
    # case data over Bluetooth. Each instrument dict's STRUCTURE is the snapshot dcf in this folder
    # (copy_instrument_dcfs) and its DATA file is the SEPARATELY-INSTALLED instrument's own .csdb
    # (..\\<App>\\<App>.csdb on device). The supervisor RECEIVES into those same .csdb files
    # (syncserver passive); the enumerator PUTs FROM them.
    menu_ext_dcfs = ["Assignment.dcf"] + [dcf for (_lbl, dcf, _dn, _fold) in INSTRUMENTS]
    ent = build_ent("MENUAPP", "MenuApp", "MenuApp.dcf", "MenuApp.fmf",
                    "MenuApp.ent.qsf", "MenuApp.ent.apc", "MenuApp.ent.mgf",
                    externals=menu_ext_dcfs)
    _write(HERE / "MenuApp.ent", json.dumps(ent, indent=2))
    menu_pff_ext = {"ASSIGNMENT_DICT": r".\MyAssignment.dat"}
    for (_lbl, _dcf, dn, fold) in INSTRUMENTS:
        menu_pff_ext[dn] = rf"..\{fold}\{fold}.csdb"
    _write(HERE / "MenuApp.pff",
           _pff("MenuApp.ent", "|type=None", externals=menu_pff_ext,   # C2: no case store; opens straight to the menu
                description=f"Supervisor Hub Menu (HUB) - {HUB_VERSION}"))


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
    write_per_enumerator_assignments(HERE)   # B4 — per-enumerator AS_<id>.dat + MyAssignment.dat
    print(f"  Assignment rows: {len(ASSIGNMENT_ROWS)}")


def copy_instrument_dcfs():
    """B6/B7 — snapshot each live instrument's main dcf into this folder so MenuApp can declare it
    EXTERNAL for the Bluetooth syncdata case exchange. Build-time copy = always current as of THIS
    build; REBUILD + redeploy the hub whenever an instrument is redeployed during UAT, so the shipped
    dcf still matches the device's .csdb schema (see the INSTRUMENTS note)."""
    cspro_root = HERE.parent   # deliverables/CSPro
    for (lbl, dcf, _dn, _fold) in INSTRUMENTS:
        src = cspro_root / lbl / dcf
        if not src.exists():
            print(f"  ! WARNING: {src} missing — MenuApp external {dcf} will NOT ship (syncdata of {lbl} will fail)")
            continue
        shutil.copyfile(src, HERE / dcf)
        print(f"  Snapshot instrument dcf: {lbl}/{dcf}")


def main():
    build_roster()
    build_assignment()
    copy_instrument_dcfs()   # B6/B7 — snapshot instrument dcfs for the external syncdata exchange
    build_login_app()
    build_menu_app()
    print("\nHub apps generated in", HERE)


if __name__ == "__main__":
    main()
