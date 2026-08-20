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

from generate_dcf import build_f4_dictionary, apply_translations

HERE = Path(__file__).parent
DCF = HERE / "HouseholdSurvey.dcf"
OUT = HERE / "HouseholdSurvey.ent.qsf"

# Build version (tester request 2026-07-02): ../versions.json is the single source of truth
# (bumped via automation/stamp_version.py, which also stamps the .pff Description for the
# CSEntry app list). This footer rides the case-key (QN) screen — the FIRST screen of every
# case in all three instruments; dict-first placement was wrong because the cover/FC block
# can sit at case-end on the form (v1.0.1). Same string in every language — UI chrome, not
# questionnaire text.
_BUILD = json.loads((HERE.parent / "versions.json").read_text(encoding="utf-8"))["F4"]
# #1191 (PSA/SJREB, 2026-08-11): survey-tool details required on the CAPI tool. The
# clearance block is defined once in ../icf_content.py — the ICF screens carry the
# same block, and two copies of a cleared reference number would eventually diverge.
import sys as _sys
_sys.path.insert(0, str(HERE.parent))
import icf_content as _icf
from notes_lookup import translate_note
# #1307: see F1 -- tells a verbatim-label caption from a designed short caption.
from cspro_helpers import caption_duplicates_question as _cap_dup
from generate_fmf import SHORT_FORM_LABELS as _SHORT

# #1190: brand-book main logo sequence on the first page — see F1/generate_qsf.py.
import base64 as _b64
_LOGO_B64 = _b64.b64encode((HERE.parent / "cover_logos.png").read_bytes()).decode()
_LOGO_HTML = f'<p><img src="data:image/png;base64,{_LOGO_B64}" width="512"/></p>'

BUILD_FOOTER = (_LOGO_HTML
                + f'<p class="instruction">Build: F4 v{_BUILD["version"]} ({_BUILD["date"]})</p>'
                + _icf.clearance_html("F4"))

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
# CONSENT_HTML REMOVED 2026-08-20 (ANA-322).
#
# It held the Annex H consent script as the CAPI question text for CONSENT_GIVEN.
# CONSENT_GIVEN itself was removed 2026-06-12, so nothing has emitted this string
# since -- it sat here unreferenced for over two months.
#
# Deleted outright rather than kept as commented-out reference text, because the
# F1 and F4 copies still carried STALE ETHICS CONTACT DETAILS (superseded SJREB /
# ASPSI email and phone). That is not merely untidy: it has already cost real work.
# An implementer once corrected this dead copy believing it was the live consent
# text, and the compiled build still shipped with no ethics-contact block at all --
# recorded in the F3 consent-certificate row of
# instruments-aug17-extract/aug17-approved-divergences.md. Leaving wrong contact
# details in the tree, even inert, keeps that trap armed for the next reader.
#
# THE LIVE CONSENT SCRIPT IS ../icf_content.py -> SCREENS['F4'], rendered by
# build_screen_html() and wired below via OVERRIDES["ICF_PART1"/"ICF_PART2"].
# Edit it there. Git history holds the removed Annex H wording if it is ever
# wanted for reference.
# ------------------------------------------------------------------

# Item-name → question-text HTML. Overrides win over the dcf-label default
# and are emitted identically for every declared language (English fallback
# until SJREB-approved ICF translations arrive).
# CONSENT_GIVEN removed 2026-06-12 — no consent DECISION is captured on the CAPI, and
# that has not changed. What DID change (2026-08-13): ASPSI sent "Suggested Layout
# (CSEntry).docx", putting the consent SCRIPT back on the device as two read-aloud
# screens with the clearance block. Text: ../icf_content.py. (The old, unemitted
# CONSENT_HTML block that this superseded was removed 2026-08-20, ANA-322.)
OVERRIDES = {
    "ICF_PART1": _icf.build_screen_html("F4", 1, _LOGO_HTML),
    "ICF_PART2": _icf.build_screen_html("F4", 2, _LOGO_HTML),
}


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
_SELECT_ALL = "SELECT ALL THAT APPLY."

