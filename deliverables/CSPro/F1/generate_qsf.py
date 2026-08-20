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
from notes_lookup import translate_note
# #1306: needed to tell a field whose caption is its label verbatim (question text would
# echo it) from one with a designed short caption (no echo). Same-folder import, the way
# generate_fmf already imports generate_dcf.
from cspro_helpers import caption_duplicates_question as _cap_dup
from generate_fmf import SHORT_FORM_LABELS as _SHORT
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
# The paper questionnaire emphasises a phrase inside some question stems and
# the CAPI rendered them flat; ASPSI asked for parity.
#
# Applied to the ENGLISH rendering only. The 7 translated locales keep their
# current (unemphasised) wording until the next re-key batch - adding markup
# to a translated string would mean guessing where the phrase falls in each
# language, and the OVERRIDES map can't be used here because it would emit one
# English blob to every language and destroy the existing translations.
#
# Phrases are DERIVED from the label, never transcribed: each pattern is
# anchored, and a label that doesn't match is returned unchanged.
#
# AUG-17 (Task 2.5). Four of the six Apr-20 patterns are RETIRED, not re-keyed,
# because the questions they emphasised no longer exist in that form: the
# Aug-17 paper carries exactly two {.underline} spans in the whole document
# (the ICF name blank and Q128), having moved to bolding whole stems, and the
# Q19-Q48 "Has the <subject> been implemented since ..." battery was reworded
# into plain Yes/No bases with a separate attribution probe. The retired rules
# matched ZERO of the 320 rebuilt labels, so keeping them would have been dead
# code claiming to do something. Retired: Q12 primary-care-licensing,
# Q14/Q17 unit-creation, the "been implemented" battery, Q43 ward allocation.
_EMPH_PATTERNS = [
    # "NN. Why was it difficult to comply with: <area>?" - the paper bolds the
    # area INCLUDING its question mark. Number-agnostic, so the Aug-17 renumber
    # did not touch it; it now serves BOTH compliance batteries (Q53-Q61
    # accreditation and Q109-Q121 DOH licensing), which print the same stem.
    (re.compile(r"^(<p>\d+\. Why was it difficult to comply with: )(.+?)(</p>)"), "b"),
    # Q152/Q153 (was Q165/Q166): bold the staff group.
    (re.compile(r"^(<p>15[23]\. What forms of professional development do you "
                r"provide to your )(doctors|nurses)(\?)"), "b"),
    # Q128: the ONE content underline the Aug-17 paper still carries (the only
    # other {.underline} span in the document is the ICF's data-collector-name
    # blank). Added at Task 2.5 rather than carried - the Apr-20 rules that
    # covered other questions were retired because their questions were
    # reworded away, and this span is newly marked.
    (re.compile(r"^(<p>\d+\. Does the facility allow )"
                r"(out-of-pocket \(OOP\) expenses)( for basic accommodation)"), "u"),
]

# Q75 (was Q88) carries TWO bolds in one stem, which the single-span loop below
# cannot express, so it gets its own anchored rule.
#
# #1189 handled this by hard-coding the whole 448-char Apr-20 paper stem here,
# because it exceeded the dcf's 255-char label cap and so could not be derived
# from the label. That override is GONE, for two reasons. It was keyed on the
# literal prefix "<p>88. ", and Aug-17's Q88 is "Have you heard about the
# Bagong Urgent Care and Ambulatory Service (BUCAS)?" - it would have replaced
# that question's text with the capitation paragraph, in English and in every
# locale falling back to English. And it is no longer needed: Aug-17 condensed
# the stem to 236 chars, so the dcf label now carries the full text itself and
# the emphasis can be derived from it like every other rule here.
_CAPITATION_RE = re.compile(
    r"^(<p>\d+\. The maximum per capita rate for YAKAP/Konsulta is )"
    r"(Php 1,700)"
    r"(.*?)"
    r"(Based on your practice, is this enough\?)"
    r"(</p>)$")


