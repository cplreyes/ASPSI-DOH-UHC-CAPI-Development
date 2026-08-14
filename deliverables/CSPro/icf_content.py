#!/usr/bin/env python3
"""Informed Consent Form (ICF) read-aloud screens — shared across F1 / F3 / F4.

Source of truth: "Suggested Layout (CSEntry).docx" (Shan, via Aly, 2026-08-13). The
layout specifies THREE instrument variants, each split across TWO read-aloud screens,
with the brand logo strip at the top and the PSA/SJREB clearance block at the bottom
of both screens. There is no Yes/No control anywhere in the layout, so nothing here
captures a consent decision — CONSENT_GIVEN stayed removed (2026-06-12); refusal is
recorded through the interview-status / BREAKOFF path as before.

This SUPERSEDES the Annex H script that each generate_qsf.py still carries as
CONSENT_HTML (unused since 2026-06-12). The wording differs materially — Annex H opens
"Hello, my name is ___ (data collector's name). I work for ...", this opens "We work
for ..." — and adds a per-instrument sentence listing what the questionnaire covers.

English-only, matching every other read-aloud block in the instruments: ASPSI has not
delivered SJREB-approved ICF translations, and authoring them here is out of bounds.
When they arrive they attach the same way question-text translations do.

Verbatim from the layout except for one correction: the layout's clearance line reads
"PSA SSRCS Clearnce No." (missing the 'a'). The deployed cover footer has always said
"Clearance" and that is the correct spelling of the PSA instrument, so the typo is not
propagated.
"""

# PSA SSRCS clearance number per instrument (the suffix identifies the questionnaire
# in the PSA table): -01 Facility Head, -03 In-Patient and Out-Patient, -04 Household.
CLEARANCE_NO = {"F1": "DOH-2651-01", "F3": "DOH-2651-03", "F4": "DOH-2651-04"}

