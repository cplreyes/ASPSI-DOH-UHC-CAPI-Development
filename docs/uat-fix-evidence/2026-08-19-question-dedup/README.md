# Question de-duplication (R25) — F3 fix evidence, 2026-08-19

**Ticket driver:** PSA/DOH review comment — a question must not appear twice on one screen.
**Ruling:** R25 (Carl-approved). **Task:** C1. **Ships as:** F3 v4.0.1, F4 v3.0.2 (F1 v3.0.1 follows).

## What was wrong

CSEntry renders two panes: the CAPI question pane, built from the `.qsf` and correctly
language-following, and the form, where every field carried an fmf `Text=` caption derived from
the dictionary label — the full **English** question stem. So the question printed twice in
English, and in a dialect the translated question printed above the full English one.

Measured across the whole instrument before the change: **309 of F3's 364** on-form captions
reproduced their own qsf question text (F4 269/322, F1 280/308).

## What changed

Question fields' on-form captions are now short numeral tags (`1.`, `2.`, `48.1.`). The question
itself lives only in the qsf pane, which follows the selected language. Two conventions handle
the cases a bare numeral cannot: specify boxes read `2. (specify)`, and where one question is
split across two fields on one screen the tag names them (`5. Month` / `5. Year`).

**Dictionary labels are untouched** — exported data, the published codebook, the case tree and
the CSWeb case view all keep the full labels.

## The screenshots

Same screen (F3, consent form, field Q1_IS_PATIENT), before and after, in English and Waray.

| file | what it shows |
|---|---|
| `BEFORE-F3-EN-q1-consent-form.png` | The question "1. Before we begin, to confirm, are you the patient?" appears **three times** on one screen: the top question banner, the form row, and the value-set box. Rows below repeat the same pattern for Q2 and Q3. |
| `AFTER-F3-EN-q1-consent-form.png` | Same screen. The question appears **once**, in the banner. Form rows read `1.`, `2.`, `2. (specify)`, `3.` |
| `BEFORE-F3-WAR-q1-consent-form.png` | Waray. The translated question is in the banner, and the **full English question sits directly beneath it** in the form row — the dialect case of the same defect. |
| `AFTER-F3-WAR-q1-consent-form.png` | Waray. Only the Waray question, once. No English question text on the screen at all. |

The two "Informed Consent — read-aloud, screen 1/2 of 2" rows keep their full captions in both
after-shots. That is deliberate: those captions are descriptive labels for the read-aloud
screens, not the consent text itself, so they duplicate nothing.

## Byte-verify

`byte-verify.txt` — run against the exact files CSDeploy packaged, on raw bytes rather than a
parsed model, so it proves what shipped rather than what the generator believes it emitted:

- the old full-stem caption is **absent** from the served `.fmf`
- the numeral tag is **present**
- the `.qsf` question text is **intact** (the question still exists to be read aloud)

It also covers the folded line-separator fix (board task #16): F3's generated `.fmf` carried
7,276 `\r\r\n` sequences, which the capture-type pass then doubled into 14,552 CRLF in the bound
file — a blank line after every line, at twice the size. All three instruments now sit at a
clean 1:1 CRLF-to-line ratio (F1 6,211, F3 7,276, F4 6,747).

## Gates run

`preflight_validate` ALL CLEAN · `fmf_block_check` OK · `verify_questions` F3 375/375, F4 333/333
reachable, PASS · `skip_boundary_check` OK (pre-existing waivers unchanged) · `csentry_verify`
PASS (CSEntry recompiles the logic on launch — the trustworthy compile gate) · Tier-1
`aug17_diff` F3 and F4 both PASS with 0 unregistered divergences · `r25_caption_check` PASS
(0 fields without a qsf prompt, 0 same-screen caption collisions).

## Still open

Server-side byte-verify of the deployed package on CSWeb was **not run** — SSH is blocked by the
auto-mode classifier, the same block hit on the F3 v4.0.0 and F1 v3.0.0 deploys. Commands are
handed off in the task report. Tablet evidence is a separate parked pass (board task #18).