def _emphasize(html):
    """Wrap the PAPI-emphasised phrase in <u>/<b>. First matching pattern wins;
    a label matching none is returned untouched."""
    m = _CAPITATION_RE.match(html)
    if m:
        return (m.group(1) + f"<b>{m.group(2)}</b>" + m.group(3)
                + f"<b>{m.group(4)}</b>" + m.group(5))
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
# THE LIVE CONSENT SCRIPT IS ../icf_content.py -> SCREENS['F1'], rendered by
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
    "ICF_PART1": _icf.build_screen_html("F1", 1, _LOGO_HTML),
    "ICF_PART2": _icf.build_screen_html("F1", 2, _LOGO_HTML),
}


# ------------------------------------------------------------------
# Per-question enumerator instructions + section read-aloud intros.
#
# KEYED BY AUG-17 PAPER QUESTION NUMBER (re-keyed from the Apr 20 deliverable
# by Task 2.5). An INT key applies to the whole question family -- the base and
# its "N.1"/"N.2" sub-questions; a "N.M" STRING key overrides that family
# default for one sub-question, and may be None to say the sub-question carries
# no instruction of its own. The intro attaches once to the first Q<n>_* item;
# the instruction (blue Instruction style) to every Q<n>_* item except
# other-specify *_TXT fields. Paper-only navigation notes (<proceed to Qx>) are
# omitted -- CAPI logic automates the routing. English-only, like the consent
# override.
#
# Provenance is recorded because the Apr-20 numbering COLLIDES with real Aug-17
# questions -- an unremapped key does not fail, it silently attaches the wrong
# note to the wrong screen. 75 of these rows are the instruction the Aug-17
# paper itself prints at that question (instruments-aug17-extract/F1-extract.md);
# 31 are the Apr-20 instruction carried to the renamed question where the Aug-17
# paper prints none. Where the two disagree the paper wins, with the two stated
# exceptions marked at their rows (52, 148).
# ------------------------------------------------------------------
_READ_ONE = "READ OPTIONS OUT LOUD. SELECT ONE ANSWER ONLY."
_READ_ALL = "READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_DNR_ALL = "DO NOT READ OPTIONS OUT LOUD. SELECT ALL THAT APPLY."
_DNR_UNPROMPTED = ("DO NOT READ OPTIONS OUT LOUD. SELECT ALL THE ANSWER "
                   "OPTIONS THAT THE RESPONDENT GIVES WITHOUT PROMPTING.")
# RETIRED by #1303 (UAT R7, 2026-08-20) — the Apr-20 probe guide. Kept here,
# unused, as the record of what the two-step battery bases used to display:
#   "DO NOT READ OPTIONS OUT LOUD. USE THE FOLLOWING GUIDE QUESTIONS TO PROBE.
#    Has this been implemented? / Do you have this? Was this implemented before
#    or after 2019? Was this implemented because of UHC? Do you plan to
#    implement it in the next 1-2 years?"
# The Aug-17 redesign turned the last three guide questions into the "N.1"
# attribution question's own stem and options, so showing this on the base
# screen asked the next screen's question a screen early.
# New at Aug-17: the two-step split gives every "N.1" attribution probe its own
# screen, and the paper prints this bare form on them -- no "READ OPTIONS OUT
# LOUD", because the enumerator is classifying an answer already given.
_SELECT_ONE = "SELECT ONE ANSWER ONLY."

