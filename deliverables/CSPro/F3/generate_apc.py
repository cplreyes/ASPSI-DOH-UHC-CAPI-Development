#!/usr/bin/env python3
"""
F3 Patient Survey — CAPI logic (.ent.apc) generator.

Emits `PatientSurvey.ent.apc` from the reviewed spec
(`F3-Skip-Logic-and-Validations.md`). Same pattern as F1's generate_apc.py:
generator-over-hand-edit, helpers via #include, dcf-driven other-specify.

Covers (generator side): #164 Outpatient/Inpatient branching (PATIENT_TYPE gates
Section G vs H, both flow to I), consent terminator, PSGC cascade (facility +
patient P_* set), GPS + verification photo, F1 linkage, the G/H/I skip logic,
and UHC9 'Other (specify)' enforcement.

  ⚠️  UNVERIFIED until compiled in CSPro Designer + run in CSEntry (no CSPro
      toolchain here). First Designer compile is the real test; fix any item-name
      / option-code mismatch at the source tables. Skip logic for Sections A–F
      and J–L + section-specific validations are a follow-up pass (see TODO).

Invoke:  python generate_apc.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import (
    other_specify_procs, select_all_validation_procs,
    range_check_proc, amount_required_procs,
)

# Per-item numeric range checks (spec §3.6/§3.9/§3.10/§3.13). (field, lo, hi, soft_over)
# Q106_DAYS is handled in CUSTOM_VALIDATION (range + pair-sanity together).
RANGE_CHECKS = [
    ("Q58_WAIT_DAYS",         0, 365,       None),
    ("Q58_WAIT_MINUTES",      0, 1440,      None),
    ("Q69_USUAL_TRAVEL_HH",   0, 24,        None),
    ("Q69_USUAL_TRAVEL_MM",   0, 59,        None),
    ("Q72_NEAREST_TRAVEL_HH", 0, 24,        None),
    ("Q72_NEAREST_TRAVEL_MM", 0, 59,        None),
    ("Q97_FINAL_AMOUNT",      0, 99999999,  None),
    ("Q106_NIGHTS",           0, 365,       90),
    ("Q115_FINAL_CASH",       0, 999999999, None),
    ("Q150_TRAVEL_HH",        0, 24,        None),
    ("Q150_TRAVEL_MM",        0, 59,        None),
]

# Cross-field / pair-sanity validations that need a custom body (spec §3.10/§3.1).
CUSTOM_VALIDATION = [
    ("Q106_DAYS",
     "PROC Q106_DAYS\npostproc\n"
     "  if Q106_DAYS < 0 or Q106_DAYS > 365 then\n"
     "    errmsg(\"Q106_DAYS must be between 0 and 365.\");\n    reenter;\n  endif;\n"
     "  if Q106_DAYS > 90 then\n"
     "    errmsg(\"Length of stay (%d days) is unusually long — confirm.\", Q106_DAYS);\n  endif;\n"
     "  if Q106_NIGHTS + Q106_DAYS < 1 then\n"
     "    errmsg(\"A confinement must be at least 1 day (nights + days).\");\n    reenter;\n  endif;\n"
     "  { #554: nights/days pair sanity — neither can be 0 while the other is > 1 }\n"
     "  if Q106_DAYS > 1 and Q106_NIGHTS = 0 then\n"
     "    errmsg(\"%d day(s) of stay but 0 nights — nights cannot be 0 when days is greater than 1. Please correct.\", Q106_DAYS);\n    reenter;\n  endif;\n"
     "  if Q106_NIGHTS > 1 and Q106_DAYS = 0 then\n"
     "    errmsg(\"%d night(s) of stay but 0 days — days cannot be 0 when nights is greater than 1. Please correct.\", Q106_NIGHTS);\n    reenter;\n  endif;"),
    ("DATE_FINAL_VISIT",
     "PROC DATE_FINAL_VISIT\npostproc\n"
     "  if DATE_FINAL_VISIT < DATE_FIRST_VISITED then\n"
     "    errmsg(\"Final-visit date cannot be earlier than the first-visit date.\");\n    reenter;\n  endif;"),
]

# SOFT plausibility cross-field warnings (spec §3.5/3.6/3.7/3.9/3.10/3.12/3.13).
# errmsg WITHOUT reenter = warn-and-continue. (attach_field, inner_body). The body
# is merged into attach_field's existing PROC if one exists, else emitted as a new
# PROC. attach_field is the LAST input field in form order so all refs are set.
SOFT_CROSS = [
    # Q45_CATEGORY senior-citizen soft-warn folded into its EXTRA_PROCS PROC (#402 gate).
    ("Q58_WAIT_MINUTES",
     "  if Q53_HAS_PCP = 1 and Q58_WAIT_DAYS = 0 and Q58_WAIT_MINUTES = 0 then\n"
     "    errmsg(\"Q58 wait time is 0 days and 0 minutes — confirm there was genuinely no wait.\");\n  endif;"),
    ("Q84_SERVICE_TYPE",
     "  if Q84_SERVICE_TYPE = 1 and PATIENT_TYPE = 2 then\n"
     "    errmsg(\"Q84 = Outpatient care but the case is flagged Inpatient (PATIENT_TYPE) — verify routing.\");\n  endif;\n"
     "  if Q84_SERVICE_TYPE = 2 and PATIENT_TYPE = 1 then\n"
     "    errmsg(\"Q84 = Inpatient care but the case is flagged Outpatient (PATIENT_TYPE) — verify routing.\");\n  endif;"),
    # #673: the Q85 'No condition / regular check-up' confirm + 'stands alone' soft-warns moved
    # into the Q85_CONDITIONS checkbox PROC's postextra block (CHECKBOX_CONVERT). Q85 is now a
    # Check Box, so the old _O19/_Oxx Yes/No flags this warn referenced no longer exist.
    ("Q144_QUALITY",
     "  if Q143_RECOMMEND = 1 and Q144_QUALITY >= 4 and Q144_QUALITY <= 5 then\n"
     "    errmsg(\"Patient would recommend (Q143=Yes) yet rated overall quality dissatisfied (Q144) — confirm.\");\n  endif;\n"
     "  if Q143_RECOMMEND = 2 and Q144_QUALITY >= 1 and Q144_QUALITY <= 2 then\n"
     "    errmsg(\"Patient would NOT recommend (Q143=No) yet rated overall quality satisfied (Q144) — confirm.\");\n  endif;"),
    ("Q150_TRAVEL_MM",
     "  if Q145_PURCHASE_FREQ <> 5 and Q150_TRAVEL_HH = 0 and Q150_TRAVEL_MM = 0 then\n"
     "    errmsg(\"Q150 travel time to pharmacy is 0h 0m — confirm the pharmacy is effectively on-site.\");\n  endif;"),
    ("Q17_INCOME_SOURCE",
     "  if (Q16_EMPLOYMENT = 4 or Q16_EMPLOYMENT = 5) and Q17_INCOME_SOURCE >= 1 and Q17_INCOME_SOURCE <= 5 then\n"
     "    errmsg(\"Q16 = unemployed but Q17 reports a paid-work income source — confirm.\");\n  endif;"),
    ("Q29_SEC_CLASS",
     # #631: re-mapped to the new 11-band income value set, preserving the original peso
     # intent (low ~under 100k; high ~100k+). SOFT confirm only. ASPSI may recalibrate the
     # socio-economic-class income thresholds against the updated brackets.
     # #398: 'Don't know' income (99) is out-of-range — bound the high-bracket test to the
     # 11 real bands so a DK answer doesn't false-trip the Class D/E "high bracket" warn.
     "  if Q29_SEC_CLASS = 1 and Q18_INCOME_BRACKET >= 1 and Q18_INCOME_BRACKET <= 2 then\n"
     "    errmsg(\"Q29 = socio-economic Class A/B but income is in the lowest bracket — confirm.\");\n  endif;\n"
     "  if Q29_SEC_CLASS = 3 and Q18_INCOME_BRACKET >= 3 and Q18_INCOME_BRACKET <= 11 then\n"
     "    errmsg(\"Q29 = socio-economic Class D/E but income is in a high bracket — confirm.\");\n  endif;"),
    ("Q115_FINAL_CASH",
     # Option B fan-out (#691): Q107 out-of-pocket is now a roster row, summed via
     # q107_oop() (was the flat Q107_PAY_01_AMT).
     "  if q107_oop() > 0 and (Q115_FINAL_CASH < q107_oop() * 0.9\n"
     "     or Q115_FINAL_CASH > q107_oop() * 1.1) then\n"
     "    errmsg(\"Q115 final cash differs by more than 10 percent from the out-of-pocket bill line (Q107) — confirm.\");\n  endif;"),
    ("Q97_FINAL_AMOUNT",
     # Option B (pilot + fan-out): Q92/Q94/Q96 out-of-pocket are all roster rows now,
     # summed via q92_oop()/q94_oop()/q96_oop() (was the flat Q9n_PAY_01_AMT fields).
     "  if Q97_FINAL_AMOUNT > 0 and (q92_oop() + q94_oop() + q96_oop()) > 0\n"
     "     and (Q97_FINAL_AMOUNT < (q92_oop() + q94_oop() + q96_oop()) * 0.9\n"
     "          or Q97_FINAL_AMOUNT > (q92_oop() + q94_oop() + q96_oop()) * 1.1) then\n"
     "    errmsg(\"Q97 final amount differs by more than 10 percent from the out-of-pocket lines (Q92/Q94/Q96) — confirm.\");\n  endif;"),
]


# ============================================================
# Q92 payment roster (Option B redesign — pilot; fixed 2026-06-19 after Marriz test)
# ============================================================
# The flat 8-source Yes/No matrix + per-source _AMT became a CheckBox (Q92_SOURCES)
# feeding a repeating roster (Q92_PAY_ROSTER). One occurrence per ticked source.
# FIXES after the Marriz test video (checkbox jumped straight to Q93 — grid skipped):
#   1. The roster record is now required=True (generate_dcf) so CSEntry auto-enters it;
#      Q92_SOURCES hard-requires >=1 ticked so the required record always has >=1 row.
#   2. Membership uses LITERAL 2-char pos() codes ("01".."08") — the proven CheckBox
#      idiom in this generator — NOT edit("99",k) (an unverified format that may have
#      yielded space-padded codes, leaving nsel=0 -> endgroup -> skipped grid).
#   3. Q92_PAY_AMT is left ENTERABLE on every row (default 0 for non-money sources) so
#      each occurrence has a stop — avoids a protected-only "zero-stop" row that could
#      hang the roster. Only Out-of-pocket(1)/Donation(2) carry a real amount; the AMT
#      postproc forces 0 back on any non-money source. Q92_PAY_SRC stays auto + protected.
Q92_ROSTER_PROCS = """\
{ ---- Q92 consultation-cost payment roster (Option B pilot) ---- }
PROC Q92_SOURCES
postproc
  { Require >=1 source ticked — the roster is a required record and needs >=1 row. }
  numeric nck;
  nck = 0;
  if pos("01", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("02", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("03", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("04", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("05", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("06", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("07", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if pos("08", Q92_SOURCES) > 0 then nck = nck + 1; endif;
  if nck = 0 then
    errmsg("92. Tick at least one payment source before continuing.");
    reenter;
  endif;

PROC Q92_PAY_LINE
preproc
  { Build one roster row per ticked source (canonical order 01..08). The curocc()-th
    ticked source -> Q92_PAY_SRC (auto + protected); end once past the last ticked
    source. Non-money sources default to amount 0 (still enterable, so the row has a
    stop). Re-runs on back-navigation. }
  numeric nsel; numeric seen;
  nsel = 0;
  if pos("01", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("02", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("03", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("04", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("05", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("06", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("07", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("08", Q92_SOURCES) > 0 then nsel = nsel + 1; endif;
  if curocc() > nsel then
    endgroup;
  endif;
  seen = 0;
  if pos("01", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 1; endif; endif;
  if pos("02", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 2; endif; endif;
  if pos("03", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 3; endif; endif;
  if pos("04", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 4; endif; endif;
  if pos("05", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 5; endif; endif;
  if pos("06", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 6; endif; endif;
  if pos("07", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 7; endif; endif;
  if pos("08", Q92_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q92_PAY_SRC = 8; endif; endif;
  protect(Q92_PAY_SRC, true);
  if Q92_PAY_SRC <> 1 and Q92_PAY_SRC <> 2 and Q92_PAY_SRC <> 7 then
    Q92_PAY_AMT = 0;   { #781: non-money source -> default 0. In-kind(7) is a money source for Q92 per ASPSI (2026-06-25). Still enterable so the row stops. }
  endif;
  Q92_PAY_LINE = curocc();
  noinput;

PROC Q92_PAY_AMT
postproc
  if Q92_PAY_AMT < 0 then
    errmsg("92. Amount cannot be negative.");
    reenter;
  endif;
  if Q92_PAY_SRC <> 1 and Q92_PAY_SRC <> 2 and Q92_PAY_SRC <> 7 and Q92_PAY_AMT <> 0 then
    errmsg("92. This source has no out-of-pocket cost — amount reset to 0.");
    Q92_PAY_AMT = 0;
  endif;
  if (Q92_PAY_SRC = 1 or Q92_PAY_SRC = 2 or Q92_PAY_SRC = 7) and Q92_PAY_AMT = 0 then
    errmsg("92. Please enter an amount greater than 0 — you selected this as a paid source (in-kind valued in pesos).");
    reenter;
  endif;
"""


# Q97.1 other-items-in-bill — Option B ROSTER (Shape B, 2026-06-19).
# Supersedes the 2-form-flat layout. SCREEN 1: Q971_SOURCES CheckBox. SCREEN 2:
# Q971_ROSTER grid (one row per ticked category; every row's amount is enterable —
# no zeroing/gating because ALL Q97.1 categories carry an amount). SCREEN 3:
# Q971_OTHER_TXT gated on pos("04", Q971_SOURCES) (after the grid, own screen).
#
# Rules (from the skill recipe):
#   1. Gate from Q971_PAY_LINE preproc (a visited field) — never from a protected field.
#   2. Literal pos("01".."04") — NEVER edit("99",k) (padded-code bug, see Q92 comment).
#   3. Do NOT protect Q971_PAY_AMT — every row is enterable (protecting hangs the roster).
#   4. Q971_PAY_SRC is auto-set + protected (correct — it's the source label, not an input).
Q971_ROSTER_PROCS = """\
{ ---- Q97.1 other-items-in-bill — CheckBox + roster (Option B Shape B) ---- }
PROC Q971_SOURCES
postproc
  { Require >=1 item ticked. The roster proc (Q971_PAY_LINE preproc, a visited field)
    handles population — gating here covers the >=1 requirement before the grid opens. }
  if length(strip(Q971_SOURCES)) = 0 then
    errmsg("97.1 Tick at least one item included in the bill (or correct Q97 if none).");
    reenter;
  endif;

PROC Q971_PAY_LINE
preproc
  { Build one roster row per ticked category (canonical order 01..04). The curocc()-th
    ticked category -> Q971_PAY_SRC (auto + protected); end once past the last ticked
    category. Every row's amount stays ENTERABLE (no zeroing — all Q97.1 categories
    carry an amount). Re-runs on back-navigation. }
  numeric nsel; numeric seen;
  nsel = 0;
  if pos("01", Q971_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("02", Q971_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("03", Q971_SOURCES) > 0 then nsel = nsel + 1; endif;
  if pos("04", Q971_SOURCES) > 0 then nsel = nsel + 1; endif;
  if curocc() > nsel then endgroup; endif;
  seen = 0;
  if pos("01", Q971_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q971_PAY_SRC = 1; endif; endif;
  if pos("02", Q971_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q971_PAY_SRC = 2; endif; endif;
  if pos("03", Q971_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q971_PAY_SRC = 3; endif; endif;
  if pos("04", Q971_SOURCES) > 0 then seen = seen + 1; if seen = curocc() then Q971_PAY_SRC = 4; endif; endif;
  protect(Q971_PAY_SRC, true);
  Q971_PAY_LINE = curocc();
  noinput;

PROC Q971_PAY_AMT
postproc
  if Q971_PAY_AMT < 0 then
    errmsg("97.1 Amount cannot be negative.");
    reenter;
  endif;

PROC Q971_OTHER_TXT
preproc
  if pos("04", Q971_SOURCES) = 0 then
    Q971_OTHER_TXT = "";   { 'Other expenses' (04) not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("04", Q971_SOURCES) > 0 and length(strip(Q971_OTHER_TXT)) = 0 then
    errmsg("97.1 'Other expenses' was ticked — please specify.");
    reenter;
  endif;
"""


# ============================================================
# Roster-proc generator (Option B fan-out, 2026-06-19)
# ============================================================
# Reproduces the proven, device-validated Q92 (PARTIAL) / Q971 (ALL-amount) patterns
# for the rest of the F3 cost-matrix cluster. Q92/Q971 keep their hand-written constants
# above (deployed verbatim); this generator emits the NEW conversions only.
#
# Footgun discipline (carried from Q92/Q971; see the skill §3/§6):
#   - LITERAL pos("01".."NN") membership — one explicit line per option code. NEVER
#     edit("99",k) (space-padded keys -> nsel=0 -> endgroup -> grid skipped).
#   - Gate from the LINE preproc (a VISITED field), never a protected field's own preproc.
#   - Do NOT protect the AMT field — every row stays enterable (protecting hangs the
#     roster). PARTIAL matrices default non-money rows to 0 (still enterable); ALL-amount
#     matrices leave every row enterable with no zeroing.
def build_roster_procs(q_no, q_label, sources, amt_codes,
                       require_msg, gated_texts=None, require_positive=False):
    """Emit the SOURCES/LINE/AMT (+ optional gated specify-text) PROCs for one
    CheckBox->roster conversion.
      q_no        question stem used in field names (Q<q_no>_SOURCES / _PAY_LINE / ...).
      sources     [(label, "NN")] — the 2-char option codes (canonical order).
      amt_codes   set of 2-char codes that carry a real amount. Empty set => ALL-amount
                  (no zeroing). A strict subset => PARTIAL (Q92 pattern: non-money rows
                  default 0 but stay enterable; the AMT postproc forces 0 back).
      gated_texts [(code, field, prompt)] — specify-text fields gated on pos(code,SOURCES).
    """
    codes = [c for _, c in sources]
    amt_nums = sorted(int(c) for c in amt_codes)
    src = f"Q{q_no}_SOURCES"
    line = f"Q{q_no}_PAY_LINE"
    srcf = f"Q{q_no}_PAY_SRC"
    amtf = f"Q{q_no}_PAY_AMT"
    partial = bool(amt_codes) and len(amt_codes) < len(codes)
    # 2-digit codes (>=10) make the per-code pos() population loop UNSAFE: pos("10", field)
    # substring-matches "10" ACROSS a 2-char code boundary (ticking 01+02 packs to "0102" and
    # falsely fires "10"). When any code reaches 2 digits, index the packed CheckBox in aligned
    # 2-char chunks instead. (#450 cross-boundary fix class — Q98/Q107/Q113.)
    two_digit = any(int(c) >= 10 for c in codes)

    L = [f"{{ ---- Q{q_no} payment roster (Option B fan-out) ---- }}",
         f"PROC {src}", "postproc",
         "  { Require >=1 source ticked — the roster grid needs >=1 row. }"]
    L.append(f"  if length(strip({src})) = 0 then")
    L.append(f'    errmsg("{require_msg}");')
    L += ["    reenter;", "  endif;", ""]

    L += [f"PROC {line}", "preproc",
          "  { Build one row per ticked source (canonical order). The curocc()-th ticked",
          f"    source -> {srcf} (auto + protected); end once past the last ticked source."
          + (" Non-money rows" if partial else " Every row"),
          ("    default amount 0 but stay enterable." if partial
           else "    amount stays enterable (all sources carry an amount)."),
          "    Re-runs on back-navigation. }"]
    if two_digit:
        # Aligned 2-char chunk indexing (2-digit-code-safe). Every ticked code => one row in
        # packed order and there are NO excluded codes here, so the curocc()-th row's source is
        # simply the curocc()-th chunk — no per-code loop needed. (do..while + [p:2] + tonumber
        # are the only forms the strict Publish packager accepts; see the #450 build notes.)
        L += ["  numeric nsel; numeric pp;",
              f"  nsel = length(strip({src})) / 2;",
              "  if curocc() > nsel then endgroup; endif;",
              "  pp = (curocc() - 1) * 2 + 1;",
              f"  {srcf} = tonumber({src}[pp:2]);"]
    else:
        L += ["  numeric nsel; numeric seen;", "  nsel = 0;"]
        for c in codes:
            L.append(f'  if pos("{c}", {src}) > 0 then nsel = nsel + 1; endif;')
        L.append("  if curocc() > nsel then endgroup; endif;")
        L.append("  seen = 0;")
        for c in codes:
            L.append(f'  if pos("{c}", {src}) > 0 then seen = seen + 1; '
                     f"if seen = curocc() then {srcf} = {int(c)}; endif; endif;")
    L.append(f"  protect({srcf}, true);")
    if partial:
        cond = " and ".join(f"{srcf} <> {n}" for n in amt_nums)
        L += [f"  if {cond} then",
              f"    {amtf} = 0;   {{ non-money source -> default 0; still enterable }}",
              "  endif;"]
    L += [f"  {line} = curocc();", "  noinput;", ""]

    L += [f"PROC {amtf}", "postproc",
          f"  if {amtf} < 0 then",
          f'    errmsg("{q_no}. Amount cannot be negative.");',
          "    reenter;", "  endif;"]
    if partial:
        cond = " and ".join(f"{srcf} <> {n}" for n in amt_nums)
        L += [f"  if {cond} and {amtf} <> 0 then",
              f'    errmsg("{q_no}. This source has no out-of-pocket cost — amount reset to 0.");',
              f"    {amtf} = 0;", "  endif;"]
    if require_positive:
        # #749: a ticked PAID source must carry an amount > 0 — entering 0 for a selected
        # paying source is a data-entry slip. Partial rosters gate only the money-code rows
        # (non-money rows are forced to 0 just above and stay 0); all-amount rosters gate
        # every row (every ticked source is, by definition, a paid source).
        if partial:
            money_cond = " or ".join(f"{srcf} = {n}" for n in amt_nums)
            L += [f"  if ({money_cond}) and {amtf} = 0 then"]
        else:
            L += [f"  if {amtf} = 0 then"]
        L += [f'    errmsg("{q_no}. Please enter an amount greater than 0 — you selected '
              'this as a paid source/item.");',
              "    reenter;", "  endif;"]

    for code, field, prompt in (gated_texts or []):
        if two_digit:
            # 2-digit-safe membership (chunk-scan) — same reason as the population loop:
            # pos("{code}", …) could cross-boundary false-match (e.g. Q107 code "10" from 01+02).
            L += ["", f"PROC {field}", "preproc",
                  "  numeric gk; numeric gn; numeric gp; numeric gt;",
                  f"  gt = 0; gn = length(strip({src})) / 2;",
                  "  do gk = 1 while gk <= gn",
                  "    gp = (gk - 1) * 2 + 1;",
                  f'    if {src}[gp:2] = "{code}" then gt = 1; endif;',
                  "  enddo;",
                  "  if gt = 0 then",
                  f'    {field} = "";   {{ not ticked -> not enterable }}',
                  "    noinput;", "  endif;", "postproc",
                  "  numeric hk; numeric hn; numeric hp; numeric ht;",
                  f"  ht = 0; hn = length(strip({src})) / 2;",
                  "  do hk = 1 while hk <= hn",
                  "    hp = (hk - 1) * 2 + 1;",
                  f'    if {src}[hp:2] = "{code}" then ht = 1; endif;',
                  "  enddo;",
                  f"  if ht = 1 and length(strip({field})) = 0 then",
                  f'    errmsg("{prompt}");',
                  "    reenter;", "  endif;"]
        else:
            L += ["", f"PROC {field}", "preproc",
                  f'  if pos("{code}", {src}) = 0 then',
                  f'    {field} = "";   {{ not ticked -> not enterable }}',
                  "    noinput;", "  endif;", "postproc",
                  f'  if pos("{code}", {src}) > 0 and length(strip({field})) = 0 then',
                  f'    errmsg("{prompt}");',
                  "    reenter;", "  endif;"]
    return "\n".join(L) + "\n"


# Q94 PER-LAB payment roster (#450, 2026-06-20). Hand-written — the by-source
# build_roster_procs template doesn't fit: the row identity is the LAB ticked in Q93_LABS
# (auto-set, name shown in the grid), the PAYMENT TYPE is ENTERED per lab, and the amount is
# gated on the entered type (= Out-of-pocket). It also scans Q93_LABS in ALIGNED 2-char
# chunks instead of pos(<code>, …): Q93's lab codes run 01..15, so a 2-digit code (10..15)
# would substring-match ACROSS a code boundary under pos() — e.g. ticking 01+02 packs to
# "0102" and pos("10", ..) would wrongly fire. Chunk scanning reads each ticked code exactly.
Q94_LAB_ROSTER_PROCS = """\
{ ---- Q94 per-lab payment roster (#450) — one row per LABORATORY TEST ticked in Q93 ---- }
PROC Q94_LAB_LINE
preproc
  numeric nsel; numeric seen; numeric k; numeric n; numeric p;
  { Count ticked labs by scanning Q93_LABS in aligned 2-char chunks (None=90 has no Q94 row).
    n = number of ticked codes (each is 2 chars); the k-th chunk starts at position (k-1)*2+1.
    Uses the proven `do k = 1 while ...` loop form (the counted `do .. to .. by` form parses
    in the compile but is REJECTED by the stricter Publish packager — #450 build note). }
  n = length(strip(Q93_LABS)) / 2;
  nsel = 0;
  do k = 1 while k <= n
    p = (k - 1) * 2 + 1;
    if Q93_LABS[p:2] <> "90" then nsel = nsel + 1; endif;
  enddo;
  if curocc() > nsel then endgroup; endif;
  { The curocc()-th ticked lab -> Q94_LAB_CODE (auto + protected; its label shows in the grid). }
  seen = 0;
  do k = 1 while k <= n
    p = (k - 1) * 2 + 1;
    if Q93_LABS[p:2] <> "90" then
      seen = seen + 1;
      if seen = curocc() then Q94_LAB_CODE = tonumber(Q93_LABS[p:2]); endif;
    endif;
  enddo;
  protect(Q94_LAB_CODE, true);
  Q94_LAB_LINE = curocc();
  noinput;

PROC Q94_LAB_AMT
preproc
  { Only Out-of-pocket(1) carries an amount; every other payment type has no OOP cost. }
  if Q94_LAB_PAY <> 1 then
    Q94_LAB_AMT = 0;
    noinput;
  endif;
postproc
  if Q94_LAB_PAY = 1 and Q94_LAB_AMT < 0 then
    errmsg("94. Amount cannot be negative.");
    reenter;
  endif;
  if Q94_LAB_PAY = 1 and Q94_LAB_AMT = 0 then
    errmsg("94. Please enter an amount greater than 0 — this test was paid out-of-pocket.");
    reenter;
  endif;
"""
Q96_ROSTER_PROCS = build_roster_procs(
    96, "96", [("Out-of-pocket", "01"), ("Free/no cost", "02"),
               ("Free, charge to PhilHealth", "03"), ("Free, charge to Private Insurance", "04"),
               ("Free, charge to HMO", "05"), ("In kind", "06"), ("Donation", "07"),
               ("Don't know", "08")],
    # #779 (ASPSI clarification 2026-06-25): In-kind (06) is NOT a peso-amount source for Q96
    # — per-question rule, not blanket. Dropped from amt_codes so In-kind becomes a non-money
    # row (amount auto-0, stays enterable but no specify/positive requirement). OOP(01) +
    # Donation(07) still carry a real amount.
    {"01", "07"},
    "96. Tick at least one payment source for the prescribed medicines before continuing.",
    require_positive=True)   # #749/#779: OOP + donation rows must be > 0 (in-kind no longer required)
Q972_ROSTER_PROCS = build_roster_procs(
    972, "97.2", [(None, "01"), (None, "02"), (None, "03"),
                  (None, "04"), (None, "05"), (None, "06")],
    set(),   # all-amount
    "97.2 Tick at least one expense item before continuing (or correct Q97 if none).",
    gated_texts=[("06", "Q972_OTHER_TXT", "97.2 'Other expenses' was ticked — please specify.")],
    require_positive=True)   # #749: every ticked expense item must be > 0
Q98_ROSTER_PROCS = build_roster_procs(
    98, "98", [(None, f"{n:02d}") for n in range(1, 16)],
    set(),   # all-amount
    "98. Tick at least one source of money used to pay for the medical costs before continuing.",
    gated_texts=[
        ("06", "Q98_OTHER_DONATION_TXT",
         "'Other Donation/Charity/Assistance' was selected in Q98. Please specify."),
        ("15", "Q98_OTHER_TXT", "'Other (specify)' was selected in Q98. Please specify.")],
    require_positive=True)   # #749: every ticked money source must be > 0

# The four NEW Section H roster conversions (#691/#692/#693). All-amount, length-9 amounts
# (the amount length lives in the dcf roster field; the apc logic is length-agnostic).
# The Q113 PhilHealth-availed gate (Q114 skip) is re-pointed to pos("08", Q113_SOURCES)
# in CHECKBOX_CONVERT below; the Q110=No skip target is re-pointed to Q113_SOURCES.
Q107_ROSTER_PROCS = build_roster_procs(
    107, "107", [(None, f"{n:02d}") for n in range(1, 11)],
    set(),
    "107. Tick at least one payment source for the total bill before continuing.",
    gated_texts=[("10", "Q107_PAY_OTHER_TXT", "107. 'Other' was ticked — please specify.")],
    require_positive=True)   # #757: every ticked payment source must be > 0
Q109_ROSTER_PROCS = build_roster_procs(
    109, "109", [(None, f"{n:02d}") for n in range(1, 10)],
    set(),
    "109. Tick at least one payment source for the medicines bought outside before continuing.",
    gated_texts=[("09", "Q109_PAY_OTHER_TXT", "109. 'Other' was ticked — please specify.")],
    require_positive=True)   # #757: every ticked payment source must be > 0
Q112_ROSTER_PROCS = build_roster_procs(
    112, "112", [(None, f"{n:02d}") for n in range(1, 10)],
    set(),
    "112. Tick at least one payment source for the services done outside before continuing.",
    gated_texts=[("09", "Q112_PAY_OTHER_TXT", "112. 'Other' was ticked — please specify.")],
    require_positive=True)   # #757: every ticked payment source must be > 0
Q113_ROSTER_PROCS = build_roster_procs(
    113, "113", [(None, f"{n:02d}") for n in range(1, 14)],
    set(),
    "113. Tick at least one payment source for the hospital bill before continuing.",
    gated_texts=[("13", "Q113_PAY_OTHER_TXT", "113. 'Other (specify)' was ticked — please specify.")],
    require_positive=True)   # #757: every ticked payment source must be > 0


def inject_soft(parts, field, body):
    """Merge a soft-check body into field's existing PROC block, or emit a new one."""
    header = f"PROC {field}\n"
    for i, blk in enumerate(parts):
        if isinstance(blk, str) and blk.startswith(header):
            parts[i] = blk.rstrip() + "\n" + body
            return "merged"
    parts.append(f"PROC {field}\npostproc\n{body}")
    parts.append("")
    return "new"

HERE = Path(__file__).parent
OUT = HERE / "PatientSurvey.ent.apc"
DCF = HERE / "PatientSurvey.dcf"

SHARED_DIR = HERE.parent / "shared"


def _inline_shared(filename):
    """Return a shared helper module's body with its own 'PROC GLOBAL' header
    stripped, for pasting INSIDE the host's single PROC GLOBAL.

    Why inline instead of #include (verified 2026-06-08 against the CSEntry loader):
    CSPro forbids `#include` inside a PROC, and CSEntry forbids any code before the
    first PROC -- so an #include of a function library satisfies neither (before
    PROC GLOBAL => "code before the first PROC"; after => "#include is not valid").
    Inlining the helper functions into PROC GLOBAL is the only arrangement both the
    Designer compiler and the CSEntry runtime loader accept.
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
  PatientSurvey (F3) — CAPI logic   (AUTOGENERATED by generate_apc.py)
  Do NOT hand-edit: edit generate_apc.py's tables and rerun.
  Spec: F3-Skip-Logic-and-Validations.md (reviewed 2026-04-21).
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

{ Option B (Q92 roster pilot): sum the consultation out-of-pocket amount from the
  Q92_PAY_ROSTER (replaces the old flat Q92_PAY_01_AMT field). Defined as a function
  so the Q97 reconciliation soft-check stays a single expression with no local
  declarations (it is merged into Q97's range-check PROC). }
function q92_oop()
  { CSPro user functions declare no return type; the value is returned by assigning
    to the function name (mirrors the inlined PSGC-Cascade helpers). Accumulate into a
    local, then assign once at the end (avoid reading the function name mid-body). }
  numeric i;
  numeric total;
  total = 0;
  do i = 1 while i <= count(Q92_PAY_ROSTER)
    if Q92_PAY_SRC(i) = 1 then
      total = total + Q92_PAY_AMT(i);
    endif;
  enddo;
  q92_oop = total;
end;

{ Option B fan-out (#674/#675/#691): out-of-pocket (SRC code 1) sums from the Q94/Q96/Q107
  rosters — same shape as q92_oop(), used in the Q97 / Q115 reconciliation soft-checks
  (replace the old flat Q9n_PAY_01_AMT / Q107_PAY_01_AMT fields). }
function q94_oop()
  numeric i;
  numeric total;
  total = 0;
  do i = 1 while i <= count(Q94_LAB_ROSTER)
    if Q94_LAB_PAY(i) = 1 then          { #450: per-lab roster — OOP(1) rows sum the amount }
      total = total + Q94_LAB_AMT(i);
    endif;
  enddo;
  q94_oop = total;
end;

function q96_oop()
  numeric i;
  numeric total;
  total = 0;
  do i = 1 while i <= count(Q96_PAY_ROSTER)
    if Q96_PAY_SRC(i) = 1 then
      total = total + Q96_PAY_AMT(i);
    endif;
  enddo;
  q96_oop = total;
end;

function q107_oop()
  numeric i;
  numeric total;
  total = 0;
  do i = 1 while i <= count(Q107_PAY_ROSTER)
    if Q107_PAY_SRC(i) = 1 then
      total = total + Q107_PAY_AMT(i);
    endif;
  enddo;
  q107_oop = total;
end;

{ Shared helpers inlined into this single PROC GLOBAL (PSGC-Cascade first so its
  ROOT_PSGC_PARENT declaration precedes all functions). #include can't be used:
  CSPro forbids it inside a PROC, and CSEntry forbids code before the first PROC.
  Requires the 4 PSGC external dicts attached to the .ent (else R_PARENT_CODE etc.
  are undeclared). }
""" + _inline_shared("PSGC-Cascade.apc") + """

""" + _inline_shared("Capture-Helpers.apc") + """

PROC PATIENTSURVEY_FF
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
  ("Withdraw Participation/Consent" = code 6); the read-aloud consent script is
  read from the printed sheet (off the CAPI). No consent gate PROC. }

{ ---- F1 linkage: facility is intrinsic to the 12-digit case-key id-block
  (REGION_CODE + PROVINCE_HUC_CODE + CITY_MUNICIPALITY_CODE + FACILITY_NO);
  F3_FACILITY_ID retired 2026-06-04. The cross-check against the synced F1
  facility set moves to the CSWeb sync step (E4-CSWeb-005). ---- }

{ ---- Single 12-digit Questionnaire Number (redesign 2026-06-11; mirrors F1) ----
  Parse the number into the component codes (FIELD_CONTROL items - downstream
  PROCs keep working), validate the 7-digit geo prefix hierarchically against
  the PSGC dicts, fill the read-only *_NAME items, and set the full PSGC codes
  on the off-form geo items so the BARANGAY cascade filters correctly. ---- }
PROC QUESTIONNAIRE_NUMBER
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

{ ---- Barangay picker (facility geo): region/province/city are derived from the
  Questionnaire Number (off-form); only barangay is picked, filtered by the
  derived city/province code. ---- }
PROC BARANGAY
onfocus
  FillBarangayValueSet(CITY_MUNICIPALITY);

{ ---- #784/#786 (Option A): structured facility address ----
  The enumerator types only the STREET line. The barangay name is derived from the
  picked BARANGAY code, the municipality name (CITY_NAME) is already derived from the
  Questionnaire Number above, and FACILITY_ADDRESS is assembled read-only as
  "Street, Barangay, Municipality" — so nothing PSGC is re-selected (#786). Both derived
  fields are computed HERE, in FACILITY_STREET's postproc (a visited field), because
  BARANGAY_NAME + FACILITY_ADDRESS are protected and CSEntry skips a protected field's own
  preproc (ref: protected-field preproc). }
PROC FACILITY_STREET
postproc
  BARANGAY_NAME = "";
  B_PARENT_CITY = CITY_MUNICIPALITY;
  if loadcase(PSGC_BARANGAY_DICT, B_PARENT_CITY) <> 0 then
    do varying numeric bi = 1 until bi > count(PSGC_BARANGAY_DICT.PSGC_BARANGAY_REC)
      if B_CODE(bi) = BARANGAY then
        BARANGAY_NAME = strip(B_NAME(bi));
      endif;
    enddo;
  endif;
  protect(BARANGAY_NAME, true);
  FACILITY_ADDRESS = strip(FACILITY_STREET);
  if length(strip(BARANGAY_NAME)) > 0 then
    if length(strip(FACILITY_ADDRESS)) > 0 then
      FACILITY_ADDRESS = strip(FACILITY_ADDRESS) + ", " + strip(BARANGAY_NAME);
    else
      FACILITY_ADDRESS = strip(BARANGAY_NAME);
    endif;
  endif;
  if length(strip(CITY_NAME)) > 0 then
    if length(strip(FACILITY_ADDRESS)) > 0 then
      FACILITY_ADDRESS = strip(FACILITY_ADDRESS) + ", " + strip(CITY_NAME);
    else
      FACILITY_ADDRESS = strip(CITY_NAME);
    endif;
  endif;
  protect(FACILITY_ADDRESS, true);

{ ---- PSGC cascade — patient geo-ID (P_* mirror) ---- }
{ patient-home geo cascade — inlined (P_* fields are F3-only; the shared
  PSGC-Cascade functions target the facility geo items REGION/PROVINCE_HUC/etc.,
  and setvalueset needs the literal field, so the P_* targets are set here). }
PROC P_REGION
onfocus
  R_PARENT_CODE = ROOT_PSGC_PARENT;
  if loadcase(PSGC_REGION_DICT, R_PARENT_CODE) > 0 then
    ValueSet vsPR;
    do varying numeric i = 1 until i > count(PSGC_REGION_DICT.PSGC_REGION_REC)
      vsPR.add(strip(R_NAME(i)), R_CODE(i));
    enddo;
    setvalueset(P_REGION, vsPR);
  endif;
PROC P_PROVINCE_HUC
onfocus
  P_PARENT_REGION = P_REGION;
  if loadcase(PSGC_PROVINCE_DICT, P_PARENT_REGION) > 0 then
    ValueSet vsPP;
    do varying numeric i = 1 until i > count(PSGC_PROVINCE_DICT.PSGC_PROVINCE_REC)
      vsPP.add(strip(P_NAME(i)), P_CODE(i));
    enddo;
    setvalueset(P_PROVINCE_HUC, vsPP);
  endif;
PROC P_CITY_MUNICIPALITY
onfocus
  C_PARENT_PROVINCE = P_PROVINCE_HUC;
  if loadcase(PSGC_CITY_DICT, C_PARENT_PROVINCE) > 0 then
    ValueSet vsPC;
    do varying numeric i = 1 until i > count(PSGC_CITY_DICT.PSGC_CITY_REC)
      vsPC.add(strip(C_NAME(i)), C_CODE(i));
    enddo;
    setvalueset(P_CITY_MUNICIPALITY, vsPC);
  endif;
PROC P_BARANGAY
onfocus
  B_PARENT_CITY = P_CITY_MUNICIPALITY;
  if loadcase(PSGC_BARANGAY_DICT, B_PARENT_CITY) > 0 then
    ValueSet vsPB;
    do varying numeric i = 1 until i > count(PSGC_BARANGAY_DICT.PSGC_BARANGAY_REC)
      vsPB.add(strip(B_NAME(i)), B_CODE(i));
    enddo;
    setvalueset(P_BARANGAY, vsPB);
  endif;

{ ---- GPS — AUTO-FETCHED on focus (2026-06-12; no manual trigger). Captured
  once (guarded on read-time), then all GPS fields protected (read-only) so
  coordinates can't be typed. Helpers in Capture-Helpers.apc. Desktop (getos
  10-19) has no GPS radio → fields stay blank there (device-only). ---- }
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

PROC P_HOME_GPS_LATITUDE
onfocus
  { Home-visit GPS (outpatient / home interview); fields are P_HOME_GPS_*. }
  if length(strip(P_HOME_GPS_READTIME)) = 0 then   { capture once; not on back-nav }
    if ReadGPSReading(120, 20) then
      P_HOME_GPS_LATITUDE   = maketext("%f", gps(latitude));
      P_HOME_GPS_LONGITUDE  = maketext("%f", gps(longitude));
      P_HOME_GPS_ALTITUDE   = maketext("%f", gps(altitude));
      P_HOME_GPS_ACCURACY   = gps(accuracy);
      P_HOME_GPS_SATELLITES = gps(satellites);
      P_HOME_GPS_READTIME   = maketext("%d", gps(readtime));
    endif;
  endif;
  { Protect ONLY once captured — see FACILITY_GPS_LATITUDE note above. }
  if length(strip(P_HOME_GPS_READTIME)) > 0 then
    protect(P_HOME_GPS_LATITUDE, true);
    protect(P_HOME_GPS_LONGITUDE, true);
    protect(P_HOME_GPS_ALTITUDE, true);
    protect(P_HOME_GPS_ACCURACY, true);
    protect(P_HOME_GPS_SATELLITES, true);
    protect(P_HOME_GPS_READTIME, true);
  endif;

{ ---- #231 Verification photo (moved to the END of the form 2026-06-12). CONDITIONAL on
  the visit outcome and soft-validated (warn, don't trap, on camera failure). ---- }
PROC VERIFICATION_PHOTO_FILENAME
preproc
  { display-only — the camera trigger fills this; it is never typed }
  noinput;

PROC CAPTURE_VERIFICATION_PHOTO
preproc
  { gate: photograph only visits where an interview occurred — 1 Completed,
    2 Completed at the Hospital, 4 Incomplete, 5 Completed at Home; skip
    3 Postponed / 6 Withdraw Participation/Consent }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 2, 4, 5) then
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

# #164 Outpatient/Inpatient routing (spec 2 Sections G-I preamble):
#   PATIENT_TYPE = 1 Outpatient -> Section G (Q88-Q104), skip H (Q105-Q115)
#   PATIENT_TYPE = 2 Inpatient  -> skip G, Section H
#   Section I (Q116+) asked for both. Gate the FIRST item of G and of H.
#   (Verify PATIENT_TYPE codes 1/2 against the dcf value set on first compile.)
BRANCHING = """\
{ ---- #164 Outpatient vs Inpatient branching ---- }
PROC Q88_WHY_VISIT
preproc
  { #441: not Outpatient -> skip Section G to the START of Section H (Q105), NOT to Q116.
    The old target (Q116) jumped past Section H entirely, so INPATIENTS lost all of Section H.
    Q105's own gate (PATIENT_TYPE <> 2 -> skip to Q116) then decides: inpatient keeps H,
    a blank/other type falls through to Q116. }
  if PATIENT_TYPE <> 1 then    { not Outpatient -> skip Section G; land at Section H start }
    skip to Q105_REASON;
  endif;

PROC Q105_REASON
preproc
  if PATIENT_TYPE <> 2 then    { not Inpatient -> skip Section H entirely }
    skip to Q116_NBB_HEARD;
  endif;
"""

# Multi-branch routing + end-of-survey + cross-field gate (spec 2 D-F/J-L).
EXTRA_PROCS = """\
{ ---- Q98 payment-matrix 'Other (specify)' gates: Option B fan-out (#689, 2026-06-19)
  re-pointed these from the old flat Q98_PAY_06 / Q98_PAY_15 flags (now removed) to
  pos("06"/"15", Q98_SOURCES). The gated-text PROCs are emitted by Q98_ROSTER_PROCS
  (build_roster_procs gated_texts=...), not here. ---- }

{ ---- #558/#694 (R4): Q114 (why no PhilHealth) gate ----
  Q114 is now a Check Box base (select_all -> tick-all); the PhilHealth-availed gate
  (Q113_PAY_08 = Yes -> skip to Q1141_1) is folded into the Q114_NO_PH checkbox PROC
  via CHECKBOX_CONVERT. The old PROC Q114_NO_PH_O01 field no longer exists. }

{ ---- Multi-branch routing (spec 2) ---- }
{ #418/#419 (R4): Q63 usual-facility block. Spec 3.6 — Q64 (facility name) and Q66-Q70
  are enabled when Q63=Yes; Q65 (why-no-usual) is enabled when Q63=No. The old logic was
  inverted: it skipped Q64 on Yes (jumped straight to Q66) and never gated Q66-Q70 off on
  No (so they were asked for everyone). Corrected routing:
    Q63=Yes(1) -> fall through to Q64 -> (Q64 postproc) skip Q65 -> Q66..Q70 -> Q71
    Q63=No(2)  -> skip Q64 -> Q65 reasons -> (Q66 preproc) skip Q66-Q70 -> Q71 }
PROC Q63_HAS_USUAL_FACILITY
postproc
  if Q63_HAS_USUAL_FACILITY = 2 then  skip to Q65_WHY_NO_USUAL; endif;  { No -> reasons-why-none (skip Q64). #529: Q65 is now the Check Box base (was _O01) }

PROC Q64_FACILITY_NAME
postproc
  skip to Q66_SAME_AS_USUAL;   { reached only when Q63=Yes -> skip Q65 why-no-usual block }

PROC Q66_SAME_AS_USUAL
preproc
  if Q63_HAS_USUAL_FACILITY <> 1 then  skip to Q71_NEAREST_TYPE; endif;  { No-usual path: skip the Q66-Q70 facility block }
postproc
  if Q66_SAME_AS_USUAL = 1 then  skip to Q68_USUAL_FAC_TYPE; endif;       { this IS the usual facility -> skip Q67 why-different }

PROC Q77_KON_REGISTERED
postproc
  if Q77_KON_REGISTERED = 2    then  skip to Q82_KON_WHY_NOT_REG; endif;  { Not registered -> reasons. #671: Q82 is now the Check Box base (was _O01) }
  if Q77_KON_REGISTERED = 3    then  skip to Q83_VISIT_REASON;    endif;  { #770: 'I've never heard of it'(3) RESTORED -> Q83 (reverses #430) }
  if Q77_KON_REGISTERED = 4    then  skip to Q83_VISIT_REASON;    endif;  { IDK(4) exits Section E -> Q83 }

{ #389/#671: the "why NOT registered" gate (registered patient falls through Q78-Q81 into
  Q82 -> skip to Section F) now lives in the Q82_KON_WHY_NOT_REG checkbox PROC's `gate`
  param (CHECKBOX_CONVERT below); the old PROC Q82_KON_WHY_NOT_REG_O01 field no longer exists. }

PROC Q159_BRAND_GEN_BOUGHT
postproc
  if Q159_BRAND_GEN_BOUGHT = 1 then  skip to Q161_WHY_BRANDED; endif;  { Branded -> why-branded (#696: Q161 now a Check Box base; skip target is the base field, not _O01) }
  { #732 (R5): 'Don't know the difference' (4) RESTORED to the paper -> Q162 (referral section
    start), reversing #618. ASPSI tester wants the paper's literal option set + routing. }
  if Q159_BRAND_GEN_BOUGHT = 4 then  skip to Q162_REFERRED;        endif;  { #732: Don't-know-the-difference -> Q162 (restored) }
  { #731 (R5): 'Not applicable' (5) -> Q164 per the paper (tester screenshot + F3_clean
    'Proceed to Q156' = field Q164_SPECIALIST, +8 numbering offset), reversing #501's Q162.
    #501 had flagged Q164 as a Q162=Yes follow-up ("orphaned" landing); per Carl 'do what the
    testers need', we follow the paper's literal routing — downstream-flow refinement is ASPSI's call. }
  if Q159_BRAND_GEN_BOUGHT = 5 then  skip to Q164_SPECIALIST;      endif;  { #731: Not applicable -> Q164 (was Q162 #501) }

{ ---- Section D: non-members skip the benefits/premium block (Q46-Q50). #529: Q46 is now
  a Check Box field — this gate moved into the Q46_BENEFITS checkbox PROC's `gate` param
  (CHECKBOX_CONVERT below); the old PROC Q46_BENEFITS_O01 field no longer exists. ---- }

{ ---- R4 sweep enabled-when GATES (#402 / #415 / #417) ---- }
PROC Q45_CATEGORY
preproc
  { #402: member-category (Q45) is PhilHealth-members-only (spec 3.5: Q45 enabled when
    Q38=Yes). A non-member must skip the whole Q45-Q50 member/benefits/premium block to Q51. }
  if Q38_PHILHEALTH_REG <> 1 then  skip to Q51_OTHER_INSURANCE; endif;
postproc
  { spec 3.5 SOFT: 'Senior citizen' category (6) but patient under 60 — warn-and-continue }
  if Q38_PHILHEALTH_REG = 1 and Q45_CATEGORY = 6 and Q6_AGE < 60 then
    errmsg("Q45 = Senior citizen but patient age (%d) is under 60 — confirm.", Q6_AGE);
  endif;

PROC Q60_SCHED_TELECON_OK
preproc
  { #415: scheduling-teleconsult-success (Q60) only if 'Teleconsultation' (option 2) was
    ticked in the Q59 Check Box (spec 3.6: Q60 enabled when Q59 includes Teleconsultation).
    #669: Q59 is now a Check Box (code "02" = Teleconsultation); the skip target Q61's old
    first option-field Q61_CONSULT_COMM_O01 is now the bare base Q61_CONSULT_COMM. }
  if pos("02", Q59_SCHED_COMM) = 0 then  skip to Q61_CONSULT_COMM; endif;

PROC Q62_CONSULT_TELECON_OK
preproc
  { #417: consultation-teleconsult-success (Q62) only if 'Teleconsultation' (option 2) was
    ticked in the Q61 Check Box (spec 3.6: Q62 enabled when Q61 includes Teleconsultation).
    #669: Q61 is now a Check Box (code "02" = Teleconsultation). }
  if pos("02", Q61_CONSULT_COMM) = 0 then  skip to Q63_HAS_USUAL_FACILITY; endif;

{ ---- Q93 labs: 'None' exclusivity (#448) + skip the Q94 cost matrix (spec G). #673: Q93 is
  now a Check Box base — the exclusivity soft-warn (pos("90") stands alone) and the 'None' ->
  skip Q94 are both folded into the Q93_LABS checkbox PROC (CHECKBOX_CONVERT below, exclusive
  + postskip params); the old PROC Q93_LABS_O17 field no longer exists. ---- }

{ ---- Section I confinement-context gates (#476/#479): ZBB 'upon admission' (Q122/Q123)
  and MAIFIP 'this last confinement' (Q126-Q129) are inpatient-only — an outpatient has no
  confinement to answer about. Q120/Q121 (general ZBB awareness) and Q130 (general spending)
  stay for both. ---- }
PROC Q122_ZBB_INFORMED
preproc
  if PATIENT_TYPE <> 2 then  skip to Q124_MAIFIP_HEARD; endif;   { #476: skip Q122/Q123 for outpatient }

PROC Q126_MAIFIP_AVAILED
preproc
  if PATIENT_TYPE <> 2 then  skip to Q130_REDUCED_SPEND; endif;  { #479: skip Q126-Q129 for outpatient }
postproc
  if Q126_MAIFIP_AVAILED = 2 then  skip to Q129_WHY_NO_MAIFIP; endif;  { #482/#700: didn't avail -> ask why-not (skip Q127/Q128); target is the Check Box base }

{ ---- Q129 'why not avail MAIFIP' (#482): only for those who did NOT avail (Q126=No=2).
  Reached directly when Q126=No; on the Q126=Yes path (after Q127/Q128) skip it to Q130.
  #700: Q129 is now a Check Box base; this gate is folded into its checkbox PROC via
  CHECKBOX_CONVERT. The old PROC Q129_WHY_NO_MAIFIP_O01 field no longer exists. ---- }

{ ---- Section L: not referred -> end of survey. Route to the closing Result-of-Visit +
  Verification Photo. Do NOT endlevel here: the photo form is the LAST form, so ending
  the level at this point skips the photo (bug found in R4 on-device review 2026-06-12). ---- }
PROC Q162_REFERRED
postproc
  if Q162_REFERRED = 2 then
    ENUM_RESULT_FINAL_VISIT = 1;   { default Completed; enumerator confirms it on the closing form }
    skip to ENUM_RESULT_FINAL_VISIT;   { skip the referred-only Q163/Q164, land on Result-of-Visit; the Verification Photo form follows it }
  endif;

{ ---- Section K/L R4 sweep (Wave 4, 2026-06-14): gating + required fixes ---- }

{ #490: Q147 meds list is required when reached (Q145<>5 already gates the whole Q146-Q151
  block, so reaching Q147 means the patient purchases meds). Was advanceable while blank. }
PROC Q147_MEDS_LIST
postproc
  if length(strip(Q147_MEDS_LIST)) = 0 then
    errmsg("Q147: list the medications taken (type 'None' if the patient takes none) — required.");
    reenter;
  endif;

{ #498: Q156 'list the GAMOT medicines' + Q157 'where got the rest' are both enabled only when
  Q155 = Yes (got meds from GAMOT). Was: Q156/Q157 always asked, Q156 advanceable while blank. }
PROC Q155_GAMOT_GOT_MEDS
postproc
  if Q155_GAMOT_GOT_MEDS = 2 then  skip to Q158_BRAND_GEN_KNOW; endif;  { No -> skip Q156/Q157 }

PROC Q156_GAMOT_MEDS_LIST
preproc
  if Q155_GAMOT_GOT_MEDS <> 1 then
    Q156_GAMOT_MEDS_LIST = "";   { gated: only when Q155 = Yes }
    noinput;
  endif;
postproc
  if Q155_GAMOT_GOT_MEDS = 1 and length(strip(Q156_GAMOT_MEDS_LIST)) = 0 then
    errmsg("Q156: list the medicines obtained from GAMOT — required when Q155 = Yes.");
    reenter;
  endif;

{ #503/#696: Q161 'why branded' is enabled only for Branded/Both (Q159 in 1,3). Generic (2)
  falls through Q160 into Q161 — gate it out to Section L. Q159 = 4/5 already skip to Q162
  earlier. Q161 is now a Check Box base; this gate is folded into the Q161_WHY_BRANDED
  checkbox PROC via CHECKBOX_CONVERT. The old PROC Q161_WHY_BRANDED_O01 field no longer exists. }

{ #799: Q169 routing. 'No, I'm not planning to' (2) -> Q171 (why not visited). 'Not yet, but
  I'm planning to' (3) -> Q172 (skip Q170 + Q171: they ARE planning to go, so 'why not' is moot).
  'Yes' (1) falls through to Q170 (the only path that reaches it). Replaces the old single
  'in 2,3 -> Q171' skip rule. }
PROC Q169_VISITED
postproc
  if Q169_VISITED = 2 then  skip to Q171_WHY_NOT;      endif;
  if Q169_VISITED = 3 then  skip to Q172_PCP_REFERRAL; endif;

{ #508: Q170 follow-up is reached only on Q169 = Yes (codes 2/3 are routed away above). After the
  follow-up, the Yes path skips Q171 'why not visited' to Q172 (spec §4.15, explicit). }
PROC Q170_FOLLOWUP
postproc
  skip to Q172_PCP_REFERRAL;

{ #511: Q177 'why hospital' is enabled only when Q172 = No (Q172 = 2 skips Q173-Q176 to Q177).
  The Q172 = Yes path falls through Q173-Q176 into Q177 — gate it out to Q178. #529: Q177 is
  now a Check Box field — this gate moved into the Q177_WHY_HOSPITAL checkbox PROC's `gate`
  param (CHECKBOX_CONVERT below); the old PROC Q177_WHY_HOSPITAL_O01 field no longer exists. }

{ ---- Q148 Check Box multi-select (R4 redesign 2026-06-12) — one alpha field of
  concatenated 2-digit condition codes (CSEntry Check Box). 'Other'=99 / 'No condition'=19
  are chosen so pos() can't false-match across code boundaries (no valid code starts with 9).
  The old 20 Yes/No items are gone, so these are hand-written (the select-all auto-gen no
  longer sees an _O run for Q148). ---- }
PROC Q148_CONDITIONS
postproc
  if length(strip(Q148_CONDITIONS)) = 0 then
    errmsg("Tick at least one medical condition (or 'No condition - Regular check-up only').");
    reenter;
  endif;
  { exclusivity (soft warn): 'No condition - Regular check-up only' (19) should stand alone }
  if pos("19", Q148_CONDITIONS) > 0 and length(strip(Q148_CONDITIONS)) > 2 then
    errmsg("'No condition - Regular check-up only' is usually the only choice — please review the conditions ticked.");
  endif;

PROC Q148_CONDITIONS_OTHER_TXT
preproc
  if pos("99", Q148_CONDITIONS) = 0 then
    Q148_CONDITIONS_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q148_CONDITIONS) > 0 and length(strip(Q148_CONDITIONS_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q148 — please specify.");
    reenter;
  endif;

"""


# --- #529 multi-select conversion: the 13 F3 'Patient Survey' select_all bases that
# became single Check Box fields (mirrors F1 generate_apc.py's CHECKBOX_CONVERT_A,
# and the hand-written F3 Q148_CONDITIONS in EXTRA_PROCS above). Each base gets a
# select->=1 validation, an optional exclusivity soft-warn (the standalone option coded
# 90 should stand alone), an optional preproc gate, and (when present) an 'Other (specify)'
# text gate on pos("99", base). Codes are from generate_dcf._cb_codes: real options 01..,
# exclusive 'I don't know'/'None' -> 90, 'Other (specify)' -> 99. (base, has_other,
# exclusive, preproc_gate). Q148 stays hand-written in EXTRA_PROCS (not in this table).
CHECKBOX_BASES = {
    "Q36_UHC_SOURCE", "Q37_UHC_UNDERSTAND", "Q46_BENEFITS", "Q65_WHY_NO_USUAL",
    "Q67_WHY_THIS_FACILITY", "Q76_KON_UNDERSTAND", "Q101_BUCAS_UNDERSTAND",
    "Q117_NBB_SOURCE", "Q118_NBB_UNDERSTAND", "Q120_ZBB_SOURCE", "Q121_ZBB_UNDERSTAND",
    "Q171_WHY_NOT", "Q177_WHY_HOSPITAL", "Q125_MAIFIP_SOURCE",   # #560 (Marriz confirmed Q125 not-read-aloud)
    "Q148_CONDITIONS",   # hand-written in EXTRA_PROCS, but a checkbox base for exclusion logic
    "Q42_DIFFICULTY", "Q50_DIFFICULTY_PAYING",   # #635/#639 Section D select_all -> Check Box
    "Q52_PLANS",   # #640 Section D insurance-plans select_all -> Check Box
    # #669/#670/#671/#673 Section E/F/G select_all -> Check Box (tick-all)
    "Q59_SCHED_COMM", "Q61_CONSULT_COMM", "Q70_USUAL_TRANSPORT", "Q73_NEAREST_TRANSPORT",
    "Q75_KON_SOURCE", "Q82_KON_WHY_NOT_REG", "Q85_CONDITIONS", "Q86_VISIT_EVENTS",
    "Q87_OTHER_ACTIONS", "Q90_NOT_CONFINED", "Q93_LABS",
    # #690/#694 Section G/H select_all -> Check Box (tick-all)
    "Q100_BUCAS_SOURCE", "Q103_BUCAS_SERVICES", "Q114_NO_PH",
    # #696 Section K/L select_all -> Check Box (tick-all)
    "Q149_WHERE_BUY", "Q153_GAMOT_SOURCE", "Q154_GAMOT_UNDERSTAND", "Q157_WHERE_REST",
    "Q160_WHY_GENERIC", "Q161_WHY_BRANDED", "Q163_CARE_TYPE",
    "Q128_MAIFIP_OOP_ITEMS",   # #481 select_all -> Check Box (+ None/Other)
    "Q129_WHY_NO_MAIFIP",   # #700 select_all -> Check Box (tick-all)
}

CHECKBOX_CONVERT = [
    # base                       has_other  exclusive  preproc_gate
    ("Q36_UHC_SOURCE",           True,  True,  None),   # 'I don't know' (90) exclusive; 'Other (Specify)' (99)
    ("Q42_DIFFICULTY",           True,  True,  None),   # #635: 'I don't know' (90) exclusive; 'Other (Specify)' (99). Reached when Q41=Yes (Q41=No skips to Q43)
    ("Q50_DIFFICULTY_PAYING",    True,  True,  None),   # #639: 'I don't know' (90) exclusive; 'Other (Specify)' (99). Reached when Q49=Yes (Q49=No skips to Q51)
    ("Q52_PLANS",                True,  True,  None),   # #640: 'I don't know' (90) exclusive; 'Others (specify)' (99). Reached when Q51=Yes (Q51=No skips to Q53)
    ("Q37_UHC_UNDERSTAND",       True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    # Q46 inherits the non-member gate that used to live on Q46_BENEFITS_O01 (Section D).
    ("Q46_BENEFITS",             True,  True,
     "  if Q38_PHILHEALTH_REG <> 1 then   { #529: non-member -> skip the benefits block (was PROC Q46_BENEFITS_O01) }\n"
     "    skip to Q51_OTHER_INSURANCE;\n  endif;"),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q65_WHY_NO_USUAL",         True,  True,  None),   # 'I don't know' (90) exclusive — NOT 'I don't know where to go for care' (05); 'Other (Specify)' (99)
    ("Q67_WHY_THIS_FACILITY",    True,  False, None),   # no None/IDK option; 'Other (Specify)' (99)
    ("Q76_KON_UNDERSTAND",       True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q101_BUCAS_UNDERSTAND",    True,  False, None),   # no None/IDK option; 'Other (specify)' (99)
    ("Q117_NBB_SOURCE",          True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q118_NBB_UNDERSTAND",      True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q125_MAIFIP_SOURCE",       True,  True,  None),   # #560 SOURCE_8: 'I don't know' (90); 'Other (Specify)' (99)
    ("Q120_ZBB_SOURCE",          True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q121_ZBB_UNDERSTAND",      True,  True,  None),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q171_WHY_NOT",             True,  False, None),   # no None/IDK option — 'Don't know how to get to facility' (06) is substantive; 'Other (Specify)' (99)
    # Q177 inherits the not-referral gate that used to live on Q177_WHY_HOSPITAL_O01 (Section L).
    ("Q177_WHY_HOSPITAL",        True,  True,
     "  if Q172_PCP_REFERRAL = 1 then   { #529: was-a-referral -> skip why-hospital (was PROC Q177_WHY_HOSPITAL_O01) }\n"
     "    skip to Q178_SAT_REFERRAL;\n  endif;"),   # 'I don't know' (90); 'Other (Specify)' (99)
    # ---- #669/#670/#671/#673 Section E/F/G select_all -> Check Box (tick-all) ----
    ("Q59_SCHED_COMM",           False, False, None),  # #669: COMM_MODES, no Other / no None-IDK
    ("Q61_CONSULT_COMM",         False, False, None),  # #669: COMM_MODES, no Other / no None-IDK
    ("Q70_USUAL_TRANSPORT",      True,  False, None),  # #670: 'Other (Specify)' (99); no None/IDK
    ("Q73_NEAREST_TRANSPORT",    True,  False, None),  # #670: 'Other (Specify)' (99); no None/IDK
    ("Q75_KON_SOURCE",           True,  True,  None),  # #671: 'I don't know' (90); 'Other (Specify)' (99)
    # Q82 inherits the not-registered gate that used to live on Q82_KON_WHY_NOT_REG_O01 (#389).
    ("Q82_KON_WHY_NOT_REG",      True,  True,
     "  if Q77_KON_REGISTERED <> 2 then   { #389/#671: only for not-registered (Q77=No=2); a registered\n"
     "                                        patient falls through Q78-Q81 into Q82 -> gate to Section F (Q83). }\n"
     "    skip to Q83_VISIT_REASON;\n  endif;"),   # 'I don't know' (90); 'Other (specify)' (99)
    # Q85 'No condition - Regular check-up only' is code 19 (NOT an exclusive 90), so the
    # generic exclusivity warn can't express it — pass the Q83=4 confirm + 'stands alone'
    # soft-warns as a postextra block on pos() membership tests (was SOFT_CROSS Q85_..._O19).
    ("Q85_CONDITIONS",           True,  False, None,
     "  if Q83_VISIT_REASON = 4 and pos(\"19\", Q85_CONDITIONS) = 0 then\n"
     "    errmsg(\"Q83 = general check-up but Q85 is not 'No condition / regular check-up only' — confirm.\");\n  endif;\n"
     "  { #435/#673: 'No condition - Regular check-up only' (19) should stand alone — warn if combined (mirrors Q148) }\n"
     "  if pos(\"19\", Q85_CONDITIONS) > 0 and length(strip(Q85_CONDITIONS)) > 2 then\n"
     "    errmsg(\"'No condition - Regular check-up only' was ticked with other condition(s) — it should usually be the only choice. Please review.\");\n  endif;"),  # 'Other (Specify)' (99)
    ("Q86_VISIT_EVENTS",         True,  False, None),  # #438: + 'Other (Specify)' (99) escape; no None/IDK
    # Q87 'Did not seek other forms of care' is code 06 (a substantive option, NOT the
    # generic exclusive 90), so the generic 90-exclusivity warn can't express it — pass a
    # postextra block (mirrors the Q85 code-19 pattern above) that enforces it. #715 was
    # marked Critical (a tester ticked 'Sought alternative care'(02) AND 'Did not seek other
    # forms of care'(06) together — logically contradictory), so this is a HARD trap:
    # errmsg + reenter forces the enumerator to leave 06 as the only choice. (No postproc
    # auto-reset of the checkbox field — a postproc reassignment to a CheckBox is not a
    # confirmed-clean re-render on CSEntry; hard error + reenter is the safe enforcement.)
    ("Q87_OTHER_ACTIONS",        True,  False, None,
     '  if pos("06", Q87_OTHER_ACTIONS) > 0 and length(strip(Q87_OTHER_ACTIONS)) > 2 then\n'
     "    errmsg(\"Q87: 'Did not seek other forms of care' cannot be combined with any other "
     'action — untick the others (or untick this) so only one applies, then continue.");\n'
     "    reenter;\n  endif;"),   # #715: code 06 is exclusive (HARD); 'Other (Specify)' (99)
    ("Q90_NOT_CONFINED",         True,  False, None),  # #673: 'Other (specify)' (99); no None/IDK
    # Q93 'None'(90) -> skip the Q94 lab-cost matrix (was PROC Q93_LABS_O17 skip, #448/#673).
    ("Q93_LABS",                 True,  True,  None,
     '  if pos("90", Q93_LABS) > 0 then   { #448/#673: \'None\' -> skip Q94 lab-cost matrix }\n'
     "    skip to Q95_PRESCRIBED;\n  endif;"),   # 'None' (90); 'Other, specify:'(16) -> (99)
    # ---- #690/#694 Section G/H select_all -> Check Box (tick-all) ----
    ("Q100_BUCAS_SOURCE",        True,  True,  None),  # #690 SOURCE_8: 'I don't know' (90); 'Other (Specify)' (99). Reached only when Q99=Yes (Q99=No skips Q100-104 -> Q116)
    ("Q103_BUCAS_SERVICES",      True,  True,  None),  # #690: 'I don't know' (90); 'Other (specify)' (99). Reached only when Q102=Yes (Q102=No skips Q103 -> Q104)
    # Q114 inherits the PhilHealth-availed gate that used to live on Q114_NO_PH_O01 (#558).
    ("Q114_NO_PH",               True,  False,
     '  if pos("08", Q113_SOURCES) > 0 then   { #558/#694 + Option B fan-out (#693): PhilHealth WAS availed\n'
     "                               (Q113 PhilHealth source = code 08 ticked) -> skip the why-not-availed\n"
     "                               reasons; go straight to the Q114.1 out-of-bill amount matrix. }\n"
     "    skip to Q1141_1;\n  endif;"),   # 'Other (specify)' (99); no None/IDK
    # ---- #696 Section K/L select_all -> Check Box (tick-all) ----
    ("Q149_WHERE_BUY",           True,  False, None),  # #696: 'Other (specify)' (99); no None/IDK
    ("Q153_GAMOT_SOURCE",        True,  True,  None),  # #696 SOURCE_8: 'I don't know' (90); 'Other (Specify)' (99). Reached when Q152=Yes
    ("Q154_GAMOT_UNDERSTAND",    True,  True,  None),  # #696: 'I don't know' (90); 'Other (specify)' (99)
    ("Q157_WHERE_REST",          True,  True,  None),  # #696/#500: 'None — got all from GAMOT' (90) exclusive; 'Other (Specify)' (99)
    ("Q160_WHY_GENERIC",         True,  True,  None),  # #696: 'I don't know' (90); 'Other (Specify)' (99). Gated by surrounding Q159 routing (Q159=1 skips it; Q161 preproc gate handles generic-only)
    # Q161 inherits the branded-only gate that used to live on Q161_WHY_BRANDED_O01 (#503).
    ("Q161_WHY_BRANDED",         True,  True,
     "  if Q159_BRAND_GEN_BOUGHT <> 1 and Q159_BRAND_GEN_BOUGHT <> 3 then   { #503/#696: why-branded only for\n"
     "                                                                        Branded(1)/Both(3); Generic(2) falls through Q160 -> gate out to Section L. }\n"
     "    skip to Q162_REFERRED;\n  endif;"),   # 'I don't know' (90); 'Other (Specify)' (99)
    ("Q163_CARE_TYPE",           True,  True,  None),  # #696: 'None of the above' (90) exclusive; 'Other (Specify)' (99)
    ("Q128_MAIFIP_OOP_ITEMS",    True,  True,  None),  # #481: 'None' (90) exclusive; 'Other (specify)' (99). Reached only when Q127=Yes (Q127=No skips Q128 -> Q130)
    # Q129 inherits the not-availed gate that used to live on Q129_WHY_NO_MAIFIP_O01 (#482).
    ("Q129_WHY_NO_MAIFIP",       True,  False,
     "  if Q126_MAIFIP_AVAILED <> 2 then   { #482/#700: only for those who did NOT avail MAIFIP\n"
     "                                        (Q126=No=2); the Q126=Yes path skips Q129 to Q130. }\n"
     "    skip to Q130_REDUCED_SPEND;\n  endif;"),   # #783: Other-specify (99) added; no None-IDK. The checkbox PROC now emits the pos("99") _OTHER_TXT gate (suppresses the generic <>99 auto-gen).
]


def _gen_checkbox_proc(base, has_other, exclusive, gate=None, postextra=None):
    """Emit the bespoke PROC(s) for one converted Check Box base — select->=1 (hard),
    an optional exclusivity soft-warn (the 90-coded standalone option should stand alone),
    an optional preproc gate, an optional postproc-tail block (postextra: a code block that
    runs AFTER the >=1 / exclusivity checks, still inside postproc — e.g. Q93 'None' ticked ->
    skip the lab-cost matrix #673, or a Q85-style pos()-based soft-warn that the generic 90
    exclusivity can't express), and (when present) the 'Other (specify)' text gate on
    pos("99", base). Mirrors F1 generate_apc._gen_checkbox_proc / the F3 Q148 hand-write."""
    qn = re.match(r"Q(\d+)", base).group(1)
    body = [f"PROC {base}"]
    if gate:
        body += ["preproc", gate]
    body += ["postproc",
             f"  if length(strip({base})) = 0 then",
             f'    errmsg("Select at least one option for Q{qn} before continuing.");',
             "    reenter;", "  endif;"]
    if exclusive:
        body += [f'  if pos("90", {base}) > 0 and length(strip({base})) > 2 then',
                 f'    errmsg("Q{qn}: an exclusive option (None / I don\'t know) should be the '
                 f'only choice - please review the options ticked.");',
                 "  endif;"]
    if postextra:
        body += [postextra]
    procs = {base: "\n".join(body)}
    if has_other:
        procs[f"{base}_OTHER_TXT"] = (
            f"PROC {base}_OTHER_TXT\npreproc\n"
            f'  if pos("99", {base}) = 0 then\n'
            f'    {base}_OTHER_TXT = "";   {{ gated: \'Other (specify)\' not ticked -> not enterable }}\n'
            f"    noinput;\n  endif;\npostproc\n"
            f'  if pos("99", {base}) > 0 and length(strip({base}_OTHER_TXT)) = 0 then\n'
            f'    errmsg("\'Other (specify)\' was ticked for Q{qn} - please specify.");\n'
            "    reenter;\n  endif;"
        )
    return procs


CHECKBOX_MULTISELECT_PROCS = {}
for _row in CHECKBOX_CONVERT:
    # rows are (base, has_other, exclusive, gate) or (..., gate, postextra)
    _b, _o, _x, _g = _row[0], _row[1], _row[2], _row[3]
    _pe = _row[4] if len(_row) > 4 else None
    CHECKBOX_MULTISELECT_PROCS.update(_gen_checkbox_proc(_b, _o, _x, _g, _pe))

# Append the generated Check Box PROCs to EXTRA_PROCS so they emit alongside the
# hand-written Q148 block and are seeded into `covered` (via CHECKBOX_COVERED).
EXTRA_PROCS = (EXTRA_PROCS.rstrip("\n")
               + "\n\n{ ---- #529/#669/#670/#671/#673: select_all -> Check Box conversions "
                 "— config-driven from CHECKBOX_CONVERT ---- }\n"
               + "\n\n".join(CHECKBOX_MULTISELECT_PROCS[k]
                             for k in sorted(CHECKBOX_MULTISELECT_PROCS))
               + "\n")

# Every field name owned by a Check Box bespoke PROC (the 13 bases + their _OTHER_TXT)
# — seeded into `covered` so the dcf-driven other-specify / select-all auto-gens skip them.
CHECKBOX_COVERED = set(CHECKBOX_MULTISELECT_PROCS)


# Validations (spec 3.3 demographics + household-composition consistency).
VALIDATION_PROCS = """\
{ ---- Validations: demographics + household composition (spec 3.3) ---- }
PROC Q5_BIRTH_MONTH
postproc
  if Q5_BIRTH_MONTH < 1 or Q5_BIRTH_MONTH > 12 then
    errmsg("Birth month must be 1-12.");
    reenter;
  endif;

PROC Q5_BIRTH_YEAR
postproc
  if Q5_BIRTH_YEAR < 1900 or Q5_BIRTH_YEAR > currentYear then
    errmsg("Birth year must be between 1900 and %d.", currentYear);
    reenter;
  endif;

PROC Q6_AGE
postproc
  if Q6_AGE < 0 or Q6_AGE > 120 then
    errmsg("Age must be 0-120.");
    reenter;
  endif;
  if abs((currentYear - Q5_BIRTH_YEAR) - Q6_AGE) > 1 then
    errmsg("Age (%d) is inconsistent with birth year %d (current year %d). Reenter.",
           Q6_AGE, Q5_BIRTH_YEAR, currentYear);
    reenter;
  endif;

PROC Q18_INCOME_BRACKET
postproc
  { #398: 'Don't know' (99) — respondent can't even estimate household income.
    No bracket amount is required; bypass the bracket<->amount reconciliation. }
  if Q18_INCOME_BRACKET = 99 then
    exit;
  endif;
  { bracket must contain Q18_INCOME_AMOUNT — #631: 11 contiguous 50k bands }
  numeric a = Q18_INCOME_AMOUNT;
  numeric ok = 0;
  if a = -98 or a = -99 then ok = 1; endif;   { #761: -98 don't-know / -99 refused -> no bracket cross-check }
  if Q18_INCOME_BRACKET = 1  and a < 50000 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 2  and a >= 50000  and a <= 99999  then ok = 1; endif;
  if Q18_INCOME_BRACKET = 3  and a >= 100000 and a <= 149999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 4  and a >= 150000 and a <= 199999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 5  and a >= 200000 and a <= 249999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 6  and a >= 250000 and a <= 299999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 7  and a >= 300000 and a <= 349999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 8  and a >= 350000 and a <= 399999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 9  and a >= 400000 and a <= 449999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 10 and a >= 450000 and a <= 499999 then ok = 1; endif;
  if Q18_INCOME_BRACKET = 11 and a >= 500000 then ok = 1; endif;
  if ok = 0 then
    errmsg("Income bracket does not match the reported amount (%d PHP/month). Reconcile.", a);
    reenter;
  endif;

PROC Q19_HH_SIZE
postproc
  if Q19_HH_SIZE < 1 or Q19_HH_SIZE > 30 then
    errmsg("Household size must be 1-30.");
    reenter;
  endif;
  if Q19_HH_SIZE > 15 then
    errmsg("Household size %d is unusually large. Confirm.", Q19_HH_SIZE);
  endif;

PROC Q20_HH_CHILDREN
postproc
  if Q20_HH_CHILDREN > Q19_HH_SIZE then
    errmsg("Children (%d) cannot exceed household size (%d).", Q20_HH_CHILDREN, Q19_HH_SIZE);
    reenter;
  endif;

PROC Q21_HH_SENIORS
postproc
  if Q21_HH_SENIORS > Q19_HH_SIZE then
    errmsg("Seniors (%d) cannot exceed household size (%d).", Q21_HH_SENIORS, Q19_HH_SIZE);
    reenter;
  endif;
  if Q20_HH_CHILDREN + Q21_HH_SENIORS > Q19_HH_SIZE then
    errmsg("Children + seniors (%d) exceed household size (%d).",
           Q20_HH_CHILDREN + Q21_HH_SENIORS, Q19_HH_SIZE);
    reenter;
  endif;

PROC Q28_WASHER
postproc
  if Q22_ELECTRICITY = 2 and (Q26_REFRIGERATOR = 1 or Q27_TELEVISION = 1 or Q28_WASHER = 1) then
    errmsg("Household reports no electricity but owns a powered appliance. Confirm.");
  endif;
"""

# Skip logic, table-driven (spec 2). Single-condition rows here; multi-branch
# routing (Q63/Q77/Q159) + end-of-survey (Q162) + cross-field gate (Q46) are in
# EXTRA_PROCS above.
SKIP_RULES = [
    # Section A — Introduction & Consent
    ("Q1_IS_PATIENT",        "Q1_IS_PATIENT = 1",            "Q4_NAME"),                 # respondent IS the patient -> skip Q2,Q3
    # Section B — Patient Profile
    ("Q8_LGBTQIA",           "Q8_LGBTQIA <> 1",              "Q10_CIVIL_STATUS"),        # #392: Q9 (LGBTQIA+ group) only when Q8=Yes
    ("Q11_PWD",              "Q11_PWD = 2",                  "Q15_EDUCATION"),
    ("Q12_PWD_SPECIFY",      "Q12_PWD_SPECIFY = 2",          "Q15_EDUCATION"),
    ("Q13_PWD_CARD",         "Q13_PWD_CARD <> 1",            "Q15_EDUCATION"),           # #393: Q14 (disability type) only when card presented & verified (Q13=1)
    ("Q30_IP",               "Q30_IP = 2",                   "Q32_4PS"),
    ("Q33_DECISION_MAKER",   "Q33_DECISION_MAKER in 1,3",    "Q35_UHC_HEARD"),
    # Section C — UHC Awareness
    ("Q35_UHC_HEARD",        "Q35_UHC_HEARD = 2",            "Q38_PHILHEALTH_REG"),
    # Section D — PhilHealth / Insurance
    ("Q38_PHILHEALTH_REG",   "Q38_PHILHEALTH_REG in 2,3",    "Q43_KNOWS_ASSIST"),
    ("Q41_REG_DIFFICULTY",   "Q41_REG_DIFFICULTY = 2",       "Q43_KNOWS_ASSIST"),
    ("Q43_KNOWS_ASSIST",     "Q43_KNOWS_ASSIST = 2",         "Q45_CATEGORY"),
    ("Q48_PREMIUM_PAY",      "Q48_PREMIUM_PAY = 3",          "Q51_OTHER_INSURANCE"),
    ("Q49_PREMIUM_DIFFICULT","Q49_PREMIUM_DIFFICULT = 2",    "Q51_OTHER_INSURANCE"),
    ("Q51_OTHER_INSURANCE",  "Q51_OTHER_INSURANCE = 2",      "Q53_HAS_PCP"),
    # Section E — Primary Care Utilization
    ("Q53_HAS_PCP",          "Q53_HAS_PCP = 2",              "Q63_HAS_USUAL_FACILITY"),
    # Q66_SAME_AS_USUAL routing now lives in EXTRA_PROCS (Q63 usual-facility block, #418/#419).
    ("Q74_KON_HEARD",        "Q74_KON_HEARD = 2",            "Q83_VISIT_REASON"),
    ("Q80_KON_KNOWS_BOOKING","Q79_KON_HAD_APPT = 2",         "Q83_VISIT_REASON"),   # #771: Q81 (appt check-up) is gated on Q79=Yes (spec §4 line 407 — "Q81 enabled when Q77=Yes AND Q79=Yes"). Q79=No -> skip Q81 -> Q83 (Q82 is Q77=No-only). The gate was missing, so Q81 wrongly showed after Q80 when Q79=No.
    # Section K — Access to Medicines
    ("Q145_PURCHASE_FREQ",   "Q145_PURCHASE_FREQ = 5",       "AREA_HAS_GAMOT"),          # Never -> skip meds-access (land on the GAMOT area-gate, #495)
    ("AREA_HAS_GAMOT",       "AREA_HAS_GAMOT = 2",           "Q158_BRAND_GEN_KNOW"),     # #495: area has no GAMOT -> skip Q152-159 (mirrors Q152=No)
    ("Q152_GAMOT_HEARD",     "Q152_GAMOT_HEARD = 2",         "Q158_BRAND_GEN_KNOW"),
    ("Q158_BRAND_GEN_KNOW",  "Q158_BRAND_GEN_KNOW = 2",      "Q162_REFERRED"),
    # Section L — Referrals
    # Q169_VISITED routing moved to a bespoke PROC in EXTRA_PROCS (#799: code 2 -> Q171, code 3 -> Q172).
    ("Q172_PCP_REFERRAL",    "Q172_PCP_REFERRAL = 2",        "Q177_WHY_HOSPITAL"),   # #529: Q177 is now the Check Box base (was _O01)
    # Section G — Outpatient Care
    # #775 (R5): Q89 -> Q90 -> Q91 now proceeds UNCONDITIONALLY. The #688 skip (Q89=No -> skip Q90)
    #   is REMOVED — tester + paper want no restriction (spec §3.8 note 10: "Q90 asked regardless of
    #   Q89; source prints no skip between Q89 and Q90"). Reverses #688. The Q90 select-all HARD rule
    #   "≥1 ticked when Q89=No" (spec line 511) is unaffected — it only fires when Q89=No.
    # Q93_LABS_O17 'None' routing now in EXTRA_PROCS (exclusivity warn must precede the skip, #448).
    ("Q95_PRESCRIBED",     "Q95_PRESCRIBED = 2",                          "Q97_FINAL_AMOUNT"),       # No prescription -> skip meds-cost matrix
    ("AREA_HAS_BUCAS",     "AREA_HAS_BUCAS = 2",                          "Q116_NBB_HEARD"),         # #464: area has no BUCAS -> skip Q99-104 (mirrors Q99=No)
    ("Q99_BUCAS_HEARD",    "Q99_BUCAS_HEARD = 2",                         "Q116_NBB_HEARD"),         # No -> end of Section G (sanity #9; skip Q100-104)
    ("Q102_BUCAS_ACCESSED","Q102_BUCAS_ACCESSED = 2",                     "Q104_WITHOUT_BUCAS"),     # No -> Q104 (skip Q103)
    # Section H — Inpatient Care
    ("Q108_MEDS_OUTSIDE",  "Q108_MEDS_OUTSIDE = 2",                       "Q110_LAB_OUTSIDE"),       # No -> skip meds-outside-cost
    ("Q110_LAB_OUTSIDE",   "Q110_LAB_OUTSIDE = 2",                        "Q113_SOURCES"),           # No -> skip Q111/Q112 to the hospital-bill pay matrix (Option B fan-out #693: was Q113_PAY_01)
    # Section I — Financial Risk Protection
    ("Q116_NBB_HEARD",     "Q116_NBB_HEARD in 2,3",                       "Q119_ZBB_HEARD"),         # No / IDK -> skip Q117,Q118
    ("Q119_ZBB_HEARD",     "Q119_ZBB_HEARD in 2,3",                       "Q124_MAIFIP_HEARD"),      # No / IDK -> skip Q120-123
    ("Q124_MAIFIP_HEARD",  "Q124_MAIFIP_HEARD in 2,3",                    "Q130_REDUCED_SPEND"),     # No / IDK -> skip Q125-129
    # Q126_MAIFIP_AVAILED routing now in EXTRA_PROCS (inpatient gate #479 + #482 No->Q129).
    ("Q127_MAIFIP_OOP",    "Q127_MAIFIP_OOP = 2",                         "Q130_REDUCED_SPEND"),     # No -> skip Q128,Q129
]

TODO_NOTE = """\
{ ============================================================================
  STILL OPEN (follow-up F3 pass):
    - Q93 "None"(O17)->Q95 (select-all None flag) + Q113_PAY_08 Yes -> Q114.1
      (PhilHealth-availed gate) — select-all/matrix patterns, transcribe per dcf.
    - Section-specific validations (spec 3.2-3.14): dates, amount ranges,
      consistency checks (e.g. Q86<=Q85 patterns).
    - Single/select-all Other-specify (non-UHC9) — per-item parent + trigger.
    - Verify PATIENT_TYPE codes (1/2) + all option codes on first Designer compile.
    - Filipino label content + setlanguage (FMF Designer side).
  DONE this pass: skip logic Sections A-C, D-F (incl. non-member benefits gate),
    E primary-care, G/H/I (#164 branching), K, L (incl. end-of-survey).
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


def uhc9_other_specify_procs(names):
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


def skip_proc(field, cond, target):
    return (f"PROC {field}\npostproc\n  if {cond} then\n    skip to {target};\n  endif;")


DISPOSITION_PROCS = """\
{ ---- #515 break-off + #561 disposition -------------------------------------------
  BREAKOFF is the case-start "interview status" control (shares the PATIENT_TYPE
  screen, so it is in the case tree from the first field, and the enumerator can tap
  back to it mid-interview). Leaving it "Continue" (1) is a no-op. Any other choice
  records the matching Result-of-Visit disposition and SKIPS straight to the closing
  Result-of-Visit field (the proven Q162_REFERRED jump) — so a withdrawn / postponed /
  stopped interview reaches the closing form without walking every required question
  (R4 #515). CASE_DISPOSITION (off-form) is the completeness sentinel the Supervisor
  App + CSWeb exports read (R4 #561): 0 In Progress (set at case open), 1 Completed,
  2 Partial. }
PROC BREAKOFF
preproc
  if not (BREAKOFF in 1, 2, 3, 4) then BREAKOFF = 1; endif;   { default "Continue" }
postproc
  if BREAKOFF <> 1 then
    if BREAKOFF = 2 then ENUM_RESULT_FINAL_VISIT = 6; endif;   { Withdraw Participation/Consent }
    if BREAKOFF = 3 then ENUM_RESULT_FINAL_VISIT = 3; endif;   { Postponed }
    if BREAKOFF = 4 then ENUM_RESULT_FINAL_VISIT = 4; endif;   { Incomplete }
    CASE_DISPOSITION = 2;   { partial / broke off }
    skip to ENUM_RESULT_FINAL_VISIT;
  endif;

PROC ENUM_RESULT_FINAL_VISIT
postproc
  { #561: classify from the final Result-of-Visit. Completed codes 1/2/5 -> Completed;
    3 Postponed, 4 Incomplete, 6 Withdraw -> Partial. }
  if ENUM_RESULT_FINAL_VISIT in 1, 2, 5 then
    CASE_DISPOSITION = 1;
  else
    CASE_DISPOSITION = 2;
  endif;
  { #515: a Postponed (3) / Withdraw (6) visit had no interview, so there is nothing to
    photograph — end the case here instead of walking into the Verification Photo form,
    whose trigger field would otherwise loop on an out-of-range stop (device-confirmed
    2026-06-21). Codes 1/2/4/5 fall through to the photo as before (this matches the
    CAPTURE_VERIFICATION_PHOTO gate exactly). }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 2, 4, 5) then
    endlevel;   { statement form (no parens) — strict packager rejects endlevel() }
  endif;
"""


def main():
    parts = [HEADER, "", CONTROL_PROCS, "", DISPOSITION_PROCS, "", BRANCHING, "", EXTRA_PROCS, "",
             VALIDATION_PROCS, "", Q92_ROSTER_PROCS, "",   # Q92 roster (Option B pilot)
             Q971_ROSTER_PROCS, "",   # Q97.1 CheckBox + roster (Option B Shape B)
             # Option B fan-out (2026-06-19): the remaining F3 cost-matrix cluster.
             Q94_LAB_ROSTER_PROCS, "", Q96_ROSTER_PROCS, "",      # Q94 per-lab (#450) + Q96
             Q972_ROSTER_PROCS, "", Q98_ROSTER_PROCS, "",         # Section G all-amount
             Q107_ROSTER_PROCS, "", Q109_ROSTER_PROCS, "",        # Section H all-amount
             Q112_ROSTER_PROCS, "", Q113_ROSTER_PROCS, ""]        # Section H all-amount
    covered = {"BREAKOFF", "ENUM_RESULT_FINAL_VISIT", "CASE_DISPOSITION",  # #515/#561 disposition PROCs
               "Q88_WHY_VISIT", "Q105_REASON",                    # branching PROCs
               "Q63_HAS_USUAL_FACILITY", "Q77_KON_REGISTERED",
               "Q159_BRAND_GEN_BOUGHT", "Q162_REFERRED",  # EXTRA_PROCS (#529: Q46_BENEFITS_O01 gone — Q46 is now a Check Box, gate folded into its checkbox PROC)
               # #671: Q82_KON_WHY_NOT_REG_O01 gone — Q82 is now a Check Box base (in CHECKBOX_COVERED); not-registered gate folded into its checkbox PROC.
               "Q64_FACILITY_NAME", "Q66_SAME_AS_USUAL",   # EXTRA_PROCS (#418/#419 Q63 block)
               "Q45_CATEGORY", "Q60_SCHED_TELECON_OK", "Q62_CONSULT_TELECON_OK",  # EXTRA_PROCS (#402/#415/#417 gates)
               # #673: Q93_LABS_O17 gone — Q93 is now a Check Box base (in CHECKBOX_COVERED); None exclusivity + Q94-skip folded into its checkbox PROC.
               "Q122_ZBB_INFORMED", "Q126_MAIFIP_AVAILED",   # EXTRA_PROCS (#476/#479 confinement gates)
               "Q148_CONDITIONS", "Q148_CONDITIONS_OTHER_TXT",  # EXTRA_PROCS (Q148 Check Box) — #491: Q148_MEDICINES_TXT removed
               "Q147_MEDS_LIST", "Q155_GAMOT_GOT_MEDS", "Q156_GAMOT_MEDS_LIST",   # EXTRA_PROCS (Wave 4 #490/#498)
               "Q169_VISITED",   # #799: bespoke routing PROC in EXTRA_PROCS (code 2 -> Q171, code 3 -> Q172)
               "Q170_FOLLOWUP",  # EXTRA_PROCS (Wave 4 #508/#511; #503/#696: Q161_WHY_BRANDED_O01 gone — Q161 now a Check Box base, gate folded into its checkbox PROC; #529: Q177_WHY_HOSPITAL_O01 gone — same)
               "Q5_BIRTH_MONTH", "Q5_BIRTH_YEAR", "Q6_AGE", "Q18_INCOME_BRACKET",
               "Q19_HH_SIZE", "Q20_HH_CHILDREN", "Q21_HH_SENIORS", "Q28_WASHER",  # VALIDATION_PROCS
               # #529: the 13 select_all -> Check Box bases (+ their _OTHER_TXT) get
               # bespoke PROCs from CHECKBOX_MULTISELECT_PROCS (added below) — seed them
               # into `covered` so the dcf-driven other-specify / select-all auto-gens
               # never mis-fire on the alpha checkbox field or its gated text.
               "Q92_SOURCES", "Q92_PAY_LINE", "Q92_PAY_SRC", "Q92_PAY_AMT",  # Q92 roster (Option B pilot)
               # Q97.1 (Option B Shape B roster): Q971_SOURCES CheckBox + the roster
               # fields (LINE/SRC/AMT) + the gated Other-specify text are owned by
               # Q971_ROSTER_PROCS (above) — seed them so amount_required_procs /
               # other_specify_procs / select-all auto-gens never double-PROC them.
               "Q971_SOURCES", "Q971_PAY_LINE", "Q971_PAY_SRC", "Q971_PAY_AMT",
               "Q971_OTHER_TXT",
               # Option B fan-out (2026-06-19): the rest of the F3 cost-matrix cluster.
               # Each converted matrix's CheckBox + 3 roster fields are owned by its
               # build_roster_procs() block; seed them (+ any gated specify-text) so the
               # dcf-driven amount-required / other-specify / select-all auto-gens never
               # double-PROC them. (The Q9n_PAY_OTHER_TXT gates here are owned by the
               # roster blocks' gated_texts, NOT by other_specify_procs.)
               "Q94_LAB_LINE", "Q94_LAB_CODE", "Q94_LAB_PAY", "Q94_LAB_AMT",  # #450 per-lab roster
               "Q96_SOURCES",  "Q96_PAY_LINE",  "Q96_PAY_SRC",  "Q96_PAY_AMT",
               "Q972_SOURCES", "Q972_PAY_LINE", "Q972_PAY_SRC", "Q972_PAY_AMT", "Q972_OTHER_TXT",
               "Q98_SOURCES",  "Q98_PAY_LINE",  "Q98_PAY_SRC",  "Q98_PAY_AMT",
               "Q98_OTHER_DONATION_TXT", "Q98_OTHER_TXT",
               "Q107_SOURCES", "Q107_PAY_LINE", "Q107_PAY_SRC", "Q107_PAY_AMT", "Q107_PAY_OTHER_TXT",
               "Q109_SOURCES", "Q109_PAY_LINE", "Q109_PAY_SRC", "Q109_PAY_AMT", "Q109_PAY_OTHER_TXT",
               "Q112_SOURCES", "Q112_PAY_LINE", "Q112_PAY_SRC", "Q112_PAY_AMT", "Q112_PAY_OTHER_TXT",
               "Q113_SOURCES", "Q113_PAY_LINE", "Q113_PAY_SRC", "Q113_PAY_AMT", "Q113_PAY_OTHER_TXT",
               *CHECKBOX_COVERED}

    parts.append("{ ---- Skip logic (spec 2) ---- }")
    for field, cond, target in SKIP_RULES:
        if field in covered:
            raise SystemExit(f"PROC collision: {field}")
        covered.add(field)
        parts.append(skip_proc(field, cond, target))
        parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — UHC9 dual-other (spec 4) ---- }")
    for field, proc in sorted(uhc9_other_specify_procs(dcf_item_names()).items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    # Auto-derived single-choice + select-all 'Other (specify)' enforcement (#148).
    os_procs, os_map, os_skipped = other_specify_procs(dcf_items_map())
    parts.append("{ ---- 'Other (specify)' enforcement — single-choice + select-all "
                 f"(auto-derived from dcf: {len(os_procs)} items) ---- }}")
    for field, proc in sorted(os_procs.items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    # Auto-derived select-all validation: >=1 option ticked (#3.5-3.14).
    sa_procs, sa_bases = select_all_validation_procs(dcf_items_map())
    sa_emitted = 0
    parts.append("{ ---- Select-all validation — >=1 option ticked "
                 "(auto-derived from dcf) ---- }")
    for field, proc in sorted(sa_procs.items()):
        if field in covered:   # last flag already drives a skip/other-specify -> don't double-PROC
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")
        sa_emitted += 1

    # Amount-required on payment-matrix _AMT fields (spec §3.9/§3.10 "if PAY=Yes, AMT>0").
    am_procs = amount_required_procs(dcf_items_map())
    am_emitted = 0
    parts.append("{ ---- Payment-matrix amount-required (auto-derived from dcf) ---- }")
    for field, proc in sorted(am_procs.items()):
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append(""); am_emitted += 1

    # Payment-matrix '>=1 row ticked' (#555/#556/#557). Option B fan-out (#691/#692/#693,
    # 2026-06-19): Q107/Q109/Q112/Q113 are now CheckBox -> roster, so their >=1-source
    # requirement is enforced by the CheckBox SOURCES postproc (build_roster_procs) — NOT
    # here. This dict is now empty (the flat _PAY_NN flag fields no longer exist; the loop
    # below self-disables on len(flags) < 2). Kept as the seam for any future flat matrix.
    paymatrix_atleast1 = {}
    pm_items = dcf_items_map()
    parts.append("{ ---- Payment-matrix '>=1 ticked' (#555/#556/#557) ---- }")
    pm_emitted = 0
    for base, desc in paymatrix_atleast1.items():
        flags = sorted(n for n in pm_items
                       if n.startswith(base + "_") and n[len(base) + 1:].isdigit())
        if len(flags) < 2:
            continue
        last = flags[-1]
        any_ticked = " or ".join(f"{f} = 1" for f in flags)
        body = (f"  if not ({any_ticked}) then\n"
                f"    errmsg(\"Select {desc} before continuing — "
                f"at least one option must be 'Yes'.\");\n"
                f"    reenter;\n  endif;")
        inject_soft(parts, last, body)
        covered.add(last)
        pm_emitted += 1

    # Per-item numeric range checks + cross-field/pair-sanity (spec §3.6–§3.13).
    parts.append("{ ---- Range + cross-field validations (spec §3.6-§3.13) ---- }")
    rng_emitted = 0
    for field, lo, hi, soft in RANGE_CHECKS:
        if field in covered:
            continue
        covered.add(field)
        parts.append(range_check_proc(field, lo, hi, hard=True, soft_over=soft))
        parts.append(""); rng_emitted += 1
    for field, proc in CUSTOM_VALIDATION:
        if field in covered:
            continue
        covered.add(field); parts.append(proc); parts.append(""); rng_emitted += 1

    # SOFT plausibility cross-field warnings (merged into existing procs where present).
    parts.append("{ ---- Soft plausibility cross-field warnings (spec §3.5-§3.13) ---- }")
    sc_merged = sc_new = 0
    for field, body in SOFT_CROSS:
        if inject_soft(parts, field, body) == "merged":
            sc_merged += 1
        else:
            sc_new += 1
        covered.add(field)

    parts.append(TODO_NOTE)
    text = "\n".join(parts).rstrip() + "\n"
    OUT.write_text(text, encoding="utf-8")
    dupes = [l for l in text.splitlines() if l.startswith("PROC ")]
    assert len(dupes) == len(set(dupes)), "duplicate PROC names emitted"
    print(f"Wrote {OUT} ({len(text)} chars, {len(dupes)} PROC blocks, no dup names).")
    print(f"  other-specify enforcement: {len(os_procs)} auto-derived "
          f"({sum(1 for _, d in os_map if d.startswith('single'))} single + "
          f"{sum(1 for _, d in os_map if d.startswith('select'))} select-all)")
    if os_skipped:
        print(f"  other-specify SKIPPED (manual review — no resolvable trigger): {', '.join(os_skipped)}")
    print(f"  select-all validation: {sa_emitted} groups got a '>=1 ticked' check "
          f"(of {len(sa_bases)} detected; rest already drive a skip/other-specify)")
    print(f"  amount-required: {am_emitted} payment-matrix _AMT procs; "
          f"range/cross-field: {rng_emitted} procs")
    print(f"  soft cross-field: {len(SOFT_CROSS)} checks ({sc_merged} merged, {sc_new} new procs)")
    print("  NEXT: create the F3 .ent in Designer (input dcf + generated.fmf), set this")
    print("  as the main logic file, compile, fix any name/code mismatch, verify in CSEntry.")


if __name__ == "__main__":
    main()
