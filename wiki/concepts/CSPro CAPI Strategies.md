---
type: concept
tags: [cspro, capi, design-strategy, forms, fields, partial-save]
source_count: 2
---

# CSPro CAPI Strategies

The Census Bureau's recommended design patterns for CAPI applications, as documented in the CSPro 8.0 user guide. Most are direct implications of running on a tablet in an interview context — limited screen real estate, no mouse, possible poor lighting, and an interviewer (not a keyer) at the controls.

## Forms

- **Fewer items per form than a PAPI app.** CAPI question text takes up to half the screen.
- **Break the instrument into topical sections** — earnings, fertility, etc. — and use one or more forms per section.
- **Avoid scrolling.** Scrolling forms are confusing in low-light, no-mouse interviews. Test at the actual tablet resolution.
- **Gather all household members at the start**, then loop. This minimizes accidental omissions later.
- **If a form contains a roster, only the roster should scroll** — never the whole form.

## Fields

| Property | Recommendation |
|---|---|
| Use Enter key | **On** — otherwise CSEntry auto-advances, which confuses interviewers. |
| Mirror fields | **Use them** — they show values from other forms, useful as on-screen reminders. |
| Protected fields | **Use them** for calculated/derived values. |
| Force out-of-range | **Almost always off** — interviewers should only enter valid responses. Define explicit "don't know", "refused", "not applicable" categories instead. |

CAPI applications use alphanumeric responses more freely than key-from-paper apps because the interviewer is interactive (e.g., capturing names directly).

## Questions

- **Customize question text in the top half of the entry window.** Different colored fonts can distinguish what the interviewer reads aloud (black) from instructions to the interviewer (blue). CSPro ships customizable styles for this.
- **Use fills** to substitute prior responses into question text — see [[wiki/concepts/CSPro Question Text and Fills]].
- **Conditional question text** — present different text based on prior responses (e.g., switch wording based on household size).

## Organization of the instrument

- **CAPI applications are almost always system-controlled** so logic determines the question order. See [[wiki/concepts/CSPro Data Entry Modes]].
- **Define topical sections** before sequencing forms. Begin/end sections, FAQ, household-roster sections may live outside the main interview flow (e.g., after the end-of-interview section).
- **Within a section, define question order**, place one or several related items per form, and let form sequence drive the interview sequence.

## Multi-language interviews

CSPro lets you define multiple CAPI languages and switch between them on the fly during an interview. The recommended workflow is:

1. **Finalize and test all question text in one language first.** This is the only way to avoid version-control hell.
2. **Translate after the source language is locked.** The question text editor displays two languages side-by-side; translators can copy-paste while seeing the original.
3. The interviewer switches languages from the in-app menu when arriving at a household that prefers a different language.

See [[wiki/concepts/CSPro Multi-Language Applications]] for the technical mechanism.

## Breaking off the interview / Partial save

CSPro **fully supports partial save** — a case can be saved before it is complete and resumed later. This is essential for any interview that might span multiple visits. To enable, check the Partial Save box in the data entry options dialog.

The `OnStop` global function can:
- intercept attempts to exit (Stop button, Alt+F4),
- prevent the exit conditionally (e.g., require a callback form to be filled),
- jump to a "schedule next visit" form before saving the partial case.

You can also store the field that was last entered, so the next session can jump back to that section automatically.

Very small applications (a listing operation, a short-form census) probably don't need partial save.

## Coming back later

When the interview is resumed, decide explicitly what should happen:

- Start from the beginning of the instrument?
- Resume at the field where the prior session ended?
- Walk through a front section to confirm household members and other vital info, then jump to where the prior session ended?

The Census Bureau recommends the third pattern for most household surveys.

## Prefilling values

Six ways to prefill a field:

1. **Persistent ID field** — uses the value from the prior case as the default for the new case. Initial value can come from the PFF.
2. **Auto-increment ID field** — increments the prior case's value by one. Starts at 1 if no prior case exists.
3. **PFF Key attribute** — sets initial values for the case's ID items.
4. **PFF Parameters section** — sets initial values for non-repeating, non-persistent items.
5. **Sequential repeating field** — auto-increments on each added roster occurrence.
6. **Field preproc** — set the value in code:
    ```
    PROC INTERVIEW_END_TIME
    preproc
        INTERVIEW_END_TIME = timestamp();
    ```

## Multimedia features (Android only)

| Feature | Use |
|---|---|
| **Audio** | Background or interactive audio recording. |
| **Barcode** | Scan barcode or QR code via the device camera. |
| **Camera** | Take a photo and save as an image. Use `image.takePhoto` (the older `execsystem("camera:...")` is deprecated). |
| **Signature** | Capture a signature as an image. Use `image.captureSignature` (the older `execsystem("signature:...")` is deprecated). |

A `Media Store` mechanism provides shared access to audio, image, and video content via `Media.Audio`, `Media.Images`, `Media.Video`. Listed via `Path.getDirectoryListing` or `dirlist`; selectable via `Path.selectFile`, `Path.showFileDialog`, or `System.selectDocument`. Android scoped storage may restrict listings — fall back to `System.selectDocument` when needed.

## Project relevance

- **Section organization** for F1 (Sections A–H), F3 (A–L), F4 (A–Q) maps cleanly onto this guidance — each questionnaire annex section becomes a CSPro section.
- **Partial save is mandatory for F4** — household interviews can run long, and respondents may need to break for fieldwork or meals. Enable from day one.
- **Filipino + English** — define both as CAPI languages from the start, then finalize all question text in English before commissioning the Filipino translation. (See [[wiki/concepts/CSPro Multi-Language Applications]].)
- **No "Force out-of-range"** — every "don't know", "refused", and "not applicable" response in F1/F3/F4 must be an explicit value-set entry.
- **Roster patterns** — F4's household roster should follow the "gather names first, then loop" pattern.
- **Photo / signature capture** — useful for facility consent forms and pretest documentation. Use the new `image.*` functions, not `execsystem`.

## Sources

- (Source: [[wiki/sources/Source - CSPro 8.0 Complete Users Guide]])
- (Source: [[wiki/sources/Source - CSPro Android CAPI Getting Started]])
