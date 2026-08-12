#!/usr/bin/env python3
"""
F4 Household Survey — CAPI logic (.ent.apc) generator.

Emits `HouseholdSurvey.ent.apc` from the reviewed spec
(`F4-Skip-Logic-and-Validations.md`). Same pattern as F1/F3 generate_apc.py.

Covers (generator side): roster loop + per-member skips, #168 roster-count vs
Q19, #167 first-member/cross-member SOFT check, Q47 auto-set, awareness skips
(D-F), Section I primary-care routing, #170 Section M bill-recall chain (gated
on Q129), #169 Section N expenditure consumed-gate (dcf-driven, all *_CONSUMED
items), consent terminator, GPS + photo, UHC9 'Other (specify)'.

  ⚠️  UNVERIFIED until compiled in CSPro Designer + run in CSEntry. Roster /
      occurrence logic (curocc/endocc/count) and skip targets especially need
      CSEntry verification against the generated FMF. Option codes marked
      "(verify)" must be checked against the dcf value sets on first compile.

Invoke:  python generate_apc.py
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    other_specify_procs, select_all_validation_procs, range_check_proc,
    numberize_errmsgs,
)
from generate_dcf import (   # roster ladders (same dir) — single source with the dcf occ labels
    FOOD_WEEKLY_ITEMS, NONFOOD_1M_ITEMS, NONFOOD_6M_ITEMS, NONFOOD_12M_ITEMS,
    HEALTH_12M_ITEMS, HEALTH_6M_ITEMS, HEALTH_1M_ITEMS, WEEKLY_OTHER_ITEMS, DK_RF_STATUS,
)

# Per-item numeric range checks (spec §3.2/§3.6/§3.12). (field, lo, hi, soft_over)
RANGE_CHECKS = [
    ("Q18_INCOME_AMOUNT",      0, 99999999, None),
    # #572: Q67 single HHMM field split into separate Hours + Minutes boxes
    # (mirrors F3 Q69_USUAL_TRAVEL_HH/MM range checks).
    ("Q67_TRAVEL_HH",          0, 24,       None),
    ("Q67_TRAVEL_MM",          0, 59,       None),
    ("TOTAL_NUMBER_OF_VISITS", 1, 10,       3),
    # Range.docx (Aly, 2026-07-08): Q95 0-999 / Q96 0-99,999. Width caps both maxima;
    # these checks block stray negatives (CSEntry accepts a typed minus, #743 class).
    ("Q95_TRAVEL_TIME_MIN",    0, 999,      None),
    ("Q96_TRAVEL_COST_PHP",    0, 99999,    None),
    ("Q199_WTP_CONSULT",       0, 99999999, None),
]

# Cross-field validations needing a custom body (spec §3.1 date ordering).
CUSTOM_VALIDATION = [
    # #1132 (2026-08-11): the #1099 DATE_*_DISP echo PROCs are removed with their
    # dictionary items and form fields at ASPSI's request — see generate_dcf.py.
    # #1132/#1174 parity (2026-08-11): the enumerator types MMDDYYYY like the paper;
    # the STORED value stays YYYYMMDD (Supervisor App + cross-instrument parsers
    # untouched). Idempotent: a stored YYYYMMDD starts with the century (20), not a
    # valid month, so the conversion branch cannot fire twice. Ported verbatim from
    # F3's #1174 block. The final-visit check also gains the notappl guards F3 got
    # in v1.4.1 — F4 still had the unguarded compare, so a blank final date
    # (single-visit case) could false-fire the error here too.
    ("DATE_FIRST_VISITED",
     "PROC DATE_FIRST_VISITED\npostproc\n"
     "  numeric fvMM; numeric fvDD; numeric fvYY; numeric fvHead;\n"
     "  if DATE_FIRST_VISITED <> notappl then\n"
     "    fvMM   = int(DATE_FIRST_VISITED / 1000000);\n"
     "    fvHead = int(DATE_FIRST_VISITED / 10000);\n"
     "    if fvMM >= 1 and fvMM <= 12 then\n"
     "      fvDD = fvHead - fvMM * 100;\n"
     "      fvYY = DATE_FIRST_VISITED - fvHead * 10000;\n"
     "      if fvDD < 1 or fvDD > 31 or fvYY < 2020 or fvYY > 2035 then\n"
     "        errmsg(\"Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.\");\n"
     "        reenter;\n"
     "      endif;\n"
     "      DATE_FIRST_VISITED = fvYY * 10000 + fvMM * 100 + fvDD;\n"
     "    else\n"
     "      if fvHead < 2020 or fvHead > 2035 then\n"
     "        errmsg(\"Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.\");\n"
     "        reenter;\n"
     "      endif;\n"
     "    endif;\n"
     "  endif;"),
    ("DATE_FINAL_VISIT",
     "PROC DATE_FINAL_VISIT\npostproc\n"
     "  numeric lvMM; numeric lvDD; numeric lvYY; numeric lvHead;\n"
     "  if DATE_FINAL_VISIT <> notappl then\n"
     "    lvMM   = int(DATE_FINAL_VISIT / 1000000);\n"
     "    lvHead = int(DATE_FINAL_VISIT / 10000);\n"
     "    if lvMM >= 1 and lvMM <= 12 then\n"
     "      lvDD = lvHead - lvMM * 100;\n"
     "      lvYY = DATE_FINAL_VISIT - lvHead * 10000;\n"
     "      if lvDD < 1 or lvDD > 31 or lvYY < 2020 or lvYY > 2035 then\n"
     "        errmsg(\"Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.\");\n"
     "        reenter;\n"
     "      endif;\n"
     "      DATE_FINAL_VISIT = lvYY * 10000 + lvMM * 100 + lvDD;\n"
     "    else\n"
     "      if lvHead < 2020 or lvHead > 2035 then\n"
     "        errmsg(\"Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.\");\n"
     "        reenter;\n"
     "      endif;\n"
     "    endif;\n"
     "  endif;\n"
     "  { conversion above runs FIRST so both sides below are YYYYMMDD. The notappl guards\n"
     "    match F1/F3: without them a blank final date (single visit) false-fires this. }\n"
     "  if DATE_FINAL_VISIT <> notappl and DATE_FIRST_VISITED <> notappl and DATE_FINAL_VISIT < DATE_FIRST_VISITED then\n"
     "    errmsg(\"Final-visit date cannot be earlier than the first-visit date.\");\n    reenter;\n  endif;"),
    # #699/#701 (Carl, 2026-06-18 — "do what the testers said"): the Q138 confinement gate
    # (#625/#626: Q129 <> Yes -> skip Q138-143 to Q144) is REMOVED. Q138 reads "from your most
    # recent VISIT, which charge was most expensive?" — testers expect Q138-Q143 to follow Q136/
    # Q137 for everyone, not only confined HHs. The internal block gates (Q140=No -> Q142,
    # Q142=No -> Q144) still apply. (If this should be reinstated for non-confined HHs, restore
    # the Q138_MOST_EXPENSIVE preproc skip-on-Q129<>1.)
    # #644: Q73 (GAMOT meds list) is REQUIRED when reached. Spec F4-Skip-Logic-and-
    # Validations.md line 408: "Required when enabled, non-blank; HARD". Q73 is only
    # reached when Q72=Yes (Q72=No skips Q73 -> Q74), so a plain non-blank postproc check
    # is sufficient — if blank, errmsg + reenter.
    ("Q73_GAMOT_MEDS_LIST",
     "PROC Q73_GAMOT_MEDS_LIST\npostproc\n"
     "  if length(strip(Q73_GAMOT_MEDS_LIST)) = 0 then\n"
     "    errmsg(\"Q72 says medicines were obtained from the GAMOT Package. Please list at least one medicine in Q73 before continuing.\");\n"
     "    reenter;\n  endif;"),
]

HERE = Path(__file__).parent
OUT = HERE / "HouseholdSurvey.ent.apc"
DCF = HERE / "HouseholdSurvey.dcf"
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


HEADER = """\
{ ============================================================================
  HouseholdSurvey (F4) — CAPI logic   (AUTOGENERATED by generate_apc.py)
  Do NOT hand-edit: edit generate_apc.py's tables and rerun.
  Spec: F4-Skip-Logic-and-Validations.md (reviewed 2026-04-21).
  ============================================================================ }

PROC GLOBAL
numeric currentYYYYMMDD;
{ Single-number redesign (2026-06-11): the questionnaire number's first 7 digits
  are a POSITIONAL slice of the 10-digit PSA PSGC - validated hierarchically
  (region exact -> region's provinces -> each province's cities). }
numeric regionFull;
numeric geoFull;
numeric geoFound;
numeric currentYear;
numeric currentMonth;

{ Shared helpers inlined into this single PROC GLOBAL (PSGC-Cascade first so its
  ROOT_PSGC_PARENT declaration precedes all functions). #include can't be used:
  CSPro forbids it inside a PROC, and CSEntry forbids code before the first PROC.
  Requires the 4 PSGC external dicts attached to the .ent. }
""" + _inline_shared("PSGC-Cascade.apc") + """

""" + _inline_shared("Capture-Helpers.apc") + """

PROC HOUSEHOLDSURVEY_FF
preproc
  currentYYYYMMDD = sysdate("YYYYMMDD");
  currentYear  = int(currentYYYYMMDD / 10000);
  currentMonth = int(currentYYYYMMDD / 100) % 100;

{ LANGUAGE_USED is captured in the QUESTIONNAIRE_NUMBER postproc (case key, the
  very first field) — see PROC QUESTIONNAIRE_NUMBER below. (Was on SURVEY_CODE,
  then INTERVIEWER_ID; both removed 2026-06-12 — consolidated to the id postproc.) }
"""

CONTROL_PROCS = """\
{ Informed consent: the separate CONSENT_GIVEN field was removed 2026-06-12.
  Consent refusal is now recorded as the Result-of-Visit disposition
  ("Withdraw Participation/Consent" = code 4); the read-aloud consent script is
  read from the printed sheet (off the CAPI). No consent gate PROC. }

{ ---- Single 12-digit Questionnaire Number (redesign 2026-06-11; mirrors F1) ----
  Parse the number into the component codes (FIELD_CONTROL items - downstream
  PROCs keep working), validate the 7-digit geo prefix hierarchically against
  the PSGC dicts, fill the read-only *_NAME items, and set the full PSGC codes
  on the off-form geo items so the BARANGAY cascade filters correctly. ---- }
PROC QUESTIONNAIRE_NUMBER
preproc
  { GPS warm-start (2026-07-19): open the radio while the enumerator types the
    case key so the fix has converged by the HH GPS capture on the geo form —
    the read is then near-instant instead of a cold acquisition. Desktop no-op. }
  WarmUpGPS();