INSTRUCTIONS = {
    # The 23 two-step battery BASES carry NO note.
    #
    # #1303 (UAT R7, 2026-08-20) — ASPSI's answer to the question this build
    # parked on the clarification list (item 2.5). These bases used to show the
    # Apr-20 probe guide (_PROBE, now retired below), which was carried forward
    # through the Aug-17 migration pending a ruling. The reviewers' point is
    # exactly the one the list raised: the redesign SPLIT each item into a plain
    # Yes/No base plus its own "N.1" attribution question, and that question now
    # asks outright what the guide told the enumerator to probe for — "was it a
    # result of the UHC Act enacted in 2019?", with "planned within the next 1-2
    # years" sitting in its option list. So the guide restated, on the base
    # screen, the very question the next screen asks. The Aug-17 paper prints no
    # note on these bases either, so bare is also the faithful rendering.
    #
    # Explicit None rather than an absent key: an absent key falls through to the
    # family default and would put some other note back on them (the same reason
    # the "N.2" family below is pinned to None).
    **dict.fromkeys([11, 14, 15, 16, 17, 18, 19, 20, 26, 27, 28, 29, 31, 32,
                     33, 34, 35], None),
    # The attribution probes. 10.1 is the one question the paper omits it on;
    # its text is identical to the other 22, so leaving it bare would be a
    # defect rather than fidelity.
    **dict.fromkeys(["10.1", "11.1", "12.1", "13.1", "14.1", "15.1", "16.1",
                     "17.1", "18.1", "19.1", "20.1", "24.1", "25.1", "26.1",
                     "27.1", "28.1", "29.1", "30.1", "31.1", "32.1", "33.1",
                     "34.1", "35.1"], _SELECT_ONE),
    # 148 keeps SELECT ONE against the paper's SELECT ALL: the paper prints a
    # 5-point satisfaction scale as a tick-all list, the dictionary is SELECT
    # ONE (registered divergence), and telling the enumerator to multi-select a
    # single-select field is the worse of the two errors.
    **dict.fromkeys(["12.2", "13.2", 21, 47, 82, 90, 97, 144, 145, 148], _READ_ONE),
    **dict.fromkeys([23, 40, 62, 63, 65, 66, 86, 91, 92, 98, 108, 124, 127,
                     133, 134, 136, 143, 146, 150, 152, 153], _READ_ALL),
    **dict.fromkeys([51, 53, 54, 55, 56, 57, 58, 59, 60, 61, 81, 83, 85, 104,
                     109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119,
                     120, 121, 138, 149], _DNR_ALL),
    **dict.fromkeys([36, 37], _DNR_UNPROMPTED),
    # The "N.2" detail questions under a _PROBE base. None, not absent: an
    # absent key falls through to the family default and would put the probe
    # guide on "what are the new roles/departments/rooms", which the Apr-20
    # build never did and the paper does not ask for.
    **dict.fromkeys(["14.2", "15.2", "16.2", "17.2", "18.2", "19.2", "35.2"], None),
    # 30's Apr-20 note also carried the ward-allocation definition. That text is
    # now printed inside Q30.1's own stem, so it is already in the dcf label and
    # repeating it here would show it twice on adjacent screens -- the #1189
    # lesson. The probe guide that remained is retired with the rest (#1303), so
    # Q30's base is now bare like its 22 siblings.
    30: None,
    # #1109: the capitation definition. #1011 stripped it OUT of the question text
    # (testers: it is the paper's italic enumerator note, not part of the spoken
    # question) but nothing put it back anywhere, so it was simply lost - the
    # enumerator had no definition at all. #1109 asks for it as a blue note, which
    # is what this class is. Wording verbatim from the paper; only the outer
    # parentheses are dropped, since they existed to set it off INSIDE the question
    # and every other note here reads as a plain sentence.
    44: ("Capitation is the amount per year per registered patient for delivering "
         "the YAKAP/Konsulta package services."),
    45: ("Performance indicators are the defined set of healthcare goods and "
         "services to be provided for each enrolled patient to receive the "
         "full capitation payment. DO NOT READ OPTIONS OUT LOUD. SELECT ALL "
         "THE ANSWER OPTIONS THAT THE RESPONDENT GIVES WITHOUT PROMPTING. "
         "RESPONDENT MAY NOT BE ALLOWED TO LOOK FOR REFERENCE PRIOR TO "
         "ANSWERING THIS QUESTION."),
    # The paper prints this definition AND the read-aloud note at 52; the note
    # extractor only captures the latter, so this row stays hand-held.
    52: ("These are the requirements for YAKAP/Konsulta accreditation "
         "outlined by DOH. " + _READ_ALL),
    142: ("Our focus is specifically on referrals external to the facility, "
          "excluding internal referrals. " + _READ_ALL),
}

