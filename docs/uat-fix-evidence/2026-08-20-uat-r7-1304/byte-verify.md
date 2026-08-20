# #1304 - survey title replaced on cover + ICF (F1/F3/F4)

ASPSI's ruling on #1304 was "Replace the whole line". The cover/ICF line changed from

    Universal Health Care (UHC) Survey-Year 2 - Reference Year 2026

to

    Universal Health Care (UHC) Survey 2026- Year 2

The separately-labelled reference-year element is gone; the reference year now sits
inside the title itself, which is what PSA Board Res. 01 s.2017-084 actually requires.

The "2026- Year 2" spacing (space BEFORE the hyphen, none after) is ASPSI's own and is
reproduced verbatim. It was flagged as a possible typo on the ticket and not amended.

## Scope correction

An earlier comment on #1304 said this line also appears in the F2 PWA masthead. It does
not. The F2 masthead renders only the two clearance lines (PSA SSRCS + SJREB); its title
strings are separate ("UHC Survey Y2 - Healthcare Worker Survey Questionnaire") and were
not part of ASPSI's request. #1304 is CSPro-only: one constant in icf_content.py feeding
3 instruments x (cover + 2 ICF screens) x 8 locales = 72 render sites.

## Verification

Source change: icf_content.py SURVEY_TITLE_HTML (single definition, consumed by
clearance_html()).

Isolation A/B: F1's .qsf was re-rendered with the OLD constant and diffed against the
new build as a line multiset. Exactly 24 lines differ, and all 24 contain the survey
title. Nothing else in the file moved. (The re-render was then reverted and asserted
byte-identical to the live build, so the check could not pass on a bad restore.)

Gates: verify_questions F1 321/321, F3 375/375, F4 333/333 all PASS (reachable,
0 dead-conditions, 0 bad-skips) - counts unchanged from before the edit.
preflight_validate: ALL CLEAN. csentry_verify: F1/F3/F4 PASS.
Designer compile: F1 11:53:25, F3 11:54:20, F4 11:55:13 - "Compile Successful",
title bar checked on each shot.

Served-package byte-verify (pulled from CSWeb, .pen bz2-decompressed, searched as
raw utf-16-le bytes - never whole-blob decoded):

    F1  12 entries  8 psgc  new title x24  old title 0  "Reference Year" 0  clearance x24  v3.1.3
    F3  12 entries  8 psgc  new title x24  old title 0  "Reference Year" 0  clearance x24  v4.1.1
    F4  13 entries  8 psgc  new title x24  old title 0  "Reference Year" 0  clearance x24  v3.1.1

(F4's 13th entry is review.html, which it ships for the Section N recap dialog.)

## Tablet evidence (Tier 1 - itel P10001L, real device)

The three PNGs here are the DEPLOYED packages: the served .zip was pulled from CSWeb and
sideloaded into labelled evidence folders (R7-F<n>-EVI), so the screenshots prove the
build testers will download. The testers' own installed app folders were not touched.

csentry-app-list.png also records the fleet-propagation gap: the installed
Facility Head / Household / Patient apps on this tablet still read v1.1.4 / v1.4.4 /
v1.1.5 (2026-07-19). Those need remove + re-add to pick up the current builds.