INSTRUCTIONS = {
    # #1069/#1070 (pretest 2026-08-05): bare "SELECT ALL THAT APPLY." on the
    # multi-selects the paper marks but that carried no note (all 9 verified
    # checkbox_multiselect in generate_dcf). Mirrors F3's #1055.
    # #1206 (2026-08-12): Q65 and Q84 join the sweep. Both are genuine
    # checkbox_multiselect captures, but the Apr-20 paper prints no grid for
    # either (Q65 is a bare "CODING FOR QUESTION 65" block; Q84's options were
    # added under #814), so neither was caught by the #1069/#1070 pass.
    **dict.fromkeys([65, 66, 70, 71, 74, 77, 78, 84, 106, 107, 202], _SELECT_ALL),
    **dict.fromkeys([4, 5, 6, 110, 111, 118, 125], _READ_ONE),
    # #1068 (pretest 2026-08-05): Q17 carries the paper's decision-maker definition
    # ahead of the standard read-instruction (same definition F3's Q34 got in #1051).
    17: ("This is the person who makes decisions on health in the family: for "
         "example, yearly immunizations, manages hospital finances, etc. "
         + _READ_ONE),
    **dict.fromkeys([7, 11, 80, 81, 112], _DNR_ONE),
    # 1176-aug17: 143 removed -- Q143 is now a plain no-receipt Amount
    # field (renumbered from the old Q141_1_NO_RECEIPT_AMT_PHP sub-item),
    # not a checkbox; it never needed a read-aloud/select-all note.
    **dict.fromkeys([82, 88, 102, 103, 109], _READ_ALL),
    **dict.fromkeys([52, 53, 55, 56, 58, 59, 85, 91, 93, 94, 113, 121, 127,
                     128, 133, 134, 137], _DNR_ALL),
    **dict.fromkeys([10, 38], _PWD_CARD),
    **dict.fromkeys([70, 71, 72], _GAMOT_FAC),
    # #1070: Q70/Q71 sit in the GAMOT-area list above (last-key-wins), so their
    # select-all note must be APPENDED, not merged from the fromkeys block.
    70: _GAMOT_FAC + " " + _SELECT_ALL,
    71: _GAMOT_FAC + " " + _SELECT_ALL,
    1: ("Note to enumerator [do not read]: This section is for the Respondent "
        "Profile. The respondent should be the main-decision maker of the "
        "household. Ask all questions in this section unless a skip rule applies."),
    12: ("If the respondent is studying - please put “No employment - not "
         "looking for work”. " + _READ_ONE),
    13: _READ_ONE + " IF MORE THAN ONE, ASK FOR THE MAIN SOURCE.",
    15: _DNR_ONE,   # #791: removed the custom "A list will be provided…" enumerator note per tester; standard read-instruction kept
    # #1202: the Q18 notes moved to INSTRUCTIONS_BY_NAME below. Q18 is two fields on one
    # paper number, so a number key sprayed the bracket's note onto the amount box too
    # (the same spray F3 fixed in #1048).
    19: ("Please count yourself and all the people who usually live with you. "
         "Please include those who are not living here now but will be back "
         "within six months, BUT do not include OFWs."),
    29: "Please choose one from the options I will mention.",
    # #1074 put the PhilHealth membership-category definitions here, in a note above the
    # question, because the two longest blow CSPro's 255-char label cap.
    # #1177 (ASPSI, 2026-08-06) asked for them BESIDE each option instead: reading a wall
    # of ten definitions before the options, then the bare options, made the enumerator
    # hold all ten in their head. The definitions now live in the Q46 value-set labels
    # (generate_dcf.py), so this note is deleted rather than duplicated — otherwise the
    # enumerator reads every definition twice. The cap is handled there by condensing the
    # two long ones; see the comment on Q46_MEMBER_CATEGORY.
    30: ("Note to enumerator [do not read]: This section is for the "
         "characteristics of the Household. The respondent can answer on behalf "
         "of the household member. However, if the household member is present "
         "during the interview, they may provide their answers. Ask all "
         "questions in this section unless a skip rule applies. For the "
         "enumerator: please check that the total number is equal to the number "
         "answered in Q19."),
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
    # 1176-aug17: moved from key 141 -- the bill-items checklist this note
    # describes is now Q140 (paper's own Aug-17 renumber); Q141 is a plain
    # yes/no payment-recall gate with no comparable note.
    140: ("IF RESPONDENT PROVIDES A RECEIPT, SELECT ALL THAT APPLY. IF NO "
          "RECEIPT WAS PROVIDED, READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."),
    # Reference-period scripts attach to the FIRST item of each group (was wrongly on the
    # LAST item of the PREVIOUS group — #678/#680/#681/#682/#683). Paper (Annex F4 Apr-20,
    # Section N): Q159 Smoking = WEEK (no MONTH script); MONTH starts Q160; 6-MONTHS starts
    # Q168; 12-MONTHS starts Q170; health 6-MONTHS starts Q178; health MONTH starts Q183.
    160: ("For the next non-food items, the reference period is the past "
          "MONTH. This could include online purchases whenever applicable."),
    168: ("For the next non-food items, the reference period is the past 6 "
          "MONTHS. This could include online purchases whenever applicable."),
    170: ("For the next non-food items, the reference period is the past 12 "
          "MONTHS (1 YEAR). This could include online purchases whenever "
          "applicable."),
    178: "For the next health products and services, the reference period is the past 6 MONTHS.",
    183: "For the next health products and services, the reference period is the past MONTH.",
    197: ("For example, you felt you needed to see a medical provider, but "
          "waited until the symptoms were more serious because you were "
          "worried about the cost of the consultation or treatment, the "
          "travel to the facility, or the time off work."),
}

