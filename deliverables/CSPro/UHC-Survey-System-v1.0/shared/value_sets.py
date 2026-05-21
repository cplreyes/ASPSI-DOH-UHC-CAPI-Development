"""value_sets.py — common CSPro value sets + the NA-code convention.

Shared option lists reused across the F1/F3/F4 dictionary generators. Each
entry is a ``(label, code)`` tuple; the writer primitives in ``cspro_helpers``
turn them into CSPro value-set objects.

NA-code convention (this engagement): "Not applicable" = the highest value at
the field width — 9 (width 1), 99 (width 2), 999 (width 3). This is NOT the
DHS 7/97 convention. See ``na_code()`` below.
"""

from __future__ import annotations


# ---- Dichotomous + small categorical sets ----------------------------------

YES_NO = [
    ("Yes", "1"),
    ("No",  "2"),
]

YES_NO_DK = [
    ("Yes",          "1"),
    ("No",           "2"),
    ("I don't know", "3"),
]

YES_NO_NA = [
    ("Yes",            "1"),
    ("No",             "2"),
    ("Not applicable", "9"),
]

SEX = [
    ("Male",   "1"),
    ("Female", "2"),
]


# ---- UHC9 — 9-option pattern for all UHC Act implementation questions -------
# Codes 1-9 are load-bearing for skip logic ("if in 5..9 then skip").

UHC9_OPTIONS = [
    ("Yes, this was implemented as a direct result of the UHC Act",                          "1"),
    ("Yes, this was pre-existing, but it has significantly improved due to the UHC Act",      "2"),
    ("Yes, this has been implemented or improved recently, but not due to the UHC Act",       "3"),
    ("Yes, other reason (specify)",                                                          "4"),
    ("No, this has not been implemented yet, but we plan to in the next 1-2 years",           "5"),
    ("No, and we have no plans to do this in the next 1-2 years",                            "6"),
    ("No, other reason (specify)",                                                           "7"),
    ("I don't know",                                                                         "8"),
    ("Not applicable",                                                                       "9"),
]

FREQUENCY = [
    ("Weekly",          "1"),
    ("Monthly",         "2"),
    ("Quarterly",       "3"),
    ("Semi-annually",   "4"),
    ("Annually",        "5"),
    ("Other (specify)", "6"),
]

WHY_DIFF_OPTIONS = [
    ("Not enough budget / too expensive",  "1"),
    ("Time-consuming",                     "2"),
    ("Limited human resources",            "3"),
    ("Legal processes",                    "4"),
    ("Compiling documentary requirements", "5"),
    ("Stringent standards",                "6"),
    ("Lack of training",                   "7"),
    ("Lack of space",                      "8"),
    ("Other (specify)",                    "9"),
]

SATISFACTION_5PT = [
    ("Very Satisfied",                     "1"),
    ("Satisfied",                          "2"),
    ("Neither Satisfied nor Dissatisfied", "3"),
    ("Dissatisfied",                       "4"),
    ("Very Dissatisfied",                  "5"),
    ("Not applicable",                     "9"),
]

ENUM_RESULT_OPTIONS = [
    ("Completed",  "1"),
    ("Postponed",  "2"),
    ("Refused",    "3"),
    ("Incomplete", "4"),
]


# ---- AAPOR final disposition codes -----------------------------------------
# AAPOR Standard Definitions 10th ed. (2023), adapted for in-person CAPI health
# surveys. 3-digit numeric (zero-filled); AAPOR decimals mapped to integers
# (x100). "000 — In Progress" is an ASPSI-internal sentinel set at case start
# by FIELD_CONTROL.preproc and rewritten to the final code on the closing form.

AAPOR_DISPOSITION_OPTIONS = [
    ("000 — In Progress (initial)",                     "000"),
    ("110 — Complete interview",                        "110"),
    ("120 — Partial interview / break-off",             "120"),
    ("210 — Refusal — respondent",                      "210"),
    ("211 — Refusal — gatekeeper / household",          "211"),
    ("220 — Non-contact — respondent unavailable",      "220"),
    ("230 — Other eligible non-interview",              "230"),
    ("310 — Unknown eligibility — facility/household",  "310"),
    ("320 — Unknown eligibility — respondent",          "320"),
    ("410 — Not eligible — out of sample / ineligible", "410"),
    ("450 — Not eligible — other",                      "450"),
]


# ---- NA-code helper --------------------------------------------------------

def na_code(width: int) -> str:
    """Return the "Not applicable" sentinel for a numeric field of ``width``.

    NA = the highest value at the field width: 9 (w1), 99 (w2), 999 (w3), ...
    This is the convention adopted for this engagement (not DHS 7/97).
    """
    if width < 1:
        raise ValueError("width must be >= 1")
    return "9" * width
