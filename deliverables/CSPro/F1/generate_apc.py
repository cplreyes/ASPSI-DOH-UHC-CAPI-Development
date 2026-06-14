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


def uhc9_other_specify_procs(names, no_other_skip_targets=None):
    """#148: enforce 'Other (specify)' text on UHC9 dual-other items.
    `<FIELD>_YES_OTHER_TXT` (parent code 4) and `<FIELD>_NO_OTHER_TXT` (code 7),
    per spec 4.13. Parent = the name minus the suffix (dcf is the truth — spec
    used shortened names like Q12_YES_OTHER_TXT).

    #376 data-loss fix: for a `_NO_OTHER_TXT` box whose parent owns a No-branch
    skip whose range originally swallowed code 7 (e.g. `in 5:9`), the parent skip
    is rewritten to EXCLUDE 7 (see exclude_code7_from_skip) so code 7 falls
    through to this box. To still skip the Yes-only follow-up afterwards, the box's
    postproc ends with `skip to <target>` — supplied via `no_other_skip_targets`
    ({parent: target}). The skip runs only after a VALID entry; for any non-7 code
    the box is `noinput`'d in preproc, and a noinput'd field never executes its
    postproc (CSPro semantic), so the trailing skip never fires for non-7 codes.
    """
    no_other_skip_targets = no_other_skip_targets or {}
    procs = {}
    for n in names:
        for suffix, code, lbl in (("_YES_OTHER_TXT", 4, "Yes, other reason"),
                                  ("_NO_OTHER_TXT", 7, "No, other reason")):
            if n.endswith(suffix):
                parent = n[: -len(suffix)]
                # #376: tail skip past the Yes-only follow-up for the No-other path
                tail = ""
                target = no_other_skip_targets.get(parent)
                if suffix == "_NO_OTHER_TXT" and target:
                    tail = (
                        f"\n  {{ #376: after the No-other text is entered, still skip the\n"
                        f"     Yes-only follow-up — code 7 was excluded from {parent}'s parent\n"
                        f"     skip so it reaches this box; runs only on a valid (code-7) entry,\n"
                        f"     since a noinput'd field never runs its postproc. }}\n"
                        f"  skip to {target};"
                    )
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
                    f"{tail}"
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
    # 4.9 Q121 "select all that apply" DOH-licensing-difficulty (Section F). #385.
    # CONFIRMED against the authoritative printed questionnaire (Filipino v2.1.1
    # Apr30, option order = dcf _O## order): the dcf models Q121 as 14 binary option
    # fields (_O01..O14), so facility-type option visibility is a PER-OPTION gate,
    # not a setvalueset on a single field — there is NO single Q121 field to retarget
    # (Q121_DYNAMIC_VALUE_SET = False in generate_dcf.py is therefore moot, not a gap).
    # Printed per-option tags:
    #   O10 "National laws and DOH issuances…"  hospital-only
    #   O11 "Emergency cart contents"           hospital-only
    #   O12 "Add-on services"                   hospital-only
    #   O13 "Public access to price information" primary-care-only
    #   O14 "None of the above"                 -> skip the why-difficult cluster to Q135
    # O01..O09 are universal. Q8_SERVICE_LEVEL=1 is Primary Care Facility; 2/3/4 are
    # hospitals. The `noinput` gate IS the safety net the spec asked for: a hidden
    # option can't be ticked, so no out-of-scope data is captured for the wrong tier.
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

