#!/usr/bin/env python3
r"""F1 form tooling: convert select-all option-field groups -> single Check Box
fields IN the hand-maintained FacilityHeadSurvey.fmf.

WHY THIS EXISTS
F1 (unlike F3/F4) has NO FMF generator — its .fmf is hand-maintained. When
generate_dcf.py turns a Q<base>_O01..On select_all into one checkbox_multiselect
field Q<base>, the dictionary changes but the FORM still carries the old N option
fields and has no entry for the new single field -> verify_questions reports
"UNREACHABLE: Q<base> not on a form" and Designer would drop/mismatch the orphans.

This rewrites the .fmf so the form matches: for each base in CONVERT it
  * transforms the FIRST <base>_O01 [Field]/[Text] pair in place into the checkbox
    field — Name/Item -> <base>, DataCaptureType -> CheckBox, question text -> the
    stem before the em-dash (drops the "— <option>" suffix); Position/Form/spacing
    are preserved so inject_blocks.py can re-lay-out screens afterwards,
  * deletes the remaining <base>_O02.. [Field]/[Text] pairs,
  * leaves <base>_OTHER_TXT untouched (it still exists in the dict).

Idempotent: a base already collapsed to a single <base> field (no _O01) is skipped.

PIPELINE ORDER (F1):
    python generate_dcf.py            # dict: select_all -> checkbox_multiselect
    python generate_apc.py            # logic: CHECKBOX_MULTISELECT_PROCS
    python fmf_checkbox_convert.py    # THIS — form: option fields -> checkbox field
    python inject_blocks.py           # re-block the form into DisplayTogether screens
Keep the four checkbox lists in sync (this CONVERT, generate_dcf's
checkbox_multiselect calls, generate_apc CHECKBOX_MULTISELECT_PROCS, and
inject_blocks._CHECKBOX_FIELDS).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FMF = HERE / "FacilityHeadSurvey.fmf"
DICT = "FACILITYHEADSURVEY_DICT"

# Bases (the #529 flagged multi-select cluster) to render as Check Box on the form.
CONVERT = [
    "Q64_APPLY_REASON",
    # #529 Sub-phase A (non-gate-chain)
    "Q75_ENROLL_RESPONSIBILITY",
    "Q76_ENROLL_INITIATIVES",
    "Q78_ENROLL_CHALL_LIST",
    "Q79_NOT_ACCRED_REASON",
    "Q94_CHARGE_ADDL_CAP_REASONS",
    "Q96_NOT_RECEIVED_REASONS",
    "Q98_PAYMENT_CHALL_LIST",
    "Q99_EXPAND_NEXT",
    # #529 Sub-phase B (Q65 gate chain)
    "Q65_ACCRED_DIFFICULT",
    "Q66_WHY_DIFF_PREVENTIVE",
    "Q67_WHY_DIFF_LAB",
    "Q68_WHY_DIFF_MEDS",
    "Q69_WHY_DIFF_INFRA",
    "Q70_WHY_DIFF_EQUIPMENT",
    "Q71_WHY_DIFF_HR",
    "Q72_WHY_DIFF_HIS",
    "Q73_WHY_DIFF_DOCS",
    "Q74_WHY_DIFF_DOH_LIC",
    # #542 Section E (BUCAS / GAMOT)
    "Q104_BUCAS_SERVICES",
    "Q105_BUCAS_FACTORS",
    "Q111_GAMOT_FACTORS",
    # Section E/G DO-NOT-READ select-all -> Check Box
    "Q117_ADDR_STOCKOUT_HOW",
    "Q151_LGU_NOT_SAT_WHY",
    "Q162_NOT_SATISFIED_WHY",
    # #636 Section C: Q34 reports-used select_all -> single Check Box.
    "Q34_DATA_REPORTS_USED",
    # #576 Carl 'finish F1': 11 more Section G/H select_all -> Check Box.
    # (#586: Q144 re-added as Check Box per PAPI; Q160 stays single select_one.)
    "Q144_DIFFICULT_REASON",
    "Q137_NBB_BARRIERS",
    "Q140_ZBB_BARRIERS",
    "Q146_MALASAKIT_WHY",
    "Q147_NO_MALASAKIT_WHY",
    "Q149_LGU_SUPPORT_FORMS",
    "Q155_SEND_REFERRAL_HOW",
    "Q156_REFERRAL_FORM_TYPE",
    "Q159_RECEIVE_REFERRAL_HOW",
    "Q163_HR_CHALL",
    "Q165_PD_DOCTORS",
    "Q166_PD_NURSES",
    # #567 parts 1 & 2: Section F DOH-licensing why-difficult battery (Q121 gate +
    # Q122-134 per-topic "why"), select_all -> Check Box (Q65->Q66-74 pattern).
    "Q121_DOH_LIC_DIFFICULT",
    "Q122_WHY_DIFF_PT_RIGHTS",
    "Q123_WHY_DIFF_PT_CARE",
    "Q124_WHY_DIFF_LEADERSHIP",
    "Q125_WHY_DIFF_HRM",
    "Q126_WHY_DIFF_INFO_MGMT",
    "Q127_WHY_DIFF_SAFE",
    "Q128_WHY_DIFF_PERF",
    "Q129_WHY_DIFF_PHYS_PLANT",
    "Q130_WHY_DIFF_PRICE_INFO",
    "Q131_WHY_DIFF_EQUIPMENT",
    "Q132_WHY_DIFF_NAT_LAWS",
    "Q133_WHY_DIFF_EMERG_CART",
    "Q134_WHY_DIFF_ADDONS",
]

_DASH = re.compile(r"\s+[—–-]\s+")  # em / en / hyphen dash: "stem — option"
_OPT = re.compile(r"^(.+?)_O\d+$")


def _split_chunks(text):
    """Split the .fmf into chunks, each starting at a '[Header]' line and running
    up to (not including) the next one. chunks[0] is any pre-'[' preamble."""
    return re.split(r"(?m)(?=^\[)", text)


def _header(ch):
    m = re.match(r"^\[([A-Za-z]+)\]", ch)
    return m.group(1) if m else None


def _name(ch):
    m = re.search(r"(?m)^Name=(\S+)\s*$", ch)
    return m.group(1) if m else None


def _get(ch, key):
    m = re.search(rf"(?m)^{re.escape(key)}=(.*)$", ch)
    return m.group(1).strip() if m else None


def _offset_pos(pos, dy, x2=None):
    """Shift a 'x1,y1,x2,y2' Position down by dy px; optionally widen x2 (text box)."""
    parts = (pos or "").split(",")
    if len(parts) != 4:
        return pos
    x1, y1, X2, y2 = parts
    if x2 is not None:
        X2 = str(x2)
    return f"{x1},{int(y1) + dy},{X2},{int(y2) + dy}"


def _ensure_other_txt(text, bases):
    """Synthesize a missing <base>_OTHER_TXT FORM field for any base the DICT carries
    an _OTHER_TXT item for but the form lacks.

    WHY: fmf_checkbox_convert's _O01 collapse only PRESERVES an _OTHER_TXT that already
    exists from the select_all era. A base that was last a single select_one field
    (e.g. #586 Q144 re-converted select_one -> Check Box) has NO _OTHER_TXT on the form,
    so generate_dcf's checkbox_multiselect(has_other) adds Q144_DIFFICULT_REASON_OTHER_TXT
    to the dict while the form has no field for it -> verify_questions 'UNREACHABLE:
    ... not on a form'. This adds it: a bare manifest Item= line after the base's, plus a
    [Field]/[Text] pair cloned from the base (y-offset, widened text box, em-dash stem +
    ' — Other (specify) text'). Idempotent — skips bases already carrying the field."""
    dcf = HERE / "FacilityHeadSurvey.dcf"
    try:
        d = json.loads(dcf.read_text(encoding="utf-8"))
    except Exception:
        return text  # dict not generated yet -> nothing to synthesize from
    dict_items = {it["name"]
                  for lvl in d.get("levels", [])
                  for rec in lvl.get("records", [])
                  for it in rec.get("items", [])}
    existing = set(re.findall(r"(?m)^Name=(\S+)\s*$", text))
    for base in bases:
        otxt = f"{base}_OTHER_TXT"
        if otxt not in dict_items or otxt in existing or base not in existing:
            continue
        # 1. group manifest: add the bare `Item=<otxt>` after the base's bare Item line.
        text = re.sub(rf"(?m)^(Item={re.escape(base)})[ \t]*$",
                      rf"\1\nItem={otxt}", text, count=1)
        # 2. [Field]/[Text]: clone the base's pair into the _OTHER_TXT field, inserted
        #    right after it so inject_blocks (gated *_TXT -> own screen) lays it out.
        chunks = _split_chunks(text)
        out, i, n = [], 0, len(chunks)
        while i < n:
            ch = chunks[i]
            out.append(ch)
            if _header(ch) == "Field" and _name(ch) == base:
                txt_ch = chunks[i + 1] if i + 1 < n and _header(chunks[i + 1]) == "Text" else None
                if txt_ch is not None:
                    out.append(txt_ch)
                    i += 1
                form = _get(ch, "Form") or "11"
                fpos = _offset_pos(_get(ch, "Position") or "1204,800,1233,820", 30, x2=2174)
                stem = _DASH.split((_get(txt_ch, "Text") or "") if txt_ch else "", 1)[0].strip()
                tpos = _offset_pos(_get(txt_ch, "Position") if txt_ch else "50,800,294,816", 30, x2=872)
                out.append(
                    f"[Field]\nName={otxt}\nPosition={fpos}\n"
                    f"Item={otxt},{DICT}\nUseUnicodeTextBox=Yes\n"
                    f"DataCaptureType=TextBox\nForm={form}\n  \n")
                out.append(f"[Text]\nPosition={tpos}\nText={stem} — Other (specify) text\n \n  \n  \n")
            i += 1
        text = "".join(out)
        existing.add(otxt)
        print(f"  synthesized missing form field: {otxt}")
    return text


def _fix_group_membership(text, bases):
    """The form's [Group]/[Form] field manifest lists each member as a bare
    `Item=<name>` line (no ',DICT' suffix — that form is the [Field]'s Item key).
    Collapse the `Item=<base>_O01..On` run there to a single `Item=<base>`,
    keeping `Item=<base>_OTHER_TXT`. CSPro errors ("field not found on the form")
    if these don't match the [Field] blocks."""
    for base in bases:
        pat = re.compile(rf"(?m)^Item={re.escape(base)}_O\d+\s*$\n?")
        first = [True]

        def repl(_m):
            if first[0]:
                first[0] = False
                return f"Item={base}\n"
            return ""

        text = pat.sub(repl, text)
    return text


def convert(text, bases):
    text = _fix_group_membership(text, bases)
    chunks = _split_chunks(text)
    out, i, done = [], 0, []
    bases = set(bases)
    n = len(chunks)
    while i < n:
        ch = chunks[i]
        nm = _name(ch) if _header(ch) == "Field" else None
        m = _OPT.match(nm) if nm else None
        if m and m.group(1) in bases:
            base = m.group(1)
            text_ch = chunks[i + 1] if i + 1 < n and _header(chunks[i + 1]) == "Text" else None
            if base not in done:
                # FIRST option of this base -> become the checkbox field, in place.
                field2 = ch.replace(f"Name={nm}", f"Name={base}", 1)
                field2 = re.sub(rf"(?m)^Item={re.escape(nm)},", f"Item={base},", field2)
                field2 = re.sub(r"(?m)^DataCaptureType=\w+", "DataCaptureType=CheckBox", field2)
                out.append(field2)
                if text_ch is not None:
                    stem = _DASH.split(_get(text_ch, "Text") or "", 1)[0].strip()
                    out.append(re.sub(r"(?m)^Text=.*$", f"Text={stem}", text_ch))
                done.append(base)
            # delete this option [Field] (+ its [Text]); first one's pair already
            # re-emitted transformed above, subsequent ones dropped entirely.
            i += 2 if text_ch is not None else 1
            continue
        out.append(ch)
        i += 1
    return "".join(out), done


def main():
    if not FMF.exists():
        sys.exit(f"not found: {FMF}")
    text = FMF.read_text(encoding="utf-8")
    new, done = convert(text, CONVERT)
    new = _ensure_other_txt(new, CONVERT)
    FMF.write_text(new, encoding="utf-8")
    print(f"checkbox-converted on form: {', '.join(done) if done else '(none)'}")
    missing = [b for b in CONVERT if b not in done]
    if missing:
        print(f"  NOT FOUND on form (already converted? check name): {', '.join(missing)}")


if __name__ == "__main__":
    main()