# Section starts re-anchored to Aug-17 (Apr-20 51/101/118/135/163 ->
# 38/88/105/122/150). Confirmed twice over: through maps/F1-renames.csv, and
# independently against the first question number after each section header in
# normalized/F1-paper.csv.
SECTION_INTROS = {
    1: "We would like to ask some of your personal information relevant to the survey.",
    7: "Next, we will be asking questions about this health facility.",
    9: ("We will now ask about your awareness of UHC, the changes that have "
        "been implemented in this facility since the UHC Act was passed in "
        "2019 and if these changes were a result of the UHC Act."),
    38: ("The next questions we will ask relate to the YAKAP/Konsulta "
         "package. Please answer to the best of your knowledge. You may "
         "answer “I don't know” if you are unsure."),
    88: "We will now ask questions related to BUCAS center and GAMOT package.",
    105: "We will now ask you about your facility’s experience with the licensing process.",
    122: ("The next set of questions covers the service delivery process. "
          "This section covers the implementation of NBB and ZBB, LGU "
          "support, and the Referral System."),
    150: "We will now proceed to the last section of this survey, which focuses on human resources.",
}

_QNUM = re.compile(r"^Q(\d{1,3})_")
# "Q12_1_UHC_ATTRIB" -> sub-question "12.1". The second group matches a SINGLE
# digit followed by another underscore, so an ordinary stem is never mistaken
# for a sub-question number.
_SUBNUM = re.compile(r"^Q(\d{1,3})_(\d)_")


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def question_extras(nm, intro_used):
    """(intro_english, instruction_english) for an item — TEXT, not HTML.

    This used to return finished HTML, and main() called it once per ITEM, outside the
    per-language loop. The English note was therefore pasted into every locale (#1216,
    #1219, #1220, #1223, #1224, #1225). Returning the English source text lets the caller
    resolve it per language via note_html(); the intro-consumed bookkeeping still happens
    exactly once per item, which is why that stays here.
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
    # Sub-question first, then the question family. A "N.M" row that is
    # present-but-None deliberately blanks the family default for that one
    # sub-question, which is why this tests membership rather than truthiness.
    sm = _SUBNUM.match(nm)
    subkey = f"{sm.group(1)}.{sm.group(2)}" if sm else None
    if subkey is not None and subkey in INSTRUCTIONS:
        instr = INSTRUCTIONS[subkey]
    else:
        instr = INSTRUCTIONS.get(q)
    if not instr or nm.endswith("_TXT"):
        instr = None
    return intro, instr


def note_html(intro_en, instr_en, lang):
    """Render the two notes in ONE language. Missing translation -> English, which is
    what the tablet shows today, so a miss is never a regression."""
    pre = f"<p>{_esc(translate_note(intro_en, lang))}</p>" if intro_en else ""
    post = (f'<p class="instruction">{_esc(translate_note(instr_en, lang))}</p>'
            if instr_en else "")
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
                intro_en, instr_en = ((None, None) if ov
                                      else question_extras(nm, intro_used))
                lines += [f"  - name: {dict_name}.{nm}", "    conditions:", "      - questionText:"]
                for lnm, _ in langs:
                    raw = labmap.get(lnm) or en
                    txt = _html(raw)
                    # EN (or a locale falling back to it). _TXT specify-box prompts are
                    # excluded, matching how question_extras() skips them for instructions -
                    # the emphasis belongs on the question, not its follow-up specify field.
                    if raw == en and not nm.endswith("_TXT"):
                        txt = _emphasize(txt)
                    # resolved PER LANGUAGE - see note_html()
                    pre, post = note_html(intro_en, instr_en, lnm)
                    body = ov or (pre + txt + post)
                    # #1306: unnumbered field -> its caption already prints this exact
                    # label, so the question pane would echo it. Keep any real intro or
                    # instruction, drop the echo.
                    if not ov and _cap_dup(nm, en, _SHORT.get(nm)):
                        body = pre + post
                    lines += [f"          {lnm}: |", f"            {body}"]
                n += 1
    lines.append("...")
    OUT.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({n} questions x {len(langs)} languages)")


if __name__ == "__main__":
    main()