# --- Check Box multi-select redesign (GH #377/#378/#379, mirrors F3 Q148) -----
# Q49/Q50/Q53/Q58 are now ONE alpha field each holding the ticked option codes
# concatenated left-to-right (CSEntry Check Box capture), so the old 20-ish Yes/No
# _O## flags are GONE. The dcf-derived auto-gens used to drive these:
#   * auto_other_specify_procs() gated <PREFIX>_OTHER_TXT on <PREFIX>_O## <> 1
#     (the 'Other' flag) — that flag no longer exists, so the gate is hand-written
#     here on `pos("99", <PREFIX>) = 0` instead (no valid code starts with 9, so a
#     pos() membership test can't false-match across code boundaries).
#   * select_all_exclusive_warning_procs() emitted the exclusive-option soft-warn on
#     the last _O## flag — also gone; the exclusivity warn is hand-written here on a
#     pos() check of the exclusive code ("I don't know").
# Keying each PROC by its field name seeds `covered` (= set(BESPOKE_PROCS)), so both
# auto-gens SKIP these fields and never mis-fire on the alpha checkbox / its text.
# 'Other' = 99 in all four (set in generate_dcf.py); the exclusive 'I don't know'
# code is 09 (Q49/Q50/Q53) / 07 (Q58).
CHECKBOX_MULTISELECT_PROCS = {
    "Q49_QUALITY_CHALL": """\
PROC Q49_QUALITY_CHALL
postproc
  if length(strip(Q49_QUALITY_CHALL)) = 0 then
    errmsg("Select at least one option for Q49 before continuing.");
    reenter;
  endif;
  { exclusivity (soft warn): 'I don't know' (09) should stand alone }
  if pos("09", Q49_QUALITY_CHALL) > 0 and length(strip(Q49_QUALITY_CHALL)) > 2 then
    errmsg("Q49: 'I don't know' is usually the only choice — please review the options ticked.");
  endif;""",
    "Q49_QUALITY_CHALL_OTHER_TXT": """\
PROC Q49_QUALITY_CHALL_OTHER_TXT
preproc
  if pos("99", Q49_QUALITY_CHALL) = 0 then
    Q49_QUALITY_CHALL_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q49_QUALITY_CHALL) > 0 and length(strip(Q49_QUALITY_CHALL_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q49 — please specify.");
    reenter;
  endif;""",
    "Q50_ACCESS_CHALL": """\
PROC Q50_ACCESS_CHALL
postproc
  if length(strip(Q50_ACCESS_CHALL)) = 0 then
    errmsg("Select at least one option for Q50 before continuing.");
    reenter;
  endif;
  { exclusivity (soft warn): 'I don't know' (09) should stand alone }
  if pos("09", Q50_ACCESS_CHALL) > 0 and length(strip(Q50_ACCESS_CHALL)) > 2 then
    errmsg("Q50: 'I don't know' is usually the only choice — please review the options ticked.");
  endif;""",
    "Q50_ACCESS_CHALL_OTHER_TXT": """\
PROC Q50_ACCESS_CHALL_OTHER_TXT
preproc
  if pos("99", Q50_ACCESS_CHALL) = 0 then
    Q50_ACCESS_CHALL_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q50_ACCESS_CHALL) > 0 and length(strip(Q50_ACCESS_CHALL_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q50 — please specify.");
    reenter;
  endif;""",
    "Q53_YK_PACKAGE": """\
PROC Q53_YK_PACKAGE
postproc
  if length(strip(Q53_YK_PACKAGE)) = 0 then
    errmsg("Select at least one option for Q53 before continuing.");
    reenter;
  endif;
  { exclusivity (soft warn): 'I don't know' (09) should stand alone }
  if pos("09", Q53_YK_PACKAGE) > 0 and length(strip(Q53_YK_PACKAGE)) > 2 then
    errmsg("Q53: 'I don't know' is usually the only choice — please review the options ticked.");
  endif;""",
    "Q53_YK_PACKAGE_OTHER_TXT": """\
PROC Q53_YK_PACKAGE_OTHER_TXT
preproc
  if pos("99", Q53_YK_PACKAGE) = 0 then
    Q53_YK_PACKAGE_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q53_YK_PACKAGE) > 0 and length(strip(Q53_YK_PACKAGE_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q53 — please specify.");
    reenter;
  endif;""",
    "Q58_PERF_INDICATORS": """\
PROC Q58_PERF_INDICATORS
postproc
  if length(strip(Q58_PERF_INDICATORS)) = 0 then
    errmsg("Select at least one option for Q58 before continuing.");
    reenter;
  endif;
  { exclusivity (soft warn): 'I don't know' (07) should stand alone }
  if pos("07", Q58_PERF_INDICATORS) > 0 and length(strip(Q58_PERF_INDICATORS)) > 2 then
    errmsg("Q58: 'I don't know' is usually the only choice — please review the options ticked.");
  endif;""",
    "Q58_PERF_INDICATORS_OTHER_TXT": """\
PROC Q58_PERF_INDICATORS_OTHER_TXT
preproc
  if pos("99", Q58_PERF_INDICATORS) = 0 then
    Q58_PERF_INDICATORS_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q58_PERF_INDICATORS) > 0 and length(strip(Q58_PERF_INDICATORS_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q58 — please specify.");
    reenter;
  endif;""",
}
BESPOKE_PROCS.update(CHECKBOX_MULTISELECT_PROCS)

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
    # Section D: reverse gate on the not-accredited block (GH #380). The Q51
    # master gate sends Q51=2 (No / not-accredited) -> Q79 (skipping the
    # accredited block Q52-Q78); Q51=1 (Yes) flows THROUGH Q52-Q78. But the
    # accredited block had no reverse skip, so after it ends (Q78) an accredited
    # facility fell straight into the not-accredited block Q79-Q84 (manifests for
    # Q51=Yes AND Q77=Yes: Q77=No already skips to Q85, Q77=Yes -> Q78 -> Q79).
    # Spec §4 is explicit: "Q79-Q84: Only entered if Q51 = No" / "If Q51 = Yes, no
    # answers should be present for Q79-Q84 (HARD)". Gate the FIRST not-accredited
    # field: bounce anyone who is NOT not-accredited (Q51 <> 2 — accredited Q51=1
    # plus any DK/other fall-through) past the whole Q79-Q84 block to Q85. The
    # legit Q51=2 path lands here via the Q51 postproc skip, sees Q51<>2 == false,
    # stays and answers Q79. Q85_CATCHMENT_AREA is the same resume point Q77=No uses.
    "Q79_NOT_ACCRED_REASON_O01": """\
PROC Q79_NOT_ACCRED_REASON_O01
preproc
  if Q51_YK_ACCRED <> 2 then   { Q79-Q84 only for not-accredited (Q51=No); accredited fall-through -> Q85 }
    skip to Q85_CATCHMENT_AREA;
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
    # Section D: Q90 costing-viable routes by its OWN answer (#381). Printed Q90
    # has NO Q51 dependency: Yes(1)/Don't-know(3) -> Q93; No(2) -> Q91. (The old
    # PROC gated each branch on a matching Q51 code, so an accredited "No" or a
    # non-accredited "Yes" fell through with no skip — wrong per the questionnaire.)
    "Q90_COSTING_VIABLE": """\
