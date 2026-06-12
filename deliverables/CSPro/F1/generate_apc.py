#!/usr/bin/env python3
"""
F1 Facility Head Survey — CAPI logic (.ent.apc) generator.

Emits `FacilityHeadSurvey.ent.apc` from the reviewed spec
(`F1-Skip-Logic-and-Validations.md`). Generator-over-hand-edit: edit the tables
below + rerun, never hand-edit the .apc in Designer (changes would be lost on
regenerate).

Covers GH issues (generator side — FMF Designer GUI + CSEntry verification are
Carl's): #146 master skip gates, #147 field skip logic, #148 hard validations,
#149 soft validations, #152 cross-field checks, #151 dynamic value sets,
#153 conditional fills, #154 consent capture, #156 disposition, #157 GPS,
#231 verification photo, #232 PSGC cascade wiring.

  ⚠️  UNVERIFIED until compiled in CSPro Designer + run in CSEntry. This was
      authored without a CSPro toolchain; treat the first Designer compile as
      the real test. Item names follow generate_dcf.py / the spec §4 templates;
      any mismatch surfaces as a compile error to fix at the source table here.

Invoke:  python generate_apc.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import select_all_exclusive_warning_procs

HERE = Path(__file__).parent
OUT = HERE / "FacilityHeadSurvey.ent.apc"
DCF = HERE / "FacilityHeadSurvey.dcf"
SHARED_DIR = HERE.parent / "shared"


def _inline_shared(filename):
    """Return a shared helper module's body with its own 'PROC GLOBAL' header
    stripped, for pasting INSIDE the host's single PROC GLOBAL.

    Why inline instead of #include (verified 2026-06-08 against the CSEntry loader):
    CSPro forbids `#include` inside a PROC, and CSEntry forbids any code before the
    first PROC -- so an #include of a function library satisfies neither. Inlining
    the helper functions into PROC GLOBAL is the only arrangement both the Designer
    compiler and the CSEntry runtime loader accept.
    """
    text = (SHARED_DIR / filename).read_text(encoding="utf-8")
    body, seen_global = [], False
    for ln in text.splitlines():
        if not seen_global:
            if ln.strip() == "PROC GLOBAL":
                seen_global = True
            continue
        body.append(ln)
    if not seen_global:
        raise RuntimeError(f"{filename}: expected a 'PROC GLOBAL' line to strip")
    return "\n".join(body).strip("\n")


def dcf_item_names():
    """All item names in the F1 dcf (the source of truth for names)."""
    names = []
    dic = json.loads(DCF.read_text(encoding="utf-8"))
    for level in dic["levels"]:
        for rec in level.get("records", []):
            for it in rec.get("items", []):
                names.append(it["name"])
    return names


def dcf_items_full():
    """name -> full item dict (labels + value sets), plus dcf order."""
    dic = json.loads(DCF.read_text(encoding="utf-8"))
    items, order = {}, []
    for level in dic["levels"]:
        for rec in level.get("records", []):
            for it in rec.get("items", []):
                items[it["name"]] = it
                order.append(it["name"])
    return items, order


def auto_other_specify_procs():
    """Generic 'Other (specify)' enforcement for the remaining *_TXT items
    (closes the spec-4.13 tail that was listed as STILL OPEN): derive each
    text field's trigger from the dcf itself.
      - select-all groups: the sibling option flag (same Q number, _O## name)
        whose EN label mentions 'other'  -> text required when flag = 1
      - single-choice:     the same-Q parent whose value set has 'other'-
        labelled code(s)                 -> text required when parent hits one
    Only emits when the trigger is unambiguous (exactly one candidate);
    everything else is returned as unmatched for the report."""
    items, order = dcf_items_full()

    def en_label(it):
        for l in it.get("labels") or []:
            if l.get("language") in (None, "EN"):
                return l.get("text", "")
        return ""

    def qnum(n):
        m = re.match(r"^Q(\d+)_", n)
        return int(m.group(1)) if m else None

    by_q = {}
    for n in order:
        q = qnum(n)
        if q is not None:
            by_q.setdefault(q, []).append(n)

    procs, unmatched = {}, []
    for n in order:
        if not n.endswith("_TXT"):
            continue
        q = qnum(n)
        if q is None:
            continue
        siblings = by_q.get(q, [])
        flags = [m for m in siblings
                 if re.search(r"_O\d+$", m)
                 and "other" in en_label(items[m]).lower()]
        if len(flags) > 1:
            # disambiguate: 'other' also appears inside unrelated option labels
            # ("other government agencies", "other health facilities") — the
            # true trigger is the option whose label ENDS with "Other (specify)"
            exact = [m for m in flags
                     if re.search(r"other(\s*\(specify\))?\s*$",
                                  en_label(items[m]), re.IGNORECASE)]
            if len(exact) == 1:
                flags = exact
        if len(flags) == 1:
            procs[n] = (
                f"PROC {n}\n"
                f"preproc\n"
                f"  if {flags[0]} <> 1 then\n"
                f"    {n} = \"\";   {{ skip + clear: 'Other (specify)' not ticked }}\n"
                f"    noinput;\n"
                f"  endif;\n"
                f"postproc\n"
                f"  if {flags[0]} = 1 and length(strip({n})) = 0 then\n"
                f"    errmsg(\"'Other (specify)' was selected for Q{q}. Please specify.\");\n"
                f"    reenter;\n"
                f"  endif;"
            )
            continue
        parents = []
        for m in siblings:
            if m == n or m.endswith("_TXT") or re.search(r"_O\d+$", m):
                continue
            vss = items[m].get("valueSets") or []
            if not vss:
                continue
            codes = []
            for v in vss[0].get("values", []):
                vlab = next((l.get("text", "") for l in v.get("labels", [])
                             if l.get("language") in (None, "EN")), "")
                if "other" in vlab.lower() and v.get("pairs"):
                    codes.append(v["pairs"][0].get("value"))
            if codes:
                parents.append((m, codes))
        if len(parents) == 1:
            m, codes = parents[0]
            cond = " or ".join(f"{m} = {c}" for c in codes)
            procs[n] = (
                f"PROC {n}\n"
                f"preproc\n"
                f"  if not ({cond}) then\n"
                f"    {n} = \"\";   {{ skip + clear: no 'other' option chosen }}\n"
                f"    noinput;\n"
                f"  endif;\n"
                f"postproc\n"
                f"  if ({cond}) and length(strip({n})) = 0 then\n"
                f"    errmsg(\"An 'other' option was selected for Q{q}. Please specify.\");\n"
                f"    reenter;\n"
                f"  endif;"
            )
        else:
            unmatched.append(n)
    return procs, unmatched


def uhc9_other_specify_procs(names):
    """#148: enforce 'Other (specify)' text on UHC9 dual-other items.
    `<FIELD>_YES_OTHER_TXT` (parent code 4) and `<FIELD>_NO_OTHER_TXT` (code 7),
    per spec 4.13. Parent = the name minus the suffix (dcf is the truth — spec
    used shortened names like Q12_YES_OTHER_TXT)."""
    procs = {}
    for n in names:
        for suffix, code, lbl in (("_YES_OTHER_TXT", 4, "Yes, other reason"),
                                  ("_NO_OTHER_TXT", 7, "No, other reason")):
            if n.endswith(suffix):
                parent = n[: -len(suffix)]
                procs[n] = (
                    f"PROC {n}\n"
                    f"preproc\n"
                    f"  if {parent} <> {code} then\n"
                    f"    {n} = \"\";   {{ skip + clear: '{lbl}' not chosen }}\n"
                    f"    noinput;\n"
                    f"  endif;\n"
                    f"postproc\n"
                    f"  if {parent} = {code} and length(strip({n})) = 0 then\n"
                    f"    errmsg(\"'{lbl}' was selected for {parent}. Please specify.\");\n"
                    f"    reenter;\n"
                    f"  endif;"
                )
    return procs


# Why-difficult display gates (spec 4.10): each Q66-74 option-set is shown only
# if the matching Q65 difficulty option was flagged; same for Q122-134 vs Q121.
# Gate fires as a first-field (O01) preproc. Question number -> option index by
# position (Q66->Q65 O01 ... Q74->Q65 O09; Q122->Q121 O01 ... Q134->Q121 O13).
WHY_DIFF_GATES = [
    (range(66, 75), "Q65_ACCRED_DIFFICULT", 66),   # Q66..Q74 -> Q65 O01..O09
    (range(122, 135), "Q121_DOH_LIC_DIFFICULT", 122),  # Q122..Q134 -> Q121 O01..O13
]


def why_difficult_gate_procs(names):
    procs = {}
    first_field_by_q = {}
    qnum_of = {}
    for n in names:
        m = re.match(r"^Q(\d+)_", n)
        if m:
            qnum_of[n] = int(m.group(1))
    for n in names:
        m = re.match(r"^Q(\d+)_(WHY_DIFF_[A-Z0-9_]+?)_O(\d+)$", n)
        if not m:
            continue
        q, opt = int(m.group(1)), int(m.group(3))
        if opt == 1:
            first_field_by_q[q] = n  # the O01 field is where the gate preproc lives
    for qrange, gate_dict, start in WHY_DIFF_GATES:
        for q in qrange:
            field = first_field_by_q.get(q)
            if not field:
                continue
            opt_idx = q - start + 1
            gate = f"{gate_dict}_O{opt_idx:02d}"
            # If the gate option wasn't flagged, skip the WHOLE Qq option cluster.
            # `skip to next` is illegal outside a repeating group (CSEntry, verified
            # 2026-06-08), so target the first field AFTER this question's cluster
            # (the next field with a different question number in dcf order).
            idx = names.index(field)
            target = next((names[j] for j in range(idx + 1, len(names))
                           if qnum_of.get(names[j]) != q), None)
            if target is None:
                continue
            # Gate options are coded Yes=1/No=2 — skip unless explicitly flagged
            # Yes. (`= 0` was a dead condition: 0 isn't in the value set and a
            # blank is notappl, not 0, so the cluster was NEVER skipped.)
            procs[field] = (
                f"PROC {field}\n"
                f"preproc\n"
                f"  if {gate} <> 1 then   {{ Q{q} cluster shown only if {gate} was flagged Yes }}\n"
                f"    skip to {target};\n"
                f"  endif;"
            )
    return procs

HEADER = """\
{ ============================================================================
  FacilityHeadSurvey — CAPI logic   (AUTOGENERATED by generate_apc.py)
  Do NOT hand-edit: edit generate_apc.py's tables and rerun.
  Spec: F1-Skip-Logic-and-Validations.md (reviewed 2026-04-21).
  ============================================================================ }

PROC GLOBAL
{ Date context for accreditation / tenure validations (see spec 4.1). }
numeric currentYYYYMMDD;
numeric currentYear;
numeric currentMonth;

{ Single-number redesign (2026-06-10): the questionnaire number's first 7 digits
  are a POSITIONAL slice of the 10-digit PSA PSGC (RR|PP|MMM = positions 1-7 per
  the adopted Questionnaire Numbering Convention) - they cannot be split into
  per-level codes (PSA provinces are 3-digit; the slice straddles levels). So
  validation resolves geoFull = first7*1000 hierarchically: region exact, then
  scan the region's provinces (a province-level match covers province-anchored
  facilities, e.g. district hospitals), else each province's cities. }
numeric regionFull;
numeric geoFull;
numeric geoFound;

{ Shared helpers inlined into this single PROC GLOBAL (PSGC-Cascade first so its
  ROOT_PSGC_PARENT declaration precedes all functions). #include can't be used:
  CSPro forbids it inside a PROC, and CSEntry forbids code before the first PROC.
  Requires the 4 PSGC external dicts attached to the .ent. }
""" + _inline_shared("PSGC-Cascade.apc") + """

""" + _inline_shared("Capture-Helpers.apc") + """
"""

# --- Application entry: init date context + (no global skips here) -----------
APP_ENTRY = """\
PROC FACILITYHEADSURVEY_FF
preproc
  currentYYYYMMDD = sysdate("YYYYMMDD");
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(currentYYYYMMDD / 100) % 100;

{ LANGUAGE_USED is captured in the QUESTIONNAIRE_NUMBER postproc (case key, the
  very first field) — see PROC QUESTIONNAIRE_NUMBER below. (Previously rode on
  SURVEY_CODE / SURVEY_TEAM_LEADER_S_NAME; consolidated to the id postproc
  2026-06-12 so it fires at the true case start regardless of FC form layout.) }
"""

# --- Interview-control scaffolding: consent gate, GPS, photo, PSGC -----------
# Item names per generate_dcf.py (FIELD_CONTROL, REC_FACILITY_CAPTURE, geo-ID).
CONTROL_PROCS = """\
{ ---- Single 12-digit Questionnaire Number (redesign 2026-06-10) ----
  The enumerator types ONE number (RR PP MMM FF CCC). Parse it into the component
  PSGC codes (kept as FIELD_CONTROL items so every downstream PROC keeps working),
  validate region/province/city against the PSGC external dicts (hard-stop on a bad
  code), and fill the read-only *_NAME items shown on the form. The full 10-digit
  PSGC codes are also written to the off-form REGION/PROVINCE_HUC/CITY_MUNICIPALITY
  items so the BARANGAY cascade filters correctly. ---- }
PROC QUESTIONNAIRE_NUMBER
postproc
  { 0. record the interview language at the true case start (§15.E) }
  LANGUAGE_USED = getlanguage();
  { 1. decompose the within-parent codes }
  REGION_CODE            = int(QUESTIONNAIRE_NUMBER / 10000000000);
  PROVINCE_HUC_CODE      = int(QUESTIONNAIRE_NUMBER / 100000000) % 100;
  CITY_MUNICIPALITY_CODE = int(QUESTIONNAIRE_NUMBER / 100000) % 1000;
  FACILITY_NO            = int(QUESTIONNAIRE_NUMBER / 1000) % 100;
  CASE_SEQ               = QUESTIONNAIRE_NUMBER % 1000;

  { 2. geo prefix: the number's first 7 digits ARE positions 1-7 of the 10-digit
       PSGC (positional slice per the adopted convention) - append 000 for the
       full geo code. It matches either a city/municipality code or, for
       province-anchored facilities (e.g. district hospitals), a province code. }
  regionFull = REGION_CODE * 100000000;
  geoFull    = int(QUESTIONNAIRE_NUMBER / 100000) * 1000;
  REGION     = regionFull;

  { 3a. region: exact match + name }
  geoFound = 0;
  R_PARENT_CODE = 0;
  if loadcase(PSGC_REGION_DICT, R_PARENT_CODE) <> 0 then
    do varying numeric ri = 1 until ri > count(PSGC_REGION_DICT.PSGC_REGION_REC)
      if R_CODE(ri) = regionFull then
        REGION_NAME = strip(R_NAME(ri));
        geoFound = 1;
      endif;
    enddo;
  endif;
  if geoFound = 0 then
    errmsg("Region code %02d not found in PSGC. Check the Questionnaire Number.", REGION_CODE);
    reenter;
  endif;

  { 3b. resolve the 7-digit prefix hierarchically: province-level match first,
       else scan that province's cities. Fills both names + the full PSGC codes
       (CITY_MUNICIPALITY feeds the barangay cascade). }
  geoFound = 0;
  P_PARENT_REGION = regionFull;
  if loadcase(PSGC_PROVINCE_DICT, P_PARENT_REGION) <> 0 then
    do varying numeric pi = 1 until pi > count(PSGC_PROVINCE_DICT.PSGC_PROVINCE_REC) or geoFound = 1
      if P_CODE(pi) = geoFull then
        { province-anchored facility: geo resolves at province level }
        PROVINCE_NAME     = strip(P_NAME(pi));
        CITY_NAME         = strip(P_NAME(pi));
        PROVINCE_HUC      = geoFull;
        CITY_MUNICIPALITY = geoFull;
        geoFound = 1;
      else
        C_PARENT_PROVINCE = P_CODE(pi);
        if loadcase(PSGC_CITY_DICT, C_PARENT_PROVINCE) <> 0 then
          do varying numeric ci = 1 until ci > count(PSGC_CITY_DICT.PSGC_CITY_REC) or geoFound = 1
            if C_CODE(ci) = geoFull then
              PROVINCE_NAME     = strip(P_NAME(pi));
              CITY_NAME         = strip(C_NAME(ci));
              PROVINCE_HUC      = P_CODE(pi);
              CITY_MUNICIPALITY = geoFull;
              geoFound = 1;
            endif;
          enddo;
        endif;
      endif;
    enddo;
  endif;
  if geoFound = 0 then
    errmsg("Geo prefix %07d not found in PSGC (no province or city/municipality matches). Check the Questionnaire Number.", int(QUESTIONNAIRE_NUMBER / 100000));
    reenter;
  endif;

  { 4. the geo names are display-only confirmations - lock them read-only }
  protect(REGION_NAME, true);
  protect(PROVINCE_NAME, true);
  protect(CITY_NAME, true);

{ Informed consent: the separate CONSENT_GIVEN field was removed 2026-06-12.
  Consent refusal is now recorded by the enumerator as the Result-of-Visit
  disposition ("Refused" = code 3); the read-aloud consent script is read from
  the printed sheet (off the CAPI). No consent gate PROC. }

{ ---- #157 Facility GPS — AUTO-FETCHED on focus (2026-06-12; no manual trigger).
  Fires when the enumerator reaches the coordinates; captured once (guarded on
  read-time), then every GPS field is protected (read-only) so coordinates can't
  be typed. ReadGPSReading() lives in Capture-Helpers.apc. Desktop (getos 10-19)
  has no GPS radio → fields stay blank there (device-only). ---- }
PROC FACILITY_GPS_LATITUDE
onfocus
  if length(strip(FACILITY_GPS_READTIME)) = 0 then   { capture once; not on back-nav }
    if ReadGPSReading(120, 20) then
      FACILITY_GPS_LATITUDE   = maketext("%f", gps(latitude));
      FACILITY_GPS_LONGITUDE  = maketext("%f", gps(longitude));
      FACILITY_GPS_ALTITUDE   = maketext("%f", gps(altitude));
      FACILITY_GPS_ACCURACY   = gps(accuracy);
      FACILITY_GPS_SATELLITES = gps(satellites);
      FACILITY_GPS_READTIME   = maketext("%d", gps(readtime));
    endif;
  endif;
  { Protect ONLY once captured — protecting a blank numeric (no fix / desktop)
    triggers "protected field is out of range - value is NOTAPPL". }
  if length(strip(FACILITY_GPS_READTIME)) > 0 then
    protect(FACILITY_GPS_LATITUDE, true);
    protect(FACILITY_GPS_LONGITUDE, true);
    protect(FACILITY_GPS_ALTITUDE, true);
    protect(FACILITY_GPS_ACCURACY, true);
    protect(FACILITY_GPS_SATELLITES, true);
    protect(FACILITY_GPS_READTIME, true);
  endif;

{ ---- #231 Verification photo (moved to the END of the form 2026-06-12). Filename
  pattern case-{12-digit case id RR-PP-MMM-FF-CCC}-verification.jpg. Now CONDITIONAL on
  the visit outcome and soft-validated (warn, don't trap, on camera failure). ---- }
PROC VERIFICATION_PHOTO_FILENAME
preproc
  { display-only — the camera trigger fills this; it is never typed }
  noinput;

PROC CAPTURE_VERIFICATION_PHOTO
preproc
  { gate: photograph only visits where an interview occurred
    (1 Completed, 4 Incomplete); skip 2 Postponed / 3 Refused }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 4) then
    VERIFICATION_PHOTO_FILENAME = "";   { clear any stale name if outcome was changed back }
    noinput;
  endif;
onfocus
  { capture once: an empty filename means no photo yet, so (re)try the camera }
  if length(strip(VERIFICATION_PHOTO_FILENAME)) = 0 then
    string fn = "case-" + maketext("%02d%02d%03d%02d%03d", REGION_CODE, PROVINCE_HUC_CODE, CITY_MUNICIPALITY_CODE, FACILITY_NO, CASE_SEQ) + "-verification.jpg";
    if TakeVerificationPhoto(fn) then
      VERIFICATION_PHOTO_FILENAME = fn;
    else
      errmsg("Verification photo not captured (camera cancelled or unavailable). Re-enter this field to retry, or note the reason in your field report.");
    endif;
  endif;
  CAPTURE_VERIFICATION_PHOTO = notappl;

{ ---- #232 / #151 Barangay cascade (single-number redesign): region/province/city
  are derived from the Questionnaire Number (off-form), so only barangay is picked
  here — its value set is filtered to the children of the derived city. CITY_MUNICIPALITY
  holds the full 10-digit city PSGC code (set in QUESTIONNAIRE_NUMBER postproc). ---- }
PROC BARANGAY
onfocus
  FillBarangayValueSet(CITY_MUNICIPALITY);
"""

# --- Bespoke PROCs transcribed verbatim from spec §4 (author-validated names).
# Each entry is keyed by the field name it owns so we never emit a duplicate
# PROC for a field that also appears in a table-driven skip below.
BESPOKE_PROCS = {
    # G1 (F2 benchmark — PROF-01 family): Q3_AGE plausibility. 2-digit field, so the
    # only impossible-high value is a typo; hard floor 18 (a facility head is an adult),
    # soft confirm at F2's tester-validated 80. Guarded against a blank (notappl) age.
    "Q3_AGE": """\
PROC Q3_AGE
postproc
  if Q3_AGE <> notappl and Q3_AGE < 18 then
    errmsg("Age (%d) is below 18 - a facility head must be an adult. Please re-enter.", Q3_AGE);
    reenter;
  endif;
  if Q3_AGE <> notappl and Q3_AGE > 80 then
    errmsg("Age (%d) is unusually high for a facility head - please confirm.", Q3_AGE);
  endif;""",
    # G3 (F2 benchmark — DISP-02 / parity with F3 + F4): final-visit date cannot precede
    # the first-visit date. Guarded so a blank final date (single visit) never false-fires.
    "DATE_OF_FINAL_VISIT_TO_THE_FACILITY": """\
PROC DATE_OF_FINAL_VISIT_TO_THE_FACILITY
postproc
  if DATE_OF_FINAL_VISIT_TO_THE_FACILITY <> notappl and DATE_FIRST_VISITED_THE_FACILITY <> notappl and DATE_OF_FINAL_VISIT_TO_THE_FACILITY < DATE_FIRST_VISITED_THE_FACILITY then
    errmsg("Final-visit date cannot be earlier than the first-visit date.");
    reenter;
  endif;""",
    # 4.2 + 4.3 eligibility / tenure (Section A) — #148 hard, #152 cross-field
    "Q5_MONTHS_AT_FACILITY": """\
PROC Q5_MONTHS_AT_FACILITY
postproc
  if (Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY) < 6 then
    errmsg("Respondent must have >= 6 months in current position. End interview and code as Refused/Incomplete.");
    ENUM_RESULT_FINAL_VISIT = 4;   { Refused/Incomplete }
    endlevel;
  endif;
  if Q5_YEARS_AT_FACILITY > (Q3_AGE - 20) then
    errmsg("Years at facility (%d) exceeds working-age years available (%d). Reenter.",
           Q5_YEARS_AT_FACILITY, Q3_AGE - 20);
    reenter;
  endif;""",
    "Q6_MONTHS_HEALTH": """\
PROC Q6_MONTHS_HEALTH
postproc
  numeric tenureMos = Q5_YEARS_AT_FACILITY * 12 + Q5_MONTHS_AT_FACILITY;
  numeric healthMos = Q6_YEARS_HEALTH * 12 + Q6_MONTHS_HEALTH;
  if healthMos < tenureMos then
    errmsg("Years in any health-related role (%d mos) cannot be less than years at this facility (%d mos).",
           healthMos, tenureMos);
    reenter;
  endif;
  if Q6_YEARS_HEALTH > (Q3_AGE - 20) then
    errmsg("Years in health (%d) exceeds working-age years available (%d).",
           Q6_YEARS_HEALTH, Q3_AGE - 20);
    reenter;
  endif;""",
    # 4.6 YAKAP accreditation date (Section D) — #148 hard
    "Q52_YK_SINCE_YEAR": """\
PROC Q52_YK_SINCE_YEAR
postproc
  if Q52_YK_SINCE_YEAR < 2019 or Q52_YK_SINCE_YEAR > currentYear then
    errmsg("YAKAP accreditation year must be between 2019 and %d.", currentYear);
    reenter;
  endif;""",
    "Q52_YK_SINCE_MONTH": """\
PROC Q52_YK_SINCE_MONTH
postproc
  if Q52_YK_SINCE_MONTH < 1 or Q52_YK_SINCE_MONTH > 12 then
    errmsg("Month must be 1-12.");
    reenter;
  endif;
  if Q52_YK_SINCE_YEAR = currentYear and Q52_YK_SINCE_MONTH > currentMonth then
    errmsg("Accreditation date is in the future. Reenter.");
    reenter;
  endif;""",
    # 4.7 registered <= eligible (Section D) — #152 cross-field
    "Q87_REGISTERED_PATIENTS": """\
PROC Q87_REGISTERED_PATIENTS
postproc
  if Q87_REGISTERED_PATIENTS > Q86_ELIGIBLE_PATIENTS then
    errmsg("Registered patients (%d) cannot exceed eligible patients (%d).",
           Q87_REGISTERED_PATIENTS, Q86_ELIGIBLE_PATIENTS);
    reenter;
  endif;""",
    # 4.8 capitation soft warning (Section D) — #149 soft (accept) + #148 hard cap
    "Q57_CAPITATION_AMT": """\
PROC Q57_CAPITATION_AMT
postproc
  if Q57_CAPITATION_AMT > 5000 then
    errmsg("Capitation %d PHP is implausibly high. Reenter or confirm.", Q57_CAPITATION_AMT);
    reenter;
  endif;
  if Q57_CAPITATION_AMT > 1700 then
    if accept("Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?", "Yes", "No") <> 1 then
      reenter;
    endif;
  endif;""",
    # 4.9 Q121 "select all that apply" DOH-licensing-difficulty (Section F).
    # Reconciled vs the Apr 20 questionnaire (#151): the dcf models Q121 as 14
    # binary option fields (_O01..O14), so facility-type option visibility is a
    # PER-OPTION gate, not a setvalueset on a single field (the old PROC named a
    # field — Q121_DOH_LIC_DIFFICULT — that does not exist in the dcf, a hard
    # compile error). Per the questionnaire: O10/O11/O12 are hospital-only, O13
    # (public access to price information) is primary-care-only, O14 = "None of
    # the above" -> skip the why-difficult cluster to Q135. Q8_SERVICE_LEVEL = 1
    # is Primary Care Facility.
    # DESIGNER-VERIFY: the `noinput` conditional-hide idiom for a multi-select
    # option is the one bit to confirm on compile; symbols all resolve.
    "Q121_DOH_LIC_DIFFICULT_O10": """\
PROC Q121_DOH_LIC_DIFFICULT_O10
preproc
  if Q8_SERVICE_LEVEL = 1 then noinput; endif;   { hospital-only option; hide for primary-care facilities }""",
    "Q121_DOH_LIC_DIFFICULT_O11": """\
PROC Q121_DOH_LIC_DIFFICULT_O11
preproc
  if Q8_SERVICE_LEVEL = 1 then noinput; endif;   { hospital-only option; hide for primary-care facilities }""",
    "Q121_DOH_LIC_DIFFICULT_O12": """\
PROC Q121_DOH_LIC_DIFFICULT_O12
preproc
  if Q8_SERVICE_LEVEL = 1 then noinput; endif;   { hospital-only option; hide for primary-care facilities }""",
    "Q121_DOH_LIC_DIFFICULT_O13": """\
PROC Q121_DOH_LIC_DIFFICULT_O13
preproc
  if Q8_SERVICE_LEVEL <> 1 then noinput; endif;  { primary-care-only option; hide for hospitals }""",
    "Q121_DOH_LIC_DIFFICULT_O14": """\
PROC Q121_DOH_LIC_DIFFICULT_O14
postproc
  if Q121_DOH_LIC_DIFFICULT_O14 = 1 then   { "None of the above" -> skip the why-difficult cluster }
    skip to Q135_NBB_CURR;
  endif;""",
}

# --- Multi-branch routing (spec 2 Section D/E/G) deferred from pass 1. Branch
# VALUES are from the spec's skip table; controlling-field item names confirmed
# against the dcf. Single-choice control fields, so these are field PROCs.
# (Verify the literal option codes for Q116/Q152 in Designer — spec gives them
# as labels, not numbers; the common cases are coded below.)
ROUTING_PROCS = {
    # Section C: Q32 "No, not submitting" (4) -> Q35
    "Q32_DATA_SUBMIT": """\
PROC Q32_DATA_SUBMIT
postproc
  if Q32_DATA_SUBMIT = 4 then       { No, not submitting }
    skip to Q35_STAFFING_CHANGED;
  endif;""",
    # Section D: Q61 = No -> Q62 (skip the reason-text item Q61.1)
    "Q61_TRANCHE_DELAY": """\
PROC Q61_TRANCHE_DELAY
postproc
  if Q61_TRANCHE_DELAY = 2 then     { No }
    skip to Q62_TRANCHE_INTERVAL;
  endif;""",
    # Section D: Q80 5-way intend-accredit routing
    "Q80_INTEND_ACCRED": """\
PROC Q80_INTEND_ACCRED
postproc
  if Q80_INTEND_ACCRED in 1,2 then  skip to Q84_PROCESS_CHALL;        endif;  { Yes (in/ not-in process) }
  if Q80_INTEND_ACCRED = 3    then  skip to Q82_DECIDED_NOT_REASON;   endif;  { No, decided not to }
  if Q80_INTEND_ACCRED = 4    then  skip to Q83_TRIED_FAILED_REASON;  endif;  { No, tried and failed }
  if Q80_INTEND_ACCRED = 5    then  skip to Q81_KNOW_HOW_START;       endif;  { No, haven't thought }
  if Q80_INTEND_ACCRED = 6    then  skip to Q85_CATCHMENT_AREA;   endif;  { I don't know }""",
    # Section D: Q90 costing-viable x Q51 accreditation status
    "Q90_COSTING_VIABLE": """\
PROC Q90_COSTING_VIABLE
postproc
  if Q90_COSTING_VIABLE = 1 and Q51_YK_ACCRED = 1 then  skip to Q91_MIN_CAP_VALUE_ACC;    endif;  { Viable + accredited }
  if Q90_COSTING_VIABLE = 2 and Q51_YK_ACCRED = 2 then  skip to Q92_MIN_CAP_VALUE_NONACC; endif;  { Not viable + non-accredited }
  if Q90_COSTING_VIABLE = 3 then                        skip to Q93_CHARGE_ADDL_CAP;      endif;  { I don't know }""",
    # Section D: Q95 received-payments (Yes-all / Yes-some) -> Q97
    "Q95_RECEIVED_PAYMENTS": """\
PROC Q95_RECEIVED_PAYMENTS
postproc
  if Q95_RECEIVED_PAYMENTS in 1,2 then   { Yes, all / Yes, some }
    skip to Q97_PAYMENT_CHALL;
  endif;""",
    # Section E: Q102 has-BUCAS 3-way (No falls through to Q103)
    "Q102_HAS_BUCAS": """\
PROC Q102_HAS_BUCAS
postproc
  if Q102_HAS_BUCAS = 1 then  skip to Q104_BUCAS_SERVICES_O01; endif;  { Yes -> services (skip Q103) }
  if Q102_HAS_BUCAS = 3 then  skip to Q108_HEARD_GAMOT;        endif;  { I don't know -> Q108 }""",
    "Q103_NO_BUCAS_REASON": """\
PROC Q103_NO_BUCAS_REASON
postproc
  skip to Q108_HEARD_GAMOT;          { any answer -> Q108 (skip Q104-107) }""",
    # Section E: Q109 GAMOT-accredited (No falls through to Q110)
    "Q109_GAMOT_ACCRED": """\
PROC Q109_GAMOT_ACCRED
postproc
  if Q109_GAMOT_ACCRED = 1 then  skip to Q111_GAMOT_FACTORS_O01; endif;  { Yes (skip Q110) }""",
    "Q110_NO_GAMOT_REASON": """\
PROC Q110_NO_GAMOT_REASON
postproc
  skip to Q112_STOCKOUT;             { any answer -> Q112 (skip Q111) }""",
    # Section E: Q116 = No / Did-not-experience -> Q118 (codes per dcf value set; verify)
    "Q116_ADDR_STOCKOUT": """\
PROC Q116_ADDR_STOCKOUT
postproc
  if Q116_ADDR_STOCKOUT in 2,3 then  { 2 = No, 3 = Did not experience (verify codes in Designer) }
    skip to Q118_DOH_LICENSED;
  endif;""",
    # Section G: Q145 Malasakit provided
    "Q145_MALASAKIT_PROVIDED": """\
PROC Q145_MALASAKIT_PROVIDED
postproc
  if Q145_MALASAKIT_PROVIDED = 2 then    { No -> skip the why-provided block to the not-provided block }
    skip to Q147_NO_MALASAKIT_WHY_O01;
  endif;""",
    # Q145=Yes path: Q146 (why-provided) is asked, then Q147 (not-provided) must
    # be skipped. Gate Q147's first field on Q145=Yes -> jump to Q148 (spec 4.10
    # first-field-preproc pattern; Q145=No reaches Q147 normally).
    "Q147_NO_MALASAKIT_WHY_O01": """\
PROC Q147_NO_MALASAKIT_WHY_O01
preproc
  if Q145_MALASAKIT_PROVIDED = 1 then   { Yes -> Q146 already asked; skip the not-provided block }
    skip to Q148_LGU_SUPPORT;
  endif;""",
    # Section G: Q152 protocol clarity (Very Clear / Clear) -> Q154
    "Q152_PHO_PROTOCOL_CLARITY": """\
PROC Q152_PHO_PROTOCOL_CLARITY
postproc
  if Q152_PHO_PROTOCOL_CLARITY in 1,2 then   { Very Clear / Clear (verify codes) }
    skip to Q154_NUM_REFERRED_OUT;
  endif;""",
}
BESPOKE_PROCS.update(ROUTING_PROCS)

# --- Table-driven skip logic (spec §2). Each row: field PROC -> if <cond> skip.
# Kept simple/dichotomous; complex multi-branch routing (Q80, Q90, Q102/Q109)
# stays bespoke/TODO below. Fields already in BESPOKE_PROCS are skipped to avoid
# duplicate PROC blocks.
SKIP_RULES = [
    # Section C — UHC Implementation
    ("Q10_HAS_PRIMARY_PKG",   "Q10_HAS_PRIMARY_PKG = 2",        "Q12_PCB_LICENSING"),
    ("Q13_PUBLIC_HEALTH_UNIT","Q13_PUBLIC_HEALTH_UNIT in 2,9",  "Q16_HEALTH_PROMO_UNIT"),
    ("Q14_PHU_CREATED",       "Q14_PHU_CREATED in 5:9",         "Q16_HEALTH_PROMO_UNIT"),
    ("Q16_HEALTH_PROMO_UNIT", "Q16_HEALTH_PROMO_UNIT in 2,9",   "Q19_NEW_ROLES"),
    ("Q17_HPU_CREATED",       "Q17_HPU_CREATED in 5:9",         "Q19_NEW_ROLES"),
    ("Q19_NEW_ROLES",         "Q19_NEW_ROLES in 5:9",           "Q21_NEW_DEPTS"),
    ("Q21_NEW_DEPTS",         "Q21_NEW_DEPTS in 5:9",           "Q23_NEW_BUILDINGS"),
    ("Q23_NEW_BUILDINGS",     "Q23_NEW_BUILDINGS in 5:9",       "Q25_NEW_ROOMS"),
    ("Q25_NEW_ROOMS",         "Q25_NEW_ROOMS in 5:9",           "Q27_INC_EQUIPMENT"),
    ("Q27_INC_EQUIPMENT",     "Q27_INC_EQUIPMENT in 5:9",       "Q29_INC_SUPPLIES"),
    ("Q29_INC_SUPPLIES",      "Q29_INC_SUPPLIES in 5:9",        "Q31_EMR_USE"),
    ("Q31_EMR_USE",           "Q31_EMR_USE in 5:8 or Q31_EMR_USE = 9", "Q35_STAFFING_CHANGED"),
    ("Q35_STAFFING_CHANGED",  "Q35_STAFFING_CHANGED = 2",       "Q37_REFERRAL_CHANGED"),
    ("Q37_REFERRAL_CHANGED",  "Q37_REFERRAL_CHANGED = 2",       "Q39_MOU_MOA"),
    # Section D — YAKAP / Konsulta
    ("Q51_YK_ACCRED",         "Q51_YK_ACCRED = 2",              "Q79_NOT_ACCRED_REASON_O01"),
    ("Q59_KNOW_PAY_FREQ",     "Q59_KNOW_PAY_FREQ = 2",          "Q61_TRANCHE_DELAY"),
    ("Q77_ENROLL_CHALL",      "Q77_ENROLL_CHALL = 2",           "Q85_CATCHMENT_AREA"),
    ("Q89_COSTING_DONE",      "Q89_COSTING_DONE = 2",           "Q91_MIN_CAP_VALUE_ACC"),
    ("Q93_CHARGE_ADDL_CAP",   "Q93_CHARGE_ADDL_CAP = 2",        "Q95_RECEIVED_PAYMENTS"),
    ("Q97_PAYMENT_CHALL",     "Q97_PAYMENT_CHALL = 2",          "Q99_EXPAND_NEXT_O01"),
    # Section E — BUCAS / GAMOT
    ("Q101_HEARD_BUCAS",      "Q101_HEARD_BUCAS = 2",           "Q108_HEARD_GAMOT"),
    ("Q108_HEARD_GAMOT",      "Q108_HEARD_GAMOT = 2",           "Q112_STOCKOUT"),
    ("Q112_STOCKOUT",         "Q112_STOCKOUT = 2",              "Q118_DOH_LICENSED"),
    # Section F — DOH Licensing
    ("Q118_DOH_LICENSED",     "Q118_DOH_LICENSED in 2,3,4",     "Q135_NBB_CURR"),
    # Section G — Service Delivery
    ("Q135_NBB_CURR",         "Q135_NBB_CURR = 2",              "Q138_ZBB_CURR"),
    ("Q138_ZBB_CURR",         "Q138_ZBB_CURR = 2",              "Q141_ALLOW_OOP_BASIC"),
    ("Q141_ALLOW_OOP_BASIC",  "Q141_ALLOW_OOP_BASIC = 2",       "Q143_DIFFICULT_BENEFIT"),
    ("Q148_LGU_SUPPORT",      "Q148_LGU_SUPPORT = 2",           "Q152_PHO_PROTOCOL_CLARITY"),
    ("Q150_LGU_SATISFIED",    "Q150_LGU_SATISFIED = 1",         "Q154_NUM_REFERRED_OUT"),
    ("Q161_REF_SATISFACTION", "Q161_REF_SATISFACTION in 1,2",   "Q163_HR_CHALL_O01"),
]

# Multi-branch / routing skips left for a follow-up pass (need careful per-branch
# transcription + ASPSI confirmation): Q80 (5-way intend-accredit), Q90 (costing
# viable x Q51), Q102/Q109 (BUCAS/GAMOT has-x branches), Q32 DATA_SUBMIT,
# Q65/Q121 "why-difficult" per-option gates (Q66-Q74, Q122-Q134).
TODO_NOTE = """\
{ ============================================================================
  STILL OPEN (need per-item data or FMF/CSEntry verification):
    - #144/#145 Filipino label content + setlanguage (FMF Designer side).
  CLOSED 2026-06-11: "Other (specify)" enforcement now auto-derived from the
    dcf for all *_TXT items (see the auto-derived section above); Q65/Q121
    why-difficult gates fixed (`<> 1` -- the old `= 0` was a dead condition,
    options are coded Yes=1/No=2, blank is notappl) which also implements the
    "None of the above only" routing: with no cluster option flagged Yes,
    every cluster skips and entry lands at Q75/Q135. Literal option codes
    audited mechanically against the dcf value sets (dead-condition scan).
  ============================================================================ }
"""


def skip_proc(field, cond, target):
    return (
        f"PROC {field}\n"
        f"postproc\n"
        f"  if {cond} then\n"
        f"    skip to {target};\n"
        f"  endif;"
    )


def main():
    parts = [HEADER, "", APP_ENTRY, "", CONTROL_PROCS, ""]

    parts.append("{ ---- Validations & cross-field checks (spec 4) ---- }")
    for field in sorted(BESPOKE_PROCS):
        parts.append(BESPOKE_PROCS[field])
        parts.append("")

    parts.append("{ ---- Skip logic (spec 2), table-driven ---- }")
    covered = set(BESPOKE_PROCS)
    for field, cond, target in SKIP_RULES:
        if field in covered:
            # field already owns a bespoke PROC — fold the skip in there instead
            raise SystemExit(
                f"PROC collision: {field} is both bespoke and a skip rule; "
                f"merge the skip into its BESPOKE_PROCS entry."
            )
        covered.add(field)
        parts.append(skip_proc(field, cond, target))
        parts.append("")

    # dcf-driven blocks (names read straight from the dictionary)
    names = dcf_item_names()

    parts.append("{ ---- Why-difficult display gates (spec 4.10) ---- }")
    for field, proc in sorted(why_difficult_gate_procs(names).items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — UHC9 dual-other items (spec 4.13) ---- }")
    for field, proc in sorted(uhc9_other_specify_procs(names).items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — auto-derived from the dcf (spec 4.13 tail) ---- }")
    auto_procs, unmatched = auto_other_specify_procs()
    auto_emitted = 0
    for field, proc in sorted(auto_procs.items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")
        auto_emitted += 1
    print(f"  other-specify: {auto_emitted} auto-derived procs; "
          f"{len([u for u in unmatched if u not in covered])} unmatched: "
          f"{[u for u in unmatched if u not in covered]}")

    parts.append("{ ---- Select-all exclusivity (soft warning — F2-benchmark deferred item) ---- }")
    excl_emitted = excl_skipped = 0
    for field, proc in sorted(select_all_exclusive_warning_procs(dcf_items_full()[0]).items()):
        if field in covered:
            excl_skipped += 1
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")
        excl_emitted += 1
    print(f"  select-all exclusivity: {excl_emitted} soft-warning procs"
          + (f" ({excl_skipped} skipped — last flag already owns a proc)" if excl_skipped else ""))

    parts.append(TODO_NOTE)

    text = "\n".join(parts).rstrip() + "\n"
    OUT.write_text(text, encoding="utf-8")
    n_procs = text.count("\nPROC ") + text.startswith("PROC ")
    print(f"Wrote {OUT} ({len(text)} chars, ~{n_procs} PROC blocks).")
    print("  NEXT: open in CSPro Designer, compile (Build > Compile), fix any")
    print("  item-name mismatches at the source tables in generate_apc.py, then")
    print("  verify the skip/validation flow in CSEntry (issues stay 'pending-verify').")


if __name__ == "__main__":
    main()
