#!/usr/bin/env python3
"""
F1 Facility Head Survey — question-text (.qsf) generator.

Multi-language CAPI prompts. CSPro form field labels ([Text] in the .fmf) are
single-language and CSPro does NOT auto-translate them; the per-language channel is
the QUESTION TEXT (.qsf), shown in the question-text bar above the form. This reads
the generated FacilityHeadSurvey.dcf (which already carries every declared language
and its translated labels, via generate_dcf.py's apply_translations) and emits one
question per item with the prompt in every language. English is the fallback.

CSPro 8.0 .qsf: each language maps directly to the HTML text (block scalar); the
{format, text} sub-map is an 8.1+ schema and trips "yaml-cpp: bad conversion" on 8.0.

Invoke:  python generate_qsf.py    # writes FacilityHeadSurvey.ent.qsf  (run after generate_dcf.py)
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DCF = HERE / "FacilityHeadSurvey.dcf"
OUT = HERE / "FacilityHeadSurvey.ent.qsf"

# Build version (tester request 2026-07-02): ../versions.json is the single source of truth
# (bumped via automation/stamp_version.py, which also stamps the .pff Description for the
# CSEntry app list). This footer rides the case-key (QN) screen — the FIRST screen of every
# case in all three instruments; dict-first placement was wrong because the cover/FC block
# can sit at case-end on the form (v1.0.1). Same string in every language — UI chrome, not
# questionnaire text.
_BUILD = json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F1"]
# #1191 (PSA/SJREB, 2026-08-11): survey-tool details required on the CAPI tool. The
# clearance block is defined once in ../icf_content.py — the ICF screens carry the
# same block, and two copies of a cleared reference number would eventually diverge.
import sys as _sys
_sys.path.insert(0, str(HERE.parent))
import icf_content as _icf
# #1190: DOH Seal / ASPSI / Bagong Pilipinas / Bawat Buhay Mahalaga on the first
# page — ASPSI sits second, in the "attached agency" slot, per ASPSI's reference
# image on #1190 (Shan, 2026-08-11). Data-URI so the image travels inside the qsf
# into the .pen with no deploy-packaging changes; ../cover_logos.png is the one
# shared asset (built by ../compose_cover_logos.py).
import base64 as _b64
_LOGO_B64 = _b64.b64encode((HERE.parent / "cover_logos.png").read_bytes()).decode()
_LOGO_HTML = f'<p><img src="data:image/png;base64,{_LOGO_B64}" width="512"/></p>'

BUILD_FOOTER = (_LOGO_HTML
                + f'<p class="instruction">Build: F1 v{_BUILD["version"]} ({_BUILD["date"]})</p>'
                + _icf.clearance_html("F1"))

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
# PAPI emphasis (#1104 / #1105 / #1119 / #1128 / #1130)
# ------------------------------------------------------------------
# The paper questionnaire underlines the subject of each Section C
# "been implemented" question and bolds the compliance area in Q122-Q134;
# the CAPI rendered them flat. ASPSI asked for parity.
#
# Applied to the ENGLISH rendering only. The 7 translated locales keep their
# current (unemphasised) wording until the next re-key batch - adding markup
# to a translated string would mean guessing where the phrase falls in each
# language, and the OVERRIDES map can't be used here because it would emit one
# English blob to every language and destroy the existing translations.
#
# Phrases are DERIVED from the label, never transcribed: each pattern is
# anchored, and a label that doesn't match is returned unchanged.
_EMPH_PATTERNS = [
    # #1185: Section C's Q12/Q14/Q17 use different stems than the Q19-48 battery
    # ("Has the facility applied for ..." / "If yes, has the creation of ...")
    # so the anchored rules below never matched them. Underline spans confirmed
    # against the ASPSI-marked paper (ticket #1185).
    (re.compile(r"^(<p>12\. Has the )(facility applied for DOH primary care licensing)( since )"), "u"),
    (re.compile(r"^(<p>1[47]\. If yes, has the )(creation of an? (?:public health|health promotion) unit)( at this facility )"), "u"),
    # Q19-Q48 battery: "NN. Has/Have the <subject> been implemented since ..."
    (re.compile(r"^(<p>\d+\. (?:Has|Have) the )(.+?)( been implemented )"), "u"),
    # Q43 is worded differently: "... has the health facility been implementing
    # <subject> since ..." - anchor it separately rather than force the rule above.
    (re.compile(r"^(<p>43\. Has the health facility been implementing )(.+?)( since )"), "u"),
    # Q122-Q134: "NN. Why was it difficult to comply with: <area>?" - the paper
    # bolds the area INCLUDING its question mark.
    (re.compile(r"^(<p>\d+\. Why was it difficult to comply with: )(.+?)(</p>)"), "b"),
    # Q165/Q166: bold the staff group.
    (re.compile(r"^(<p>16[56]\. What forms of professional development do you "
                r"provide to your )(doctors|nurses)(\?)"), "b"),
]


def _emphasize(html):
    """Wrap the PAPI-emphasised phrase in <u>/<b>. First matching pattern wins;
    a label matching none is returned untouched."""
    # #1189: the EN question text for Q88 is the VERBATIM paper stem (448 chars
    # — over the dcf label cap, so it cannot derive from the label; the dcf
    # keeps the condensed <=255 string that the locale translations key to).
    # Both paper bolds included. Locales falling back to English get this too.
    if html.startswith("<p>88. "):
        return ("<p>88. The maximum per capita rate amount for YAKAP/Konsulta "
                "is at Php <b>1,700</b> across private and public facilities. "
                "According to PhilHealth, 40% of the capitation amount will be "
                "released as the first tranche after the first patient "
                "encounter. The remaining 60% will be released based on the "
                "size of the registered catchment population by December and "
                "performance targets that year. <b>Based on your practice, is "
                "this enough?</b></p>")
    for rx, tag in _EMPH_PATTERNS:
        m = rx.search(html)
        if m:
            return (html[:m.start()] + m.group(1)
                    + f"<{tag}>{m.group(2)}</{tag}>" + m.group(3)
                    + html[m.end():])
    return html


# ------------------------------------------------------------------
# Informed Consent Form — Annex H (SJREB-approved, F1 Facility Head
# variant, verbatim; English-only until ASPSI delivers ICF translations).
# Rendered as the CAPI question text of CONSENT_GIVEN so the enumerator
# reads PART I aloud from the question-text bar, then records Yes/No
# (No → endlevel per PROC CONSENT_GIVEN).
# ------------------------------------------------------------------
CONSENT_HTML = "".join([
    _p("heading2", "Informed Consent Form"),
    _p("instruction",
       "This informed consent form must be obtained before conducting the interview. "
       "You are required to read this entire consent form aloud exactly as written. "
       "After reading this form to the respondent, you must complete and sign the "
       "verification consent form."),
    _p("heading3", "PART I: Information about the study"),
    _p("normal",
       "Hello, my name is __________________ (data collector name). I work for Asian "
       "Social Project Services, Inc. (ASPSI). I am here to invite you to participate "
       "in a study about the Universal Health Care (UHC) and packages of programs like "
       "Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), Zero Balance "
       "Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS), and "
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
       "will never include your name in information shared with the government or in "
       "any reports. Your name will be kept separately from your answers in a private, "
       "secure location. For this interview, it is also important to respect other "
       "people’s privacy and not tell anyone else what we talked about today. With all "
       "research, there’s a small chance that someone else might get to see your data. "
       "We try our best to prevent that, but if it happens, we’ll tell you as soon as "
       "possible."),
    _p("normal",
       "Aside from this, there are no other risks to you if you take part in this "
       "study. As a benefit of the research, the knowledge gained may help the "
       "government and DOH better support your healthcare needs. You are free to "
       "decline participation or to stop at any time. Choosing not to participate will "
       "not result in any penalty, and you will not have to pay anything to take part "
       "in this study."),
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
# CONSENT_GIVEN removed 2026-06-12 — no consent DECISION is captured on the CAPI, and
# that has not changed. What DID change (2026-08-13): ASPSI sent "Suggested Layout
# (CSEntry).docx", putting the consent SCRIPT back on the device as two read-aloud
# screens with the clearance block. Its wording supersedes CONSENT_HTML above (which
# remains unemitted, kept only as the Annex H reference). Text: ../icf_content.py.
OVERRIDES = {
    "ICF_PART1": _icf.build_screen_html("F1", 1, _LOGO_HTML),
    "ICF_PART2": _icf.build_screen_html("F1", 2, _LOGO_HTML),
}


# ------------------------------------------------------------------
# Per-question enumerator instructions + section read-aloud intros,
# transcribed from Annex F1 (Apr 20 deliverable). Keyed by paper question
# number: the intro attaches once to the first Q<n>_* item; the instruction
# (blue Instruction style) to every Q<n>_* item except other-specify *_TXT
# fields. Paper-only navigation notes (<proceed to Qx>) are omitted — CAPI
# logic automates the routing. English-only, like the consent override.
# ------------------------------------------------------------------
_READ_ONE = "READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY."
_READ_ALL = "READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_DNR_ALL = "DO NOT READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_DNR_UNPROMPTED = ("DO NOT READ OPTIONS OUT LOUD. SELECT ALL THE ANSWER "
                   "OPTIONS THAT THE RESPONDENT GIVES WITHOUT PROMPTING.")
_PROBE = ("DO NOT READ OPTIONS OUT LOUD. USE THE FOLLOWING GUIDE QUESTIONS TO "
          "PROBE. Has this been implemented? / Do you have this? Was this "
          "implemented before or after 2019? Was this implemented because of "
          "UHC? Do you plan to implement it in the next 1-2 years?")

INSTRUCTIONS = {
    **dict.fromkeys([12, 14, 17, 19, 21, 23, 25, 27, 29, 31, 36, 38, 39, 40,
                     41, 42, 44, 45, 46, 47, 48], _PROBE),
    # #387: Q157/Q158 are select-one. #576: Q161 is single-select (rating scale) —
    # moved out of _READ_ALL so its instruction reads "SELECT ONE ANSWER ONLY".
    **dict.fromkeys([15, 18, 32, 60, 95, 103, 110, 157, 158, 161], _READ_ONE),
    **dict.fromkeys([34, 53, 75, 76, 78, 79, 99, 104, 105, 111, 121, 137, 140,
                     146, 147, 149, 156, 159, 163, 165, 166], _READ_ALL),
    **dict.fromkeys([64, 66, 67, 68, 69, 70, 71, 72, 73, 74, 94, 96, 98, 117,
                     122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132,
                     133, 134, 151, 162], _DNR_ALL),
    **dict.fromkeys([49, 50], _DNR_UNPROMPTED),
    43: ("Under UHC, basic ward allocation is as follows: 90% for government "
         "general hospitals; 70% for government specialty hospitals, and 10% "
         "for private hospitals. " + _PROBE),
    # #1109: the capitation definition. #1011 stripped it OUT of the Q57 question text
    # (testers: it is the paper's italic enumerator note, not part of the spoken question)
    # but nothing put it back anywhere, so it was simply lost - the enumerator had no
    # definition at all. #1109 asks for it as a blue note, which is what this class is.
    # Wording verbatim from the paper (raw/Project-Deliverable-1/F1.txt); only the outer
    # parentheses are dropped, since they existed to set it off INSIDE the question and
    # every other note here (43/58/65/88) reads as a plain sentence.
    57: ("Capitation is the amount per year per registered patient for delivering "
         "the YAKAP/Konsulta package services."),
    58: ("Performance indicators are the defined set of healthcare goods and "
         "services to be provided for each enrolled patient to receive the "
         "full capitation payment. DO NOT READ OPTIONS OUT LOUD. SELECT ALL "
         "THE ANSWER OPTIONS THAT THE RESPONDENT GIVES WITHOUT PROMPTING. "
         "RESPONDENT MAY NOT BE ALLOWED TO LOOK FOR REFERENCE PRIOR TO "
         "ANSWERING THIS QUESTION."),
    65: ("These are the requirements for YAKAP/Konsulta accreditation "
         "outlined by DOH. " + _READ_ALL),
    # (#1189: the old 88 entry is gone — the tranche mechanics now live verbatim
    # inside the full Q88 stem emitted by _emphasize; a note here would duplicate.)
    155: ("Our focus is specifically on referrals external to the facility, "
          "excluding internal referrals. " + _READ_ALL),
}

SECTION_INTROS = {
    1: "We would like to ask some of your personal information relevant to the survey.",
    7: "Next, we will be asking questions about this health facility.",
    9: ("We will now ask about your awareness of UHC, the changes that have "
        "been implemented in this facility since the UHC Act was passed in "
        "2019 and if these changes were a result of the UHC Act."),
    51: ("The next questions we will ask relate to the YAKAP/Konsulta "
         "package. Please answer to the best of your knowledge. You may "
         "answer “I don't know” if you are unsure."),
    101: "We will now ask questions related to BUCAS center and GAMOT package.",
    118: "We will now ask you about your facility’s experience with the licensing process.",
    135: ("The next set of questions covers the service delivery process. "
          "This section covers the implementation of NBB and ZBB, LGU "
          "support, and the Referral System."),
    163: "We will now proceed to the last section of this survey, which focuses on human resources.",
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
    dict_name = d.get("name", "FACILITYHEADSURVEY_DICT")
    langs = [(l["name"], l.get("label", l["name"]))
             for l in (d.get("languages") or [{"name": "EN", "label": "English"}])]

    lines = ["---", "fileType: Question Text", "version: CSPro 8.0", "languages:"]
    for nm, lb in langs:
        lines += [f"  - name: {nm}", f"    label: {lb}"]
    lines.append(STYLES)
    lines.append("questions:")

    # the id item never appears in the records loop below, so emit its (footer-only) entry here
    qn = d["levels"][0]["ids"]["items"][0]["name"]
    lines += [f"  - name: {dict_name}.{qn}", "    conditions:", "      - questionText:"]
    for lnm, _ in langs:
        lines += [f"          {lnm}: |", f"            {BUILD_FOOTER}"]

    seen, n = set(), 0
    intro_used = set()
    for lvl in d["levels"]:
        for rec in lvl.get("records", []):
            for it in rec.get("items", []):
                nm = it["name"]
                if it.get("contentType") in ("image", "audio", "document", "geometry"):
                    continue   # binary items: off-form, no question prompt (#713)
                if nm in seen:
                    continue
                seen.add(nm)
                labmap = {l.get("language"): l.get("text", "") for l in (it.get("labels") or [])}
                en = labmap.get("EN") or nm
                ov = OVERRIDES.get(nm)
                pre, post = ("", "") if ov else question_extras(nm, intro_used)
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                for lnm, _ in langs:
                    raw = labmap.get(lnm) or en
                    txt = _html(raw)
                    # EN (or a locale falling back to it). _TXT specify-box prompts are
                    # excluded, matching how question_extras() skips them for instructions -
                    # the emphasis belongs on the question, not its follow-up specify field.
                    if raw == en and not nm.endswith("_TXT"):
                        txt = _emphasize(txt)
                    body = ov or (pre + txt + post)
                    lines += [f"          {lnm}: |", f"            {body}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
