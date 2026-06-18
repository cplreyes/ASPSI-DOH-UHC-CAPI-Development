#!/usr/bin/env python3
"""
F3 Patient Survey — question-text (.qsf) generator.

Multi-language CAPI prompts. CSPro form field labels ([Text] in the .fmf) are
single-language and CSPro does NOT auto-translate them; the per-language channel is
the QUESTION TEXT (.qsf), shown in the question-text bar above the form. This reads
the generated PatientSurvey.dcf (which already carries every declared language and
its translated labels, via generate_dcf.py's apply_translations) and emits one
question per item with the prompt in every language. English is the fallback.
Verified rendering Waray ("Klase hin Pasyente" for PATIENT_TYPE) in CSEntry 2026-06-08.

CSPro 8.0 .qsf: each language maps directly to the HTML text (block scalar); the
{format, text} sub-map is an 8.1+ schema and trips "yaml-cpp: bad conversion" on 8.0.

Invoke:  python generate_qsf.py     # writes PatientSurvey.ent.qsf  (run after generate_dcf.py)
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DCF = HERE / "PatientSurvey.dcf"
OUT = HERE / "PatientSurvey.ent.qsf"

STYLES = """styles:
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
      font-family: Arial;font-size: 18px;"""


def _html(text):
    t = (text or "").replace("\n", " ").replace("\r", " ").strip()
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<p>{t}</p>"


def _p(cls, text):
    return f'<p class="{cls}">{text}</p>'


# ------------------------------------------------------------------
# Informed Consent Form — Annex H (SJREB-approved, F3 Inpatient and
# Outpatient variant, verbatim; English-only until ASPSI delivers ICF
# translations). Rendered as the CAPI question text of CONSENT_GIVEN so
# the enumerator reads PART I aloud from the question-text bar, then
# records Yes/No (No → endlevel per PROC CONSENT_GIVEN).
# ------------------------------------------------------------------
CONSENT_HTML = "".join([
    _p("heading2", "Informed Consent Form"),
    _p("instruction",
       "This informed consent form is to be obtained before conducting the interview. "
       "You must read this entire consent form aloud exactly as written. After you "
       "have read this form to the respondent, you must complete and sign the "
       "verification consent form."),
    _p("heading3", "PART I: Information about the Study"),
    _p("normal",
       "Hello, my name is __________________ (data collector’s name). I work for Asian "
       "Social Project Services, Inc. (ASPSI). I am here to ask you to participate in "
       "a study about the Universal Health Care (UHC) and packages of programs like "
       "Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance "
       "Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) centers, and "
       "Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The "
       "Department of Health (DOH) funded this study. Please let me tell you more "
       "about the study."),
    _p("normal",
       "This study aims to generate evidence on the overall experience of the general "
       "public to support continuous monitoring, evaluation, and learning of the "
       "implementation of the UHC Act and its Implementing Rules and Regulations (IRR)."),
    _p("normal",
       "Would you like to participate as a respondent in the study? The interview may "
       "last for more or less than an hour."),
    _p("normal",
       "We are committed to protecting your privacy. If you choose to participate, we "
       "will never share your family’s or other household members’ personal "
       "information outside of the study team. We will never include your name in "
       "information shared with the government or in any reports. Your name will be "
       "kept separately from your answers in a private, secure location. For this "
       "interview, it is also important to respect other people’s privacy and not tell "
       "anyone else what we talked about today. With all research, there’s a small "
       "chance that someone else might get to see your data. We try our best to "
       "prevent that, but if it happens, we’ll tell you as soon as possible."),
    _p("normal",
       "Aside from this, there are no other risks to you if you take part in this "
       "study. As a benefit of the research, the knowledge gained may help the "
       "government and DOH better support your healthcare needs. We shall also provide "
       "Php 100 as a token of appreciation for the time you’ve shared with us."),
    _p("normal",
       "Nothing bad will happen if you do not want to be in this study. You can decide "
       "to stop being in the study at any time. You will never have to pay anything to "
       "be in the study."),
    _p("normal",
       "Do you have any questions about the study or about what I have told you?"),
    _p("normal",
       "If you have concerns or questions about your rights as a participant, you can "
       "contact:"),
    _p("normal",
       "<b>Single Joint Research Ethics Board (SJREB) at the Philippines Department of "
       "Health</b><br/>Email: sjreb.doh@gmail.com<br/>National Tel: (02) 651-7800 "
       "local 1328<br/>Tel: +63 936 992 5513"),
    _p("normal",
       "<b>Department of Health</b><br/>Name: Lindsley Jeremiah D. Villarante<br/>"
       "Email: ldvillarante@doh.gov.ph<br/>Tel: +63 (02) 8651-7800 local 1432"),
    _p("normal",
       "<b>Asian Social Project Services, Inc.</b><br/>Name: Paulyn Jean A. Claro<br/>"
       "Email: aspsiglobal@gmail.com<br/>Tel: +63 917 819 6884"),
    _p("instruction",
       "Record the respondent’s decision: 1 = Yes (consent given — continue the "
       "interview); 2 = No (consent refused — the interview ends)."),
])

# Item-name → question-text HTML. Overrides win over the dcf-label default
# and are emitted identically for every declared language (English fallback
# until SJREB-approved ICF translations arrive).
# CONSENT_GIVEN removed 2026-06-12 — consent script is read from the printed
# sheet (off the CAPI), so no question-text override. (CONSENT_HTML above is
# kept as reference only; nothing emits it.)
OVERRIDES = {}


# ------------------------------------------------------------------
# Per-question enumerator instructions + section read-aloud intros,
# transcribed from Annex F3 (Apr 20 deliverable). Keyed by paper question
# number: the intro attaches once to the first Q<n>_* item; the instruction
# (blue Instruction style) to every Q<n>_* item except other-specify *_TXT
# fields. Paper-only navigation notes (<proceed to Qx>, skip-to rules) are
# omitted — CAPI logic automates the routing. English-only, like consent.
# ------------------------------------------------------------------
_READ_ONE = "READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY."
_READ_ALL = "READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_DNR_ONE = "DO NOT READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY."
_DNR_ALL = "DO NOT READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_PWD_CARD = ("Enumerator Instruction (DO NOT READ ALOUD): If the PWD "
             "Identification Card is presented, record the type of disability "
             "as indicated on the card. Do not ask the respondent directly.")
_RECEIPT = ("If patient provides a receipt, select all that apply. If no "
            "receipt was provided, read options out loud. Select all that "
            "apply. If yes, indicate the amount spent.")
_GAMOT_AREA = "Enumerator: Applicable only to respondents in areas with GAMOT."

INSTRUCTIONS = {
    **dict.fromkeys([8, 9, 10, 16, 34, 45, 48, 84, 123, 164, 165, 178], _READ_ONE),
    **dict.fromkeys([15, 30, 39, 40, 41, 169], _DNR_ONE),
    **dict.fromkeys([42, 50, 52, 85, 86, 163], _READ_ALL),
    **dict.fromkeys([36, 37, 46, 65, 67, 76, 101, 117, 118, 120, 121, 125,
                     171, 177], _DNR_ALL),
    **dict.fromkeys([153, 154, 155, 156], _GAMOT_AREA),
    971: _RECEIPT,  # #455: the receipt/"select all that apply" note belongs on Q97.1 (the Q971_* bill-items battery), NOT on Q97 (Q97_FINAL_AMOUNT, a single cash figure). Re-keyed 97 -> 971 so _QNUM attaches it to the Q971_* fields. (#559: also not on Q114, a reasons select-all.)
    **dict.fromkeys([14], _PWD_CARD),
    4: ("Note to enumerator [do not read]: This section is for the Patient "
        "Profile. Ask all questions in this section unless a skip rule applies."),
    17: _READ_ONE + " IF MORE THAN ONE, ASK FOR THE MAIN SOURCE.",
    18: ("Enumerator note: Tick the income category that corresponds to the "
         "respondent’s approximate household income."),
    29: "Please choose one from the options I will mention.",
    31: (_DNR_ONE + " For enumerator: A list will be provided to ensure "
         "accurate details."),
    35: ("Note to enumerator [do not read]: This section is for the Patient’s "
         "awareness on Universal Health Care. Ask all questions in this "
         "section unless a skip rule applies."),
    38: ("Note to enumerator [do not read]: This section is for the Patient’s "
         "PhilHealth Registration and Health Insurance. Ask all questions in "
         "this section unless a skip rule applies."),
    53: ("Note to enumerator [do not read]: This section is about the "
         "Patient’s Primary Care Utilization. Ask all questions in this "
         "section unless a skip rule applies. A primary care provider is your "
         "first contact healthcare provider (i.e., general practitioner "
         "doctor) for an undiagnosed concern or continuing care of varied "
         "medical conditions."),
    71: ("An institution that primarily delivers primary care services or the "
         "initial-contact facility for coordinated care (e.g., RHU, health "
         "center, general practitioner clinic)."),
    83: ("Note to enumerator [do not read]: This section is for the Patient’s "
         "Health-Seeking Behavior. Ask all questions in this section unless a "
         "skip rule applies. " + _READ_ONE),
    94: "To be asked for each lab test ticked in Q93.",
    99: ("Q99 to Q103 are applicable only to respondents in areas with BUCAS "
         "center. Otherwise, skip."),
    141: ("For example, they did not disclose any of your private medical "
          "information to anyone not involved in your care."),
    142: ("For example, your consultation was done in a private area, and no "
          "one could overhear your private medical information."),
    147: "PLEASE LIST DOWN ALL MEDICINES THAT YOU TOOK FOR THE HEALTH CONDITION.",
    150: ("A Pharmacy is an ancillary primary care facility with a FDA LTO "
          "where registered medicines can be bought."),
    152: ("Q152 to Q157, Q159 are applicable only to respondents in areas "
          "with GAMOT. Otherwise, skip."),
}

SECTION_INTROS = {
    4: ("Before proceeding to the survey proper, we would like to ask the "
        "patient about their personal information."),
    35: "We will now ask about the patient’s awareness of the Universal Health Care (UHC).",
    38: ("The next questions we will be asking are related to the patient’s "
         "PhilHealth registration experience. We will also confirm their "
         "PhilHealth registration status and membership, and their "
         "registration to other health insurance."),
    53: "We will now ask questions about the patient’s access to a primary care provider.",
    74: "We will now ask about the patient’s awareness of the YAKAP/Konsulta package.",
    83: ("We will now be asking about the patient’s actions taken for health "
         "concerns. This includes the type of services and facilities they "
         "access for their health and well-being."),
    88: ("For the following questions, we will ask about the patient’s most "
         "current outpatient visit."),
    98: ("I would like to know where you got the money to pay for medical "
         "costs incurred (IN ___, and ____) at the (FACILITY TYPE IN ___)."),
    99: ("We will now ask about the patient’s awareness about BUCAS and the "
         "services they accessed in a BUCAS Center."),
    105: ("For the following questions, we will ask about the patient’s most "
          "current inpatient visit."),
    113: ("I would like to know where you got the money to pay for medical "
          "costs incurred (IN ___, and ____) at the (FACILITY TYPE INPUT)."),
    116: "For this section, we will be asking about your awareness of NBB, ZBB, and MAIFIP.",
    131: ("The following questions relate to the patient’s most recent "
          "experience with [facility_name_input] as an [inpatient] or "
          "[outpatient], where we invited you to participate in our survey "
          "on [date_formatted]."),
    145: ("The next questions we will be asking are related to the patient’s "
          "access to medicines. We would like to know how easy or difficult "
          "it is for them to purchase or receive medicines. We will also ask "
          "some questions about their views in buying generic or branded "
          "medicines."),
    152: ("We will now ask about the patient’s awareness about the GAMOT "
          "package and the medicines they availed in a GAMOT pharmacy."),
    162: "We will be asking about the patient’s experience and satisfaction on referrals.",
}

# Filipino read-aloud scripts (#407/#410/#411/#433), exact-matched from the v2.1.2 source
# (no machine translation). FIL renders these; other languages fall back to the EN script
# above until similarly translated. Q4 + Q113 not in source as exact matches -> stay EN.
SECTION_INTROS_FIL = {
    35: "Magtatanong kami ngayon tungkol sa kaalaman ng pasyente sa Universal Health Care (UHC).",
    38: ("Ang mga susunod na tanong ay tungkol sa karanasan ng pasyente sa pagpaparehistro sa "
         "PhilHealth. Kukumpirmahin din namin ang status ng pagpaparehistro at pagiging miyembro "
         "sa PhilHealth, pati na rin ang kanilang pagpaparehistro sa iba pang health insurance."),
    53: "Magtatanong kami ngayon tungkol sa access ng pasyente sa isang primary care provider.",
    74: "Magtatanong kami ngayon tungkol sa kaalaman ng pasyente sa YAKAP/Konsulta package.",
    83: ("Magtatanong kami ngayon tungkol sa mga ginawa ng pasyente na pangkalusugan. Kabilang "
         "dito ang uri ng mga serbisyong ginagamit at mga pasilidad na pinupuntahan para sa "
         "kalusugan at kagalingan."),
    88: "Para sa mga susunod na tanong, magtatanong kami tungkol sa pinakahuling outpatient visit ng pasyente.",
    98: ("Nais naming malaman kung saan nanggaling ang pera na ipinanambayad sa mga gastusing "
         "medikal (IN ___, at ___) sa (URI NG PASILIDAD SA ___)."),
    99: "Magtatanong kami ngayon tungkol sa kaalaman ng pasyente sa BUCAS at sa mga serbisyong natanggap sa isang BUCAS Center.",
    105: "Para sa mga susunod na tanong, magtatanong kami tungkol sa pinakahuling inpatient visit ng pasyente.",
    116: "Para sa seksyon na ito, magtatanong kami tungkol sa kaalaman ninyo tungkol sa NBB, ZBB at MAIFIP.",
    131: ("Ang mga sumusunod na tanong ay may kaugnayan sa pinakahuling karanasan ng pasyente sa "
          "[facility_name_input] bilang isang [inpatient] o [outpatient], kung saan inanyayahan "
          "kayong lumahok sa aming survey noong [date_formatted]."),
    145: ("Ang mga susunod na tanong ay may kaugnayan sa access ng pasyente sa mga gamot. Nais "
          "naming malaman kung gaano kadali o kahirap na bumili o tumanggap ng mga gamot. "
          "Magtatanong din kami ng ilang katanungan tungkol sa kanilang pananaw sa pagbili ng "
          "generic o branded na gamot."),
    152: "Itatanong namin ngayon ang tungkol sa kaalaman ng pasyente sa GAMOT package at sa mga gamot na nakuha sa isang GAMOT pharmacy.",
    162: "Tatanungin namin ang karanasan at kasiyahan ng pasyente sa referral.",
}

_QNUM = re.compile(r"^Q(\d{1,3})_")

# Facility-name piping (#421/#443/#488/#510): the question stems carry a literal
# placeholder [facility_name_input] / [FACILITY_NAME_INPUT]. CSPro CAPI question text
# supports fills — a logic expression wrapped in double tildes, evaluated at runtime
# (https://www.csprousers.org/help/CSPro/create_fills_in_questions.html). FACILITY_NAME
# is the cover-level facility field, in scope for the whole case, so ~~FACILITY_NAME~~
# renders the captured name in the prompt (every language). Double tilde = plain-text
# fill (FACILITY_NAME has no HTML to preserve).
_FACILITY_PLACEHOLDER_RE = re.compile(r"\[?\bfacility_name_input\b\]?", re.IGNORECASE)
# Patient-type piping (#485): the Section J script reads "...as an [inpatient] o/or
# [outpatient]...". Pipe the captured PATIENT_TYPE value label (Outpatient/Inpatient)
# via getvaluelabel so the enumerator sees the actual type. [date_formatted] is left
# as-is (ambiguous which date field, and the tester asked only for facility + type).
_PATIENT_TYPE_PAIR_RE = re.compile(
    r"\[inpatient\]\s*(?:o|or)\s*\[outpatient\]|\[outpatient\]\s*(?:o|or)\s*\[inpatient\]",
    re.IGNORECASE)


def _pipe_fills(text):
    text = _FACILITY_PLACEHOLDER_RE.sub("~~FACILITY_NAME~~", text)
    text = _PATIENT_TYPE_PAIR_RE.sub("~~getvaluelabel(PATIENT_TYPE)~~", text)
    return text


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def question_extras(nm, intro_used):
    """(intro_q | None, instr | None, intro_here) — caller builds per-language pre/post.
    The intro attaches once, to the first item at/after its target question (within +3 —
    some paper intros sit before unnumbered or merged fields)."""
    m = _QNUM.match(nm)
    if not m:
        return None, None, False
    q = int(m.group(1))
    intro_q = None
    for tgt in SECTION_INTROS:
        if tgt not in intro_used and tgt <= q <= tgt + 3:
            intro_q = tgt
            intro_used.add(tgt)
            break
    instr = INSTRUCTIONS.get(q) if not nm.endswith("_TXT") else None
    return intro_q, instr, (intro_q is not None)


def build_extras(intro_q, instr, intro_here, lnm):
    """Per-language (pre, post): section read-aloud script in the CURRENT language (FIL
    translated #407/#410/#411/#433, other dialects EN fallback); the do-not-read enumerator
    note stays English. At a section start, script + note form one block BEFORE the question."""
    pre = post = ""
    if intro_q is not None:
        script = (SECTION_INTROS_FIL.get(intro_q) if lnm == "FIL" else None) or SECTION_INTROS[intro_q]
        pre = f"<p>{_esc(script)}</p>"
    if instr:
        if intro_here:
            pre += f'<p class="instruction">{_esc(instr)}</p>'
        else:
            post = f'<p class="instruction">{_esc(instr)}</p>'
    return pre, post


def main():
    d = json.loads(DCF.read_text(encoding="utf-8"))
    dict_name = d.get("name", "PATIENTSURVEY_DICT")
    langs = [(l["name"], l.get("label", l["name"]))
             for l in (d.get("languages") or [{"name": "EN", "label": "English"}])]

    lines = ["---", "fileType: Question Text", "version: CSPro 8.0", "languages:"]
    for nm, lb in langs:
        lines += [f"  - name: {nm}", f"    label: {lb}"]
    lines.append(STYLES)
    lines.append("questions:")

    seen, n = set(), 0
    intro_used = set()
    for lvl in d["levels"]:
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                nm = it["name"]
                if nm in seen:
                    continue
                seen.add(nm)
                labmap = {l.get("language"): l.get("text", "") for l in (it.get("labels") or [])}
                en = labmap.get("EN") or nm
                ov = OVERRIDES.get(nm)
                extras = (None, None, False) if ov else question_extras(nm, intro_used)
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                for lnm, _ in langs:
                    if ov:
                        body = ov
                    else:
                        pre, post = build_extras(*extras, lnm)
                        body = pre + _html(labmap.get(lnm) or en) + post
                    body = _pipe_fills(body)
                    lines += [f"          {lnm}: |", f"            {body}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