postproc
  LANGUAGE_USED = getlanguage();   { record interview language at case start (§15.E) }
  if not (CASE_DISPOSITION in 1, 2) then
    CASE_DISPOSITION = 0;   { #561: mark In Progress at case open; a force-quit case keeps 0 }
  endif;
  REGION_CODE            = int(QUESTIONNAIRE_NUMBER / 10000000000);
  PROVINCE_HUC_CODE      = int(QUESTIONNAIRE_NUMBER / 100000000) % 100;
  CITY_MUNICIPALITY_CODE = int(QUESTIONNAIRE_NUMBER / 100000) % 1000;
  FACILITY_NO            = int(QUESTIONNAIRE_NUMBER / 1000) % 100;
  CASE_SEQ               = QUESTIONNAIRE_NUMBER % 1000;

  regionFull = REGION_CODE * 100000000;
  geoFull    = int(QUESTIONNAIRE_NUMBER / 100000) * 1000;
  REGION     = regionFull;

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

  geoFound = 0;
  P_PARENT_REGION = regionFull;
  if loadcase(PSGC_PROVINCE_DICT, P_PARENT_REGION) <> 0 then
    do varying numeric pi = 1 until pi > count(PSGC_PROVINCE_DICT.PSGC_PROVINCE_REC) or geoFound = 1
      if P_CODE(pi) = geoFull then
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

  protect(REGION_NAME, true);
  protect(PROVINCE_NAME, true);
  protect(CITY_NAME, true);

{ ---- Barangay picker (household geo): region/province/city derived from the
  Questionnaire Number (off-form); only barangay picked, filtered by the
  derived city/province code. ---- }
PROC BARANGAY
onfocus
  FillBarangayValueSet(CITY_MUNICIPALITY);

{ ---- GPS — AUTO-FETCHED on focus (2026-06-12; no manual trigger). F4 captures
  the HOUSEHOLD location into LATITUDE/LONGITUDE + HH_GPS_* (not the F1 FACILITY_*
  names). Captured once (guarded on read-time), then all GPS fields protected
  (read-only). Desktop (getos 10-19) has no GPS radio → blank there (device-only). ---- }
PROC LATITUDE
onfocus
  if length(strip(HH_GPS_READTIME)) = 0 then   { capture once; not on back-nav }
    { 15 s budget: the radio has been warm since the case key (WarmUpGPS), so a
      fresh fix normally arrives in ~1-2 s; 15 s only caps the no-signal case. }
    if ReadGPSReading(15, 20) then
      LATITUDE          = maketext("%f", gps(latitude));
      LONGITUDE         = maketext("%f", gps(longitude));
      HH_GPS_ALTITUDE   = maketext("%f", gps(altitude));
      HH_GPS_ACCURACY   = gps(accuracy);
      HH_GPS_SATELLITES = gps(satellites);
      HH_GPS_READTIME   = maketext("%d", gps(readtime));
    endif;
  endif;
  { Protect ONLY once captured — protecting a blank numeric (no fix / desktop)
    triggers "protected field is out of range - value is NOTAPPL". }
  if length(strip(HH_GPS_READTIME)) > 0 then
    protect(LATITUDE, true);
    protect(LONGITUDE, true);
    protect(HH_GPS_ALTITUDE, true);
    protect(HH_GPS_ACCURACY, true);
    protect(HH_GPS_SATELLITES, true);
    protect(HH_GPS_READTIME, true);
    ReleaseGPS();   { F4's only GPS block — close the radio once captured }
  endif;

{ ---- #231 Verification photo (moved to the END of the form 2026-06-12). CONDITIONAL on
  the visit outcome and soft-validated (warn, don't trap, on camera failure). ---- }
PROC VERIFICATION_PHOTO_FILENAME
preproc
  { display-only — the camera trigger fills this; it is never typed }
  noinput;

PROC CAPTURE_VERIFICATION_PHOTO
preproc
  { gate: photograph only visits where an interview occurred (1 Completed,
    3 Incomplete); skip 2 Postponed / 4 Withdraw Participation/Consent }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 3) then
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
"""

# Roster loop (spec 4.5): per-member skips + #167 first-member soft check +
# #168 roster-count = Q19 + Q47 auto-set from any member's private insurance.
ROSTER_PROCS = """\
{ ---- Household roster loop (C_HOUSEHOLD_ROSTER, max 20) ---- }
PROC MEMBER_LINE_NO
preproc
  { Auto-end the roster once the declared household size (Q19) is reached --
    without this, entry rolls into member N+1 and the enumerator must know to
    end the group manually. Also auto-fill the line number from the occurrence.
    Column-wise Section C (2026-06-26): the occurrence-establishing first roster form
    carries Q30_NAME + Q31_PRESENT (a coded auto-advancing field) so the member set is
    COMMITTED before the per-question column-wise forms — a name-ONLY first form loses
    occurrences 2+ on exit (CSEntry discards the dynamically-built tail of a single-
    enterable-field roster; proven on desktop CSEntry). All other Section C questions are
    one-per-form (each asked for every member before the next). }
  if curocc() > Q19_HH_SIZE_TOTAL then
    endgroup;
  endif;
  MEMBER_LINE_NO = curocc();
  noinput;

PROC Q34_RELATIONSHIP
postproc
  { #167: first roster entry is normally Self/Head (soft confirm) }
  if curocc() = 1 and not (Q34_RELATIONSHIP in 1,2) then   { 1=Self, 2=Head (verify codes) }
    errmsg("First roster entry is normally the respondent (Self) or HH head. Confirm.");
  endif;

{ Section C renders COLUMN-WISE (one roster form per question — the "Household
  Characteristic Target Interface", spike-validated 2026-06-26): CSEntry asks each question
  for ALL members before the next. Intra-member conditionality can no longer be a
  `skip to <field>` (the target now lives on a DIFFERENT roster form), so each conditional
  question carries a PER-OCCURRENCE preproc gate `if <not-applicable> then skip to next` that
  skips THIS member on THAT question's screen and advances to the next occurrence (the proven
  Q45.2 gate / Q32 spike pattern). Q35 (disability?) and Q45 (PhilHealth registered?) are
  asked of every member, so they no longer route — their old forward-skips moved DOWNSTREAM
  onto Q36/Q37/Q38 (disability detail) and Q45.1/Q46/Q45.2 (PhilHealth detail). The specify
  free-text (Q38/Q46/Q45.2 _OTHER_TXT) keeps its auto-derived noinput gate, which already
  skips non-'Other' occurrences correctly on its own single-field roster form. }

PROC Q36_SPECIFY_DISABILITY
preproc
  { Asked only for members who identify as having a disability (Q35 = Yes=1). }
  if Q35_HAS_DISABILITY = 0 then skip to next; endif;

PROC Q37_PWD_CARD
preproc
  { #604: card view asked only when the member wants to specify the disability
    (Q35 = Yes AND Q36 = Yes). The Q35 guard catches members whose Q36 was skipped
    (notappl) upstream. }
  if Q35_HAS_DISABILITY = 0 or Q36_SPECIFY_DISABILITY = 0 then skip to next; endif;

PROC Q38_DISABILITY_TYPE
preproc
  { #605: Q38 reads the *presented* PWD card, so ask only when the card was shown
    (Q35=Yes AND Q36=Yes AND Q37=Yes/1). Q37 <> 1 also covers No/Refused and the notappl
    members the upstream gates skipped. }
  if Q35_HAS_DISABILITY = 0 or Q36_SPECIFY_DISABILITY = 0 or Q37_PWD_CARD <> 1 then
    skip to next;
  endif;

PROC Q45_1_PIN_REG_WHEN
preproc
  { #563/#565: PIN-registration timing is Yes-only (Q45 = registered = 1). No/IDK members
    are skipped on this screen. }
  if Q45_PHILHEALTH_REG <> 1 then skip to next; endif;

PROC Q46_MEMBER_CATEGORY
preproc
  { #563: membership category is Yes-only (Q45 = registered = 1). }
  if Q45_PHILHEALTH_REG <> 1 then skip to next; endif;

PROC Q45_2_WHY_NOT_REG
preproc
  { #795: 'why not registered' is No-only (Q45 = No = 2). Yes/IDK members are skipped on this
    screen. The Other(88) specify text is gated by the auto-derived
    Q45_2_WHY_NOT_REG_OTHER_TXT PROC (noinput when <> 88). }
  if Q45_PHILHEALTH_REG <> 2 then skip to next; endif;

PROC Q49_PRIVATE_INS
postproc
  if Q49_PRIVATE_INS = 2 then        { no private insurance -> skip Q50, advance to next member }
    skip to next;                    { 'next' = next C_PRIVATE_INS_ROSTER occurrence }
  endif;

PROC C_HOUSEHOLD_ROSTER_FORM
postproc
  { #168 roster-count sanity (spec finding #7). Attached to the roster GROUP
    (C_HOUSEHOLD_ROSTER_FORM), NOT the C_HOUSEHOLD_ROSTER record — a record symbol
    can't have a PROC (CSEntry, verified 2026-06-08). The group postproc fires once
    after all occurrences are entered. }
  if count(C_HOUSEHOLD_ROSTER) <> Q19_HH_SIZE_TOTAL then
    { soft warning: reenter is not available from a group postproc, so flag it and
      let the enumerator navigate back to fix the roster or Q19. }
    errmsg("Roster has %d members but Q19 says %d. Go back and reconcile.",
           count(C_HOUSEHOLD_ROSTER), Q19_HH_SIZE_TOTAL);
  endif;

PROC Q47_HH_HAS_PRIVATE_INS
postproc
  { #612 (Carl go/no-go 2026-06-20): Q47 is the HH-level gate for the Q48-Q50 private-
    insurance block, which now runs AFTER this gate as a separate per-member pass
    (C_PRIVATE_INS_ROSTER). No(2) -> no private insurance in the HH -> skip the whole
    Q48-Q50 block straight to Section D (Q51). Yes(1) -> fall through into the private-
    insurance roster. (The old preproc auto-set Q47 by looking ahead at Q49 because
    Q48-Q50 used to be entered BEFORE Q47; with Q47 asked first, that look-ahead is gone.) }
  if Q47_HH_HAS_PRIVATE_INS <> 1 then
    skip to Q51_UHC_HEARD;
  endif;
"""

# Private-insurance second-pass roster loop (C_PRIVATE_INS_ROSTER, max 20) — #525/#612/#613.
# Mirrors MEMBER_LINE_NO: auto-iterate to exactly the household-roster member count so the
# enumerator never re-adds rows (the member name is piped, not re-entered). Reached only when
# Q47 = Yes (the Q47 postproc above skips this whole record otherwise).
PRIV_ROSTER_PROCS = """\
{ ---- Private-insurance roster loop (C_PRIVATE_INS_ROSTER, max 20) ---- }
PROC PRIV_MEMBER_LINE_NO
preproc
  if curocc() > count(C_HOUSEHOLD_ROSTER) then
    endgroup;                        { auto-end at the household-roster member count }
  endif;
  PRIV_MEMBER_LINE_NO = curocc();
  noinput;

PROC Q48_OTHER_INS_REG
postproc
  { #613.2 (Carl go/no-go 2026-06-20 — tester Marriz logic): being registered with another
    health insurance plan implies coverage, so Q48 = Yes auto-sets Q49 = Yes (covered, as a
    member) and jumps to Q50 (specify which). Q48 = No / Don't-know -> ask Q49 normally
    (Yes = covered as a dependent / No = not covered). Q49's value set is Yes/No/DK (the paper
    has no member-vs-dependent split), so the 'dependent' case is captured as Q49 = Yes when
    Q48 <> Yes. }
  if Q48_OTHER_INS_REG = 1 then
    Q49_PRIVATE_INS = 1;
    skip to Q50_PRIVATE_INS_OTHER_TXT;
  endif;
"""

# R1a (2026-07-03): the hand-written PROCs lives in procs/extra_procs.apc — a real .apc fragment,
# editable/diffable as CSPro code. Spliced verbatim at generation time.
EXTRA_PROCS = (Path(__file__).resolve().parent / "procs" / "extra_procs.apc").read_text(encoding="utf-8")


# --- #529 (+#573/#574, +#577-585/#588/#590-591) multi-select conversion: the F4
# 'Household Survey' select_all bases that became single Check Box fields (mirrors F3
# generate_apc.py's CHECKBOX_CONVERT). Each base gets a select->=1 validation (hard), an
# optional exclusivity soft-warn (the standalone option coded 90 should stand alone), an
# optional preproc gate, and (when present) an 'Other (specify)' text gate on
# pos("99", base). Codes are from generate_dcf._cb_codes: real options 01.., exclusive
# 'I don't know'/'None' -> 90, 'Other (specify)' -> 99. (base, has_other, exclusive,
# preproc_gate).
#
# F4 special-case discovery (grep of every <base>_O0 reference in this file): the #529
# batch's only refs were three SKIP_RULES targets (Q85/Q93/Q94 _O01), repointed to the
# bare base. The #577+ batch adds two more skip-target repoints (Q82, Q107 _O01 -> base;
# Q105=2 chains into Q107) plus ONE gated preproc to migrate: Q78_WHY_BRANDED carried a
# `PROC Q78_WHY_BRANDED_O01` branded-only preproc (Q76 in 1,3) — its body is moved into
# the CHECKBOX_CONVERT gate param below, and the `skip to Q78_WHY_BRANDED_O01` in PROC
# Q76_BRAND_OR_GEN postproc is repointed to the bare base. All other entries gate=None.
CHECKBOX_BASES = {
    "Q52_UHC_SOURCE", "Q53_UHC_UNDERSTAND", "Q55_YAKAP_SOURCE", "Q56_YAKAP_UNDERSTAND",
    "Q58_BUCAS_SOURCE", "Q59_BUCAS_UNDERSTAND", "Q61_BUCAS_SERVICES",
    "Q65_CONDITIONS", "Q66_WHERE_BUY", "Q85_BENEFITS", "Q91_WHY_WENT",
    "Q93_WHY_NOT", "Q94_TRANSPORT", "Q113_WHY_NOT", "Q121_WHY_HOSPITAL",
    "Q70_GAMOT_SOURCE", "Q71_GAMOT_UNDERSTAND",   # #573/#574
    "Q127_NBB_SOURCE", "Q128_NBB_UNDERSTAND", "Q133_ZBB_SOURCE", "Q134_ZBB_UNDERSTAND",
    "Q137_MAIFIP_SOURCE",
    "Q141_BILL_ITEMS", "Q143_HOW_PAID",   # #615/#616 Section M bill select_all -> Check Box
    "Q196_FOREGONE",   # #638 Section O foregone-care select_all -> Check Box
    # #577-585/#588/#590-591: 10 more 'Household Survey' select_all -> Check Box (tick-all)
    "Q74_WHERE_REST", "Q77_WHY_GENERIC", "Q78_WHY_BRANDED", "Q82_DIFFICULTY_REASONS",
    "Q88_DIFF_PAYING", "Q102_VISIT_REASON", "Q103_CARE_TYPE", "Q106_FORGONE_WHY",
    "Q107_OTHER_ACTIONS", "Q109_TYPE",
    "Q202_WORRY_REASONS",   # #668 Section Q finance-worry reasons select_all -> Check Box
    "Q84_WHERE_ASSIST",   # #814: Section H where-to-seek-assistance free-text -> 10-option Check Box
}

CHECKBOX_CONVERT = [
    # base                       has_other  exclusive  preproc_gate
    ("Q52_UHC_SOURCE",           True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q53_UHC_UNDERSTAND",       True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q55_YAKAP_SOURCE",         True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q56_YAKAP_UNDERSTAND",     True,  True,  None),   # 'I don't know' (90) exclusive; #824: 'There are no benefits in the package' (05) HARD-standalone via CHECKBOX_EXTRA_STANDALONE (reverses the F3-Q46-mirror decision); 'Other (Specify)' (99)
    ("Q58_BUCAS_SOURCE",         True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q59_BUCAS_UNDERSTAND",     True,  False, None),   # no None/IDK option; 'Other (specify)' (99)
    ("Q61_BUCAS_SERVICES",       True,  True,  None),   # #570: 'I don't know' (90) exclusive; 'Other (specify)' (99)
    ("Q65_CONDITIONS",           True,  True,  None),   # #642: 'No condition - Regular check-up only' is now 90-coded exclusive (was an ordinary option, tickable alongside real conditions — tester FAIL); soft-warn if combined with others. 'Other (Specify)' (99); substantive 'Other infection' stays 01.. (see _cb_codes 'specif' fix)
    ("Q66_WHERE_BUY",            True,  False, None),   # #568: no None/IDK option; 'Other (specify)' (99)
    ("Q85_BENEFITS",             True,  True,  None),   # 'I don't know' (90) exclusive ('no benefits to being a member' stays an 01.. option, mirroring F3 Q46); 'Other (Specify)' (99)
    ("Q91_WHY_WENT",             True,  False, None),   # no None/IDK option; 'Other (Specify)' (99)
    ("Q93_WHY_NOT",              True,  True,
     "  { #624/#650: Q93 (why NO usual facility) applies when Q89=No(2) OR Q89=I-don't-know(3)\n"
     "    -- both mean no established usual facility. The Q89=Yes/Q90=No path (Q91 -> Q92)\n"
     "    falls through to here, so skip Q93 for everyone EXCEPT the Q89 No/IDK respondents. }\n"
     "  if Q89_HAS_USUAL_FACILITY <> 2 and Q89_HAS_USUAL_FACILITY <> 3 then\n"
     "    skip to Q94_TRANSPORT;\n"
     "  endif;"),                                 # 'I don't know' (90) exclusive — NOT 'I don't know where to go for care' (05); 'Other (Specify)' (99)
    ("Q94_TRANSPORT",            True,  False, None),   # no None/IDK option; 'Other (Specify)' (99)
    ("Q113_WHY_NOT",             True,  False, None),   # no None/IDK option — 'Don't know how to get to facility' (06) is substantive; 'Other (Specify)' (99)
    ("Q121_WHY_HOSPITAL",        True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q127_NBB_SOURCE",          True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q128_NBB_UNDERSTAND",      True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q133_ZBB_SOURCE",          True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q134_ZBB_UNDERSTAND",      True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q137_MAIFIP_SOURCE",       True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q70_GAMOT_SOURCE",         True,  True,  None),   # #573 'I don't know' (90); 'Other (Specify)' (99)
    ("Q71_GAMOT_UNDERSTAND",     True,  True,  None),   # #574 'I don't know' (90); 'Other (specify)' (99)
    # --- #577-585/#588/#590-591: 10 more tick-all conversions ---
    ("Q74_WHERE_REST",           True,  True,  None),   # #645: 'Not applicable' is now 90-coded exclusive (was ordinary per #585 — tester FAIL: tickable alongside real sources; N/A means none apply); soft-warn if combined. 'Other (Specify)' (99)
    ("Q77_WHY_GENERIC",          True,  True,  None),   # #578: 'I don't know' (90) exclusive; 'Not applicable' stays 01..; 'Other (Specify)' (99). Q77 asked for Generic/Both (falls through Q76 postproc) — no preproc gate
    ("Q78_WHY_BRANDED",          True,  True,
     "  if Q76_BRAND_OR_GEN <> 1 and Q76_BRAND_OR_GEN <> 3 then   { only Branded (1) or Both (3) answer why-branded }\n"
     "    skip to Q79_REG_SOURCE;\n"
     "  endif;"),                                       # #578: gate migrated from old PROC Q78_WHY_BRANDED_O01 preproc; 'I don't know' (90) exclusive; 'Other (Specify)' (99)
    ("Q82_DIFFICULTY_REASONS",   True,  True,  None),   # #582: 'I don't know' (90) exclusive; 'Other (Specify)' (99). Not a skip-target (Q81=No skips PAST it to Q83); falls through from Q81=Yes
    ("Q88_DIFF_PAYING",          True,  True,  None),   # #582: 'I don't know' (90) exclusive; 'Other (Specify)' (99)
    ("Q84_WHERE_ASSIST",         True,  False, None),   # #814: 10-option tick-all; 'Other (Specify)' (99); no 90 exclusive; the Q83=2 skip already jumps past it
    ("Q102_VISIT_REASON",        True,  False, None),   # #583: no None/IDK option; 'Other (Specify)' (99)
    ("Q103_CARE_TYPE",           True,  True,  None),   # #800: added exclusive 'No, I haven't accessed any form of medical care' (90) so accessed-nothing respondents can satisfy 'select >=1'; soft-warn if combined. 'Other (Specify)' (99)
    ("Q106_FORGONE_WHY",         True,  True,  None),   # #584: 'I don't know' (90) exclusive; 'Other (Specify)' (99). Skip-target from Q105=2 (skip rule repointed to bare base)
    ("Q107_OTHER_ACTIONS",       True,  True,  None),   # #655: 'Did not seek other forms of care' is now 90-coded exclusive (was substantive per #584 — tester FAIL: tickable alongside real actions; if you sought nothing else, no action co-applies); soft-warn if combined. 'Other (Specify)' (99). Skip-target from Q105=2 chains via the bare base
    ("Q109_TYPE",                True,  True,  None),   # #588: 'None of the above' (11->90) exclusive; 'Other (Specify)' (12->99)
    ("Q141_BILL_ITEMS",          True,  False, None),   # #615/#1098: 'Other expenses' keeps paper code 07 (CHECKBOX_OTHER_CODE) — _OTHER_TXT now gated on 07 (was ungated; prompted even when unticked)
    ("Q143_HOW_PAID",            True,  False, None),   # #616: 'Other (Specify)' (10->99); no None/IDK exclusive; reached via Q142=Yes (Q142=No skips to Q144)
    ("Q196_FOREGONE",            True,  False, None),   # #638: 'Other (please specify)' (99); 'We do not forego care' (07) stays ordinary (no 90 exclusive). Reached only when Q195=None (#637 skip routes other Q195 answers to Q197)
    ("Q202_WORRY_REASONS",       True,  False, None),   # #668: 3 reasons + #686 'Other (Specify)' (99, has_other) -> emit gated _OTHER_TXT; no None/IDK exclusive
]


def _gen_checkbox_proc(base, has_other, exclusive, gate=None, postproc_tail=None, extra_standalone=None,
                       other_code="99"):
    """Emit the bespoke PROC(s) for one converted Check Box base — select->=1 (hard),
    an optional exclusivity soft-warn (the 90-coded standalone option should stand alone),
    an optional preproc gate, an optional postproc tail (e.g. a `skip to` that fires
    AFTER the option-count validation), and (when present) the 'Other (specify)' text
    gate on the base's Other code (99 by default; CHECKBOX_OTHER_CODE overrides for
    bases whose Other option is not 99-coded, e.g. Q141/07 — #1098). Ported from F3
    generate_apc._gen_checkbox_proc (+ tail)."""
    qn = re.match(r"Q(\d+)", base).group(1)
    body = [f"PROC {base}"]
    if gate:
        body += ["preproc", gate]
    body += ["postproc"]
    if postproc_tail and has_other:
        # locals for the chunk-scan '99' tail guard below (declared at block top)
        body += ["  numeric tgN; numeric tgK; numeric tgP; numeric tgHit;"]
    body += [f"  if length(strip({base})) = 0 then",
             f'    errmsg("Select at least one option for Q{qn} before continuing.");',
             "    reenter;", "  endif;"]
    if exclusive:
        # #1075-#1080 (pretest 2026-08-05): HARD block (reenter), was a soft warn.
        # Testers: DK/None ticked alongside real options must not proceed. Applies
        # class-wide to every exclusive base (fixing only the 6 ticketed questions
        # would leave the same defect on the other ~19 for the next wave). Positive
        # pos() match on the field's own value — notappl-safe; same structure as the
        # neighboring hard 'select >=1' and #798 standalone checks (field-proven).
        body += [f'  if pos("90", {base}) > 0 and length(strip({base})) > 2 then',
                 f'    errmsg("Q{qn}: an exclusive option (None / I don\'t know) cannot be '
                 f'combined with other answers - untick the others or untick it.");',
                 "    reenter;",
                 "  endif;"]
    # #798: named non-90 standalone options that must HARD-block when combined with anything
    # else (e.g. Q85 "There are no benefits to being a member" — code 04).
    for _code, _label in (extra_standalone or []):
        body += [f'  if pos("{_code}", {base}) > 0 and length(strip({base})) > 2 then',
                 f'    errmsg("Q{qn}: \'{_label}\' cannot be combined with other answers - '
                 f'untick the others or untick this option.");',
                 "    reenter;",
                 "  endif;"]
    if postproc_tail:
        if has_other:
            # #656: don't let the tail skip jump PAST the Other-specify box. When
            # 'Other' is ticked, the base field must fall through to the _OTHER_TXT box
            # (which re-runs the same tail after capturing the text); otherwise the
            # unconditional skip fires first and the specify box never appears. Guard
            # the base tail on 'Other' NOT ticked. 2026-07-02 #450-class fix: the '99'
            # membership chunk-scans (pos("99") false-matched e.g. 09+90 -> "0990").
            body += ["  tgHit = 0;",
                     f"  tgN = length(strip({base})) / 2;",
                     "  do tgK = 1 while tgK <= tgN",
                     "    tgP = (tgK - 1) * 2 + 1;",
                     f"    if tonumber({base}[tgP:2]) = {int(other_code)} then tgHit = 1; endif;",
                     "  enddo;",
                     "  if tgHit = 0 then", postproc_tail, "  endif;"]
        else:
            body += [postproc_tail]
    procs = {base: "\n".join(body)}
    if has_other:
        # 2026-07-02 #450-class fix: '99' membership via an aligned 2-char chunk scan
        # (pos("99") false-matched when a 9-ending code preceded a 9-starting one,
        # e.g. 09+90 packs "0990" — the postproc then hard-blocked until junk was typed).
        other_body = (
            f"PROC {base}_OTHER_TXT\npreproc\n"
            f"  numeric otN; numeric otK; numeric otP; numeric otHit;\n"
            f"  otHit = 0;\n"
            f"  otN = length(strip({base})) / 2;\n"
            f"  do otK = 1 while otK <= otN\n"
            f"    otP = (otK - 1) * 2 + 1;\n"
            f"    if tonumber({base}[otP:2]) = {int(other_code)} then otHit = 1; endif;\n"
            f"  enddo;\n"
            f"  if otHit = 0 then\n"
            f'    {base}_OTHER_TXT = "";   {{ gated: \'Other (specify)\' not ticked -> not enterable }}\n'
            f"    noinput;\n  endif;\npostproc\n"
            f"  numeric otN2; numeric otK2; numeric otP2; numeric otHit2;\n"
            f"  otHit2 = 0;\n"
            f"  otN2 = length(strip({base})) / 2;\n"
            f"  do otK2 = 1 while otK2 <= otN2\n"
            f"    otP2 = (otK2 - 1) * 2 + 1;\n"
            f"    if tonumber({base}[otP2:2]) = {int(other_code)} then otHit2 = 1; endif;\n"
            f"  enddo;\n"
            f"  if otHit2 = 1 and length(strip({base}_OTHER_TXT)) = 0 then\n"
            f'    errmsg("\'Other (specify)\' was ticked for Q{qn} - please specify.");\n'
            "    reenter;\n  endif;"
        )
        if postproc_tail:
            other_body += "\n" + postproc_tail   # #656: continue to the tail target after Other text
        procs[f"{base}_OTHER_TXT"] = other_body
    return procs


# Optional postproc tails for specific Check Box bases — fire AFTER the
# >=1-option validation. Q113 (why-not-planning, asked only when Q112=2): once
# answered, route straight to Section L gate Q126 — Q114-Q125 belong to the
# Q112=Yes/Not-yet branch which Q113 is NOT on. (#590-593 Q112 cluster.)
CHECKBOX_POSTPROC_TAILS = {
    "Q113_WHY_NOT": "  skip to Q126_NBB_HEARD;   { after why-not -> Section L NBB (skip Q114-Q125 referral-experience tail) }",
}

# #798: named non-90 options that must HARD-block when ticked alongside anything else.
# Q85 "There are no benefits to being a member" (code 04) — saying there are NO benefits
# is contradictory with selecting specific benefits.
CHECKBOX_EXTRA_STANDALONE = {
    "Q85_BENEFITS": [("04", "There are no benefits to being a member")],
    # #824: Q56 "There are no benefits in the package" (05) — same contradiction class as
    # Q85/04: claiming NO benefits while ticking specific benefits. pos() is cross-boundary-
    # safe for both fields (a false "05"/"04" match needs a 0-ending code followed by a
    # 5-/4-starting one; the only 0-ending code in either value set is 90 and no code starts
    # with 5 or 4 — so the #450 chunk-scan is not required here; re-check if codes change).
    "Q56_YAKAP_UNDERSTAND": [("05", "There are no benefits in the package")],
    # #1178 (ASPSI review 2026-08-07): Q196 "We do not forego care" (07) - saying the
    # household foregoes NO care is contradictory with naming specific foregone care.
    # Coded 07, not 90, so the generic exclusive branch never matched it. pos() is
    # cross-boundary-safe: a false "07" needs a 0-ending code followed by a 7-starting
    # one, and none of Q196's codes (01-07, 99) end in 0.
    "Q196_FOREGONE": [("07", "We do not forego care")],
}

# #1098 (pretest 2026-08-05): bases whose 'Other (specify)' option is NOT 99-coded.
# Q141 'Other expenses' kept its paper code 07 through the #615 conversion, so the
# default pos(99) gate never matched and its _OTHER_TXT was left ungated — the
# specify box prompted even when 07 wasn't ticked. Gate on the real code instead
# of recoding 07->99 (zero data-code changes mid-pretest).
CHECKBOX_OTHER_CODE = {
    "Q141_BILL_ITEMS": "07",
}

CHECKBOX_MULTISELECT_PROCS = {}
for _b, _o, _x, _g in CHECKBOX_CONVERT:
    CHECKBOX_MULTISELECT_PROCS.update(
        _gen_checkbox_proc(_b, _o, _x, _g, CHECKBOX_POSTPROC_TAILS.get(_b),
                           CHECKBOX_EXTRA_STANDALONE.get(_b),
                           CHECKBOX_OTHER_CODE.get(_b, "99")))

# Append the generated Check Box PROCs to EXTRA_PROCS so they emit alongside the rest
# and are seeded into `covered` (via CHECKBOX_COVERED).
EXTRA_PROCS = (EXTRA_PROCS.rstrip("\n")
               + "\n\n{ ---- #529 + #573/#574 + #577-585/#588/#590-591: select_all -> Check "
                 "Box conversions — config-driven from CHECKBOX_CONVERT ---- }\n"
               + "\n\n".join(CHECKBOX_MULTISELECT_PROCS[k]
                             for k in sorted(CHECKBOX_MULTISELECT_PROCS))
               + "\n")

# Every field name owned by a Check Box bespoke PROC (the 17 bases + their _OTHER_TXT)
# — seeded into `covered` so the dcf-driven other-specify / select-all auto-gens skip
# them (the alpha checkbox base carries the 'Other (Specify)' code 99 in its value set,
# which would otherwise mis-fire the generic single-choice other-specify gate).
CHECKBOX_COVERED = set(CHECKBOX_MULTISELECT_PROCS)


VALIDATION_PROCS = """\
{ ---- Validations: respondent demographics + household composition (spec 3.3) ---- }
PROC Q2_BIRTH_MONTH
postproc
  if Q2_BIRTH_MONTH < 1 or Q2_BIRTH_MONTH > 12 then
    errmsg("Birth month must be 1-12.");
    reenter;
  endif;

PROC Q2_BIRTH_YEAR
postproc
  if Q2_BIRTH_YEAR < 1900 or Q2_BIRTH_YEAR > currentYear then
    errmsg("Birth year must be between 1900 and %d.", currentYear);
    reenter;
  endif;

PROC Q2_1_AGE
postproc
  if Q2_1_AGE < 0 or Q2_1_AGE > 120 then
    errmsg("Age must be 0-120.");
    reenter;
  endif;
  if abs((currentYear - Q2_BIRTH_YEAR) - Q2_1_AGE) > 1 then
    errmsg("Age (%d) is inconsistent with birth year %d. Reenter.", Q2_1_AGE, Q2_BIRTH_YEAR);
    reenter;
  endif;

PROC Q19_HH_SIZE_TOTAL
postproc
  if Q19_HH_SIZE_TOTAL < 1 or Q19_HH_SIZE_TOTAL > 20 then
    errmsg("Household size must be 1-20.");
    reenter;
  endif;
  if Q19_HH_SIZE_TOTAL > 10 then
    errmsg("Household size %d is unusually large. Confirm.", Q19_HH_SIZE_TOTAL);
  endif;

PROC Q20_HH_CHILDREN
postproc
  if Q20_HH_CHILDREN > Q19_HH_SIZE_TOTAL then
    errmsg("Children (%d) cannot exceed household size (%d).", Q20_HH_CHILDREN, Q19_HH_SIZE_TOTAL);
    reenter;
  endif;

PROC Q21_HH_SENIORS
postproc
  if Q21_HH_SENIORS > Q19_HH_SIZE_TOTAL then
    errmsg("Seniors (%d) cannot exceed household size (%d).", Q21_HH_SENIORS, Q19_HH_SIZE_TOTAL);
    reenter;
  endif;
  if Q20_HH_CHILDREN + Q21_HH_SENIORS > Q19_HH_SIZE_TOTAL then
    errmsg("Children + seniors (%d) exceed household size (%d).",
           Q20_HH_CHILDREN + Q21_HH_SENIORS, Q19_HH_SIZE_TOTAL);
    reenter;
  endif;

{ ---- Roster per-member validations (spec 3.4) ---- }
PROC Q32_AGE
postproc
  if Q32_AGE < 0 or Q32_AGE > 120 then
    errmsg("Member age must be 0-120.");
    reenter;
  endif;

PROC Q39_CIVIL_STATUS
postproc
  if Q32_AGE < 15 and Q39_CIVIL_STATUS <> 1 then   { 1 = Single (verify code) }
    errmsg("Member is under 15 but civil status is not Single. Confirm.");
  endif;

{ ---- Income amount must fall within reported bracket (spec 3.2, HARD) ---- }
PROC Q18_INCOME_BRACKET
postproc
  numeric a = Q18_INCOME_AMOUNT;
  numeric ok = 0;
  if a = -98 or a = -99 then ok = 1; endif;   { #793: -98 don't-know / -99 refused -> no bracket cross-check }
  if Q18_INCOME_BRACKET = 1 and a < 40000 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 2 and a >= 40000 and a <= 59999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 3 and a >= 60000 and a <= 99999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 4 and a >= 100000 and a <= 249999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 5 and a >= 250000 and a <= 499999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 6 and a >= 500000 then ok = 1; endif;
  { #813: bracket 7 (Refuse) is only valid when the amount itself was refused/unknown
    (-98/-99, already ok'd above per #793). With a real amount entered the bracket is
    derivable, so refusing it is a HARD inconsistency. }
  if ok = 0 then
    if Q18_INCOME_BRACKET = 7 then
      errmsg("Q18: an income amount was provided (%d PHP), so the bracket cannot be 'Refuse to answer'. Select the bracket that matches the amount (or re-enter the amount as -99 if the respondent refused).", a);
    else
      errmsg("Income bracket does not match the reported amount (%d PHP). Reconcile.", a);
    endif;
    reenter;
  endif;
"""

# Section D-F awareness + Section I primary-care + Section M bill-recall (spec 4.6-4.8)
SKIP_RULES = [
    # Section B — Respondent Profile
    # Q5 ("which LGBTQIA+ group do you identify with?") only applies when Q4 = Yes.
    # Q4 codes: 1 Yes / 2 No / 3 Not comfortable / 4 Don't know / 5 Refused — every
    # non-Yes answer makes Q5 nonsensical, so skip Q5(+its other-specify) to Q6 unless
    # Q4 = 1. (#518: Q4 = No was wrongly requiring Q5.) "<> 1" not "= 2" so the CAPI
    # non-response codes 3/4/5 skip too, matching the printed form's "If No -> Q6".
    ("Q4_LGBTQIA",           "Q4_LGBTQIA <> 1",             "Q6_CIVIL_STATUS"),
    ("Q7_IS_PWD",            "Q7_IS_PWD = 2",               "Q11_EDUCATION"),
    # #598 (ASPSI/Carl, 2026-06-17 — go-with-ASPSI): Q8 "Would you like to specify the type
    # of disability?" = No skips the rest of the disability block (Q9 PWD card + Q10 type) to
    # Q11 — the respondent declined to give detail, so don't ask for the card or type. Making
    # Q8 a skip SOURCE also takes it off the same screen as Q9 (the tester's other complaint).
    # (Carl's call: Q8=No -> Q11, NOT the ticket's literal "Q8=Yes -> Q11", which would have
    # reversed #523 and dropped the type for people who AGREED to specify it.)
    ("Q8_SPECIFY_DISABILITY","Q8_SPECIFY_DISABILITY = 2",   "Q11_EDUCATION"),
    # Q10 (disability type) appears only for PWDs who agreed to specify (Q8=Yes, guaranteed
    # here) AND presented or declined a card (Q9=1 or Q9=2). #523 scenarios A (Q8Y,Q9Y) and
    # C (Q8Y,Q9N) -> show Q10; Q9=3 (refused to present card) -> Q11. (Scenario B (Q8N,*) now
    # exits earlier at the Q8=No rule above, so the Q9 gate no longer needs the Q8 term.)
    # #698: Q10 reads "Based on the PRESENTED PWD card, what type…" — it is unanswerable
    # unless a card was actually presented (Q9 = 1). So Q9 = 2 (card not available) and
    # Q9 = 3 (refused to present) both skip Q10 -> Q11. (Adjusts the #523 branch that let
    # Q9 = 2 fall through to Q10, which contradicted Q10's own "presented card" wording.)
    ("Q9_PWD_CARD",          "Q9_PWD_CARD <> 1",            "Q11_EDUCATION"),
    ("Q14_IP_MEMBER",        "Q14_IP_MEMBER = 2",           "Q16_4PS"),
    # Section C roster — PhilHealth-registration detail (#563/#565) is now a bespoke
    # PROC Q45_PHILHEALTH_REG in ROSTER_PROCS (skip to next when <>Yes, jumping over the
    # new Q45.1 PIN date + Q46 category) — the old "skip to Q48_NAME_FIRST" target is gone
    # now that Q48-Q50 moved to the C_PRIVATE_INS_ROSTER second pass.
    # Section G — Access to Medicines
    ("Q62_PURCHASE_FREQ",    "Q62_PURCHASE_FREQ = 5",       "AREA_HAS_GAMOT"),    # Never -> skip Rx/where/travel (lands on the now-auto-answered GAMOT gate -> falls through to Q69, #643/#797)
    # #797: AREA_HAS_GAMOT = 2 -> skip Q69-76 REMOVED — GAMOT block is asked of everyone now (gate auto-answers Yes + noinput)
    ("Q69_GAMOT_HEARD",      "Q69_GAMOT_HEARD = 2",         "Q75_BRAND_GEN_KNOWS"),
    # #575 (ASPSI, 2026-06-17 — go-with-ASPSI): Q72 "obtained meds via GAMOT?" = No skips
    # only Q73 (the GAMOT meds list) but STILL asks Q74 "where did you get the rest" (you
    # sourced them outside GAMOT). Was -> Q75 (skipped Q73+Q74); spec doc said Q75 but ASPSI
    # confirmed Q74 is the intended target. Q74 -> Q75 chains on naturally afterwards.
    ("Q72_GAMOT_OBTAINED",   "Q72_GAMOT_OBTAINED = 2",      "Q74_WHERE_REST"),
    # #538: REMOVED the Q75=No -> Q79 skip. Q75 ("know branded vs generic difference?") = No
    # must now fall through to Q76 (was wrongly exiting Section G). Q76 still terminates the
    # section on its own (PROC Q76_BRAND_OR_GEN: code 9 'Not applicable' -> Q79; Branded ->
    # Q78; Generic/Both -> Q77 -> Q78 -> Q79). No replacement skip needed — natural fall-through.
    # Section H — PhilHealth / Insurance
    ("Q81_REG_DIFFICULTY",   "Q81_REG_DIFFICULTY = 2",      "Q83_KNOWS_ASSIST"),
    ("Q83_KNOWS_ASSIST",     "Q83_KNOWS_ASSIST = 2",        "Q85_BENEFITS"),   # #529: Q85 is now a Check Box base (was _O01)
    ("Q86_PREMIUM_PAY",      "Q86_PREMIUM_PAY = 3",         "Q89_HAS_USUAL_FACILITY"),  # #726: skip-to-Q89 only on code 3 "No, I do not pay premiums"; was =2 "Yes, my employer pays" (a YES/payer answer that must proceed to Q87)
    ("Q87_PREMIUM_DIFFICULT","Q87_PREMIUM_DIFFICULT = 2",   "Q89_HAS_USUAL_FACILITY"),
    # D-F awareness gates
    # value sets are Yes(1)/No(2) only — no "Don't know" code 3 here (matches F3's
    # UHC/KON/BUCAS heard gates which use "= 2"); the old "in 2,3" carried a dead 3.
    ("Q51_UHC_HEARD",        "Q51_UHC_HEARD = 2",           "Q54_YAKAP_HEARD"),
    ("Q54_YAKAP_HEARD",      "Q54_YAKAP_HEARD = 2",         "AREA_HAS_BUCAS"),    # -> auto-answered BUCAS gate -> falls through to Q57 (#641/#796)
    # #796: AREA_HAS_BUCAS = 2 -> skip Q57-61 REMOVED — BUCAS block is asked of everyone now (gate auto-answers Yes + noinput)
    ("Q57_BUCAS_HEARD",      "Q57_BUCAS_HEARD = 2",         "Q62_PURCHASE_FREQ"),
    ("Q60_BUCAS_ACCESSED",   "Q60_BUCAS_ACCESSED = 2",      "Q62_PURCHASE_FREQ"),
    # Section I primary-care routing
    # #650: Q89 (yes_no_dk) — route 'I don't know' (3) the SAME as 'No' (2): both mean
    # the respondent has no established usual facility, so jump to Q93 (why-not) and skip
    # Q90-Q92 / Q89.1 (which assume a Yes/known facility). Keeps the IDK option but stops it
    # falling through to questions that presume a usual facility. (The Q93 preproc gate below
    # is widened to admit the IDK path too, so Q93 is actually shown.)
    ("Q89_HAS_USUAL_FACILITY","Q89_HAS_USUAL_FACILITY = 2 or Q89_HAS_USUAL_FACILITY = 3", "Q93_WHY_NOT"),  # #529/#650: Q93 is a Check Box base (was _O01)
    # #827 (2026-07-03, supersedes #652's DIRECTION): Q90 "Is this the facility you usually
    # go to for general health concerns?". Yes(1) -> skip to Q94: their usual facility IS the
    # general-care facility, so Q91 "why did you go [elsewhere]" / Q92 "type of that facility"
    # don't apply (every Q91 option compares the visited facility against 'my usual one').
    # No(2) falls through Q91 -> Q92 -> Q93's preproc gate (Q89=1 on this path) self-skips
    # to Q94 — exactly the tester-requested "Q91, Q92, then skip to Q94". This now MATCHES
    # F4-Skip-Logic-and-Validations.md §Section-I. History: the paper prints Yes->Q91 /
    # No->Q96; #652 (2026-06-20) overrode No->Q94 keeping Yes->Q91; #827 flips the direction.
    # ASPSI to be notified: BOTH directions now depart from the printed Q90 routing on purpose.
    ("Q90_IS_USUAL_FOR_GENERAL","Q90_IS_USUAL_FOR_GENERAL = 1","Q94_TRANSPORT"),
    # #654: REMOVED the Q97=No -> Q100 skip. Q97 ("do you know how to book/access care")
    # is independent of Q98/Q99 (phone-advice availability when the facility is open/closed);
    # the paper shows no skip, so Q98/Q99 must be asked regardless of Q97. (Tester confirmed
    # against the paper questionnaire.)
    # Section J — Health-Seeking Behavior (Q101-Q107). #544: Q105 "forgone care" = No
    # means there was no forgone care, so Q106 "why did you forgo" is N/A -> skip it to
    # Q107 (other actions). Spec (generate_dcf Section J): "Q105 No -> Q107 (bypass Q106)".
    ("Q105_FORGONE_CARE",    "Q105_FORGONE_CARE = 2",       "Q107_OTHER_ACTIONS"),  # #584: Q107 is now a Check Box base (was _O01)
    # Section K — Referrals (Q108-Q125). Q108/Q112 cluster/Q119/Q120 routing.
    # Q108 (yes_no 1/2): No referral -> skip the ENTIRE Section K (Q109-Q125) to
    # Section L NBB gate Q126. (#588: was falling through to Q109.)
    ("Q108_REFERRED",        "Q108_REFERRED = 2",           "Q126_NBB_HEARD"),
    # Q119 (yes_no 1/2): visit was NOT a PCF referral -> skip Q120 (PCP-knows, the
    # Q119=Yes branch) straight to Q121 why-hospital. (#594: was falling to Q120.)
    ("Q119_PCF_REFERRAL",    "Q119_PCF_REFERRAL = 2",       "Q121_WHY_HOSPITAL"),
    # Q120 (yes_no_dk 1/2/3): only reached on the Q119=Yes branch. Q121 belongs to
    # the Q119=No branch, so for EVERY Q120 answer skip Q121 -> Q122 (both branches
    # reconverge at Q122). (#595: Yes was falling through to Q121.) Unconditional
    # skip — no value test, so no dead-condition risk.
    ("Q120_PCP_KNOWS",       "1 = 1",                       "Q122_PCP_DISCUSSED_PLACES"),
    # Section L — NBB awareness (Q126-Q131). Q126 (yes_no_dk 1/2/3): not heard of NBB
    # (No=2 OR I-don't-know=3) -> skip Q127 sources + Q128 understanding to Section M
    # gate Q132. (#596: was falling through to Q127; IDK=3 also covered.)
    ("Q126_NBB_HEARD",       "Q126_NBB_HEARD = 2 or Q126_NBB_HEARD = 3", "Q132_ZBB_HEARD"),
    # Section M bill-recall chain (#170), gated on Q129 confinement
    # #625/#626 (ASPSI, 2026-06-17): Q129 (HH confined?) = No(2) OR Don't-know(3) -> Q132 (ZBB
    # awareness is asked REGARDLESS of confinement per the printed form / spec §M note), NOT
    # straight to Q144. Only the bill-recall tail (Q138-Q143) is confinement-dependent and is
    # gated separately at Q138 (CUSTOM_VALIDATION). Was "= 2 -> Q144" (followed spec line 180,
    # which contradicts the §M note; tester + note win). Q129=Yes(1) -> Q130 (NBB utilization).
    ("Q129_HH_CONFINED",     "Q129_HH_CONFINED = 2 or Q129_HH_CONFINED = 3", "Q132_ZBB_HEARD"),
    # #661 (Carl go/no-go 2026-06-20 — NBB = DOH-retained-only): Q130 HOSPITAL_TYPE
    # (1 Public / 2 DOH-retained hospital / 3 Private). Q131 (NBB out-of-pocket) is asked
    # ONLY when the most-recent confinement was in a DOH-retained hospital (code 2). Public
    # (1) and Private (3) skip Q131 -> Q132. (The questionnaire-spec "all public" reading was
    # overridden by Carl's call to scope NBB to DOH-retained, matching the tester's report.)
    # Q130 is a skip SOURCE, so the skip-aware fmf deriver also gives it its own screen.
    ("Q130_HOSPITAL_TYPE",   "Q130_HOSPITAL_TYPE <> 2",     "Q132_ZBB_HEARD"),
    # Section M ZBB/MAIFIP awareness sub-blocks. #627: Q132 ZBB_HEARD (yes_no_dk 1/2/3)
    # = No(2) OR Don't-know(3) -> skip ZBB sources/understanding/OOP (Q133-Q135) to Q136
    # (spec §M line 190). #628: Q136 MAIFIP_HEARD = No/Don't-know -> skip Q137 sources to
    # Q138 (spec line 192). Q133/Q134 already gated on Q132=Yes, Q137 on Q136=Yes, but the
    # respondent-facing routing skip was missing so No/DK fell through to the source list.
    ("Q132_ZBB_HEARD",       "Q132_ZBB_HEARD = 2 or Q132_ZBB_HEARD = 3",     "Q136_MAIFIP_HEARD"),
    ("Q136_MAIFIP_HEARD",    "Q136_MAIFIP_HEARD = 2 or Q136_MAIFIP_HEARD = 3", "Q138_MOST_EXPENSIVE"),
    ("Q140_RECALL_BREAKDOWN","Q140_RECALL_BREAKDOWN = 2",   "Q142_RECALL_PAYMENT"),    # no breakdown -> skip Q141/Q141.1
    ("Q142_RECALL_PAYMENT",  "Q142_RECALL_PAYMENT = 2",     "N_FOOD_ITEM(1)"),  # no payment -> skip Q143 -> Section N food grid row 1 (Option C 2026-07-03; explicit occurrence — the skip source is outside the roster)
    # Section O #637: Q195 = any willing-to-set-aside answer (Less than 1%/1-3%/4-6%/
    # More than 6%/Don't know = codes 2-6) bypasses Q196 (the "what care would you
    # forego" item) -> Q197. Only Q195 = "None" (1) falls through to Q196. (Already
    # documented in generate_dcf Section O comment; the routing skip was missing.)
    ("Q195_INCOME_PCT",      "Q195_INCOME_PCT <> 1",        "Q197_DELAYED_CARE"),
    # Section Q end-of-survey skips (final section — nothing substantive follows Q202;
    # SURVEY_TEAM_LEADER_S_NAME is the first case-end admin field).
    # #702: Q200 = "Refused to answer" (4) -> end the respondent questions (skip Q201/Q202).
    ("Q200_REDUCED_SPEND",   "Q200_REDUCED_SPEND = 4",      "SURVEY_TEAM_LEADER_S_NAME"),
    # #703: Q201 = "Not worried at all" (4) -> no worry-reasons to give -> skip Q202.
    ("Q201_WORRIED",         "Q201_WORRIED = 4",            "SURVEY_TEAM_LEADER_S_NAME"),
]

BILL_VALIDATION = """\
{ ---- Bill-recall cap (spec 4.8): no-receipt amount cannot exceed total bill ---- }
PROC Q141_1_NO_RECEIPT_AMT_PHP
postproc
  if Q141_1_NO_RECEIPT_AMT_PHP > Q139_FINAL_AMOUNT_PHP then
    errmsg("No-receipt amount (%d) exceeds total bill (%d). Verify.",
           Q141_1_NO_RECEIPT_AMT_PHP, Q139_FINAL_AMOUNT_PHP);
    reenter;
  endif;
"""

TODO_NOTE = """\
{ ============================================================================
  STILL OPEN (follow-up F4 pass):
    - Section N subtotals (Q157/Q177/Q182/Q185 _SUBTOTAL_TOTAL_PHP): auto-compute
      from each panel's _PURCHASED_PHP + _INKIND_PHP sums; make enumerator-readonly
      (spec finding #9 / §4.9). Needs the per-panel item membership.
    - Per-member sub-questionnaire loops conditional on age/relation (#166).
    - Q23 water-source multi-category branch (Q24/Q25/Q26) + non-UHC9 Other-specify.
    - Max-roster soft warning at unusual sizes (#168 second half).
    - Skip logic for the remaining sections + single/select-all Other-specify.
    - Verify ALL option codes + roster/occurrence flow (curocc/endocc/count) in
      CSEntry against the generated FMF — this is the riskiest part untested.
  ============================================================================ }
"""


def dcf_item_names():
    names = []
    dic = json.loads(DCF.read_text(encoding="utf-8"))
    for level in dic["levels"]:
        for rec in level.get("records", []):
            for it in rec.get("items", []):
                names.append(it["name"])
    return names


def dcf_items_map():
    """{name: item_dict} for every item in the dcf (for other-specify derivation)."""
    items = {}
    dic = json.loads(DCF.read_text(encoding="utf-8"))
    for level in dic["levels"]:
        for rec in level.get("records", []):
            for it in rec.get("items", []):
                items[it["name"]] = it
    return items


# --- Column-wise Section C occurrence bound (2026-06-26) ----------------------------------
# Section C is split into ONE roster form per question (the "Household Characteristic Target
# Interface"). The member set is ESTABLISHED on the first roster form (MEMBER_LINE_NO +
# Q30_NAME + Q31_PRESENT), whose MEMBER_LINE_NO preproc endgroups at Q19. Occurrences are
# shared across all the per-question forms (desktop-CSEntry confirmed: Q32 occ2 auto-carries
# the Q30 name of member 2). BUT each downstream per-question form has no occurrence control
# of its own, so advancing past the last member would CREATE A PHANTOM occurrence (occ Q19+1
# with a NOTAPPL line). Fix: give every per-question roster field the SAME endgroup bound as
# the first form, so it auto-ends at Q19 members. Injected as the first preproc statement of
# each field's PROC (creating the preproc / whole PROC where none exists).
_ROSTER_ESTABLISH = {"MEMBER_LINE_NO", "Q30_NAME", "Q31_PRESENT"}
_ENDGROUP_BOUND = ("  if curocc() > Q19_HH_SIZE_TOTAL then endgroup; endif;"
                   "   { column-wise: auto-end this question at the Q19 member count }")


def roster_bound_fields():
    """Section C roster items that need a per-form occurrence bound (everything after the
    establishing first form)."""
    dic = json.loads(DCF.read_text(encoding="utf-8"))
    for level in dic["levels"]:
        for rec in level.get("records", []):
            if rec["name"] == "C_HOUSEHOLD_ROSTER":
                return [it["name"] for it in rec.get("items", [])
                        if it["name"] not in _ROSTER_ESTABLISH]
    return []


def inject_roster_occurrence_bounds(text, fields):
    """Insert the endgroup bound as the FIRST preproc statement of every per-question Section C
    roster field. Three cases: (a) PROC has a preproc -> insert after the 'preproc' line;
    (b) PROC exists but is postproc-only -> prepend a preproc section; (c) no PROC -> append a
    preproc-only PROC."""
    for f in fields:
        m = re.search(rf"(?m)^PROC {re.escape(f)}[ \t]*$", text)
        if not m:
            text += f"\nPROC {f}\npreproc\n{_ENDGROUP_BOUND}\n"
            continue
        body_start = m.end()
        nxt = re.search(r"(?m)^PROC ", text[body_start:])
        body_end = body_start + nxt.start() if nxt else len(text)
        body = text[body_start:body_end]
        pp = re.search(r"(?m)^preproc[ \t]*$", body)
        if pp:
            insert_at = body_start + pp.end()
            text = text[:insert_at] + "\n" + _ENDGROUP_BOUND + text[insert_at:]
        else:
            text = (text[:body_start] + "\npreproc\n" + _ENDGROUP_BOUND
                    + text[body_start:])
    return text


# Section N subtotal panels (spec finding #9 / §4.9, item ranges from §lines 549-552).
# Each subtotal auto-computes from its panel's _PURCHASED_PHP + _INKIND_PHP and is
# protected (enumerator cannot edit). Ranges are the AUTHORITATIVE spec ranges — NOT
# auto-derived by record order, because non-subtotaled items (Q158-Q172 restaurant /
# non-food) sit between the food and 12-month-health panels and must be excluded.
SUBTOTAL_PANELS = {
    "Q157_FOOD_SUBTOTAL_TOTAL_PHP":       (144, 156),
    # #633: Q177 = "Total value of 175 and 176" per the questionnaire's own Q177 text
    # + tester. Q173 (Health insurance) and Q174 (Other insurance) are NOT part of this
    # 12-month health subtotal — they're standalone insurance items. (Spec doc line 550's
    # "Q173..Q176" was a transcription error; the rendered Q177 label is authoritative.)
    "Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP": (175, 176),
    "Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP":  (178, 181),
    "Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP":  (183, 184),
}


def _subtotal_members(sub, items):
    """The _PURCHASED_PHP + _INKIND_PHP fields that feed a subtotal panel, by spec
    Q-number range (ordered)."""
    import re as _re
    lo, hi = SUBTOTAL_PANELS[sub]
    qnum = _re.compile(r"^Q(\d+)_")
    members = []
    for n in sorted(items):
        if not (n.endswith("_PURCHASED_PHP") or n.endswith("_INKIND_PHP")):
            continue
        m = qnum.match(n)
        if m and lo <= int(m.group(1)) <= hi:
            members.append(n)
    return members


# #677 (Carl go/no-go 2026-06-20): 'Don't know the amount' sentinel for Section N expenditure
# amounts. #743 (2026-06-23): the missing-amount sentinels are now NEGATIVE — -98 "don't know",
# -99 "refuse to answer" — replacing the old in-range 99999999. Negatives are clearly out-of-range
# for a peso amount (no spend is negative), so they can't be confused with a real value; they are
# non-zero (so they satisfy the consumed-needs-an-amount validation) and are EXCLUDED from the
# subtotal sums below. Must match the "-98/-99" hint in generate_dcf._expenditure_item, and the
# harmonization codebook §0.2 recodes them -> Stata .c (don't know) / .b (refused).
DK_AMOUNT = -98
REFUSED_AMOUNT = -99


def _subtotal_compute_body(sub, items, indent="  "):
    """The accumulate + protect() statements for a Section N subtotal, ready to embed in
    the FOLLOWER field's preproc (the question right after the subtotal — see #617).

    #617 (root-caused at runtime 2026-06-17). Two CSPro facts force this shape:
      1. A protect()ed field is SKIPPED WITHOUT running its preproc, so computing the
         subtotal in its own preproc never ran -> it stayed `notappl` and its range check
         HARD-ERRORED ("out of range - value is NOTAPPL"), blocking the interview.
      2. In a DisplayTogether amount matrix the NOT-consumed items' amount-field gate
         preprocs never run, so those amounts stay `notappl`; AND `if X = notappl then
         X = 0` does NOT work in CSPro (notappl = notappl is falsy), so a coalesce can't
         rescue them. A plain `sum(members)` therefore hits a notappl term and the whole
         subtotal becomes notappl (wrong value, masked by the init=0 so it doesn't crash).

    Robust compute: accumulate ONLY the items whose _CONSUMED = 1 (Yes). `_CONSUMED` is
    always a valid 1/2 (never notappl), and a consumed item's amounts are always entered
    (the amount box rejects blank), so no notappl ever enters the sum. Not-consumed items
    contribute nothing — their notappl amounts are never referenced."""
    members = _subtotal_members(sub, items)
    if not members:
        return None
    # group the _PURCHASED_PHP / _INKIND_PHP amounts by their item base
    by_base = {}
    order = []
    for m in members:
        base = m[:-len("_PURCHASED_PHP")] if m.endswith("_PURCHASED_PHP") else m[:-len("_INKIND_PHP")]
        if base not in by_base:
            by_base[base] = []; order.append(base)
        by_base[base].append(m)
    lines = [f"{indent}{sub} = 0;   {{ #617: accumulate only CONSUMED items -> no notappl propagation }}"]
    for base in order:
        amts = by_base[base]
        consumed = f"{base}_CONSUMED"
        # #677/#743: add each amount only if it is NOT a missing-amount sentinel
        # (DK_AMOUNT=-98 don't-know, REFUSED_AMOUNT=-99 refused), so an unknown/refused
        # amount never corrupts the subtotal.
        adds = " ".join(f"if {a} <> {DK_AMOUNT} and {a} <> {REFUSED_AMOUNT} then {sub} = {sub} + {a}; endif;" for a in amts)
        if consumed in items:
            lines.append(f"{indent}if {consumed} = 1 then {adds} endif;")
        else:
            # no consumed gate for this item -> it's always asked, so always add it
            lines.append(f"{indent}{adds}")
    lines.append(f"{indent}protect({sub}, true);")
    return "\n".join(lines)


def subtotal_init_compute_procs(names, items):
    """#617 (Critical, root-caused at runtime 2026-06-17): a protect()ed Section N
    subtotal is range-checked the instant flow reaches it (on DisplayTogether block
    exit), but CSEntry SKIPS the protected field WITHOUT executing its own preproc, so
    it stayed `notappl` and HARD-ERRORED ("out of range - value is NOTAPPL"), blocking
    the whole interview at Q157 (also Q177/Q182/Q185). Neither a combined nor an
    own-screen layout helps (the protected field is never focused either way), and the
    block-exit field is data-dependent (the last item's _CONSUMED when not consumed, its
    _INKIND_PHP when consumed), so no single preceding-field proc reliably fires first.

    Fix = two guaranteed-run sites per panel, both first-fields-of-a-block (their
    preprocs always run on block entry):
      * INIT the subtotal to 0 + protect in the panel's FIRST member's _CONSUMED preproc.
        Runs on block entry, so the protected field is a valid 0 (never notappl) when the
        block exits and validates it -> the blocking error can never fire.
      * COMPUTE the real sum + protect in the FOLLOWER field's preproc (the question right
        after the subtotal). Runs once the whole panel is done with every amount final,
        regardless of which field was the block-exit field.
    Adjacent panels share a field (e.g. the 6M-health first member IS the 12M-health
    follower), so statements are accumulated per field and emitted as one preproc."""
    import re as _re
    qn = _re.compile(r"^Q(\d+)_")
    pre = {}  # field -> [statement blocks], in emission order

    def add(field, stmt):
        pre.setdefault(field, []).append(stmt)

    for sub, (lo, hi) in SUBTOTAL_PANELS.items():
        if sub not in names:
            continue
        members = _subtotal_members(sub, items)
        if not members:
            continue
        # init at the panel's first member _CONSUMED (block entry)
        first_consumed = next(
            (n for n in names if n.endswith("_CONSUMED")
             and qn.match(n) and int(qn.match(n).group(1)) == lo), None)
        if first_consumed:
            add(first_consumed,
                f"  {sub} = 0;   {{ #617 init: protected subtotal must be valid (not notappl) when its block exits }}\n"
                f"  protect({sub}, true);")
        # real compute at the follower (field right after the subtotal)
        idx = names.index(sub)
        follower = names[idx + 1] if idx + 1 < len(names) else None
        if follower:
            body = _subtotal_compute_body(sub, items, indent="  ")
            add(follower, f"  { '{' } #617 real {sub} sum, now that the panel is complete { '}' }\n{body}")

    procs = {}
    for field, blocks in pre.items():
        procs[field] = f"PROC {field}\npreproc\n" + "\n".join(blocks)
    return procs


def expenditure_gate_procs(names):
    """#169 (spec 4.9) — combined-view edition (#708/#709, 2026-06-19): for each
    Section N item, gate its two amounts (*_PURCHASED_PHP, *_INKIND_PHP) from the
    item's *_CONSUMED field, NOT from each amount's own preproc.

    WHY this moved off the amount preprocs (was: set-0 + `skip to next`).
    -------------------------------------------------------------------
    #708/#709 put each item's {consumed / purchased / in-kind} triplet on ONE
    DisplayTogether (DG) screen (see generate_fmf.derive_block_plan EXPENDITURE_TRIPLET
    grouping). On a DG screen CSEntry renders EVERY member field regardless of skip
    logic, and a `skip to` issued from a field on a combined screen is exactly the
    gate-boundary the form deriver refuses to cross — the skip cannot meaningfully
    "skip over" a sibling already rendered on the same screen and causes focus/exit
    anomalies. The old gate's `skip to next` therefore cannot live inside a DG block.

    DG-safe replacement (brief's recommended fallback): drive the gate from the
    *_CONSUMED field's POSTPROC — a *visited* field (CONSUMED is the first field in the
    block, always entered) — never from the protected amount's own preproc (#617 rule).
    When not consumed (No=2): set each amount to a valid 0 and protect() it (read-only,
    skipped for entry, but still rendered on the combined screen). When consumed (=1):
    unprotect so the amount is enterable. The amount is always a valid 0, never notappl,
    so the #617 'out of range - value is NOTAPPL' class of error cannot fire here, and
    the subtotal compute (subtotal_init_compute_procs) — which sums only _CONSUMED = 1
    items — is unaffected (it never reads a not-consumed amount).

    Returns {consumed_field: postproc_text} where postproc_text begins with 'postproc'.
    main() merges this with any preproc the same _CONSUMED field already carries (the
    #617 subtotal-init preproc on each panel's first member) into ONE PROC block."""
    procs = {}
    have = set(names)
    bases = [n[: -len("_CONSUMED")] for n in names if n.endswith("_CONSUMED")]
    for base in bases:
        consumed = f"{base}_CONSUMED"
        amts = [a for a in (f"{base}_PURCHASED_PHP", f"{base}_INKIND_PHP") if a in have]
        if not amts:
            continue
        not_consumed, consumed_branch = [], []
        # #680.1 (Carl go/no-go 2026-06-20): every household has housing (actual rent if rented,
        # imputed value if owned), so 'Not consumed' on Q167 Housing is almost always an error.
        # Soft-warn the enumerator (errmsg continues — no reenter, in case there's a genuine
        # reason). Fires in the not-consumed branch.
        if base == "Q167_HOUSING":
            not_consumed.append('    errmsg("Housing should almost always have a value — actual '
                'rent if rented, or the estimated value of rent if owned. If the household has '
                'housing, go back and mark Yes and enter the amount.");')
        for amt in amts:
            not_consumed.append(f"    {amt} = 0;   {{ item not consumed -> no spend }}")
            not_consumed.append(f"    protect({amt}, true);")
            # #755/#818 (2026-07-02): pre-fill 0 so the enumerator can press Enter through an
            # amount they have nothing to record for. Guard = special(): true only while the
            # field holds notappl/missing — i.e. "no real value yet". The previous
            # `not ({amt} > 0)` guard was INVERTED: CSPro special values compare GREATER than
            # any number, so a fresh notappl amount had `> 0` true and the pre-fill never ran,
            # leaving the DisplayTogether triplet stuck at NOTAPPL (#818, and #805 before it:
            # "does not accept any value"). special() preserves real values (incl. 0) and the
            # -98/-99 sentinels on back-nav.
            consumed_branch.append(
                f"    if special({amt}) then {amt} = 0; endif;   {{ #755/#818 pre-fill: no-value-yet -> 0 }}")
            consumed_branch.append(f"    protect({amt}, false);   {{ enterable when consumed }}")
        body = (
            "postproc\n"
            f"  if {consumed} = 2 then\n"
            + "\n".join(not_consumed) + "\n"
            "  else\n"
            + "\n".join(consumed_branch) + "\n"
            "  endif;"
        )
        procs[consumed] = body
    return procs


def consumed_amount_validation_procs(names):
    """#677 (Carl go/no-go 2026-06-20 — the tester's suggestion): a Section N item marked
    "Consumed by HH" (=1) must have at least ONE of its amounts (*_PURCHASED_PHP spent
    purchasing / *_INKIND_PHP value received in-kind/gift/own-produced) GREATER THAN 0 —
    consumed-but-both-zero is contradictory, so don't let the interview advance past the
    item. Hard-block (errmsg + reenter) on the item's LAST amount field, which is the
    DisplayTogether block-exit field when consumed (#617 note), so the check fires once
    both amounts are final. Layout-independent — keeps the #708/#709 combined view.

    Pairs with expenditure_gate_procs: that one zeroes+protects the amounts when NOT
    consumed (so this validation never trips on a not-consumed item — its amounts are a
    protected 0 and the `{consumed} = 1` guard is false).

    Returns {last_amount_field: postproc_text} ('postproc' header)."""
    procs = {}
    have = set(names)
    bases = [n[: -len("_CONSUMED")] for n in names if n.endswith("_CONSUMED")]
    for base in bases:
        consumed = f"{base}_CONSUMED"
        amts = [a for a in (f"{base}_PURCHASED_PHP", f"{base}_INKIND_PHP") if a in have]
        if consumed not in have or not amts:
            continue
        last_amt = amts[-1]               # block-exit field when the item is consumed
        # #818: special-value-safe form — fires when every amount is 0 OR still blank
        # (notappl is not in the -99/-98/1:99999999 list), so a blank-passed amount can
        # neither silently satisfy the at-least-one check nor leak NOTAPPL onward.
        zero_cond = " and ".join(
            f"not ({a} in {REFUSED_AMOUNT}, {DK_AMOUNT}, 1:99999999)" for a in amts)
        status_guard = _dkrf_677_guard(f"{base}_AMT_STATUS")
        procs[last_amt] = (
            "postproc\n"
            f"  if {status_guard}{consumed} = 1 and {zero_cond} then\n"
            "    errmsg(\"This item is marked consumed by the household, so enter the amount "
            "spent purchasing it and/or the estimated value if received in-kind, as a gift, "
            "or own-produced — at least one must be greater than 0. If the household genuinely "
            "does not know an amount, enter -98; if they refuse to answer, enter -99 (do not "
            "read those codes aloud).\");\n"
            "    reenter;\n"
            "  endif;"
        )
    return procs


def flat_expenditure_amount_procs(names):
    """#832/#833 (2026-07-04): the flat Section N weekly singles (Q158 restaurant, Q159
    tobacco) are the only expenditure items not rosterized. They previously used the
    CONSUMED-postproc + protect() gate (expenditure_gate_procs); on their DisplayTogether
    screen the runtime protect(amt, false) did not reliably re-render the sibling amounts
    enterable, so 'YES not accepting any value'. Switch them to the EXACT roster gate
    (Q144-Q156): the gate lives in each amount's OWN preproc with noinput (DG-safe, no
    skip-to) + a special() pre-fill, and NO protect(), so amounts are always enterable when
    consumed. #677 (consumed-needs->=1-amount) rides on the last amount's postproc, reusing
    the identical wording via consumed_amount_validation_procs. Returns {amount_field: proc}."""
    procs = {}
    have = set(names)
    v677 = consumed_amount_validation_procs(names)   # {last_amt: 'postproc\n...'} — identical wording
    bases = [b[: -len("_CONSUMED")] for b in names if b.endswith("_CONSUMED")]
    for base in bases:
        consumed = f"{base}_CONSUMED"
        amts = [a for a in (f"{base}_PURCHASED_PHP", f"{base}_INKIND_PHP") if a in have]
        if consumed not in have or not amts:
            continue
        for a in amts:
            gate = (
                "preproc\n"
                "  { #832/#833 roster-parity gate (Q144-Q156): not consumed -> 0 + noinput\n"
                "    (DG-safe, no skip-to, no protect); consumed -> #755/#818 special() pre-fill\n"
                "    so Enter passes an empty amount. Always enterable when consumed. }\n"
                f"  if {consumed} = 2 then\n"
                f"    {a} = 0;\n"
                "    noinput;\n"
                "  else\n"
                f"    if special({a}) then {a} = 0; endif;\n"
                "  endif;"
            )
            proc = f"PROC {a}\n{gate}"
            if a in v677:                # last amount also carries the #677 postproc
                proc = f"{proc}\n{v677[a]}"
            procs[a] = proc
    return procs


def uhc9_other_specify_procs(names):
    procs = {}
    for n in names:
        for suffix, code, lbl in (("_YES_OTHER_TXT", 4, "Yes, other reason"),
                                  ("_NO_OTHER_TXT", 7, "No, other reason")):
            if n.endswith(suffix):
                parent = n[: -len(suffix)]
                procs[n] = (
                    f"PROC {n}\npreproc\n"
                    f"  if {parent} <> {code} then\n"
                    f"    {n} = \"\";   {{ skip + clear: '{lbl}' not chosen }}\n"
                    f"    noinput;\n  endif;\n"
                    f"postproc\n"
                    f"  if {parent} = {code} and length(strip({n})) = 0 then\n"
                    f"    errmsg(\"'{lbl}' was selected for {parent}. Please specify.\");\n"
                    f"    reenter;\n  endif;"
                )
    return procs


def _dkrf_gate_branch(status):
    """The DK/RF branch spliced into a roster amount preproc gate (empty when the flag is
    off). When AMT_STATUS is DK(2)/RF(3) the amount is already -98/-99 (set by the status
    postproc), so skip entry. Post-.format so single braces are fine."""
    if not DK_RF_STATUS:
        return ""
    return (f"  elseif {status} in 2, 3 then\n"
            f"    noinput;   {{ #7 DK/RF: amount already -98/-99 from the status field }}\n")


def _dkrf_677_guard(status):
    """Prefix for the #677 consumed-needs-an-amount condition — only fires on 'gave'(1)."""
    return f"{status} = 1 and " if DK_RF_STATUS else ""


def _amt_status_proc(prefix):
    """#7 per-item DK/RF gate proc (empty when the flag is off). Asked only when consumed
    (not-consumed rows default to 'gave'(1) + noinput). DK(2) -> both amounts -98; RF(3) ->
    both -99. Amounts then skipped (roster: the gate branch above; flat: shown pre-set)."""
    if not DK_RF_STATUS:
        return ""
    c, st = f"{prefix}_CONSUMED", f"{prefix}_AMT_STATUS"
    p, k = f"{prefix}_PURCHASED_PHP", f"{prefix}_INKIND_PHP"
    return f'''PROC {st}
preproc
  {{ #7 DK/RF gate - only asked when consumed; not-consumed -> 'gave' + noinput. }}
  if {c} <> 1 then
    {st} = 1;
    noinput;
  endif;
postproc
  {{ Don't know -> both amounts {DK_AMOUNT}; Refused -> both {REFUSED_AMOUNT} (excluded from subtotals). }}
  if {st} = 2 then
    {p} = {DK_AMOUNT}; {k} = {DK_AMOUNT};
  elseif {st} = 3 then
    {p} = {REFUSED_AMOUNT}; {k} = {REFUSED_AMOUNT};
  endif;
'''


def section_n_food_roster_procs():
    """Option C food roster (N_FOOD_ROSTER, 13 rows = Q144-Q156).
    #834 Option A (2026-07-06): the per-row special() pre-fill AND the per-row #677 reenter
    were REMOVED - both fired during partial-save resume-replay (rows read transiently
    notappl on 'go to last position'): the pre-fill zeroed the stored amount and #677
    hard-blocked at row 1. Amounts are now left enterable (not-consumed still auto-0 +
    noinput); completeness is checked ONCE at section end (Q186, soft - no reenter, in
    section_n_review_proc); the subtotal accumulator excludes notappl AND the -98/-99
    sentinels via 'in 0:99999999'."""
    nmax = len(FOOD_WEEKLY_ITEMS)
    ladder = []
    for k, (_, label) in enumerate(FOOD_WEEKLY_ITEMS, start=1):
        kw = "if" if k == 1 else "elseif"
        ladder.append(f'  {kw} curocc() = {k} then N_FOOD_ITEM = "{label}";')
    ladder.append("  endif;")
    ladder_txt = "\n".join(ladder)

    amount_gate = (
        "preproc\n"
        "  {{ #834 Option A: not consumed -> auto 0 + noinput. Consumed -> LEFT ENTERABLE with\n"
        "    NO special() pre-fill (the pre-fill zeroed stored amounts on partial-save resume-\n"
        "    replay, #834). Completeness is checked once at section end (Q186), not per row. }}\n"
        "  if N_FOOD_CONSUMED = 2 then\n"
        "    {f} = 0;\n"
        "    noinput;\n"
        "  endif;\n"
        "\n"
        "postproc\n"
        "  {{ Range.docx hardening (2026-07-08): valid = 0..99999999 (width caps the max)\n"
        "    or the -98/-99 sentinels; block stray negatives (CSEntry accepts a typed\n"
        "    minus). Replay-safe: the partial-save resume transient reads 0/notappl,\n"
        "    never < 0 (#834/#835 class checked before adding). }}\n"
        "  if {f} < 0 and {f} <> -98 and {f} <> -99 then\n"
        "    errmsg(\"Amount must be 0-99999999, or -98 if the household does not know / -99 if they refuse to answer.\");\n"
        "    reenter;\n"
        "  endif;"
    )

    gate_p = amount_gate.format(f="N_FOOD_PURCHASED_PHP")
    gate_k = amount_gate.format(f="N_FOOD_INKIND_PHP")
    if DK_RF_STATUS:
        _br = _dkrf_gate_branch("N_FOOD_AMT_STATUS")
        gate_p = gate_p.replace("  endif;", _br + "  endif;", 1)
        gate_k = gate_k.replace("  endif;", _br + "  endif;", 1)
    status_proc = _amt_status_proc("N_FOOD")
    return f"""{{ ---- Section N Option C: weekly-food roster (N_FOOD_ROSTER, fixed 13 rows = Q144-Q156) ---- }}
PROC N_FOOD_ITEM
preproc
  {{ Auto-name this grid row from the WHO/SHA item list (one occurrence per item). }}
{ladder_txt}
  noinput;
{status_proc}
PROC N_FOOD_PURCHASED_PHP
{gate_p}

PROC N_FOOD_INKIND_PHP
{gate_k}

PROC Q157_FOOD_SUBTOTAL_TOTAL_PHP
preproc
  {{ Q157 food subtotal (spec 4.9) - computed in Q157's OWN preproc + noinput (#617: a
    protected field skips its preproc; a group proc gets wiped by record P buffer init).
    LOCAL accumulator (q92_oop rule). #834: amounts can now be blank (notappl), so add only
    real non-negative amounts - 'in 0:99999999' excludes notappl AND the -98/-99 sentinels
    (#743). Re-runs on back-nav + resume. }}
  numeric nfr_i; numeric nfr_total;
  nfr_total = 0;
  do nfr_i = 1 while nfr_i <= {nmax}
    if N_FOOD_CONSUMED(nfr_i) = 1 then
      if N_FOOD_PURCHASED_PHP(nfr_i) in 0:99999999 then
        nfr_total = nfr_total + N_FOOD_PURCHASED_PHP(nfr_i);
      endif;
      if N_FOOD_INKIND_PHP(nfr_i) in 0:99999999 then
        nfr_total = nfr_total + N_FOOD_INKIND_PHP(nfr_i);
      endif;
    endif;
  enddo;
  Q157_FOOD_SUBTOTAL_TOTAL_PHP = nfr_total;
  noinput;
"""


# Fan-out roster specs (2026-07-03): (field prefix, dcf item list, subtotal field | None).
SECTION_N_FANOUT = [
    ("N_WKOTH", WEEKLY_OTHER_ITEMS, None),   # #832/#833: restaurant + tobacco, rosterized
    ("N_NF1M",  NONFOOD_1M_ITEMS,  None),
    ("N_NF6M",  NONFOOD_6M_ITEMS,  None),
    ("N_NF12M", NONFOOD_12M_ITEMS, None),
    ("N_H12M",  HEALTH_12M_ITEMS,  "Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP"),
    ("N_H6M",   HEALTH_6M_ITEMS,   "Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP"),
    ("N_H1M",   HEALTH_1M_ITEMS,   "Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP"),
]


def section_n_fanout_procs():
    """Section N fan-out rosters - exact replica of the food-grid procs.
    #834 Option A (2026-07-06): the per-row special() pre-fill AND the per-row #677 reenter
    were REMOVED (both fired destructively during partial-save resume-replay). Amounts left
    enterable; not-consumed still auto-0 + noinput; completeness checked once at section end
    (Q186, soft - in section_n_review_proc); subtotals exclude notappl AND -98/-99 sentinels
    via 'in 0:99999999'."""
    blocks = ["{ ---- Section N fan-out: remaining recall blocks as rosters (2026-07-03) ---- }"]
    amount_gate = (
        "preproc\n"
        "  {{ #834 Option A: not consumed -> auto 0 + noinput. Consumed -> LEFT ENTERABLE, NO\n"
        "    special() pre-fill (it clobbered stored amounts on resume-replay, #834).\n"
        "    Completeness checked once at section end (Q186), not per row. }}\n"
        "  if {c} = 2 then\n"
        "    {f} = 0;\n"
        "    noinput;\n"
        "  endif;\n"
        "\n"
        "postproc\n"
        "  {{ Range.docx hardening (2026-07-08): valid = 0..99999999 (width caps the max)\n"
        "    or the -98/-99 sentinels; block stray negatives (CSEntry accepts a typed\n"
        "    minus). Replay-safe: the partial-save resume transient reads 0/notappl,\n"
        "    never < 0 (#834/#835 class checked before adding). }}\n"
        "  if {f} < 0 and {f} <> -98 and {f} <> -99 then\n"
        "    errmsg(\"Amount must be 0-99999999, or -98 if the household does not know / -99 if they refuse to answer.\");\n"
        "    reenter;\n"
        "  endif;"
    )
    for prefix, items_list, subtotal in SECTION_N_FANOUT:
        ladder = []
        for k, (_, label) in enumerate(items_list, start=1):
            kw = "if" if k == 1 else "elseif"
            ladder.append(f'  {kw} curocc() = {k} then {prefix}_ITEM = "{label}";')
        ladder.append("  endif;")
        ladder_txt = "\n".join(ladder)
        _fo_gate_p = amount_gate.format(c=prefix + "_CONSUMED", f=prefix + "_PURCHASED_PHP")
        _fo_gate_k = amount_gate.format(c=prefix + "_CONSUMED", f=prefix + "_INKIND_PHP")
        if DK_RF_STATUS:
            _fb = _dkrf_gate_branch(prefix + "_AMT_STATUS")
            _fo_gate_p = _fo_gate_p.replace("  endif;", _fb + "  endif;", 1)
            _fo_gate_k = _fo_gate_k.replace("  endif;", _fb + "  endif;", 1)
        _fo_status = _amt_status_proc(prefix)
        blocks.append(f"""PROC {prefix}_ITEM
preproc
  {{ Auto-name this grid row from the WHO/SHA item list (one occurrence per item). }}
{ladder_txt}
  noinput;
{_fo_status}
PROC {prefix}_PURCHASED_PHP
{_fo_gate_p}

PROC {prefix}_INKIND_PHP
{_fo_gate_k}
""")
        if subtotal:
            blocks.append(f"""PROC {subtotal}
preproc
  {{ Health subtotal (device-proven pattern): TOTAL field's OWN preproc + noinput, LOCAL
    accumulator; sums CONSUMED=1 rows of {prefix}_ROSTER. #834: 'in 0:99999999' excludes
    notappl AND the -98/-99 sentinels (#743). Not protect(), not a group proc. }}
  numeric nsr_i; numeric nsr_total;
  nsr_total = 0;
  do nsr_i = 1 while nsr_i <= {len(items_list)}
    if {prefix}_CONSUMED(nsr_i) = 1 then
      if {prefix}_PURCHASED_PHP(nsr_i) in 0:99999999 then
        nsr_total = nsr_total + {prefix}_PURCHASED_PHP(nsr_i);
      endif;
      if {prefix}_INKIND_PHP(nsr_i) in 0:99999999 then
        nsr_total = nsr_total + {prefix}_INKIND_PHP(nsr_i);
      endif;
    endif;
  enddo;
  {subtotal} = nsr_total;
  noinput;
""")
    return "\n".join(blocks)


def section_n_review_proc():
    """Section N end-of-section recap (htmldialog review.html) + #834 Option A completeness
    reminder. Both fire from Q186_CURRENT_INCOME preproc (first Section O field). The
    reminder is SOFT (errmsg, no reenter - a per-row reenter is what the resume replay
    tripped on, #834); it counts Section N items marked consumed whose amount is still
    blank or both-zero (the retired per-row #677 predicate) across all 7 rosters and warns
    once. Stored subtotals (Q157/Q177/Q182/Q185) read direct; restaurant/smoking/non-food
    summed here; every sum uses 'in 0:99999999' (excludes notappl + -98/-99), so an
    incomplete/blank amount can never poison the grand total. JSON: {"v":[9 php],"grand":php};
    review.html holds the labels."""
    rosters = [("N_FOOD", len(FOOD_WEEKLY_ITEMS))] + [(p, len(it)) for p, it, _ in SECTION_N_FANOUT]
    chk = [
        "  { #834 Option A: section-end completeness reminder (soft, NO reenter). Counts Section N",
        "    items marked consumed whose amount is still blank or both-zero (same predicate as the",
        "    retired per-row #677) across all 7 rosters, then warns once. Flow always continues. }",
        "  nmiss = 0;",
    ]
    for prefix, cnt in rosters:
        chk.append(f"  do mchk = 1 while mchk <= {cnt}")
        chk.append(
            f"    if {prefix}_CONSUMED(mchk) = 1"
            f" and not ({prefix}_PURCHASED_PHP(mchk) in -99, -98, 1:99999999)"
            f" and not ({prefix}_INKIND_PHP(mchk) in -99, -98, 1:99999999)"
            f" then nmiss = nmiss + 1; endif;")
        chk.append("  enddo;")
    chk += [
        "  if nmiss > 0 then",
        '    errmsg("Reminder: %d Section N item(s) marked consumed by the household still have no '
        'amount. Go back to Section N and enter the amount spent and/or the in-kind value for each '
        '(or -98 if the household does not know, -99 if they refuse). You may continue, but please '
        'check.", nmiss);',
        "  endif;",
    ]
    chk_txt = "\n".join(chk) + "\n"
    return (
"{ ---- Section N end-of-section: #834 completeness reminder + expenditure recap (review.html) ---- }\n"
"PROC Q186_CURRENT_INCOME\n"
"preproc\n"
"  { All locals declared first (CSPro: declarations precede executable statements). }\n"
"  numeric nmiss; numeric mchk;\n"
"  numeric srv_i;\n"
"  numeric srv_rest; numeric srv_smoke;\n"
"  numeric srv_nf1m; numeric srv_nf6m; numeric srv_nf12m;\n"
"  numeric srv_grand;\n"
"  string  srv_j; string srv_res;\n"
+ chk_txt +
"  { Read back the 9 Section N block subtotals to the respondent before funding sources.\n"
"    Stored subtotals read direct; restaurant/smoking/non-food summed here. Every sum uses\n"
"    'in 0:99999999' so notappl + -98/-99 are excluded. Informational modal - OK to Q186. }\n"
"  { #832/#833: restaurant (Q158) + tobacco (Q159) are N_WKOTH_ROSTER occ 1 + occ 2. }\n"
"  srv_rest = 0;\n"
"  if N_WKOTH_CONSUMED(1) = 1 then\n"
"    if N_WKOTH_PURCHASED_PHP(1) in 0:99999999 then srv_rest = srv_rest + N_WKOTH_PURCHASED_PHP(1); endif;\n"
"    if N_WKOTH_INKIND_PHP(1) in 0:99999999 then srv_rest = srv_rest + N_WKOTH_INKIND_PHP(1); endif;\n"
"  endif;\n"
"  srv_smoke = 0;\n"
"  if N_WKOTH_CONSUMED(2) = 1 then\n"
"    if N_WKOTH_PURCHASED_PHP(2) in 0:99999999 then srv_smoke = srv_smoke + N_WKOTH_PURCHASED_PHP(2); endif;\n"
"    if N_WKOTH_INKIND_PHP(2) in 0:99999999 then srv_smoke = srv_smoke + N_WKOTH_INKIND_PHP(2); endif;\n"
"  endif;\n"
"  srv_nf1m = 0;\n"
"  do srv_i = 1 while srv_i <= 8\n"
"    if N_NF1M_CONSUMED(srv_i) = 1 then\n"
"      if N_NF1M_PURCHASED_PHP(srv_i) in 0:99999999 then srv_nf1m = srv_nf1m + N_NF1M_PURCHASED_PHP(srv_i); endif;\n"
"      if N_NF1M_INKIND_PHP(srv_i) in 0:99999999 then srv_nf1m = srv_nf1m + N_NF1M_INKIND_PHP(srv_i); endif;\n"
"    endif;\n"
"  enddo;\n"
"  srv_nf6m = 0;\n"
"  do srv_i = 1 while srv_i <= 2\n"
"    if N_NF6M_CONSUMED(srv_i) = 1 then\n"
"      if N_NF6M_PURCHASED_PHP(srv_i) in 0:99999999 then srv_nf6m = srv_nf6m + N_NF6M_PURCHASED_PHP(srv_i); endif;\n"
"      if N_NF6M_INKIND_PHP(srv_i) in 0:99999999 then srv_nf6m = srv_nf6m + N_NF6M_INKIND_PHP(srv_i); endif;\n"
"    endif;\n"
"  enddo;\n"
"  srv_nf12m = 0;\n"
"  do srv_i = 1 while srv_i <= 5\n"
"    if N_NF12M_CONSUMED(srv_i) = 1 then\n"
"      if N_NF12M_PURCHASED_PHP(srv_i) in 0:99999999 then srv_nf12m = srv_nf12m + N_NF12M_PURCHASED_PHP(srv_i); endif;\n"
"      if N_NF12M_INKIND_PHP(srv_i) in 0:99999999 then srv_nf12m = srv_nf12m + N_NF12M_INKIND_PHP(srv_i); endif;\n"
"    endif;\n"
"  enddo;\n"
"  srv_grand = Q157_FOOD_SUBTOTAL_TOTAL_PHP + srv_rest + srv_smoke\n"
"            + srv_nf1m + srv_nf6m + srv_nf12m\n"
"            + Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP + Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP\n"
"            + Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP;\n"
'  srv_j = maketext("%d", Q157_FOOD_SUBTOTAL_TOTAL_PHP)\n'
'        + "," + maketext("%d", srv_rest) + "," + maketext("%d", srv_smoke)\n'
'        + "," + maketext("%d", srv_nf1m) + "," + maketext("%d", srv_nf6m) + "," + maketext("%d", srv_nf12m)\n'
'        + "," + maketext("%d", Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP)\n'
'        + "," + maketext("%d", Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP)\n'
'        + "," + maketext("%d", Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP)\n'
'        + "," + maketext("%d", srv_grand);\n'
'  srv_res = htmldialog("review.html", inputData := srv_j);\n'
    )


def skip_proc(field, cond, target):
    return f"PROC {field}\npostproc\n  if {cond} then\n    skip to {target};\n  endif;"


DISPOSITION_PROCS = """\
{ ---- #515 break-off + #561 disposition (F4) ----------------------------------------
  BREAKOFF is the case-start "Interview status" control (its own first form, so it is in
  the case tree from the first field, and the enumerator can tap back to it mid-interview).
  Leaving it "Continue" (1) is a no-op. Any other choice records the matching Result-of-
  Visit disposition and SKIPS to the closing Result-of-Visit field, so a withdrawn /
  postponed / stopped visit reaches the closing form without walking every required
  question (R4 #515). CASE_DISPOSITION (off-form) is the completeness sentinel the
  Supervisor App + CSWeb exports read (R4 #561): 0 In Progress, 1 Completed, 2 Partial.
  F4 result codes: 1 Completed, 2 Postponed, 3 Incomplete, 4 Withdraw. }
PROC BREAKOFF
preproc
  { The guard MUST list every valid code — anything outside it is silently reset to
    Continue. Widened to 1..7 on 2026-07-14; leaving it at 1..4 would have erased every
    replacement the moment the field was revisited. }
  if not (BREAKOFF in 1, 2, 3, 4, 5, 6, 7) then BREAKOFF = 1; endif;   { default "Continue" }
postproc
  if BREAKOFF <> 1 then
    { 2–4: the interview STARTED and then stopped. }
    if BREAKOFF = 2 then ENUM_RESULT_FINAL_VISIT = 4; endif;   { Withdraw Participation/Consent }
    if BREAKOFF = 3 then ENUM_RESULT_FINAL_VISIT = 2; endif;   { Postponed }
    if BREAKOFF = 4 then ENUM_RESULT_FINAL_VISIT = 3; endif;   { Incomplete }
    { 5–7: the interview NEVER STARTED (refused at the door / not found / ineligible).
      Per ASPSI, every such unit is replaced by a substitute, so all three land on
      Replaced(5) — BREAKOFF keeps the reason. Replacements = count(BREAKOFF in 5,6,7).
      Postponed(3) is NOT a replacement: that unit is revisited, not substituted. }
    if BREAKOFF in 5, 6, 7 then ENUM_RESULT_FINAL_VISIT = 5; endif;   { Replaced }
    CASE_DISPOSITION = 2;   { partial / not completed }
    skip to ENUM_RESULT_FINAL_VISIT;
  endif;

PROC ENUM_RESULT_FINAL_VISIT
postproc
  { #561: classify from the final Result-of-Visit. F4 Completed = code 1 only. }
  if ENUM_RESULT_FINAL_VISIT = 1 then
    CASE_DISPOSITION = 1;
  else
    CASE_DISPOSITION = 2;
  endif;
  { #515: a Postponed (2) / Withdraw (4) visit had no interview, so there is nothing to
    photograph — end the case here instead of walking into the Verification Photo form,
    whose trigger field would otherwise loop on an out-of-range stop. Codes 1/3 fall
    through to the photo as before (this matches the CAPTURE_VERIFICATION_PHOTO gate). }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 3) then
    endlevel;
  endif;
"""


def main():
    names = dcf_item_names()
    parts = [HEADER, "", CONTROL_PROCS, "", DISPOSITION_PROCS, "", ROSTER_PROCS, "", PRIV_ROSTER_PROCS, "",
             section_n_food_roster_procs(), "",
             section_n_fanout_procs(), "",
             section_n_review_proc(), "",
             BILL_VALIDATION, "", EXTRA_PROCS, "", VALIDATION_PROCS, ""]
    covered = {"BREAKOFF", "ENUM_RESULT_FINAL_VISIT", "CASE_DISPOSITION",  # #515/#561 disposition PROCs
               "AREA_HAS_BUCAS", "AREA_HAS_GAMOT",  # #796/#797 auto-answer + noinput (EXTRA_PROCS)
               "MEMBER_LINE_NO", "Q34_RELATIONSHIP", "Q35_HAS_DISABILITY",
               # Column-wise Section C (2026-06-26): per-occurrence preproc gates live in
               # ROSTER_PROCS for every conditional roster question. Q35/Q45 are always asked
               # (no PROC now) but stay covered so no auto-gen mis-fires on them.
               "Q36_SPECIFY_DISABILITY", "Q37_PWD_CARD", "Q38_DISABILITY_TYPE",  # #604/#605 disability chain
               "Q45_PHILHEALTH_REG", "Q45_1_PIN_REG_WHEN", "Q46_MEMBER_CATEGORY",  # #563/#565 PhilHealth Yes-only
               "Q45_2_WHY_NOT_REG",   # #795: No-only gate (ROSTER_PROCS); _OTHER_TXT stays auto-gen
               "PRIV_MEMBER_LINE_NO", "Q48_OTHER_INS_REG",  # #525/#612/#613: priv-ins 2nd pass
               "N_FOOD_ITEM", "N_FOOD_CONSUMED", "N_FOOD_PURCHASED_PHP",   # Option C food roster:
               "N_FOOD_INKIND_PHP", "Q157_FOOD_SUBTOTAL_TOTAL_PHP",   # bespoke procs (2026-07-03)
               # Fan-out rosters + health subtotals (2026-07-03): section_n_fanout_procs
               "N_NF1M_ITEM", "N_NF1M_CONSUMED", "N_NF1M_PURCHASED_PHP", "N_NF1M_INKIND_PHP",
               "N_NF6M_ITEM", "N_NF6M_CONSUMED", "N_NF6M_PURCHASED_PHP", "N_NF6M_INKIND_PHP",
               "N_NF12M_ITEM", "N_NF12M_CONSUMED", "N_NF12M_PURCHASED_PHP", "N_NF12M_INKIND_PHP",
               "N_H12M_ITEM", "N_H12M_CONSUMED", "N_H12M_PURCHASED_PHP", "N_H12M_INKIND_PHP",
               "N_H6M_ITEM", "N_H6M_CONSUMED", "N_H6M_PURCHASED_PHP", "N_H6M_INKIND_PHP",
               "N_H1M_ITEM", "N_H1M_CONSUMED", "N_H1M_PURCHASED_PHP", "N_H1M_INKIND_PHP",
               "Q177_HEALTH_12M_SUBTOTAL_TOTAL_PHP", "Q182_HEALTH_6M_SUBTOTAL_TOTAL_PHP",
               "Q185_HEALTH_1M_SUBTOTAL_TOTAL_PHP",
               # #7 DK/RF amount-status gate fields (exist only when DK_RF_STATUS is on):
               "N_FOOD_AMT_STATUS", "N_NF1M_AMT_STATUS", "N_NF6M_AMT_STATUS", "N_NF12M_AMT_STATUS",
               "N_H12M_AMT_STATUS", "N_H6M_AMT_STATUS", "N_H1M_AMT_STATUS",
               "N_WKOTH_AMT_STATUS",
               "Q186_CURRENT_INCOME",   # Section N recap htmldialog fires from its preproc
               "Q49_PRIVATE_INS", "C_HOUSEHOLD_ROSTER_FORM", "Q47_HH_HAS_PRIVATE_INS",
               "Q141_1_NO_RECEIPT_AMT_PHP",
               # (#615's ungated-_OTHER_TXT workaround removed by #1098: Q141's specify
               # box is now a gated Check Box _OTHER_TXT via CHECKBOX_OTHER_CODE=07,
               # so CHECKBOX_COVERED carries Q141_BILL_ITEMS_OTHER_TXT.)
               "Q1_IS_HH_HEAD",  # EXTRA_PROCS (#520 soft confirm)
               "Q135_ZBB_OOP",  # EXTRA_PROCS (#664 DOH-retained gate)
               "Q76_BRAND_OR_GEN", "Q79_REG_SOURCE",  # EXTRA_PROCS (Q78_WHY_BRANDED now a Check Box base, covered via CHECKBOX_COVERED)
               "Q112_VISITED",  # EXTRA_PROCS (#590-593 Q112 referral-visit multi-branch)
               "Q117_SPECIALIST_FOLLOWUP",  # EXTRA_PROCS (#816 Q112=Yes gate + spec §K Q117=No -> Q119)
               "Q194_OTHER_SOURCE",  # EXTRA_PROCS (#684 >=1 funding-source aggregate check)
               "Q2_BIRTH_MONTH", "Q2_BIRTH_YEAR", "Q2_1_AGE", "Q19_HH_SIZE_TOTAL",
               "Q20_HH_CHILDREN", "Q21_HH_SENIORS", "Q32_AGE", "Q39_CIVIL_STATUS",
               "Q18_INCOME_BRACKET",  # VALIDATION_PROCS
               # #529: the 17 select_all -> Check Box bases (+ their _OTHER_TXT) get
               # bespoke PROCs from CHECKBOX_MULTISELECT_PROCS (in EXTRA_PROCS) — seed
               # them into `covered` so the dcf-driven other-specify / select-all
               # auto-gens never mis-fire on the alpha checkbox field or its gated text.
               *CHECKBOX_COVERED}

    parts.append("{ ---- Skip logic: awareness / primary-care / bill-recall ---- }")
    for field, cond, target in SKIP_RULES:
        if field in covered:
            raise SystemExit(f"PROC collision: {field}")
        covered.add(field)
        parts.append(skip_proc(field, cond, target)); parts.append("")

    # Desk-test pilot (dormant): F4_PILOT_JUMP=<FIELD> at generation time emits a
    # Q3 postproc jump straight to the named field, so deep questions are reachable
    # in a few fields for proof-of-fix captures / engine checks (F3's F3_PILOT_JUMP
    # pattern; host = Q3_SEX — Q1/Q2 already own PROCs). OFF by default — NEVER set
    # for a deploy build.
    _pilot_target = os.environ.get("F4_PILOT_JUMP")
    if _pilot_target and "Q3_SEX" not in covered:
        covered.add("Q3_SEX")
        parts.append("{ ---- desk-test pilot: jump to %s (dormant) ---- }" % _pilot_target)
        parts.append("PROC Q3_SEX" + chr(10) + "postproc" + chr(10)
                     + f"  skip to {_pilot_target};")
        parts.append("")

    # #708/#709 combined-view: the Section N amount gate now lives in each item's
    # *_CONSUMED POSTPROC (DG-safe: visited field, no `skip to` inside the DG block) and
    # the #617 subtotal-init lives in some of those same *_CONSUMED PREPROCs. Build both
    # dicts here and MERGE per field into one PROC block (preproc + postproc), so the
    # panel-first-member fields (Q144/Q175/Q178/Q183) carry both sections without a
    # duplicate-PROC collision. (gate_procs[field] = 'postproc\n...'; st_init full PROC
    # strings — split out the preproc body for the merge.)
    # Option C (2026-07-03): the rosterized food block (N_FOOD_*) carries bespoke procs
    # in section_n_food_roster_procs() — exclude its fields from the flat Section N
    # suffix-driven auto-gens (gate / subtotal / #677 validation) so nothing double-emits.
    flat_names = [n for n in names if not n.startswith(
        ("N_FOOD_", "N_WKOTH_", "N_NF1M_", "N_NF6M_", "N_NF12M_", "N_H12M_", "N_H6M_", "N_H1M_"))]
    # #832/#833: flat expenditure amounts (Q158/Q159) are now gated in their OWN preproc
    # (flat_expenditure_amount_procs, roster parity). The protect-based CONSUMED-postproc gate
    # (expenditure_gate_procs) is retired for the DG combined view — it left amounts locked.
    gate_procs = {}
    st_procs = subtotal_init_compute_procs(flat_names, dcf_items_map())

    def _preproc_body(proc_text):
        # st_procs entries are 'PROC <field>\npreproc\n<body>' — return '<body>'.
        return proc_text.split("\npreproc\n", 1)[1]

    parts.append("{ ---- Section N consumed-gate (#169) + subtotal init/compute "
                 "(#9/#617) — merged per _CONSUMED field (#708/#709 combined-view) ---- }")
    handled_consumed = set()
    for field, postproc_body in sorted(gate_procs.items()):
        if field in covered:
            # a _CONSUMED field with a bespoke PROC elsewhere — should not happen for
            # Section N, but skip defensively rather than emit a duplicate.
            continue
        if field in st_procs:
            preproc_body = _preproc_body(st_procs[field])
            proc = f"PROC {field}\npreproc\n{preproc_body}\n{postproc_body}"
            handled_consumed.add(field)
        else:
            proc = f"PROC {field}\n{postproc_body}"
        covered.add(field); parts.append(proc); parts.append("")

    # Remaining subtotal procs whose field was NOT a gated _CONSUMED (the follower fields,
    # and any _CONSUMED panel-first member with no amounts — none today). Emit standalone.
    parts.append("{ ---- Section N subtotals — auto-compute + protect at follower (#9/#617, spec §4.9) ---- }")
    for field, proc in sorted(st_procs.items()):
        if field in handled_consumed:
            continue
        if field in covered:
            raise SystemExit(f"#617 subtotal proc collides with an existing proc: {field}")
        covered.add(field); parts.append(proc); parts.append("")

    # #832/#833: flat Section N items (Q158/Q159) — roster-parity amount gate (noinput +
    # special() pre-fill, no protect) with #677 folded onto the last amount's postproc.
    parts.append("{ ---- Section N flat items (Q158/Q159): roster-parity amount gate + #677 (#832/#833) ---- }")
    for field, proc in sorted(flat_expenditure_amount_procs(flat_names).items()):
        if field in covered:
            raise SystemExit(f"flat expenditure amount proc collides with an existing proc: {field}")
        covered.add(field); parts.append(proc); parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — UHC9 dual-other ---- }")
    for field, proc in sorted(uhc9_other_specify_procs(names).items()):
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append("")

    # Auto-derived single-choice + select-all 'Other (specify)' enforcement (#148).
    os_procs, os_map, os_skipped = other_specify_procs(dcf_items_map())
    parts.append("{ ---- 'Other (specify)' enforcement — single-choice + select-all "
                 f"(auto-derived from dcf: {len(os_procs)} items) ---- }}")
    for field, proc in sorted(os_procs.items()):
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append("")

    # (Section N subtotal procs are now emitted above, merged into / alongside the
    # consumed-gate procs — see the #708/#709 combined-view block.)

    # Auto-derived select-all validation: >=1 option ticked.
    sa_procs, sa_bases = select_all_validation_procs(dcf_items_map())
    sa_emitted = 0
    parts.append("{ ---- Select-all validation — >=1 option ticked (auto-derived from dcf) ---- }")
    for field, proc in sorted(sa_procs.items()):
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append(""); sa_emitted += 1

    # Per-item numeric range checks + date-ordering cross-field (spec §3.1/§3.2/§3.6/§3.12).
    parts.append("{ ---- Range + cross-field validations (spec §3.1-§3.12) ---- }")
    rng_emitted = 0
    for field, lo, hi, soft in RANGE_CHECKS:
        if field in covered:
            continue
        covered.add(field)
        # #793 missing-value standard: the household-income amount accepts -98/-99 sentinels.
        # (Q199_WTP_CONSULT is a coded 1-9 field, not a free peso amount — no sentinels.)
        allow_sent = field == "Q18_INCOME_AMOUNT"
        parts.append(range_check_proc(field, lo, hi, hard=True, soft_over=soft, allow_sentinels=allow_sent))
        parts.append(""); rng_emitted += 1
    for field, proc in CUSTOM_VALIDATION:
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append(""); rng_emitted += 1

    parts.append(TODO_NOTE)
    text = "\n".join(parts).rstrip() + "\n"
    # Column-wise Section C: bound every per-question roster form to Q19 members (prevents
    # phantom occurrences on advance past the last member). Done as a text pass so it covers
    # bespoke gates, auto-gen other-specify, and fields with no PROC uniformly.
    rb_fields = roster_bound_fields()
    text = inject_roster_occurrence_bounds(text, rb_fields)
    # R2 (2026-07-03): inline errmsg literals -> numbered messages + .ent.mgf
    # (stable numbers via messages-registry.json; displayed text unchanged).
    text = numberize_errmsgs(text, HERE, OUT.with_suffix(".mgf"), "HouseholdSurvey")
    OUT.write_text(text, encoding="utf-8")
    procs = [l for l in text.splitlines() if l.startswith("PROC ")]
    assert len(procs) == len(set(procs)), "duplicate PROC names emitted"
    print(f"Wrote {OUT} ({len(text)} chars, {len(procs)} PROC blocks, no dup names).")
    print(f"  other-specify enforcement: {len(os_procs)} auto-derived "
          f"({sum(1 for _, d in os_map if d.startswith('single'))} single + "
          f"{sum(1 for _, d in os_map if d.startswith('select'))} select-all)")
    if os_skipped:
        print(f"  other-specify SKIPPED (manual review — no resolvable trigger): {', '.join(os_skipped)}")
    print(f"  select-all validation: {sa_emitted} groups got a '>=1 ticked' check (of {len(sa_bases)} detected)")
    print(f"  Section N subtotals: {len(st_procs)} init/compute procs (#617 init=0 + follower sum)")
    print(f"  range/cross-field: {rng_emitted} procs")
    print("  NEXT: create the F4 .ent in Designer (input dcf + generated.fmf), compile,")
    print("  then verify the ROSTER + expenditure flow in CSEntry (riskiest untested part).")


if __name__ == "__main__":
    main()