# Item-NAME-keyed instructions — for notes belonging to ONE component of a multi-field
# question, where the paper-number key would spray the note across every Q<n>_* field.
# Wins over the number-keyed map above. Mirrors F3's map (#1048).
INSTRUCTIONS_BY_NAME = {
    # #1202: Q18 renders as the paper's two parts. The amount box gets the missing-value
    # note (the -98/-99 sentinels the apc already accepts); the dropdown gets the category
    # note. Both used to sit inside the dictionary labels, so they rendered as question text.
    "Q18_INCOME_AMOUNT": ("Enumerator note: Ensure that the respondent will provide a valid "
                          "response. In case the respondent fails to provide one, input -98 "
                          "for “I don’t know” and -99 for “Refuse to Answer”."),
    "Q18_INCOME_BRACKET": ("Enumerator note: Select the income category that corresponds to "
                           "the respondent’s approximate household income."),
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
    # #683.3: the "funds for health care" section transition belongs before Q186 (Section O),
    # NOT before Q183 (which is a health-MONTH expenditure item). Merged here with the #634
    # financial-sources battery lead-in — both are read once before Q186 per the paper.
    186: ("In the next section, we would like to know more about the funds "
          "that you use for health care. In the last 12 months, which of the "
          "following financial sources did your household use to pay "
          "out-of-pocket for any medical, dental service with or without "
          "overnight stay, medicines, and health products?"),
}

_QNUM = re.compile(r"^Q(\d{1,3})_")
# Sub-question pattern: Q<n>_<m>_...  e.g. Q141_1_NO_RECEIPT_AMT_PHP, Q2_1_AGE, Q89_1_*.
# These are decimal sub-items (Q141.1, Q2.1, Q89.1), NOT the parent question Q<n>, so they
# must NOT inherit the parent's enumerator instruction (#667: Q141_1 wrongly showed the
# Q141 receipt note). _QNUM still captures the parent int for SECTION_INTRO placement, but
# the INSTRUCTIONS note is suppressed for sub-questions below.
_SUBQ = re.compile(r"^Q\d{1,3}_\d+_")


# ------------------------------------------------------------------
# Section C name-piping (#610/#613.3) + roster line-number context (#601/#614).
# Per-member questions show the member's name piped from the household roster's Q30_NAME
# so the enumerator never loses track of whose row it is. Q42-Q44 reference Q30_NAME in
# their own occurrence; the Q48-Q50 private-insurance pass (C_PRIVATE_INS_ROSTER) references
# the SAME household-roster member by occurrence. The paper "(NAME)" token is replaced inline.
# Fills (~~expr~~) live ONLY in the question text (.qsf) and evaluate on-device; the dcf
# label / bold header still shows "(NAME)" literally (pre-existing, not a regression).
# ------------------------------------------------------------------
# (NAME) English + (PANGALAN) Tagalog member-name placeholders, replaced inline with the fill.
_NAME_TOKEN_RE = re.compile(r"\((?:NAME|PANGALAN)\)", re.IGNORECASE)
# #610 originally piped the member-name header onto only Q42-Q44. The "Household
# Characteristic Target Interface" (ASPSI, 2026-06) wants that blue "Household member:
# <name> (Roster line N)" header on EVERY Section C per-member question (Q31-Q46), so the
# enumerator/respondent always knows whose row each question is for. Derive the full set
# from the C_HOUSEHOLD_ROSTER record so it can't drift as fields change — excluding
# MEMBER_LINE_NO (noinput control, never shown) and Q30_NAME (the name-entry screen itself,
# which carries the section note, not a self-referential header).
def _hh_roster_fields():
    for _lvl in build_f4_dictionary()["levels"]:
        for _rec in _lvl.get("records", []):
            if _rec["name"] == "C_HOUSEHOLD_ROSTER":
                return {it["name"] for it in _rec["items"]
                        if it["name"] not in ("MEMBER_LINE_NO", "Q30_NAME")}
    return {"Q42_GSIS", "Q43_SSS", "Q44_PAGIBIG"}   # defensive fallback (prior #610 scope)


