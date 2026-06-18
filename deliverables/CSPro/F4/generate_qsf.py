#!/usr/bin/env python3
"""
F4 Household Survey — question-text (.qsf) generator.

Multi-language CAPI prompts. CSPro form field labels ([Text] in the .fmf) are
single-language and CSPro does NOT auto-translate them; the per-language channel is
the QUESTION TEXT (.qsf), shown in the question-text bar above the form. This reads
the generated HouseholdSurvey.dcf (which already carries every declared language and
its translated labels, via generate_dcf.py's apply_translations) and emits one
question per item with the prompt in every language. English is the fallback.

CSPro 8.0 .qsf: each language maps directly to the HTML text (block scalar); the
{format, text} sub-map is an 8.1+ schema and trips "yaml-cpp: bad conversion" on 8.0.

Invoke:  python generate_qsf.py      # writes HouseholdSurvey.ent.qsf  (run after generate_dcf.py)
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DCF = HERE / "HouseholdSurvey.dcf"
OUT = HERE / "HouseholdSurvey.ent.qsf"

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
# Informed Consent Form — Annex H (SJREB-approved, F4 Household variant,
# verbatim; English-only until ASPSI delivers ICF translations).
# Rendered as the CAPI question text of CONSENT_GIVEN so the enumerator
# reads PART I aloud from the question-text bar, then records Yes/No
# (No → endlevel per PROC CONSENT_GIVEN).
# ------------------------------------------------------------------
CONSENT_HTML = "".join([
    _p("heading2", "Informed Consent Form"),
    _p("instruction",
       "This informed consent form is to be obtained before conducting the interview. "
       "You must read this entire consent form aloud exactly as written. After you "
       "have read this form to the respondent, you must complete and sign the "
       "verification consent form."),
    _p("heading3", "PART I: Information about the study"),
    _p("normal",
       "Hello, my name is __________________ (data collector’s name). I work for Asian "
       "Social Project Services, Inc. (ASPSI). I am here to ask you to participate in "
       "a study about the Universal Health Care (UHC) and packages of programs like "
       "Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance "
       "Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) center, and "
       "Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT). The "
       "Department of Health funded this study. Please let me tell you more about the "
       "study."),
    _p("normal",
       "This study aims to generate evidence on the overall experience of the general "
       "public to support continuous monitoring, evaluation, and learning of the "
       "implementation of the UHC Act and its Implementing Rules and Regulations (IRR)."),
    _p("normal",
       "Would you like to participate as a respondent in the study? The interview may "
       "last for more or less than an hour."),
    _p("normal",
       "We are committed to protecting your privacy. If you choose to participate, we "
       "will never share your family’s or child’s personal information outside of the "
       "study team. We will never include your name in information shared with the "
       "government or in any reports. Your name will be kept separately from your "
       "answers in a private, secure location. For this interview, it is also "
       "important to respect other people’s privacy and not tell anyone else what we "
       "talked about today. With all research, there’s a small chance that someone "
       "else might get to see your data. We do our best to prevent that, but if it "
       "happens, we’ll let you know as soon as possible."),
    _p("normal",
       "Aside from this, there are no other risks to you if you take part in this "
       "study. As a benefit of the research, the knowledge gained may help the "
       "government and DOH better support your healthcare needs. We shall also provide "
       "Php 100 as a token of appreciation for the time you’ve shared with us."),
    _p("normal",
       "Nothing bad will happen if you do not want to be in this study. You can decide "
       "to stop the interview at any time. You will never have to pay anything to be "
       "in the study."),
    _p("normal",
       "Do you have any questions about the study or about what I have told you?"),
    _p("normal",
       "If you have concerns or questions about your rights as a participant, you can "
       "contact:"),
    _p("normal",
       "<b>Single Joint Research Ethics Board (SJREB) at the Philippines Department of "
       "Health</b><br/>Email: sjreb@doh.gov.ph<br/>National Tel: (02) 8651-7800 "
       "local 1326, 1328"),
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
# transcribed from Annex F4 (Apr 20 deliverable). Keyed by paper question
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
_GAMOT_FAC = "Enumerator: Applicable only to respondents in areas with GAMOT facility."

INSTRUCTIONS = {
    **dict.fromkeys([4, 5, 6, 17, 110, 111, 118, 125], _READ_ONE),
    **dict.fromkeys([7, 11, 80, 81, 112], _DNR_ONE),
    **dict.fromkeys([82, 88, 102, 103, 109, 143], _READ_ALL),
    **dict.fromkeys([52, 53, 55, 56, 58, 59, 85, 91, 93, 94, 113, 121, 127,
                     128, 133, 134, 137], _DNR_ALL),
    **dict.fromkeys([10, 38], _PWD_CARD),
    **dict.fromkeys([70, 71, 72], _GAMOT_FAC),
    1: ("Note to enumerator [do not read]: This section is for the Respondent "
        "Profile. The respondent should be the main-decision maker of the "
        "household. Ask all questions in this section unless a skip rule applies."),
    12: ("If the respondent is studying - please put “No employment - not "
         "looking for work”. " + _READ_ONE),
    13: _READ_ONE + " IF MORE THAN ONE, ASK FOR THE MAIN SOURCE.",
    15: (_DNR_ONE + " For enumerator: A list will be provided to ensure "
         "accurate details."),
    18: ("Enumerator note: Tick the income category that corresponds to the "
         "respondent’s approximate household income."),
    19: ("Please count yourself and all the people who usually live with you. "
         "Please include those who are not living here now but will be back "
         "within six months, BUT do not include OFWs."),
    29: "Please choose one from the options I will mention.",
    30: ("For the enumerator: please check that the total number is equal to "
         "the number answered in Q19."),
    51: ("Note to enumerator [do not read]: This section is for awareness of "
         "the Universal Health Care (UHC). Ask all questions in this section "
         "unless a skip rule applies."),
    54: ("Note to enumerator [do not read]: This section is for awareness of "
         "the YAKAP/Konsulta package. Ask all questions in this section "
         "unless a skip rule applies."),
    57: ("Note to enumerator [do not read]: This section is for awareness of "
         "the BUCAS and the services you have accessed in a BUCAS Center. "
         "Ask all questions in this section unless a skip rule applies. Q57 "
         "to Q61 are applicable only to respondents in areas with BUCAS."),
    61: "SELECT ALL THAT APPLY.",
    62: ("Note to enumerator [do not read]: This section is for the Access to "
         "Medicines of the household. For this section, we will ask the "
         "respondent about how easy or difficult it is for them to purchase "
         "or receive medicines. Ask all questions in this section unless a "
         "skip rule applies."),
    64: "PLEASE LIST DOWN ALL MEDICINES THAT YOU TOOK FOR THE HEALTH CONDITION.",
    67: ("A Pharmacy is an ancillary primary care facility with a FDA LTO "
         "where registered medicines can be bought."),
    69: ("Note to enumerator [do not read]: This section is for awareness of "
         "the GAMOT package and generic and branded medicines. Ask all "
         "questions in this section unless a skip rule applies. Q69 to Q74, "
         "Q76 are applicable only to respondents in areas with GAMOT."),
    73: "Enumerator: Applicable only to respondents in areas with GAMOT.",
    79: ("Note to enumerator [do not read]: This section is for PhilHealth "
         "registration experience and registration status and membership. "
         "Ask all questions in this section unless a skip rule applies. "
         + _DNR_ONE),
    89: ("Note to enumerator [do not read]: This section is for Access to a "
         "primary care provider. Ask all questions in this section unless a "
         "skip rule applies."),
    92: "PROBE: Is your usual facility a health unit/center? Is it a hospital?",
    95: ("Please note the response for one way only from the time the "
         "respondent left their place of residence and arrived at the facility."),
    96: ("Please specify in Philippine pesos. Please confirm the ONE-WAY "
         "cost: from house to facility ONLY."),
    97: ("Note to enumerator [do not read]: This section is for Access to a "
         "primary care facility. Ask all questions in this section unless a "
         "skip rule applies."),
    101: ("Note to enumerator [do not read]: This section is for the "
          "Household members’ health-seeking behavior and outcomes. Ask all "
          "questions in this section unless a skip rule applies."),
    108: ("Note to enumerator [do not read]: This section is for the "
          "Experiences and Satisfaction with Referrals. Ask all questions in "
          "this section unless a skip rule applies."),
    126: ("Note to enumerator [do not read]: This section is for No Balance "
          "Billing Awareness and Utilization. Ask all questions in this "
          "section unless a skip rule applies."),
    132: ("Note to enumerator [do not read]: This section is for Zero "
          "Balance Billing Awareness and Utilization. Ask all questions in "
          "this section unless a skip rule applies."),
    141: ("IF RESPONDENT PROVIDES A RECEIPT, SELECT ALL THAT APPLY. IF NO "
          "RECEIPT WAS PROVIDED, READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."),
    159: ("For the next non-food items, the reference period is the past "
          "MONTH. This could include online purchases whenever applicable."),
    167: ("For the next non-food items, the reference period is the past 6 "
          "MONTHS. This could include online purchases whenever applicable."),
    169: ("For the next non-food items, the reference period is the past 12 "
          "MONTHS (1 YEAR). This could include online purchases whenever "
          "applicable."),
    177: "For the next health products and services, the reference period is the past 6 MONTHS.",
    182: "For the next health products and services, the reference period is the past MONTH.",
    197: ("For example, you felt you needed to see a medical provider, but "
          "waited until the symptoms were more serious because you were "
          "worried about the cost of the consultation or treatment, the "
          "travel to the facility, or the time off work."),
}

SECTION_INTROS = {
    1: ("Before proceeding to the survey proper, we would like to ask you "
        "some personal information."),
    30: "We will now ask for some personal information about your household members.",
    51: "We will now ask about your awareness of the Universal Health Care (UHC).",
    54: "We will now ask about your awareness of the YAKAP/Konsulta package.",
    57: ("We will now ask about your awareness of BUCAS and the services you "
         "have accessed in a BUCAS Center."),
    62: ("The next questions we will be asking are related to your access to "
         "medicines. We would like to know how easy or difficult it is for "
         "you and members of your household to purchase or receive medicines."),
    69: ("We will now ask about your awareness of the GAMOT package, and the "
         "medicines you availed in a GAMOT pharmacy. We will also ask some "
         "questions about your views in buying generic or branded medicines."),
    79: ("The next questions we will be asking are related your PhilHealth "
         "registration experience. We will also confirm your PhilHealth "
         "registration status and membership."),
    89: "We will now ask questions about your access to a primary care provider.",
    97: ("In this section of the survey, I will now ask about how you access "
         "care in the last 6 months in a primary care facility. Examples of "
         "primary care facilities are RHUs, Health Center, and Barangay "
         "Health Station."),
    101: ("We will now be asking about you and your household members’ "
          "actions taken for health concerns. This includes the type of "
          "services and facilities you access for your health and well-being."),
    108: "We will be asking about your experiences and satisfaction on referrals.",
    126: "We will now ask about your awareness of the No Balance Billing (NBB).",
    132: "We will now ask about your awareness of the Zero Balance Billing (ZBB).",
    144: ("We are now on the last few sections of the survey questionnaire. "
          "In this section, I would like to ask you questions about your "
          "household consumption of various food, non-food, and health "
          "products and services. I will ask about what your household used "
          "or consumed. First, I will ask which items your household used, "
          "and if you bought them, how much you spent. Then, I will ask "
          "about items your household used but did not buy—such as those you "
          "produced yourselves, received as gifts, or got for free—and you "
          "can estimate their value. Please do not include items bought for "
          "business, resale, or for making other products. Let me start with "
          "questions about your household consumption of food and beverages "
          "over the past week. In this first part, I would like to ask you "
          "to exclude meals, snacks and beverages prepared by restaurants "
          "and the like, including take-aways."),
    159: ("The next questions will focus on your household’s consumption of "
          "non-food and non-health expenses."),
    175: ("We will now move on to your household’s consumption or use of "
          "health products and services in the past 12 months."),
    183: ("In the next section, we would like to know more about the funds "
          "that you use for health care."),
    # #634: Section O (Sources of Funds, Q186-Q196) read-aloud lead-in for the
    # financial-sources battery — was missing before Q186 (tester-supplied paper text).
    186: ("In the last 12 months, which of the following financial sources did "
          "your household use to pay out-of-pocket for any medical, dental "
          "service with or without overnight stay, medicines, and health "
          "products?"),
}

_QNUM = re.compile(r"^Q(\d{1,3})_")


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def question_extras(nm, intro_used):
    """(pre, post) HTML for an item: section intro + enumerator instruction."""
    m = _QNUM.match(nm)
    if not m:
        return "", ""
    q = int(m.group(1))
    pre = post = ""
    # the intro attaches once, to the first item at/after its target question
    # (within +3 — some paper intros sit before unnumbered or merged fields)
    for tgt in SECTION_INTROS:
        if tgt not in intro_used and tgt <= q <= tgt + 3:
            pre = f"<p>{_esc(SECTION_INTROS[tgt])}</p>"
            intro_used.add(tgt)
            break
    instr = INSTRUCTIONS.get(q)
    if instr and not nm.endswith("_TXT"):
        post = f'<p class="instruction">{_esc(instr)}</p>'
    return pre, post


def main():
    d = json.loads(DCF.read_text(encoding="utf-8"))
    dict_name = d.get("name", "HOUSEHOLDSURVEY_DICT")
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
                pre, post = ("", "") if ov else question_extras(nm, intro_used)
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                for lnm, _ in langs:
                    body = ov or (pre + _html(labmap.get(lnm) or en) + post)
                    lines += [f"          {lnm}: |", f"            {body}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