# Screen 1 = who we are + what the study is + what this questionnaire covers + the ask.
# Screen 2 = privacy + risks/benefits + voluntariness + "any questions?".
SCREENS = {
    "F1": (
        [
            "We work for Asian Social Project Services, Inc. (ASPSI).  We are here to "
            "invite you to participate in a study about the Universal Health Care (UHC) "
            "and packages of programs like Yaman ng Kalusugan Program (YAKAP), No Balance "
            "Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory "
            "Services (BUCAS), and Guaranteed and Accessible Medications for Outpatient "
            "Treatment (GAMOT). The Department of Health funded this study. Please let me "
            "tell you more about the study.",

            "This study aims to generate evidence on the overall experience of the general "
            "public to support continuous monitoring, evaluation, and learning of the "
            "implementation of the UHC Act and its Implementing Rules and Regulations "
            "(IRR). The questions for this survey cover facility/facility head profile, "
            "UHC implementation changes since 2019, specialized programs (YAKAP/Konsulta, "
            "NBB/ZBB, BUCAS, GAMOT), DOH licensing, PhilHealth accreditation, NBB/ZBB "
            "policies, referral systems, human resource challenges, and secondary data "
            "such as hospital census and staffing statistics.",

            "Would you like to participate as a respondent in the study? The interview may "
            "last for more or less than an hour.",
        ],
        [
            "We are committed to protecting your privacy. If you choose to participate, we "
            "will never include your name in information shared with the government or in "
            "any reports. Your name will be kept separately from your answers in a private, "
            "secure location. For this interview, it is also important to respect other "
            "people’s privacy and not tell anyone else what we talked about today. With "
            "all research, there’s a small chance that someone else might get to see your "
            "data. We try our best to prevent that, but if it happens, we’ll tell you as "
            "soon as possible.",

            "Aside from this, there are no other risks to you if you take part in this "
            "study. As a benefit of the research, the knowledge gained may help the "
            "government and DOH better support your healthcare needs. You are free to "
            "decline participation or to stop at any time. Choosing not to participate will "
            "not result in any penalty, and you will not have to pay anything to take part "
            "in this study.",

            "Do you have any questions about the study or about what I have told you?",
        ],
    ),
    "F3": (
        [
            "We work for Asian Social Project Services, Inc. (ASPSI).  We are here to ask "
            "you to participate in a study about the Universal Health Care (UHC) and "
            "packages of programs like Yaman ng Kalusugan Program (YAKAP), No Balance "
            "Billing (NBB), Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory "
            "Services (BUCAS) centers, and Guaranteed and Accessible Medications for "
            "Outpatient Treatment (GAMOT). The Department of Health (DOH) funded this "
            "study. Please let me tell you more about the study.",

            "This study aims to generate evidence on the overall experience of the general "
            "public to support continuous monitoring, evaluation, and learning of the "
            "implementation of the UHC Act and its Implementing Rules and Regulations "
            "(IRR). The questions will cover your Patient Profile, awareness of UHC and "
            "PhilHealth registration, primary care usage, health-seeking behaviors, "
            "specific experiences during your visit, medical costs and payment sources, "
            "specialized programs (YAKAP/Konsulta, BUCAS, GAMOT, NBB, ZBB, and MAIFIP), "
            "access to medicines, and the referral experiences.",

            "Would you like to participate as a respondent in the study? The interview may "
            "last for more or less than an hour.",
        ],
        [
            "We are committed to protecting your privacy. If you choose to participate, we "
            "will never share your family’s or other household members’ personal "
            "information outside of the study team. We will never include your name in "
            "information shared with the government or in any reports. Your name will be "
            "kept separately from your answers in a private, secure location. For this "
            "interview, it is also important to respect other people’s privacy and not tell "
            "anyone else what we talked about today. With all research, there’s a small "
            "chance that someone else might get to see your data. We try our best to "
            "prevent that, but if it happens, we’ll tell you as soon as possible.",

            "Aside from this, there are no other risks to you if you take part in this "
            "study. As a benefit of the research, the knowledge gained may help the "
            "government and DOH better support your healthcare needs. We shall also provide "
            "Php 100 as a token of appreciation for the time you’ve shared with us.",

            "Nothing bad will happen if you do not want to be in this study. You can decide "
            "to stop being in the study at any time. You will never have to pay anything to "
            "be in the study.",

            "Do you have any questions about the study or about what I have told you?",
        ],
    ),
    "F4": (
        [
            "We work for Asian Social Project Services, Inc. (ASPSI). We are here to ask you "
            "to participate in a study about the Universal Health Care (UHC) and packages of "
            "programs like Yaman ng Kalusugan Program (YAKAP), No Balance Billing (NBB), "
            "Zero Balance Billing (ZBB), Bagong Urgent Care and Ambulatory Services (BUCAS) "
            "center, and Guaranteed and Accessible Medications for Outpatient Treatment "
            "(GAMOT). The Department of Health funded this study. Please let me tell you "
            "more about the study.",

            "This study aims to generate evidence on the overall experience of the general "
            "public to support continuous monitoring, evaluation, and learning of the "
            "implementation of the UHC Act and its Implementing Rules and Regulations "
            "(IRR). The questions will cover your household profiles, awareness and use of "
            "UHC programs like YAKAP/Konsulta, BUCAS, GAMOT, NBB, and ZBB, PhilHealth "
            "registration, health-seeking behaviors, primary care usage, referral "
            "experiences, and household expenditures.",

            "Would you like to participate as a respondent in the study? The interview may "
            "last for more or less than an hour.",
        ],
        [
            "We are committed to protecting your privacy. If you choose to participate, we "
            "will never share your family’s or child’s personal information outside of the "
            "study team. We will never include your name in information shared with the "
            "government or in any reports. Your name will be kept separately from your "
            "answers in a private, secure location. For this interview, it is also important "
            "to respect other people’s privacy and not tell anyone else what we talked about "
            "today. With all research, there’s a small chance that someone else might get to "
            "see your data. We do our best to prevent that, but if it happens, we’ll let you "
            "know as soon as possible.",

            "Aside from this, there are no other risks to you if you take part in this "
            "study. As a benefit of the research, the knowledge gained may help the "
            "government and DOH better support your healthcare needs. We shall also provide "
            "Php 100 as a token of appreciation for the time you’ve shared with us.",

            "Nothing bad will happen if you do not want to be in this study. You can decide "
            "to stop the interview at any time. You will never have to pay anything to be in "
            "the study.",

            "Do you have any questions about the study or about what I have told you?",
        ],
    ),
}

# Dictionary labels for the two acknowledgment items. These are what appear in the
# codebook and as the on-form field label; the read-aloud script itself is question
# text (see build_screen_html), not a dict label — the 255-char dcf-label cap makes
# that the only workable split anyway.
ITEM_LABELS = {
    "ICF_PART1": "Informed Consent — read-aloud, screen 1 of 2 (study, coverage, the ask)",
    "ICF_PART2": "Informed Consent — read-aloud, screen 2 of 2 (privacy, risks, voluntariness)",
}

# Single-option acknowledgment: tapping it advances to the next screen. A value set is
# required because a field with no capture control is never drawn (the #1102 lesson —
# CSEntry paints entry controls, so a display-only field would leave a blank screen).
CONTINUE_OPTIONS = [("Continue", "1")]


def clearance_html(instrument):
    """The PSA/SJREB clearance block that sits at the foot of both ICF screens."""
    return ('<p class="instruction">PSA SSRCS Clearance No. '
            f'{CLEARANCE_NO[instrument]} &middot; issued July 2026 &middot; valid until '
            '31 July 2027<br/>SJREB: ICF ver. 07/25/2026 &middot; Translated '
            'Questionnaire ver. 06/05/2026</p>')


def build_screen_html(instrument, part, logo_html=""):
    """Full question-text HTML for one ICF screen (part = 1 or 2).

    Returned as a single line: the .qsf emits each language's body as one indented
    line under a `|` block scalar, so an embedded newline would corrupt the YAML.
    """
    paras = SCREENS[instrument][part - 1]
    body = "".join(f'<p class="normal">{t}</p>' for t in paras)
    return logo_html + body + clearance_html(instrument)