PROC Q90_COSTING_VIABLE
postproc
  if Q90_COSTING_VIABLE = 2 then     skip to Q91_MIN_CAP_VALUE_ACC; endif;  { No -> Q91 }
  if Q90_COSTING_VIABLE in 1,3 then  skip to Q93_CHARGE_ADDL_CAP;   endif;  { Yes / Don't know -> Q93 }""",
    # Section D master gate (#383): the costing block splits by accreditation.
    # Printed: "Q85 to Q91; Q93 to Q100 are only relevant to YAKAP-accredited,
    # otherwise proceed to Q101" + "Q92 is only relevant to not-accredited."
    #   - Accredited (Q51=1): answer Q85-Q91, SKIP Q92, answer Q93-Q100 -> Q101.
    #   - Not-accredited (Q51=2): Q84 -> SKIP Q85-Q91 -> answer Q92 -> SKIP Q93-Q100 -> Q101.
    # Q85 first-field preproc: a not-accredited respondent jumps the whole accredited
    # costing block straight to Q92. (An accredited respondent stays and answers Q85.)
    "Q85_CATCHMENT_AREA": """\
PROC Q85_CATCHMENT_AREA
preproc
  if Q51_YK_ACCRED = 2 then   { not-accredited: skip the accredited costing block Q85-Q91 -> Q92 }
    skip to Q92_MIN_CAP_VALUE_NONACC;
  endif;""",
    # Q92 (#383): only the not-accredited reach it as a question; accredited respondents
    # arrive here via fall-through from the Q85-Q91 block and must SKIP it. preproc bounces
    # accredited past Q92 to Q93; postproc sends the not-accredited (who answered Q92) past
    # the entire Q93-Q100 accredited block to Section E (Q101).
    "Q92_MIN_CAP_VALUE_NONACC": """\
PROC Q92_MIN_CAP_VALUE_NONACC
preproc
  if Q51_YK_ACCRED <> 2 then   { accredited (or any non-2): Q92 is not for them -> Q93 }
    skip to Q93_CHARGE_ADDL_CAP;
  endif;
postproc
  { not-accredited finished Q92 -> skip the accredited block Q93-Q100, go to Section E }
  skip to Q101_HEARD_BUCAS;""",
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
preproc
  { #384: Q116/Q117 only if heard GAMOT (Q108=Yes) AND accredited (Q109=Yes) AND had a
    stockout (Q112=Yes) — spec 3.6 GATE. Otherwise skip both to Q118. }
  if not (Q108_HEARD_GAMOT = 1 and Q109_GAMOT_ACCRED = 1 and Q112_STOCKOUT = 1) then
    skip to Q118_DOH_LICENSED;
  endif;
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
    # Section G: Q152 protocol clarity. #386: printed Q152 is "only for respondents
    # from public hospitals" — public hospital = Q7_OWNERSHIP=1 (Public) AND
    # Q8_SERVICE_LEVEL in 2,3,4 (Level 1/2/3 Hospital; Q8=1 is a Primary Care
    # Facility). preproc gates ENTRY: any non-public-hospital skips both Q152 and its
    # follow-up Q153 to Q154. postproc keeps the clarity routing (Very Clear/Clear
    # need no "which protocol unclear" detail -> skip Q153 -> Q154).
    "Q152_PHO_PROTOCOL_CLARITY": """\
PROC Q152_PHO_PROTOCOL_CLARITY
preproc
  if not (Q7_OWNERSHIP = 1 and Q8_SERVICE_LEVEL in 2,3,4) then
    skip to Q154_NUM_REFERRED_OUT;   { Q152/Q153 only for public hospitals }
  endif;
postproc
  if Q152_PHO_PROTOCOL_CLARITY in 1,2 then   { Very Clear / Clear -> skip Q153 detail }
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


def _skip_codes_for(field, cond):
    """The set of parent codes that satisfy `cond` for `field`, for the simple
    SKIP_RULES forms used here: `FIELD in lo:hi`, `FIELD in a,b,c`, `FIELD = N`,
    `FIELD <> N`, and `or`-joined combinations of those (e.g. Q31's
    `FIELD in 5:8 or FIELD = 9`). Returns None if the condition isn't one of these
    recognized shapes (so callers leave it untouched rather than guess)."""
    codes, ok = set(), True
    for clause in re.split(r"\s+or\s+", cond.strip()):
        c = clause.strip()
        m = re.fullmatch(rf"{re.escape(field)}\s+in\s+(\d+)\s*:\s*(\d+)", c)
        if m:
            codes |= set(range(int(m.group(1)), int(m.group(2)) + 1)); continue
        m = re.fullmatch(rf"{re.escape(field)}\s+in\s+([\d,\s]+)", c)
        if m:
            codes |= {int(x) for x in re.findall(r"\d+", m.group(1))}; continue
        m = re.fullmatch(rf"{re.escape(field)}\s*=\s*(\d+)", c)
        if m:
            codes.add(int(m.group(1))); continue
        # `<>` and anything else: not a positive-membership clause we can reason
        # about for "does code 7 get swallowed" — bail and leave the rule alone.
        ok = False
    return codes if ok else None


def exclude_code7_from_skip(field, cond):
    """Rewrite a No-branch skip condition so code 7 (No-other) falls THROUGH
    instead of being swallowed (#376). Re-emits the surviving codes as a single
    `FIELD in a,b,...` membership (e.g. `in 5:9` -> `in 5,6,8,9`; Q31's
    `in 5:8 or = 9` -> `in 5,6,8,9`). Returns the new condition, or the original
    unchanged if 7 isn't in the skip set or the form isn't recognized."""
    codes = _skip_codes_for(field, cond)
    if codes is None or 7 not in codes:
        return cond
    survivors = sorted(codes - {7})
    return f"{field} in {','.join(str(c) for c in survivors)}"


def dual_other_no_skip_map(skip_rules, dcf_names):
    """{parent: target} for every SKIP_RULES row that (a) has a `_NO_OTHER_TXT`
    box in the dcf and (b) whose No-branch skip range originally swallowed code 7.
    Drives BOTH the parent-skip rewrite (exclude 7) AND the trailing `skip to
    <target>` appended to the NO_OTHER box, so the two stay in lockstep (#376)."""
    have = set(dcf_names)
    out = {}
    for field, cond, target in skip_rules:
        if f"{field}_NO_OTHER_TXT" not in have:
            continue
        codes = _skip_codes_for(field, cond)
        if codes is not None and 7 in codes:
            out[field] = target
    return out


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

    # dcf-driven names read up-front so the #376 dual-other map can be built
    # before we emit the skip PROCs (the map drives the skip rewrite too).
    names = dcf_item_names()

    # #376 (GH F1 Section C): the No-branch skip for an "implementation status"
    # question swallowed code 7 ("No, other reason (specify)"), jumping over its
    # `_NO_OTHER_TXT` box -> the other-reason text was never collected (data loss).
    # Build {parent: target} for every such question (has a NO_OTHER box AND its
    # skip range includes 7); use it to (1) exclude 7 from the parent skip and
    # (2) append `skip to <target>` to the NO_OTHER box so the Yes-only follow-up
    # is still skipped after the other-reason text is entered.
    dual_other_skips = dual_other_no_skip_map(SKIP_RULES, names)

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
        # #376: drop code 7 from the No-branch range so No-other reaches its box
        cond = exclude_code7_from_skip(field, cond) if field in dual_other_skips else cond
        parts.append(skip_proc(field, cond, target))
        parts.append("")

    parts.append("{ ---- Why-difficult display gates (spec 4.10) ---- }")
    for field, proc in sorted(why_difficult_gate_procs(names).items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — UHC9 dual-other items (spec 4.13) ---- }")
    for field, proc in sorted(uhc9_other_specify_procs(names, dual_other_skips).items()):
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
