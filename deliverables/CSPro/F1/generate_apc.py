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
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cspro_helpers import select_all_exclusive_warning_procs, numberize_errmsgs

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

    def other_codes(m):
        """The value-set codes on item `m` whose EN label mentions 'other'."""
        vss = items[m].get("valueSets") or []
        if not vss:
            return []
        codes = []
        for v in vss[0].get("values", []):
            vlab = next((l.get("text", "") for l in v.get("labels", [])
                         if l.get("language") in (None, "EN")), "")
            if "other" in vlab.lower() and v.get("pairs"):
                codes.append(v["pairs"][0].get("value"))
        return codes

    def display_qnum(name):
        """`Q12_1_UHC_ATTRIB` -> 'Q12.1'; `Q21_DATA_SUBMIT` -> 'Q21'. Used only for the
        enumerator-facing errmsg, so it reads as the printed question number."""
        m = re.match(r"^Q(\d+)_(\d+)_", name)
        if m:
            return f"Q{m.group(1)}.{m.group(2)}"
        m = re.match(r"^Q(\d+)_", name)
        return f"Q{m.group(1)}" if m else name

    def gated_text_proc(n, cond, label):
        return (
            f"PROC {n}\n"
            f"preproc\n"
            f"  if not ({cond}) then\n"
            f"    {n} = \"\";   {{ skip + clear: no 'other' option chosen }}\n"
            f"    noinput;\n"
            f"  endif;\n"
            f"postproc\n"
            f"  if ({cond}) and length(strip({n})) = 0 then\n"
            f"    errmsg(\"An 'other' option was selected for {label}. Please specify.\");\n"
            f"    reenter;\n"
            f"  endif;"
        )

    procs, unmatched = {}, []
    for n in order:
        if not n.endswith("_TXT"):
            continue
        # #529: a checkbox base's _OTHER_TXT is gated by pos("99", base) in the
        # checkbox PROC / why_difficult_gate_procs — never by the auto-derived
        # `parent = <other code>` path (the base is alpha, the _O## flag is gone).
        if n.endswith("_OTHER_TXT") and n[:-len("_OTHER_TXT")] in CHECKBOX_BASES:
            continue
        # AUG-17 (Task 2.4): STEM-FIRST match, tried before the same-Q sibling scan.
        # The house naming convention is `<PARENT>_OTHER_TXT`, so when the literal stem
        # is itself an item offering an 'other' code, that IS the parent — no inference
        # needed. This matters because the two-step split put TWO other-bearing items
        # under one question number: Q12 now holds Q12_1_UHC_ATTRIB *and* Q12_2_PHU_ROLE,
        # Q13 holds Q13_1_UHC_ATTRIB *and* Q13_2_HPU_ROLE, Q35 holds Q35_1_UHC_ATTRIB *and*
        # Q35_2_PCQM_MEASURES. The sibling scan below sees 2 candidate parents for each,
        # gives up, and leaves the text box UNGATED — answerable with no 'Other' ticked.
        # Five boxes were exposed; the stem match resolves all five exactly.
        stem = n[: -len("_OTHER_TXT")] if n.endswith("_OTHER_TXT") else None
        if stem and stem in items:
            codes = other_codes(stem)
            if codes:
                cond = " or ".join(f"{stem} = {c}" for c in codes)
                procs[n] = gated_text_proc(n, cond, display_qnum(stem))
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
    ({parent: target}).

    #630/#632 fix: that trailing skip MUST be guarded `if {parent} = {code}`. The
    original code left it unconditional on the false premise that "a noinput'd field
    never runs its postproc". In CSEntry `noinput` only suppresses data ENTRY — the
    postproc STILL executes. So the unconditional skip fired for EVERY parent value
    (incl. the Yes branches 1-4 that noinput this box), wrongly dropping the Yes-only
    follow-up for the whole Section C chain (Q15/Q18/Q20/Q22/Q24/Q26/Q28/Q30/Q32-34).
    Guarding on the No-other code makes it fire only when the box is genuinely shown.

    AUG-17 (Task 2.4): this emits NOTHING against the rebuilt dictionary, and that is the
    correct end state, not a re-key miss. The Aug-17 two-step split replaced the nine-option
    "UHC9" implementation-status sets with a Yes/No base plus a `Q<NN>_1_UHC_ATTRIB` probe,
    and each retired UHC9 item shed both dual-other companions — 22 parents x 2 boxes = 44
    `_YES_OTHER_TXT`/`_NO_OTHER_TXT` items deleted, 0 remaining (verified against the built
    .dcf). ELEVEN emitted skip rules went with them; they are DELIBERATELY DROPPED, not
    re-keyed:
      * 9 `_NO_OTHER_TXT` trailing `skip to` tails (the #376/#630/#632 pair-rewrite), on the
        parents whose No-branch range swallowed code 7 — Q14_PHU_CREATED, Q17_HPU_CREATED,
        Q19_NEW_ROLES, Q21_NEW_DEPTS, Q23_NEW_BUILDINGS, Q25_NEW_ROOMS, Q27_INC_EQUIPMENT,
        Q29_INC_SUPPLIES, Q31_EMR_USE (all Apr-20 names). Their whole reason for existing —
        a 9-option set where codes 5:9 meant "No, ..." and code 7 meant "No, other reason" —
        no longer exists: the Aug-17 bases are plain Yes(1)/No(2), so no skip range can
        swallow a No-other code, and there is no No-other box to reach.
      * 2 that survive under new names rather than retiring, because their sources are
        ordinary specify boxes on questions that carried through the renumber:
        Q103_OTHER_TXT -> Q90_OTHER_TXT and Q110_OTHER_TXT -> Q97_OTHER_TXT, both re-keyed
        in ROUTING_PROCS below. (Task 2.3 §11 counted all 11 as unresolved because it mapped
        through `maps/F1-renames.csv`, which carries no rows for derived `_OTHER_TXT`
        companions; the correct split is 9 retired + 2 re-keyed.)
    The MACHINERY stays: this function, `dual_other_no_skip_map`, `exclude_code7_from_skip`
    and `_skip_codes_for` are all intact and still exercised by the SKIP_RULES conditions,
    which are deliberately kept in the recognized shapes (`FIELD = N`, `FIELD in a,b`,
    `FIELD in lo:hi`). If a dual-other item ever returns, the pair-rewrite works unchanged.
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
                        f"\n  {{ #630/#632: skip the Yes-only follow-up ONLY for the real\n"
                        f"     No-other branch (code {code}). noinput suppresses ENTRY but the\n"
                        f"     postproc STILL runs in CSEntry, so an unconditional skip here\n"
                        f"     fired for the Yes branches too and dropped the follow-up. }}\n"
                        f"  if {parent} = {code} then\n"
                        f"    skip to {target};\n"
                        f"  endif;"
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


# Why-difficult display gates (spec 4.10): each Q53-61 option-set is shown only
# if the matching Q52 difficulty option was flagged; same for Q109-121 vs Q108.
# Both batteries are Check Box (Q52->Q53-61 via #529; Q108->Q109-121 via #567
# parts 1 & 2), so the gate is `pos("0N", <gate_cb>) = 0` on the Check Box field.
# Question number -> option index by POSITION, PRESERVED 1:1 from the original
# select_all gating (Q53->Q52 opt 01 ... Q61->Q52 opt 09; Q109->Q108 opt 01 ...).
# (qrange, gate_field, start, code_override). code_override maps a follow-up question
# number -> the Q-gate option code it actually gates on, for batteries whose tail is
# REORDERED vs the positional q-start+1 default.
#
# AUG-17 (Task 2.4): re-anchored from Q66-74/Q65 and Q122-134/Q121 to the Aug-17
# numbers. The licensing battery moved bodily to Section F Q108 (gate) + Q109-Q121.
WHY_DIFF_GATES = [
    (range(53, 62), "Q52_ACCRED_DIFFICULT", 53, None),   # Q53..Q61 -> Q52 opt 01..09 (positional — correct)
    # F1-LOGIC-01 fix (2026-06-27), RE-VERIFIED against the Aug-17 value set (Task 2.4):
    # the printed follow-up tail is still REORDERED vs the gate's option codes, so positional
    # mapping would again invert the PCF-only/hospital-only gating. Per Q108_DOH_LIC_DIFFICULT_VS1:
    # Q117=public-access-to-price-information(13, PCF-only), Q118=equipment(09),
    # Q119=national-laws(10), Q120=emergency-cart(11, hospitals only),
    # Q121=add-on-services(12, hospitals only). Q109-Q116 stay positional (01..08).
    (range(109, 122), "Q108_DOH_LIC_DIFFICULT", 109,
     {117: "13", 118: "09", 119: "10", 120: "11", 121: "12"}),
]


# #529: every select_all base is a single Check Box field. As of #567 (parts 1 & 2)
# the Section F DOH-licensing why-difficult battery (Q108 gate + Q109-121 per-topic
# "why") is ALSO converted — mirroring the proven Q52->Q53-61 gated-battery pattern.
# why_difficult_gate_procs reads this set to switch the Q108->Q109-121 gates to
# `pos("0N", Q108_DOH_LIC_DIFFICULT) = 0`.
#
# AUG-17 (Task 2.4): DERIVED FROM THE DICTIONARY, no longer a hand-maintained literal.
# `cspro_helpers.checkbox_multiselect` emits exactly one shape — a single `alpha` item
# carrying a value set — and nothing else in F1 has that shape. This is the same
# derivation `generate_fmf.py` adopted in Task 2.3, which reproduced F3's hand-maintained
# 51-name literal exactly (51/51, no drift either direction).
#
# WHY DERIVED. This was one of FOUR copies that had to move together; missing one
# silently DEMOTES a multi-select to a single-select DropDown, a data-loss regression
# that had already happened twice (#529 batch, #635/#639/#640). Two copies retired with
# the injectors in 2.3, 2.3 derived the .fmf's, and this — the last hand-maintained one —
# is derived here. `automation/optimize_capture_types.CHECKBOX` remains the only literal,
# and it is the one the gates check.
def _derive_checkbox_bases():
    """-> {names} of checkbox_multiselect bases: single alpha items carrying a value set."""
    items, _ = dcf_items_full()
    return {n for n, it in items.items()
            if it.get("contentType") == "alpha" and it.get("valueSets")}


CHECKBOX_BASES = _derive_checkbox_bases()


def why_difficult_gate_procs(names, checkbox_fields):
    """Each Q66-74 (Q122-134) is shown only if the matching Q65 (Q121) difficulty was
    flagged. After the checkbox conversions (Q65/Q66-74 via #529, Q121/Q122-134 via
    #567 parts 1 & 2) both gate fields are single Check Box fields, so the gate is
    `pos("0N", <gate_cb>) = 0` and the preproc lives on the Check Box field itself,
    carrying the select->=1 validation + 'Other' gate too. (The else-branch _O01-field
    gate is retained for any battery still left as select_all.)"""
    procs = {}
    qnum_of = {n: int(re.match(r"^Q(\d+)_", n).group(1))
               for n in names if re.match(r"^Q(\d+)_", n)}
    primary = {}                                   # question number -> gate field
    for n in names:
        if n in checkbox_fields:
            primary[qnum_of[n]] = n                # Check Box base
    for n in names:
        q = qnum_of.get(n)
        if n.endswith("_O01") and q is not None and q not in primary:
            primary[q] = n                         # non-converted: the _O01 field
    for qrange, gate_dict, start, override in WHY_DIFF_GATES:
        gate_cb = gate_dict in checkbox_fields
        gateq = start - 1
        for q in qrange:
            field = primary.get(q)
            if not field:
                continue
            opt_idx = q - start + 1
            code = (override or {}).get(q, f"{opt_idx:02d}")   # F1-LOGIC-01: reordered tail uses explicit code
            idx = names.index(field)
            target = next((names[j] for j in range(idx + 1, len(names))
                           if qnum_of.get(names[j]) != q), None)
            if target is None:
                continue
            if gate_cb:
                # 2026-07-02 #450-class fix: membership via an aligned 2-char chunk scan.
                # pos("NN", <cb>) substring-matches ACROSS code boundaries once the gate
                # list carries 2-digit codes (Q121 has 09-13: ticking 01+02 packs "0102",
                # which contains "10" and falsely opened the hospitals-only batteries;
                # their >=1 postproc then hard-forced a fabricated answer). do..while +
                # [p:2] + tonumber are the strict-Publish-safe forms (#450 build notes).
                cond_block = (
                    f"  numeric wdN; numeric wdK; numeric wdP; numeric wdHit;\n"
                    f"  wdHit = 0;\n"
                    f"  wdN = length(strip({gate_dict})) / 2;\n"
                    f"  do wdK = 1 while wdK <= wdN\n"
                    f"    wdP = (wdK - 1) * 2 + 1;\n"
                    f"    if tonumber({gate_dict}[wdP:2]) = {int(code)} then wdHit = 1; endif;\n"
                    f"  enddo;\n"
                    f"  if wdHit = 0 then   {{ Q{q} shown only if Q{gateq} difficulty option {code} ticked }}\n"
                    f"    skip to {target};\n  endif;"
                )
            else:
                cond_block = (
                    f"  if {gate_dict}_O{int(code):02d} <> 1 then   {{ Q{q} cluster shown only if {gate_dict}_O{int(code):02d} flagged Yes }}\n"
                    f"    skip to {target};\n  endif;"
                )
            if field in checkbox_fields:           # gate + validation on the Check Box
                procs[field] = (
                    f"PROC {field}\npreproc\n"
                    + cond_block + "\npostproc\n"
                    f"  if length(strip({field})) = 0 then\n"
                    f'    errmsg("Select at least one option for Q{q} before continuing.");\n'
                    f"    reenter;\n  endif;"
                )
                otxt = f"{field}_OTHER_TXT"
                if otxt in names:
                    procs[otxt] = (
                        f"PROC {otxt}\npreproc\n"
                        f'  if pos("99", {field}) = 0 then\n'
                        f'    {otxt} = "";   {{ gated: \'Other (specify)\' not ticked }}\n'
                        f"    noinput;\n  endif;\npostproc\n"
                        f'  if pos("99", {field}) > 0 and length(strip({otxt})) = 0 then\n'
                        f'    errmsg("\'Other (specify)\' was ticked for Q{q} - please specify.");\n'
                        f"    reenter;\n  endif;"
                    )
            else:                                  # non-converted select_all -> _O01 gate
                procs[field] = (
                    f"PROC {field}\npreproc\n" + cond_block
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
# R1a (2026-07-03): the single-QN parse/validate + PSGC-gate control block lives in procs/control_procs.apc — a real .apc fragment,
# editable/diffable as CSPro code. Spliced verbatim at generation time.
CONTROL_PROCS = (Path(__file__).resolve().parent / "procs" / "control_procs.apc").read_text(encoding="utf-8")

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
    # #1132 (ASPSI 2026-08-06, Carl 2026-08-09): the enumerator types the date in the
    # PAPI's MMDDYYYY order; storage stays YYYYMMDD. Converting on exit keeps every
    # downstream consumer untouched — the final<first comparison below, the MM/DD/YYYY
    # echo (#1099), the Supervisor App, and F3/F4 stored parity.
    #
    # Idempotent BY CONSTRUCTION, which is what makes this safe on a revisited field:
    # a value already stored as YYYYMMDD starts with the century (20), and 20 is not a
    # valid month, so the conversion branch cannot fire twice on the same value. The
    # else-branch then range-checks the year so genuine typos still get caught rather
    # than being silently accepted as "already converted".
    "DATE_FIRST_VISITED_THE_FACILITY": """\
PROC DATE_FIRST_VISITED_THE_FACILITY
postproc
  numeric fvMM; numeric fvDD; numeric fvYY; numeric fvHead;
  if DATE_FIRST_VISITED_THE_FACILITY <> notappl then
    fvMM   = int(DATE_FIRST_VISITED_THE_FACILITY / 1000000);
    fvHead = int(DATE_FIRST_VISITED_THE_FACILITY / 10000);
    if fvMM >= 1 and fvMM <= 12 then
      fvDD = fvHead - fvMM * 100;
      fvYY = DATE_FIRST_VISITED_THE_FACILITY - fvHead * 10000;
      if fvDD < 1 or fvDD > 31 or fvYY < 2020 or fvYY > 2035 then
        errmsg("Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.");
        reenter;
      endif;
      DATE_FIRST_VISITED_THE_FACILITY = fvYY * 10000 + fvMM * 100 + fvDD;
    else
      if fvHead < 2020 or fvHead > 2035 then
        errmsg("Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.");
        reenter;
      endif;
    endif;
  endif;""",
    "DATE_OF_FINAL_VISIT_TO_THE_FACILITY": """\
PROC DATE_OF_FINAL_VISIT_TO_THE_FACILITY
postproc
  numeric lvMM; numeric lvDD; numeric lvYY; numeric lvHead;
  if DATE_OF_FINAL_VISIT_TO_THE_FACILITY <> notappl then
    lvMM   = int(DATE_OF_FINAL_VISIT_TO_THE_FACILITY / 1000000);
    lvHead = int(DATE_OF_FINAL_VISIT_TO_THE_FACILITY / 10000);
    if lvMM >= 1 and lvMM <= 12 then
      lvDD = lvHead - lvMM * 100;
      lvYY = DATE_OF_FINAL_VISIT_TO_THE_FACILITY - lvHead * 10000;
      if lvDD < 1 or lvDD > 31 or lvYY < 2020 or lvYY > 2035 then
        errmsg("Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.");
        reenter;
      endif;
      DATE_OF_FINAL_VISIT_TO_THE_FACILITY = lvYY * 10000 + lvMM * 100 + lvDD;
    else
      if lvHead < 2020 or lvHead > 2035 then
        errmsg("Type the date as MMDDYYYY - for example 08092026 for 9 August 2026.");
        reenter;
      endif;
    endif;
  endif;
  { conversion above runs FIRST so both sides of this comparison are YYYYMMDD }
  if DATE_OF_FINAL_VISIT_TO_THE_FACILITY <> notappl and DATE_FIRST_VISITED_THE_FACILITY <> notappl and DATE_OF_FINAL_VISIT_TO_THE_FACILITY < DATE_FIRST_VISITED_THE_FACILITY then
    errmsg("Final-visit date cannot be earlier than the first-visit date.");
    reenter;
  endif;""",
    # #1132 retest (2026-08-10): the two #1099 DATE_*_DISP echo PROCs are
    # REMOVED with their dictionary items at ASPSI's request — see generate_dcf.py.

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
    # 4.6 YAKAP accreditation date (Section D) — #148 hard.  Aug-17: Q52 -> Q39.
    "Q39_YK_SINCE_YEAR": """\
PROC Q39_YK_SINCE_YEAR
postproc
  if Q39_YK_SINCE_YEAR < 2019 or Q39_YK_SINCE_YEAR > currentYear then
    errmsg("YAKAP accreditation year must be between 2019 and %d.", currentYear);
    reenter;
  endif;""",
    "Q39_YK_SINCE_MONTH": """\
PROC Q39_YK_SINCE_MONTH
postproc
  if Q39_YK_SINCE_MONTH < 1 or Q39_YK_SINCE_MONTH > 12 then
    errmsg("Month must be 1-12.");
    reenter;
  endif;
  if Q39_YK_SINCE_YEAR = currentYear and Q39_YK_SINCE_MONTH > currentMonth then
    errmsg("Accreditation date is in the future. Reenter.");
    reenter;
  endif;""",
    # F1-VALID-01 (2026-06-27): eligible-patients had NO upper bound (9999999 was silently
    # accepted, inflating the registered<=eligible ceiling). A single YAKAP/Konsulta provider's
    # catchment eligible count above ~500k is implausible -> SOFT confirm (no reenter) so an
    # obvious data-entry slip is surfaced without ever hard-blocking a genuinely large facility.
    # Aug-17: Q86 -> Q73.
    "Q73_ELIGIBLE_PATIENTS": """\
PROC Q73_ELIGIBLE_PATIENTS
postproc
  if Q73_ELIGIBLE_PATIENTS > 500000 then
    errmsg("Eligible patients (%d) is unusually high for one provider's catchment — please confirm.", Q73_ELIGIBLE_PATIENTS);
  endif;""",
    # 4.7 registered <= eligible (Section D) — #152 cross-field.  Aug-17: Q87 -> Q74.
    "Q74_REGISTERED_PATIENTS": """\
PROC Q74_REGISTERED_PATIENTS
postproc
  if Q74_REGISTERED_PATIENTS > Q73_ELIGIBLE_PATIENTS then
    errmsg("Registered patients (%d) cannot exceed eligible patients (%d).",
           Q74_REGISTERED_PATIENTS, Q73_ELIGIBLE_PATIENTS);
    reenter;
  endif;""",
    # 4.8 capitation soft warning (Section D) — #149 soft (accept) + #148 hard cap.
    # Aug-17: Q57 -> Q44.
    "Q44_CAPITATION_AMT": """\
PROC Q44_CAPITATION_AMT
postproc
  if Q44_CAPITATION_AMT > 5000 then
    errmsg("Capitation %d PHP is implausibly high. Reenter or confirm.", Q44_CAPITATION_AMT);
    reenter;
  endif;
  if Q44_CAPITATION_AMT > 1700 then
    if accept("Capitation %d exceeds the PHP 1,700 PhilHealth max. Confirm?", "Yes", "No") <> 1 then
      reenter;
    endif;
  endif;""",
    "Q78_MIN_CAP_VALUE_ACC": """\
PROC Q78_MIN_CAP_VALUE_ACC
postproc
  { #533 soft check: Q78 is the minimum per-capita rate the facility would accept, asked
    after the costing/enough questions imply PHP 1,700 may be insufficient. A minimum BELOW
    the current PHP 1,700 PhilHealth max is unusual — confirm rather than block. Q78 is only
    ever a skip TARGET (never a source), so a bespoke postproc here drops no routing.
    Aug-17: Q91 -> Q78. }
  if Q78_MIN_CAP_VALUE_ACC > 0 and Q78_MIN_CAP_VALUE_ACC < 1700 then
    if accept("Q78 minimum acceptable capitation (%d PHP) is below the PHP 1,700 PhilHealth max — confirm?", "Yes", "No") <> 1 then
      reenter;
    endif;
  endif;""",
    # 4.9 DOH-licensing-difficulty gate (Section F). #385 / #567.  Aug-17: Q121 -> Q108.
    # Q108 is a single Check Box field (no per-option _O## fields), so the former
    # per-option PROCs are GONE:
    #   - "None of the above" -> skip-to-Q122: now IMPLICIT. 'None' recodes to 90
    #     and is exclusive, so no 01-13 codes are present and every Q109-121 display
    #     gate `pos("0N", Q108_DOH_LIC_DIFFICULT) = 0` fires -> the cluster skips to Q122.
    #     This is also exactly what the Aug-17 paper prints for Q108
    #     ("IF None of the above GOTO <proceed to Q122>").
    #   - codes 10/11/12 (hospital-only) + 13 (PCF-only) visibility (#567 part 3 / #385)
    #     are RE-ESTABLISHED on the single Check Box field via a dynamic value set
    #     (setvalueset on Q8_SERVICE_LEVEL) instead of the old per-option `noinput` —
    #     see the Q108 entry + note in CHECKBOX_CONVERT_A below. Q108 select->=1 +
    #     exclusivity('None'=90) come from CHECKBOX_CONVERT_A / _gen_checkbox_proc.
}

# --- Check Box multi-select redesign (GH #377/#378/#379, mirrors F3 Q148) -----
# Q36/Q37/Q40/Q45 are ONE alpha field each holding the ticked option codes
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
# 'Other' = 99 in all of them (set in generate_dcf.py).
#
# AUG-17 (Task 2.4) re-key + code re-verification against the rebuilt value sets:
#   Q49 -> Q36 (exclusive "I don't know" = 09)      Q50 -> Q37 (09)
#   Q53 -> Q40 (09 + 'All of the above' 08)         Q58 -> Q45 (07 + 'No requirements' 05)
#   Q64 -> Q51 (no exclusive option)
# Every code above was re-read off the Aug-17 dictionary, not carried on trust — the
# renumber shifted question numbers but left these lists' option ORDER and codes fixed
# (Task 2.2 §5 holds codes/order stable so pretest data and `val:` translation keys survive).
CHECKBOX_MULTISELECT_PROCS = {
    "Q36_QUALITY_CHALL": """\
PROC Q36_QUALITY_CHALL
postproc
  if length(strip(Q36_QUALITY_CHALL)) = 0 then
    errmsg("Select at least one option for Q36 before continuing.");
    reenter;
  endif;
  { exclusivity (HARD — #1106..#1131): 'I don't know' (09) should stand alone }
  if pos("09", Q36_QUALITY_CHALL) > 0 and length(strip(Q36_QUALITY_CHALL)) > 2 then
    errmsg("Q36: 'I don't know' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;""",
    "Q36_QUALITY_CHALL_OTHER_TXT": """\
PROC Q36_QUALITY_CHALL_OTHER_TXT
preproc
  if pos("99", Q36_QUALITY_CHALL) = 0 then
    Q36_QUALITY_CHALL_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q36_QUALITY_CHALL) > 0 and length(strip(Q36_QUALITY_CHALL_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q36 — please specify.");
    reenter;
  endif;""",
    "Q37_ACCESS_CHALL": """\
PROC Q37_ACCESS_CHALL
postproc
  if length(strip(Q37_ACCESS_CHALL)) = 0 then
    errmsg("Select at least one option for Q37 before continuing.");
    reenter;
  endif;
  { exclusivity (HARD — #1106..#1131): 'I don't know' (09) should stand alone }
  if pos("09", Q37_ACCESS_CHALL) > 0 and length(strip(Q37_ACCESS_CHALL)) > 2 then
    errmsg("Q37: 'I don't know' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;""",
    "Q37_ACCESS_CHALL_OTHER_TXT": """\
PROC Q37_ACCESS_CHALL_OTHER_TXT
preproc
  if pos("99", Q37_ACCESS_CHALL) = 0 then
    Q37_ACCESS_CHALL_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q37_ACCESS_CHALL) > 0 and length(strip(Q37_ACCESS_CHALL_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q37 — please specify.");
    reenter;
  endif;""",
    "Q40_YK_PACKAGE": """\
PROC Q40_YK_PACKAGE
postproc
  if length(strip(Q40_YK_PACKAGE)) = 0 then
    errmsg("Select at least one option for Q40 before continuing.");
    reenter;
  endif;
  { exclusivity (HARD — #1106..#1131): 'I don't know' (09) should stand alone }
  if pos("09", Q40_YK_PACKAGE) > 0 and length(strip(Q40_YK_PACKAGE)) > 2 then
    errmsg("Q40: 'I don't know' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;
  { #526 exclusivity (HARD — #1108): 'All of the above' (08) implies every item — it should stand alone }
  if pos("08", Q40_YK_PACKAGE) > 0 and length(strip(Q40_YK_PACKAGE)) > 2 then
    errmsg("Q40: 'All of the above' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;""",
    "Q40_YK_PACKAGE_OTHER_TXT": """\
PROC Q40_YK_PACKAGE_OTHER_TXT
preproc
  if pos("99", Q40_YK_PACKAGE) = 0 then
    Q40_YK_PACKAGE_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q40_YK_PACKAGE) > 0 and length(strip(Q40_YK_PACKAGE_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q40 — please specify.");
    reenter;
  endif;""",
    "Q45_PERF_INDICATORS": """\
PROC Q45_PERF_INDICATORS
postproc
  if length(strip(Q45_PERF_INDICATORS)) = 0 then
    errmsg("Select at least one option for Q45 before continuing.");
    reenter;
  endif;
  { exclusivity (HARD — #1106..#1131): 'I don't know' (07) should stand alone }
  if pos("07", Q45_PERF_INDICATORS) > 0 and length(strip(Q45_PERF_INDICATORS)) > 2 then
    errmsg("Q45: 'I don't know' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;
  { #1188: 'No requirements' (05) is a SECOND standalone option the #1106 pass
    missed — it starts with "no " but not "none"/"no initiative", so nothing
    ever matched it (the same class as Q143/Q152/Q153 in v1.3.0). }
  if pos("05", Q45_PERF_INDICATORS) > 0 and length(strip(Q45_PERF_INDICATORS)) > 2 then
    errmsg("Q45: 'No requirements' must be the only choice — untick it or the other options before continuing.");
    reenter;
  endif;""",
    "Q45_PERF_INDICATORS_OTHER_TXT": """\
PROC Q45_PERF_INDICATORS_OTHER_TXT
preproc
  if pos("99", Q45_PERF_INDICATORS) = 0 then
    Q45_PERF_INDICATORS_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q45_PERF_INDICATORS) > 0 and length(strip(Q45_PERF_INDICATORS_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q45 — please specify.");
    reenter;
  endif;""",
    # --- #529 multi-select conversion (select_all -> checkbox): Q51 (no exclusive option) ---
    "Q51_APPLY_REASON": """\
PROC Q51_APPLY_REASON
postproc
  if length(strip(Q51_APPLY_REASON)) = 0 then
    errmsg("Select at least one option for Q51 before continuing.");
    reenter;
  endif;""",
    "Q51_APPLY_REASON_OTHER_TXT": """\
PROC Q51_APPLY_REASON_OTHER_TXT
preproc
  if pos("99", Q51_APPLY_REASON) = 0 then
    Q51_APPLY_REASON_OTHER_TXT = "";   { gated: 'Other (specify)' not ticked -> not enterable }
    noinput;
  endif;
postproc
  if pos("99", Q51_APPLY_REASON) > 0 and length(strip(Q51_APPLY_REASON_OTHER_TXT)) = 0 then
    errmsg("'Other (specify)' was ticked for Q51 — please specify.");
    reenter;
  endif;""",
}


# --- #529 multi-select conversion, Sub-phase A: config-driven checkbox PROCs.
# Each base gets a select->=1 validation, an optional exclusivity soft-warn (a
# standalone option coded 90 should stand alone), an optional preproc gate, and
# (when present) an 'Other (specify)' text gate on pos("99",field). Mirrors the
# hand-written Q49/Q50/Q53/Q58 pattern. (base, has_other, exclusive, preproc_gate)
# Rows are (base, has_other, exclusive, preproc_gate) or (…, preproc_gate, postproc_exit).
# AUG-17 (Task 2.4): every name re-keyed and every `exclusive` code re-read off the
# rebuilt value sets rather than carried on trust — one of them CHANGED (Q150, below).
CHECKBOX_CONVERT_A = [
    # Q52 gates Q53-61 (handled in why_difficult_gate_procs); here it just gets its
    # own select->=1 + exclusivity ('None of the above' coded 90). No 'Other'.
    # Paper Q52: "IF None of the above GOTO <proceed to 62>" — implicit, see Q108 below.
    ("Q52_ACCRED_DIFFICULT",        False, True, None),
    ("Q62_ENROLL_RESPONSIBILITY",   True, True,  None),
    ("Q63_ENROLL_INITIATIVES",      True, True,  None),
    # Q65 = "what challenges have you faced" (ACCREDITED arm, reached only via Q64=Yes).
    # DEFECT-FIX (F1-inventory.md §7 defect 3, register row "F1 | Q65,Q68,Q69,Q70,Q71"):
    # the paper prints NO exit skip after Q65, so an accredited facility falls straight
    # into the NOT-accredited block Q66-Q71 — only a banner at extract L1290 prevents it.
    # The explicit exit sends it where Q64=No already goes, the accredited costing block.
    # (The register row states the target for this group as Q79; that is right for
    # Q68-Q71 and wrong for Q65 — Q79 is the NOT-accredited minimum-capitation item.
    # Implemented per the inventory's per-defect split; register annotated by Task 2.4.)
    ("Q65_ENROLL_CHALL_LIST",       True, False, None,
     "  if Q38_YK_ACCRED = 1 then   { accredited: Q66-Q71 are the not-accredited block }\n"
     "    skip to Q72_CATCHMENT_AREA;\n  endif;"),
    # Q66 inherits the not-accredited block gate that used to live on Q79_..._O01.
    ("Q66_NOT_ACCRED_REASON",       True, False,
     "  if Q38_YK_ACCRED <> 2 then   { Q66-Q71 only for not-accredited (Q38=No); "
     "accredited fall-through -> Q72 }\n    skip to Q72_CATCHMENT_AREA;\n  endif;"),
    ("Q81_CHARGE_ADDL_CAP_REASONS", True, False, None),
    ("Q83_NOT_RECEIVED_REASONS",    True, True,  None),
    ("Q85_PAYMENT_CHALL_LIST",      True, True,  None),
    ("Q86_EXPAND_NEXT",             True, True,  None),
    # #542 Section E (BUCAS/GAMOT) — Other-specify, no exclusive option. Q91/Q98 are
    # skip TARGETS (Q89=Yes -> Q91, Q96=Yes -> Q98); those skip-to refs point at the
    # base in the Q89/Q96 ROUTING_PROCS.
    ("Q91_BUCAS_SERVICES",          True, False, None),
    ("Q92_BUCAS_FACTORS",           True, False, None),
    ("Q98_GAMOT_FACTORS",           True, False, None),
    # Section E/G DO-NOT-READ select-all -> Check Box. All three carry an 'Other
    # (specify)' (code 99). None is a skip TARGET: Q104 is reached via Q103's gate/skip
    # (Q103 in 2,3 -> Q105); Q138 via Q137=1 -> Q139; Q149 via Q148 in 1,2 -> Q150 —
    # every skip-to ref points at the *next question*, so nothing to repoint -> gate=None.
    # Q138 has a standalone 'I don't know' (recoded 90) -> exclusive.
    ("Q104_ADDR_STOCKOUT_HOW",      True, False, None),
    ("Q138_LGU_NOT_SAT_WHY",        True, True,  None),
    ("Q149_NOT_SATISFIED_WHY",      True, False, None),
    # #636 Section C: reports-used select_all -> single Check Box. has_other =
    # 'Other (specify)' (12th option, recoded 99). exclusive = False: no standalone
    # 'None'/'I don't know' option (so _cb_codes produces no 90 code). The DOH-IS gate
    # is unchanged in shape: Q21's postproc routes Q21=4 ('No, not submitting') -> Q24,
    # skipping Q22+Q23; Q21 in {1,2,3,5} flows through Q22 -> Q23 normally. That skip-to
    # ref targets Q24_STAFFING_CHANGED (the question AFTER Q23) -> gate=None.
    ("Q23_DATA_REPORTS_USED",       True, False, None),
    # AUG-17 NEW (Task 2.2 added the item): Q35.2 "what primary care quality measures are
    # you implementing?" — a 3-option tick-list with 'Other (specify)' (99), no exclusive
    # option. It is NOT a skip target and needs no gate of its own: Q35=No skips both
    # Q35.1 and Q35.2 to Q36 via the two-step battery rule, and Q35=Yes walks both.
    ("Q35_2_PCQM_MEASURES",         True, False, None),
    # #576 Carl 'finish F1': 11 more Section G/H select_all -> Check Box. has_other =
    # every one carries an 'Other (specify)' (code 99). exclusive = the list has a
    # standalone option _cb_codes recodes to 90 ('None of the above' for Q124/Q127).
    # Q133/Q134/Q136/Q142/Q146 = Other-only, no exclusive. Q143 'No standard referral
    # form' and Q152/Q153 'No forms ... provided' do NOT start with 'none'/'no initiative'
    # nor contain "don't know", so _cb_codes leaves them as normal sequential codes ->
    # they pass their literal code instead.
    # #586: Q131 (ex-Q144) re-converted to Check Box (PAPI shows checkboxes). Other-specify
    # (code 99) present; no exclusive None/IDK option -> exclusive=False. Not a skip target.
    ("Q131_DIFFICULT_REASON",       True, False, None),
    # #734: Q147 'where do patients go for services not available' -> Check Box (PAPI shows
    # checkboxes; resolves the #576/#586 flag). has_other=False: 'Other, (specify)' is a plain
    # tickable option (99) with NO _OTHER_TXT box (verified against the Aug-17 dictionary —
    # still none). 'I don't know' (90) is exclusive -> True. Terminal multi-select, no gate.
    ("Q147_EXTERNAL_SERVICES_GO",   False, True, None),
    ("Q124_NBB_BARRIERS",           True, True,  None),
    ("Q127_ZBB_BARRIERS",           True, True,  None),
    ("Q133_MALASAKIT_WHY",          True, False, None),
    # Q134 inherits the Q132=Yes -> skip-to-Q135 gate that used to live on the old
    # Q147_NO_MALASAKIT_WHY_O01 field's preproc. Q132=No reaches Q134 normally
    # (Q132's postproc sends No -> Q134 directly, matching paper "IF No GOTO Q134").
    ("Q134_NO_MALASAKIT_WHY",       True, False,
     "  if Q132_MALASAKIT_PROVIDED = 1 then   { Yes -> Q133 already asked; skip the "
     "not-provided block }\n    skip to Q135_LGU_SUPPORT;\n  endif;"),
    ("Q136_LGU_SUPPORT_FORMS",      True, False, None),
    ("Q142_SEND_REFERRAL_HOW",      True, False, None),
    ("Q143_REFERRAL_FORM_TYPE",     True, "05", None),
    ("Q146_RECEIVE_REFERRAL_HOW",   True, False, None),
    # AUG-17 CHANGE, not a re-key: ex-Q163 was `exclusive=True` on an "I don't know"
    # option coded 90. The Aug-17 paper prints Q150 with FIVE options and no "I don't
    # know" (Task 2.2 §4 / §10 — ASPSI's own #1126 addition did not survive their Aug-17
    # rewrite, and is on the 0.7 clarification list). There is no 90 code in the rebuilt
    # value set, so an exclusivity check would be a permanently dead condition.
    ("Q150_HR_CHALL",               True, False, None),
    ("Q152_PD_DOCTORS",             True, "08", None),
    ("Q153_PD_NURSES",              True, "06", None),
    # #567 parts 1 & 2: Section F DOH-licensing why-difficult battery.
    # Q108 = the gate (14 options, last is 'None of the above' -> recoded 90 ->
    # exclusive; no 'Other'). It gates Q109-121 the same way Q52 gates Q53-61; the
    # per-question gate PROCs are emitted by why_difficult_gate_procs (keyed off
    # CHECKBOX_BASES), so Q108 here just gets its own select->=1 + exclusivity check.
    # The paper's "IF None of the above GOTO <proceed to Q122>" is implicit: ticking
    # 'None' (90) means no 01-13 codes are present, so EVERY Q109-121 gate
    # `pos("0N",...)=0` fires and the whole cluster is skipped to Q122.
    #
    # #385: per-option hospital-only / PCF-only visibility (#567 part 3) is
    # re-established — not via per-option `noinput` (those fields do not exist on a
    # single Check Box), but via a dynamic value set swapped in Q108's preproc
    # (spec §4.9 pattern). The two facility-specific value sets are defined on the field
    # in generate_dcf.py: _PCF_VS1 drops the hospital-only options (codes 10/11/12),
    # _HOSP_VS1 drops the PCF-only option (code 13); both keep 'None' (90). The gate is
    # keyed on Q8_SERVICE_LEVEL (1 = Primary Care Facility; 2/3/4 = Level 1/2/3 Hospital).
    # A PCF therefore never sees the hospital-only ticks and a hospital never sees the
    # PCF-only tick, going forward — and on back-nav the value set is re-applied on
    # preproc re-entry, so the irrelevant options stay hidden either direction.
    ("Q108_DOH_LIC_DIFFICULT",      False, True,
     "  { #385 facility-type-aware option visibility (spec §4.9) }\n"
     "  if Q8_SERVICE_LEVEL = 1 then   { Primary Care Facility }\n"
     "    setvalueset(Q108_DOH_LIC_DIFFICULT, Q108_DOH_LIC_DIFFICULT_PCF_VS1);\n"
     "  else                           { Level 1/2/3 Hospital }\n"
     "    setvalueset(Q108_DOH_LIC_DIFFICULT, Q108_DOH_LIC_DIFFICULT_HOSP_VS1);\n"
     "  endif;"),
    # NOTE: Q109-121 are deliberately NOT listed here. Exactly like Q53-61 (gated by
    # Q52), the per-topic "why" Check Box fields get their full PROC — display gate
    # `pos("0N", Q108_DOH_LIC_DIFFICULT) = 0` + select->=1 + 'Other (specify)' gate —
    # from why_difficult_gate_procs(). Adding them here would shadow that gate PROC
    # (BESPOKE_PROCS is seeded into `covered` first) and SILENTLY DROP the skip logic.
]


def _gen_checkbox_proc(base, has_other, exclusive, gate=None, exit_skip=None):
    """`gate` is a preproc block (entry gate); `exit_skip` a postproc block appended
    LAST (block exit). Both are raw .apc text. A postproc `reenter` above terminates
    the PROC, so a validation failure can never fall into the exit skip."""
    qn = re.match(r"Q(\d+)", base).group(1)
    body = [f"PROC {base}"]
    if gate:
        body += ["preproc", gate]
    body += ["postproc",
             f"  if length(strip({base})) = 0 then",
             f'    errmsg("Select at least one option for Q{qn} before continuing.");',
             "    reenter;", "  endif;"]
    if exclusive:
        # #1106-#1131 (ASPSI review 2026-08-06): HARD block, not a soft warn. The
        # exclusive code is 90 by convention, but a few lists code their "No ..."
        # option sequentially (Q156=05, Q165=08, Q166=06) - pass the code as a str.
        code = exclusive if isinstance(exclusive, str) else "90"
        body += [f'  if pos("{code}", {base}) > 0 and length(strip({base})) > 2 then',
                 f'    errmsg("Q{qn}: an exclusive option (None / No initiatives / Do not know) '
                 f'must be the only choice - untick it or the other options before continuing.");',
                 "    reenter;", "  endif;"]
    if exit_skip:
        body.append(exit_skip)
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


for _row in CHECKBOX_CONVERT_A:
    _b, _o, _x, _g = _row[:4]
    _e = _row[4] if len(_row) > 4 else None
    CHECKBOX_MULTISELECT_PROCS.update(_gen_checkbox_proc(_b, _o, _x, _g, _e))
BESPOKE_PROCS.update(CHECKBOX_MULTISELECT_PROCS)

# AUG-17 (Task 2.4) guard: every configured checkbox base must actually BE one in the
# built dictionary. Before this, `CHECKBOX_BASES` was a hand-kept literal and a rename
# could silently drop a base out of it, demoting a >=7-option multi-select to a
# single-select DropDown (the #529 / #635 data-loss class). CHECKBOX_BASES is now derived,
# so the remaining risk is the reverse — a CHECKBOX_CONVERT_A row naming an item that is
# not (or is no longer) an alpha+value-set field. Fail loudly at generation instead.
_cfg_bases = {r[0] for r in CHECKBOX_CONVERT_A} | {
    n for n in CHECKBOX_MULTISELECT_PROCS if not n.endswith("_OTHER_TXT")}
_not_cb = sorted(_cfg_bases - CHECKBOX_BASES)
if _not_cb:
    raise SystemExit(
        "checkbox config names non-checkbox item(s) in the dcf: " + ", ".join(_not_cb))

# --- Multi-branch routing (spec 2 Section D/E/G) deferred from pass 1. Branch
# VALUES are from the spec's skip table; controlling-field item names confirmed
# against the dcf. Single-choice control fields, so these are field PROCs.
# (Verify the literal option codes for Q116/Q152 in Designer — spec gives them
# as labels, not numbers; the common cases are coded below.)
ROUTING_PROCS = {
    # Section C DOH-IS fan (Q21-Q23), second entry point. Paper Q21: "IF No, we are not
    # submitting these data GOTO <proceed to Q24>" — code 4. The FIRST entry point is
    # paper Q20 "IF No GOTO <proceed to Q24>", which the two-step battery table below
    # produces for free: Q21/Q22/Q23 are not battery bases, so Q20's No-skip target is
    # the next base, Q24. Codes 1/2/3 (submitting somewhere) and 5 (Other, specify — new
    # at Aug-17) flow through Q22 (frequency) -> Q23 (reports used) normally.
    "Q21_DATA_SUBMIT": """\
PROC Q21_DATA_SUBMIT
postproc
  if Q21_DATA_SUBMIT = 4 then       { No, we are not submitting these data }
    skip to Q24_STAFFING_CHANGED;
  endif;""",
    # Section D: Q48 = No -> Q49 (skip the reason-text item Q48.1).
    # Paper Q48: "IF No GOTO <proceed to 49>". The Q49 target is the NUM half of the
    # hybrid numeric+band pair, which is the first of the two on the form.
    "Q48_TRANCHE_DELAY": """\
PROC Q48_TRANCHE_DELAY
postproc
  if Q48_TRANCHE_DELAY = 2 then     { No }
    skip to Q49_TRANCHE_INTERVAL_NUM;
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
    # (#529) Q66 is a Check Box field — its not-accredited gate (Q38<>2 -> Q72)
    # lives in the Q66_NOT_ACCRED_REASON checkbox PROC's preproc (CHECKBOX_CONVERT_A);
    # the old Q79_NOT_ACCRED_REASON_O01 field no longer exists.
    #
    # Section D: Q67 6-way intend-accredit routing.  Paper Q67 branch matrix:
    #   Yes, already in process (1)      -> Q71      Yes, not yet in process (2) -> Q71
    #   No, decided not to (3)           -> Q69      No, tried and failed (4)    -> Q70
    #   No, haven't thought about it (5) -> Q68      I don't know (6)            -> Q72 (paper)
    #
    # DEFECT-FIX (F1-inventory.md §7 defect 1; register row "F1 | Q67"): the paper's
    # "I don't know -> Q72" contradicts the block gate. Q67 is asked ONLY of NOT-accredited
    # facilities (Q38=No -> Q66), but Q72-Q78 is banner-gated to ACCREDITED facilities
    # (extract L1340). The correct landing for a not-accredited respondent is Q79, the
    # not-accredited minimum-capitation question (L1391). Routed there explicitly rather
    # than relying on Q72's preproc bounce to do it second-hand.
    "Q67_INTEND_ACCRED": """\
PROC Q67_INTEND_ACCRED
postproc
  if Q67_INTEND_ACCRED in 1,2 then  skip to Q71_PROCESS_CHALL;        endif;  { Yes (in/ not-in process) }
  if Q67_INTEND_ACCRED = 3    then  skip to Q69_DECIDED_NOT_REASON;   endif;  { No, decided not to }
  if Q67_INTEND_ACCRED = 4    then  skip to Q70_TRIED_FAILED_REASON;  endif;  { No, tried and failed }
  if Q67_INTEND_ACCRED = 5    then  skip to Q68_KNOW_HOW_START;       endif;  { No, haven't thought }
  { defect-fix: paper sends 'I don't know' to Q72 (accredited-only block); Q67 is
    not-accredited-only, so the correct exit is Q79. }
  if Q67_INTEND_ACCRED = 6    then  skip to Q79_MIN_CAP_VALUE_NONACC; endif;  { I don't know }""",
    # DEFECT-FIX (F1-inventory.md §7 defect 2; register row "F1 | Q65,Q68,Q69,Q70,Q71"):
    # Q68-Q71 are the four MUTUALLY EXCLUSIVE tails of the Q67 branch matrix — each is
    # banner-gated to exactly one Q67 answer — but the paper prints no exit skip on any of
    # them, so the printed flow walks a respondent through all four and then falls into the
    # accredited-only Q72 block. Give each its own exit to Q79.
    #
    # Until now only Q71 was effectively covered (by Q72's preproc bounce), so a
    # "haven't thought about it" respondent answering Q68 was then asked Q69 (why decided
    # not to) and Q70 (what went wrong with the application) — questions for branches they
    # did not take. That is the live half of this defect and these four exits close it.
    "Q68_KNOW_HOW_START": """\
PROC Q68_KNOW_HOW_START
postproc
  skip to Q79_MIN_CAP_VALUE_NONACC;   { Q67=5 tail; Q69-Q71 belong to other branches }""",
    "Q69_DECIDED_NOT_REASON": """\
PROC Q69_DECIDED_NOT_REASON
postproc
  skip to Q79_MIN_CAP_VALUE_NONACC;   { Q67=3 tail }""",
    "Q70_TRIED_FAILED_REASON": """\
PROC Q70_TRIED_FAILED_REASON
postproc
  skip to Q79_MIN_CAP_VALUE_NONACC;   { Q67=4 tail }""",
    "Q71_PROCESS_CHALL": """\
PROC Q71_PROCESS_CHALL
postproc
  skip to Q79_MIN_CAP_VALUE_NONACC;   { Q67 in 1,2 tail; the not-accredited block ends here }""",
    # Section D: Q77 costing-viable routes by its OWN answer (#381). Printed Q77
    # has NO accreditation dependency: Yes(1)/Don't-know(3) -> Q80; No(2) -> Q78.
    # (The old PROC gated each branch on a matching accreditation code, so an accredited
    # "No" or a non-accredited "Yes" fell through with no skip — wrong per the paper,
    # which prints exactly "IF Yes GOTO Q80; IF No GOTO Q78; IF I don't know GOTO Q80".)
    "Q77_COSTING_VIABLE": """\
PROC Q77_COSTING_VIABLE
postproc
  if Q77_COSTING_VIABLE = 2 then     skip to Q78_MIN_CAP_VALUE_ACC; endif;  { No -> Q78 }
  if Q77_COSTING_VIABLE in 1,3 then  skip to Q80_CHARGE_ADDL_CAP;   endif;  { Yes / Don't know -> Q80 }""",
    # Section D master gate (#383): the costing block splits by accreditation.
    # Printed: "Q72 to Q78; Q80 to Q87 are only relevant to YAKAP-accredited,
    # otherwise proceed to Q88" + "Q79 is only relevant to not-accredited."
    #   - Accredited (Q38=1): answer Q72-Q78, SKIP Q79, answer Q80-Q87 -> Q88.
    #   - Not-accredited (Q38=2): Q71 -> SKIP Q72-Q78 -> answer Q79 -> SKIP Q80-Q87 -> Q88.
    # Q72 first-field preproc: a not-accredited respondent jumps the whole accredited
    # costing block straight to Q79. (An accredited respondent stays and answers Q72.)
    # Retained as belt-and-braces now that Q67-Q71 each carry an explicit Q79 exit.
    "Q72_CATCHMENT_AREA": """\
PROC Q72_CATCHMENT_AREA
preproc
  if Q38_YK_ACCRED = 2 then   { not-accredited: skip the accredited costing block Q72-Q78 -> Q79 }
    skip to Q79_MIN_CAP_VALUE_NONACC;
  endif;""",
    # Q79 (#383): only the not-accredited reach it as a question; accredited respondents
    # arrive here via fall-through from the Q72-Q78 block and must SKIP it. preproc bounces
    # accredited past Q79 to Q80; postproc sends the not-accredited (who answered Q79) past
    # the entire Q80-Q87 accredited block to Section E (Q88).
    "Q79_MIN_CAP_VALUE_NONACC": """\
PROC Q79_MIN_CAP_VALUE_NONACC
preproc
  if Q38_YK_ACCRED <> 2 then   { accredited (or any non-2): Q79 is not for them -> Q80 }
    skip to Q80_CHARGE_ADDL_CAP;
  endif;
postproc
  { not-accredited finished Q79 -> skip the accredited block Q80-Q87, go to Section E }
  skip to Q88_HEARD_BUCAS;""",
    # Section D: Q82 received-payments (Yes-all / Yes-some) -> Q84
    "Q82_RECEIVED_PAYMENTS": """\
PROC Q82_RECEIVED_PAYMENTS
postproc
  if Q82_RECEIVED_PAYMENTS in 1,2 then   { Yes, all / Yes, some }
    skip to Q84_PAYMENT_CHALL;
  endif;""",
    # #541: Q87 ('what additional features would you add?') is only relevant when
    # 'Additional features' (Q86 option, checkbox code 03) is ticked. It was an ungated
    # free-text -> answerable even when Additional features was not selected (wrong data).
    # Gate it on pos("03", Q86_EXPAND_NEXT): noinput when not ticked; require text when it is.
    # This is also the paper's Q86 per-option routing ("IF Additional features GOTO Q87,
    # everything else GOTO Q88") expressed on a multi-select, where a per-option GOTO
    # cannot be written as a single skip.
    "Q87_ADDL_FEATURES": """\
PROC Q87_ADDL_FEATURES
preproc
  if pos("03", Q86_EXPAND_NEXT) = 0 then   { 'Additional features' not ticked in Q86 -> N/A }
    Q87_ADDL_FEATURES = "";
    noinput;
  endif;
postproc
  if pos("03", Q86_EXPAND_NEXT) > 0 and length(strip(Q87_ADDL_FEATURES)) = 0 then
    errmsg("'Additional features' was ticked in Q86 - please specify what you would add.");
    reenter;
  endif;""",
    # Section E: Q89 has-BUCAS 3-way (No falls through to Q90).
    # Paper Q89: "IF Yes GOTO Q91; IF No GOTO Q90"; code 3 (I don't know) has no printed
    # branch, so it exits Section E's BUCAS block to the GAMOT block at Q95 — the same
    # treatment the pre-Aug-17 build gave it.
    "Q89_HAS_BUCAS": """\
PROC Q89_HAS_BUCAS
postproc
  if Q89_HAS_BUCAS = 1 then  skip to Q91_BUCAS_SERVICES; endif;  { Yes -> services (skip Q90) }
  if Q89_HAS_BUCAS = 3 then  skip to Q95_HEARD_GAMOT;    endif;  { I don't know -> Q95 }""",
    # #1023/#1024 (pretest 2026-08-04): the unconditional skip JUMPED OVER the
    # specify field, so choosing Other (5) never opened the text box. Route through the
    # specify field on 5; its own postproc resumes the skip. Paper Q90: "<then proceed to Q95>".
    "Q90_NO_BUCAS_REASON": """\
PROC Q90_NO_BUCAS_REASON
postproc
  if Q90_NO_BUCAS_REASON <> 5 then
    Q90_OTHER_TXT = "";                { not Other -> clear + skip Q91-Q94 }
    skip to Q95_HEARD_GAMOT;
  endif;
  { Other (5) -> fall through to Q90_OTHER_TXT }""",
    "Q90_OTHER_TXT": """\
PROC Q90_OTHER_TXT
postproc
  if length(strip(Q90_OTHER_TXT)) = 0 then
    errmsg("Q90: 'Other (specify)' was selected. Please specify.");
    reenter;
  endif;
  skip to Q95_HEARD_GAMOT;             { specify captured -> resume the Q90 skip }""",
    # DEFECT-FIX (F1-inventory.md §7 defect 8; register row "F1 | Q94"): the Q94 banner
    # reads "facilities located in areas with a BUCAS Center", but the only reachable path
    # to Q94 is Q89 = Yes — facilities that HAVE one, not merely are near one. Gate it on
    # the reachable path explicitly so a back-navigation that changes Q89 away from Yes
    # cannot leave a stale Q94 answer enterable.
    "Q94_BUCAS_DECONGEST": """\
PROC Q94_BUCAS_DECONGEST
preproc
  if Q89_HAS_BUCAS <> 1 then   { Q91-Q94 are for facilities that HAVE a BUCAS Center }
    skip to Q95_HEARD_GAMOT;
  endif;""",
    # Section E: Q96 GAMOT-accredited (No falls through to Q97). Paper: "IF Yes GOTO Q98".
    "Q96_GAMOT_ACCRED": """\
PROC Q96_GAMOT_ACCRED
postproc
  if Q96_GAMOT_ACCRED = 1 then  skip to Q98_GAMOT_FACTORS; endif;  { Yes (skip Q97) }""",
    # #1024 (tester comment): same skip-over-the-specify-field bug as Q90.
    # Paper Q97: "<After responding, proceed to Q99>".
    "Q97_NO_GAMOT_REASON": """\
PROC Q97_NO_GAMOT_REASON
postproc
  if Q97_NO_GAMOT_REASON <> 5 then
    Q97_OTHER_TXT = "";                { not Other -> clear + skip Q98 }
    skip to Q99_STOCKOUT;
  endif;
  { Other (5) -> fall through to Q97_OTHER_TXT }""",
    "Q97_OTHER_TXT": """\
PROC Q97_OTHER_TXT
postproc
  if length(strip(Q97_OTHER_TXT)) = 0 then
    errmsg("Q97: 'Other (specify)' was selected. Please specify.");
    reenter;
  endif;
  skip to Q99_STOCKOUT;                { specify captured -> resume the Q97 skip }""",
    # DEFECT-FIX (F1-inventory.md §7 defect 6; register row "F1 | Q102"; ASPSI
    # clarification item 5): the paper prints NO gate between Q101 and Q102, and the two
    # ask the same thing in different units —
    #     Q101 "How many days did the stock-out last?"      1 = 30 days and less
    #                                                        2 = 31-60 days
    #                                                        3 = More than 60 days
    #     Q102 "On average, how many months do these ...?"  1 = less than a month
    #                                                        2 = 1-2 months  3 = 3-4 months
    #                                                        4 = 5-6 months  5 = more than 6
    # For Q101 = 1 the month band is fully determined ("less than a month"); for Q101 = 2
    # it is likewise determined ("1-2 months"). ONLY Q101 = 3 leaves Q102 informative.
    # So Q102 is asked on Q101 = 3 alone. Deliberately a gate, not a derivation: filling
    # Q102 from Q101 would fabricate an answer the respondent never gave. ASPSI is asked
    # to confirm the intended condition (clarification item 5); until they do, this is the
    # minimal gate that removes the duplication without inventing data.
    "Q102_STOCKOUT_AVG": """\
PROC Q102_STOCKOUT_AVG
preproc
  if Q101_STOCKOUT_DURATION <> 3 then   { <= 60 days: the month band is implied by Q101 }
    skip to Q103_ADDR_STOCKOUT;
  endif;""",
    # Section E: Q103 = No / Did-not-experience -> Q105.
    # Paper Q103: "IF No GOTO Q105; IF Did not experience stock outs ... GOTO Q105".
    "Q103_ADDR_STOCKOUT": """\
PROC Q103_ADDR_STOCKOUT
preproc
  { #384: Q103/Q104 only if heard GAMOT (Q95=Yes) AND accredited (Q96=Yes) AND had a
    stockout (Q99=Yes) — spec 3.6 GATE. Otherwise skip both to Q105. }
  if not (Q95_HEARD_GAMOT = 1 and Q96_GAMOT_ACCRED = 1 and Q99_STOCKOUT = 1) then
    skip to Q105_DOH_LICENSED;
  endif;
postproc
  if Q103_ADDR_STOCKOUT in 2,3 then  { 2 = No, 3 = Did not experience stock outs }
    skip to Q105_DOH_LICENSED;
  endif;""",
    # Section G: Q132 Malasakit provided.  Paper: "IF No GOTO <proceed to Q134>".
    "Q132_MALASAKIT_PROVIDED": """\
PROC Q132_MALASAKIT_PROVIDED
postproc
  if Q132_MALASAKIT_PROVIDED = 2 then    { No -> skip the why-provided block to the not-provided block }
    skip to Q134_NO_MALASAKIT_WHY;
  endif;""",
    # Q132=Yes path: Q133 (why-provided) is asked, then Q134 (not-provided) must be
    # skipped. #576: Q134 is a Check Box base; that gate (Q132=Yes -> skip to Q135) lives
    # in Q134_NO_MALASAKIT_WHY's checkbox PROC preproc (CHECKBOX_CONVERT_A gate param).
    # Q132=No reaches Q134 normally via the postproc skip above.
    #
    # Section G: Q139 protocol clarity. #386: printed Q139 is "only for respondents
    # from public hospitals" — public hospital = Q7_OWNERSHIP=1 (Public) AND
    # Q8_SERVICE_LEVEL in 2,3,4 (Level 1/2/3 Hospital; Q8=1 is a Primary Care
    # Facility). preproc gates ENTRY: any non-public-hospital skips both Q139 and its
    # follow-up Q140 to Q141. postproc keeps the clarity routing (Very Clear/Clear
    # need no "which protocol unclear" detail -> skip Q140 -> Q141).
    "Q139_PHO_PROTOCOL_CLARITY": """\
PROC Q139_PHO_PROTOCOL_CLARITY
preproc
  if not (Q7_OWNERSHIP = 1 and Q8_SERVICE_LEVEL in 2,3,4) then
    skip to Q141_NUM_REFERRED_OUT;   { Q139/Q140 only for public hospitals }
  endif;
postproc
  if Q139_PHO_PROTOCOL_CLARITY in 1,2 then   { Very Clear / Clear -> skip Q140 detail }
    skip to Q141_NUM_REFERRED_OUT;
  endif;""",
}
BESPOKE_PROCS.update(ROUTING_PROCS)

# --- #744 break-off + completeness disposition (ported from the F3/F4 Cluster-5 pattern).
# BREAKOFF is the case-start "interview status" control (placed on the first interactive
# form by inject_breakoff.py). Leaving it "Continue" (1) is a no-op; any other choice records
# the matching Result-of-Final-Visit code and SKIPS straight to that closing field, so a
# withdrawn / postponed / stopped interview reaches the closing form without walking every
# required question. CASE_DISPOSITION (off-form) is the completeness sentinel the Supervisor
# App + CSWeb exports read (0 In progress at case open, 1 Completed, 2 Partial). F1 result
# codes: 1 Completed, 2 Postponed, 3 Refused, 4 Incomplete (the photo gate fires for 1/4 only).
DISPOSITION_PROCS = {
    "BREAKOFF": """\
PROC BREAKOFF
preproc
  { The guard MUST list every valid code - anything outside it is silently reset to
    Continue. Widened to 1..7 on 2026-07-14; leaving it at 1..4 would have erased every
    replacement the moment the field was revisited. }
  if not (BREAKOFF in 1, 2, 3, 4, 5, 6, 7) then BREAKOFF = 1; endif;   { default "Continue interview" }
postproc
  if BREAKOFF <> 1 then
    { 2-4: the interview STARTED and then stopped. }
    if BREAKOFF = 2 then ENUM_RESULT_FINAL_VISIT = 3; endif;   { Respondent withdrew -> Refused }
    if BREAKOFF = 3 then ENUM_RESULT_FINAL_VISIT = 2; endif;   { Postponed / reschedule }
    if BREAKOFF = 4 then ENUM_RESULT_FINAL_VISIT = 4; endif;   { Stop - other -> Incomplete }
    { 5-7: the interview NEVER STARTED (refused at the door / not found / ineligible).
      Per ASPSI, every such unit is replaced by a substitute, so all three land on
      Replaced(5) - BREAKOFF keeps the reason. Replacements = count(BREAKOFF in 5,6,7).
      Postponed(3) is NOT a replacement: that unit is revisited, not substituted. }
    if BREAKOFF in 5, 6, 7 then ENUM_RESULT_FINAL_VISIT = 5; endif;   { Replaced }
    CASE_DISPOSITION = 2;   { partial / not completed }
    skip to ENUM_RESULT_FINAL_VISIT;
  endif;""",
    "ENUM_RESULT_FINAL_VISIT": """\
PROC ENUM_RESULT_FINAL_VISIT
postproc
  { #744/#561: classify completeness from the final Result-of-Visit. Completed(1) -> Completed;
    Postponed(2) / Refused(3) / Incomplete(4) -> Partial. }
  if ENUM_RESULT_FINAL_VISIT = 1 then
    CASE_DISPOSITION = 1;
  else
    CASE_DISPOSITION = 2;
  endif;
  { A Postponed(2) / Refused(3) visit had no interview, so there is nothing to photograph -
    end the case here instead of walking into the Verification Photo form (whose trigger
    would otherwise loop on an out-of-range stop; F3/F4 device-confirmed 2026-06-21). Codes
    1/4 fall through to the photo, matching the CAPTURE_VERIFICATION_PHOTO gate (in 1, 4). }
  if not (ENUM_RESULT_FINAL_VISIT in 1, 4) then
    { #1209 (mirrors F3): F1's Facility GPS form is dead last, after the photo, so this
      early exit never reaches it and ReleaseGPS() never runs. gpsRadioOpen is a
      session-lived PROC GLOBAL, so leaking it "open" here suppressed gps(open) for
      every later case in the same CSEntry session. Hand the radio back. }
    ReleaseGPS();
    endlevel;   { statement form (no parens) - strict packager rejects endlevel() }
  endif;
  { #1209 (mirrors F3): re-assert the radio for the end-of-case Facility GPS form so it
    converges during the photo step. Also the only warm-up a RESUMED partial case gets -
    the QUESTIONNAIRE_NUMBER preproc WarmUpGPS() does not fire when CSEntry resumes at a
    mid-case field. }
  WarmUpGPS();""",
}
BESPOKE_PROCS.update(DISPOSITION_PROCS)

# --- Table-driven skip logic (spec §2). Each row: field PROC -> if <cond> skip.
# Kept simple/dichotomous; complex multi-branch routing (Q80, Q90, Q102/Q109)
# stays bespoke/TODO below. Fields already in BESPOKE_PROCS are skipped to avoid
# duplicate PROC blocks.
SKIP_RULES = [
    # Section C's 23 two-step battery gates are GENERATED from TWO_STEP_BATTERY below —
    # do not hand-write them here.
    # Section D — YAKAP / Konsulta
    ("Q38_YK_ACCRED",         "Q38_YK_ACCRED = 2",              "Q66_NOT_ACCRED_REASON"),
    ("Q46_KNOW_PAY_FREQ",     "Q46_KNOW_PAY_FREQ = 2",          "Q48_TRANCHE_DELAY"),
    ("Q64_ENROLL_CHALL",      "Q64_ENROLL_CHALL = 2",           "Q72_CATCHMENT_AREA"),
    ("Q76_COSTING_DONE",      "Q76_COSTING_DONE = 2",           "Q78_MIN_CAP_VALUE_ACC"),
    ("Q80_CHARGE_ADDL_CAP",   "Q80_CHARGE_ADDL_CAP = 2",        "Q82_RECEIVED_PAYMENTS"),
    ("Q84_PAYMENT_CHALL",     "Q84_PAYMENT_CHALL = 2",          "Q86_EXPAND_NEXT"),
    # Section E — BUCAS / GAMOT.  These three are the module gates: each awareness /
    # experience question's No-path closes its whole module.
    #   Q88 No -> Q95   skips the BUCAS block Q89-Q94
    #   Q95 No -> Q99   skips the GAMOT block Q96-Q98
    #   Q99 No -> Q105  skips the stock-out block Q100-Q104 and exits Section E
    ("Q88_HEARD_BUCAS",       "Q88_HEARD_BUCAS = 2",            "Q95_HEARD_GAMOT"),
    ("Q95_HEARD_GAMOT",       "Q95_HEARD_GAMOT = 2",            "Q99_STOCKOUT"),
    ("Q99_STOCKOUT",          "Q99_STOCKOUT = 2",               "Q105_DOH_LICENSED"),
    # Section F — DOH Licensing.  Paper Q105: No (2) / "No, but have submitted requirements
    # and waiting for license" (3) / "I don't know what DOH licensing is" (4) all -> Q122,
    # jumping the whole of Section F (Q106-Q121).
    ("Q105_DOH_LICENSED",     "Q105_DOH_LICENSED in 2,3,4",     "Q122_NBB_CURR"),
    # Section G — Service Delivery
    ("Q122_NBB_CURR",         "Q122_NBB_CURR = 2",              "Q125_ZBB_CURR"),
    ("Q125_ZBB_CURR",         "Q125_ZBB_CURR = 2",              "Q128_ALLOW_OOP_BASIC"),
    ("Q128_ALLOW_OOP_BASIC",  "Q128_ALLOW_OOP_BASIC = 2",       "Q130_DIFFICULT_BENEFIT"),
    ("Q135_LGU_SUPPORT",      "Q135_LGU_SUPPORT = 2",           "Q139_PHO_PROTOCOL_CLARITY"),
    # DEFECT-FIX (F1-inventory.md §7 defect 4; register row "F1 | Q137"): the paper sends
    # Q137 = Yes to Q141, which ORPHANS Q139 and Q140 — the Provincial Health Office
    # protocol-clarity pair, which have nothing to do with LGU satisfaction. Under the
    # printed routing the ONLY reliable way to reach Q139 is the "no LGU support" path
    # (Q135 No -> Q139), so every satisfied respondent silently loses two questions.
    # Retarget the Yes-skip to Q139: it still skips Q138 ("why not satisfied"), which is
    # all the paper's skip was for, and Q139/Q140 stay reachable on every path.
    ("Q137_LGU_SATISFIED",    "Q137_LGU_SATISFIED = 1",         "Q139_PHO_PROTOCOL_CLARITY"),
    # Paper Q148: "Very Satisfied ... GOTO Q150; Satisfied ... GOTO Q150" — skips Q149.
    # Register row "F1 | Q148": the paper's "SELECT ALL THAT APPLY" banner is a mislabel;
    # this is a mutually-exclusive 5-point scale whose top two options carry skips, so it
    # is built SELECT ONE (a single numeric item in the dictionary, not a Check Box base)
    # and the skip below is a plain membership test rather than a pos() scan.
    ("Q148_REF_SATISFACTION", "Q148_REF_SATISFACTION in 1,2",   "Q150_HR_CHALL"),
]


# --- Aug-17 two-step battery (Section C) -------------------------------------------
# The Aug-17 rewrite replaced 18 nine-option "UHC9" implementation-status questions with
# a TWO-STEP structure: a Yes/No base, then a `Q<NN>_1_UHC_ATTRIB` probe ("If yes, was it
# a result of the UHC Act enacted in 2019?"), and for seven of them a further `.2` detail
# question (the unit's role, the list of new departments, ...). 23 pairs in all.
#
# GATING IS REAL SKIP LOGIC, NOT DISPLAY GROUPING. Task 2.3 put every probe on its OWN
# screen precisely because CSEntry renders every field of a DisplayTogether screen
# regardless of skip or noinput logic (UAT R4, GH #371/#372) — sharing a screen with the
# base would leave the probe answerable after a "No". So each base needs a skip.
#
# The table is the paper's skip column, one row per base, in printed order:
#     Q10 "IF No GOTO <proceed to Q11>"      ... Q11 "IF No GOTO <proceed to Q12>"
#     Q12 "IF No GOTO <proceed to Q13>; IF Not applicable GOTO <proceed to Q13>"
#     Q13 "IF No GOTO <proceed to Q14>; IF Not applicable GOTO <proceed to Q14>"
#     Q14..Q19 "IF No GOTO <next>"           Q20 "IF No GOTO <proceed to Q24>"
#     Q24..Q34 "IF No GOTO <next>"           Q35 "IF No GOTO <proceed to Q36>"
#
# The TARGET is not stored: it is the next base in this list, or TWO_STEP_EXIT for the
# last. That is what makes Q20 -> Q24 fall out for free — Q21/Q22/Q23 are the DOH-IS fan,
# not battery bases, so they are simply not in the list and Q20's No-skip clears them,
# exactly as the paper prints. Ten of these 23 rows are re-keys of pre-Aug-17 rules;
# THIRTEEN are new, because under UHC9 a single nine-option item carried both steps and
# had nothing to gate.
#
# `codes` is the paper's change-signal read per row rather than assumed: the probe is
# asked on Yes(1) only, and everything else skips. Q12 and Q13 are the only two bases
# with a "Not applicable" option and they are the only two whose printed skip names a
# second value — so the table is checked against the dictionary at generation time
# (_assert_two_step_codes) instead of being trusted.
TWO_STEP_EXIT = "Q36_QUALITY_CHALL"

TWO_STEP_BATTERY = [
    ("Q10_HAS_PRIMARY_PKG",   (2,)),      # primary care packages
    ("Q11_PCB_LICENSING",     (2,)),      # applied for a DOH primary care licence
    ("Q12_PUBLIC_HEALTH_UNIT", (2, 9)),   # + Q12.2 main role of the public health unit
    ("Q13_HEALTH_PROMO_UNIT", (2, 9)),    # + Q13.2 main role of the health promotion unit
    ("Q14_NEW_ROLES",         (2,)),      # + Q14.2 which new roles
    ("Q15_NEW_DEPTS",         (2,)),      # + Q15.2 which new departments
    ("Q16_NEW_BUILDINGS",     (2,)),      # + Q16.2 what the buildings are used for
    ("Q17_NEW_ROOMS",         (2,)),      # + Q17.2 what the rooms are used for
    ("Q18_INC_EQUIPMENT",     (2,)),      # + Q18.2 which equipment
    ("Q19_INC_SUPPLIES",      (2,)),      # + Q19.2 which supplies
    ("Q20_EMR_USE",           (2,)),      # -> Q24: also clears the DOH-IS fan Q21-Q23
    ("Q24_STAFFING_CHANGED",  (2,)),
    ("Q25_REFERRAL_CHANGED",  (2,)),
    ("Q26_MOU_MOA",           (2,)),
    ("Q27_NBB",               (2,)),
    ("Q28_ZBB",               (2,)),
    ("Q29_NO_COPAY",          (2,)),
    ("Q30_WARD_ALLOC",        (2,)),
    ("Q31_CPG",               (2,)),
    ("Q32_DOH_LIC_STD",       (2,)),
    ("Q33_PHIC_ACCRED",       (2,)),
    ("Q34_SVC_DELIVERY_PROT", (2,)),
    ("Q35_PCQM",              (2,)),      # + Q35.2 which quality measures -> Q36
]


def two_step_skip_rules():
    """-> SKIP_RULES-shaped rows for the 23 two-step battery gates.

    One row per base: skip past its probe (and any `.2` detail question) to the next
    base, on every code that is not the change signal.
    """
    rows = []
    for i, (base, codes) in enumerate(TWO_STEP_BATTERY):
        target = (TWO_STEP_BATTERY[i + 1][0] if i + 1 < len(TWO_STEP_BATTERY)
                  else TWO_STEP_EXIT)
        cond = (f"{base} = {codes[0]}" if len(codes) == 1
                else f"{base} in {','.join(str(c) for c in codes)}")
        rows.append((base, cond, target))
    return rows


def _assert_two_step_codes(items):
    """The declared skip codes must be exactly the base's non-Yes codes.

    Cheap insurance against the two ways this table can silently go wrong: a typo'd code
    (the skip never fires, so the probe is asked after a No — the #371 defect the whole
    own-screen design exists to prevent), and a dictionary change that adds or drops an
    option without the gate following it."""
    bad = []
    for base, codes in TWO_STEP_BATTERY:
        it = items.get(base)
        if it is None:
            bad.append(f"{base}: not in the dictionary")
            continue
        vs = (it.get("valueSets") or [{}])[0]
        actual = {}
        for v in vs.get("values", []):
            lab = next((l.get("text", "") for l in v.get("labels", [])
                        if l.get("language") in (None, "EN")), "")
            if v.get("pairs"):
                actual[int(v["pairs"][0]["value"])] = lab.strip().lower()
        non_yes = {c for c, lab in actual.items() if lab != "yes"}
        if non_yes != set(codes):
            bad.append(f"{base}: declared {sorted(codes)}, dictionary non-Yes codes "
                       f"{sorted(non_yes)} ({actual})")
    if bad:
        raise SystemExit("two-step battery gate mismatch:\n  " + "\n  ".join(bad))


TODO_NOTE = """\
{ ============================================================================
  STILL OPEN (need per-item data or FMF/CSEntry verification):
    - #144/#145 Filipino label content + setlanguage (FMF Designer side).
  CLOSED 2026-06-11: "Other (specify)" enforcement now auto-derived from the
    dcf for all *_TXT items (see the auto-derived section above); Q52/Q108
    why-difficult gates fixed (`<> 1` -- the old `= 0` was a dead condition,
    options are coded Yes=1/No=2, blank is notappl) which also implements the
    "None of the above only" routing: with no cluster option flagged Yes,
    every cluster skips and entry lands at Q62/Q122. Literal option codes
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

    # Aug-17 two-step battery: 23 generated gate rows, checked against the dictionary's
    # own value sets before anything is emitted.
    items_by_name = dcf_items_full()[0]
    _assert_two_step_codes(items_by_name)
    skip_rules = two_step_skip_rules() + SKIP_RULES

    # #376 (GH F1 Section C): the No-branch skip for an "implementation status"
    # question swallowed code 7 ("No, other reason (specify)"), jumping over its
    # `_NO_OTHER_TXT` box -> the other-reason text was never collected (data loss).
    # Build {parent: target} for every such question (has a NO_OTHER box AND its
    # skip range includes 7); use it to (1) exclude 7 from the parent skip and
    # (2) append `skip to <target>` to the NO_OTHER box so the Yes-only follow-up
    # is still skipped after the other-reason text is entered.
    dual_other_skips = dual_other_no_skip_map(skip_rules, names)

    parts.append("{ ---- Validations & cross-field checks (spec 4) ---- }")
    for field in sorted(BESPOKE_PROCS):
        parts.append(BESPOKE_PROCS[field])
        parts.append("")

    parts.append("{ ---- Skip logic (spec 2), table-driven ---- }")
    covered = set(BESPOKE_PROCS)
    covered.add("CASE_DISPOSITION")   # #744 off-form sentinel, set in logic only — no PROC of its own
    for field, cond, target in skip_rules:
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
    print(f"  skip rules: {len(skip_rules)} emitted "
          f"({len(TWO_STEP_BATTERY)} two-step battery gates + {len(SKIP_RULES)} table rows); "
          f"{len(dual_other_skips)} #376 dual-other rewrites")

    # Desk-test pilot (dormant): F1_PILOT_JUMP=<FIELD> at generation time emits a
    # Q1 postproc jump straight to the named field, so deep questions are reachable
    # in a few fields for proof-of-fix captures / engine checks (F3's F3_PILOT_JUMP
    # pattern). OFF by default — NEVER set for a deploy build.
    _pilot_target = os.environ.get("F1_PILOT_JUMP")
    if _pilot_target and "Q1_NAME" not in covered:
        covered.add("Q1_NAME")
        parts.append("{ ---- desk-test pilot: jump to %s (dormant) ---- }" % _pilot_target)
        parts.append("PROC Q1_NAME" + chr(10) + "postproc" + chr(10)
                     + f"  skip to {_pilot_target};")
        parts.append("")

    parts.append("{ ---- Why-difficult display gates (spec 4.10) ---- }")
    for field, proc in sorted(why_difficult_gate_procs(names, CHECKBOX_BASES).items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")

    parts.append("{ ---- 'Other (specify)' enforcement — UHC9 dual-other items (spec 4.13) ---- }")
    uhc9_procs = uhc9_other_specify_procs(names, dual_other_skips)
    for field, proc in sorted(uhc9_procs.items()):
        if field in covered:
            continue
        covered.add(field)
        parts.append(proc)
        parts.append("")
    print(f"  UHC9 dual-other: {len(uhc9_procs)} procs"
          + ("  (0 is CORRECT for Aug-17 — the two-step split deleted all 44 "
             "_YES_OTHER_TXT/_NO_OTHER_TXT items; see uhc9_other_specify_procs' docstring)"
             if not uhc9_procs else ""))

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
    # R2 (2026-07-03): inline errmsg literals -> numbered messages + .ent.mgf
    # (stable numbers via messages-registry.json; displayed text unchanged).
    text = numberize_errmsgs(text, HERE, OUT.with_suffix(".mgf"), "FacilityHeadSurvey")
    OUT.write_text(text, encoding="utf-8")
    n_procs = text.count("\nPROC ") + text.startswith("PROC ")
    print(f"Wrote {OUT} ({len(text)} chars, ~{n_procs} PROC blocks).")
    print("  NEXT: open in CSPro Designer, compile (Build > Compile), fix any")
    print("  item-name mismatches at the source tables in generate_apc.py, then")
    print("  verify the skip/validation flow in CSEntry (issues stay 'pending-verify').")


if __name__ == "__main__":
    main()