_PIPE_HH = _hh_roster_fields()
_PIPE_PRIV = {"Q48_OTHER_INS_REG", "Q49_PRIVATE_INS", "Q50_PRIVATE_INS_OTHER_TXT"}
# Option C food roster (2026-07-03): every grid-row question leads with WHICH item the row
# is for — the auto-filled N_FOOD_ITEM piped as a bold header (Section C piping pattern).
# Fan-out (2026-07-03): every Section N roster pipes its row's auto-filled *_ITEM into
# each grid question as a bold header (Section C piping pattern). Maps member -> ITEM field.
_EXP_ROSTER_PREFIXES = ("N_FOOD", "N_WKOTH", "N_NF1M", "N_NF6M", "N_NF12M", "N_H12M", "N_H6M", "N_H1M")
_PIPE_EXP = {f"{p}_{s}": f"{p}_ITEM"
             for p in _EXP_ROSTER_PREFIXES
             for s in ("CONSUMED", "AMT_STATUS", "PURCHASED_PHP", "INKIND_PHP")}
# Read-once section intros: attached to each roster's first row (logic: curocc() = 1).
_ROSTER_INTROS = {"N_FOOD_CONSUMED": 144, "N_NF1M_CONSUMED": 160, "N_NF6M_CONSUMED": 168,
                  "N_NF12M_CONSUMED": 170, "N_H12M_CONSUMED": 175, "N_H6M_CONSUMED": 178,
                  "N_H1M_CONSUMED": 183}
_HH_NAME_FILL = "~~strip(Q30_NAME)~~"
_PRIV_NAME_FILL = "~~strip(Q30_NAME(curocc()))~~"

# Roster line-1 (respondent) cross-check notes (#603/#606/#607/#609). For roster line 1
# (the respondent), these per-member questions should match the respondent's own Section B
# answers; show the prior answer as a blue note so the enumerator can cross-check without
# paging back. getvaluelabel() prints the coded answer's label; fills evaluate on-device.
# (Option (b) from the tester — a reminder note, not a hard cross-field warning.)
_ROSTER_CROSSCHECK = {
    "Q35_HAS_DISABILITY": ("If this is line 1 (the respondent): compare with their Section B "
                           "disability answer Q7 — <b>~~getvaluelabel(Q7_IS_PWD)~~</b>."),
    "Q39_CIVIL_STATUS":   ("If this is line 1 (the respondent): should match their Section B "
                           "civil status Q6 — <b>~~getvaluelabel(Q6_CIVIL_STATUS)~~</b>."),
    "Q40_EDUCATION":      ("If this is line 1 (the respondent): should match their Section B "
                           "education Q11 — <b>~~getvaluelabel(Q11_EDUCATION)~~</b>."),
    "Q41_EMPLOYMENT":     ("If this is line 1 (the respondent): should match their Section B "
                           "employment Q12 — <b>~~getvaluelabel(Q12_EMPLOYMENT)~~</b>."),
}


def _pipe_member_name(nm, html):
    """Prefix the roster member's name + line number and replace the inline '(NAME)' token
    for the Section C per-member questions. Runs AFTER _html escaping so the ~~fill~~ is not
    HTML-escaped (parens in '(NAME)' are not escaped either, so the inline sub still matches)."""
    if nm in _PIPE_HH:
        ctx = (f'<p class="instruction">Household member: {_HH_NAME_FILL} '
               f'(Roster line ~~MEMBER_LINE_NO~~ — line 1 is the respondent)</p>')
        return ctx + _NAME_TOKEN_RE.sub(_HH_NAME_FILL, html)
    if nm in _PIPE_PRIV:
        ctx = (f'<p class="instruction">Household member: {_PRIV_NAME_FILL} '
               f'(Roster line ~~PRIV_MEMBER_LINE_NO~~)</p>')
        return ctx + _NAME_TOKEN_RE.sub(_PRIV_NAME_FILL, html)
    if nm in _PIPE_EXP:
        return f'<p><b>~~strip({_PIPE_EXP[nm]})~~</b></p>' + html
    return html


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def question_extras(nm, intro_used):
    """(intro_english, instruction_english) for an item — TEXT, not HTML.

    This returned finished HTML and main() called it once per ITEM, outside the
    per-language loop, so the English note went into every locale - 108 F4 question
    screens showed English whatever language was chosen (#1216/#1219/#1220/#1223/#1224/
    #1225). Returning the English source lets the caller resolve it per language via
    note_html(). The intro-consumed bookkeeping stays here so it still runs once per item.
    """
    m = _QNUM.match(nm)
    if not m:
        return None, None
    q = int(m.group(1))
    intro = None
    # the intro attaches once, to the first item at/after its target question
    # (within +3 — some paper intros sit before unnumbered or merged fields)
    for tgt in SECTION_INTROS:
        if tgt not in intro_used and tgt <= q <= tgt + 3:
            intro = SECTION_INTROS[tgt]
            intro_used.add(tgt)
            break
    # #1202: an explicit item-name key wins over the paper-number map (F3 #1048 pattern).
    # A name key is deliberate, so it is exempt from the #667 _TXT/_SUBQ suppression.
    instr = INSTRUCTIONS_BY_NAME.get(nm)
    # #667: suppress the parent question's instruction note on decimal sub-questions
    # (Q<n>_<m>_…, e.g. Q141_1_NO_RECEIPT_AMT_PHP) and on free-text *_TXT capture fields.
    if instr is None and not nm.endswith("_TXT") and not _SUBQ.match(nm):
        instr = INSTRUCTIONS.get(q)
    return intro, instr


