# 1306 / 1307 / 1309 - repeating text on unnumbered fields

## What the testers saw

Every field on the administrative forms printed its label TWICE on one screen:
"Respondent name and signature" above "Respondent name and signature" above the box.
Reported for F1 (#1306), F4 (#1307) and F3 (#1309); the forms named in all three
tickets are the same class - Field Control, Health Facility / FC Geographic ID,
Respondent name block, Patient Type, Closing Case, Case Verification Photo.

## Root cause

CSEntry paints the qsf QUESTION TEXT and the field's on-form [Text] CAPTION on the
same screen. cspro_helpers.question_caption() classifies a field with no question
number and no designed short caption as kind "keep-full" - its caption is the label
VERBATIM. Such a field also has no qsf override, so its question text is that same
label. Hence the doubling. Numbered fields were never affected: their caption is the
numeral tag ("1.") and the question text is the full question, which is the R25 design.

The helper's own docstring already anticipated this: it lists "an UNNUMBERED field
whose label is a full-sentence question, which would otherwise keep a caption identical
to its qsf text" as a reason to supply a short caption.

## Fix

New cspro_helpers.caption_duplicates_question(). Each instrument's generate_qsf now
drops the echoed label from the QUESTION PANE for those fields, keeping any genuine
intro/instruction text.

The caption is kept, NOT the question text. The left-hand section navigator renders
captions, so blanking those instead would have left the navigator full of empty rows.

Fields with a designed SHORT_FORM_LABELS caption are untouched - their caption is the
short form and their question text is the full label, so nothing was duplicated. Each
generator imports its OWN instrument's map rather than assuming.

## Scope, measured not guessed

F1  39 of 320 question entries de-duplicated
F3  48 of 374
F4  45 of 325
Numbered questions wrongly blanked: ZERO in all three.
Cover screen (logos + clearance, 122 KB) and both ICF consent scripts are untouched -
they carry qsf overrides, so their text differs from the caption.

## Verification

verify_questions F1 321/321, F3 375/375, F4 333/333 PASS - preflight ALL CLEAN
Designer compile Successful for all three, title bars checked
Served packages: F1 12 entries/8 PSGC v3.1.4, F3 12/8 v6.0.1, F4 13/8 v3.1.2;
caption text still present in each, question pane blank for the sampled offender.

## Evidence

BEFORE-tester-f1-doubled.png  the tester's own capture on v3.1.3 - every Section A
                              field printed twice
AFTER-F1-v3.1.4-single.png    same instrument on v3.1.4, Health Facility and Geographic
                              Identification form: "Classification" renders ONCE, and
                              the navigator still shows full field captions