def note_html(intro_en, instr_en, lang):
    """Render the two notes in ONE language; missing translation keeps English, which is
    what the tablet shows today, so a miss is never a regression."""
    pre = f"<p>{_esc(translate_note(intro_en, lang))}</p>" if intro_en else ""
    post = (f'<p class="instruction">{_esc(translate_note(instr_en, lang))}</p>'
            if instr_en else "")
    return pre, post


def main():
    # Build the dictionary IN-MEMORY (full-length labels) instead of reading the on-disk
    # HouseholdSurvey.dcf, whose labels write_dcf() caps at 255 chars via
    # _truncate_long_labels. That 255 cap is correct for the dcf/fmf bold header, but the
    # qsf inherited it and truncated long Section N prompts mid-sentence in the CAPI
    # question-text bar (#741/#742/#745: Q152/159/162/163/164/168/169/171/178/179/180/181/
    # 183/184 were cut at "— In the..."). The qsf question text has no length limit, so it
    # carries the FULL prompt. Mirrors the #748 in-memory-build fix in generate_fmf.
    d = build_f4_dictionary()
    d = apply_translations(d, HERE / "translations")
    dict_name = d.get("name", "HOUSEHOLDSURVEY_DICT")
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
                intro_en, instr_en = ((None, None) if ov
                                      else question_extras(nm, intro_used))
                # Option C (2026-07-03): the Section N intro script reads ONCE — attached
                # to the food grid's first row via a qsf condition (logic: curocc() = 1);
                # the trailing logic-less condition is the default text for rows 2-13.
                if nm in _ROSTER_INTROS:
                    _tgt = _ROSTER_INTROS[nm]
                    intro_used.add(_tgt)
                    _is_intro = _tgt in SECTION_INTROS
                    _src = SECTION_INTROS[_tgt] if _is_intro else INSTRUCTIONS[_tgt]
                    lines += [f"  - name: {dict_name}.{nm}", "    conditions:",
                              "      - logic: curocc() = 1", "        questionText:"]
                    for lnm, _ in langs:
                        # per-language, like the main loop: this read-once roster intro was
                        # emitting one English string into all eight locales
                        _t = _esc(translate_note(_src, lnm))
                        intro = (f"<p>{_t}</p>" if _is_intro
                                 else f'<p class="instruction">{_t}</p>')
                        body = intro + _pipe_member_name(nm, _html(labmap.get(lnm) or en))
                        lines += [f"          {lnm}: |", f"            {body}"]
                    lines += ["      - questionText:"]
                    for lnm, _ in langs:
                        body = _pipe_member_name(nm, _html(labmap.get(lnm) or en))
                        lines += [f"          {lnm}: |", f"            {body}"]
                    n += 1
                    continue
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                cc = _ROSTER_CROSSCHECK.get(nm)   # #603/#606/#607/#609 line-1 cross-check note
                for lnm, _ in langs:
                    pre, post = note_html(intro_en, instr_en, lnm)   # per LANGUAGE
                    body = ov or (pre + _html(labmap.get(lnm) or en) + post)
                    # #1307: unnumbered field -> the caption already prints this label;
                    # keep intro/instruction, drop the echoed label.
                    if not ov and _cap_dup(nm, en, _SHORT.get(nm),
                                           (rec.get("occurrences") or {}).get("maximum", 1) > 1):
                        body = pre + post
                    body = _pipe_member_name(nm, body)   # Section C name/line piping
                    if cc:
                        body = body + f'<p class="instruction">{cc}</p>'
                    lines += [f"          {lnm}: |", f"            {body}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
