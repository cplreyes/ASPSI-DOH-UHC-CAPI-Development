---
type: source-summary
source: "[[raw/Project Deliverable 1/Annex F2_Healthcare Worker Survey Questionnaire_UHC Year 2_April 08.pdf]]"
date_ingested: 2026-04-09
tags: [questionnaire, healthcare-worker, f2, survey-instrument]
---

# Source — Annex F2: Healthcare Worker Survey Questionnaire

Healthcare Worker Survey Questionnaire for [[wiki/concepts/UHC Survey Year 2|UHC Survey Year 2]], 14 pages. Self-administered via online forms (Google Forms) or paper in areas with unstable connectivity.

## Structure

| Section | Topic | Key Data Collected |
|---|---|---|
| **A. Healthcare Worker Profile** | Respondent demographics | Personal info, profession, employment status, tenure |
| **B. UHC Awareness** | UHC knowledge | Awareness of UHC Act, understanding of key provisions |
| **C. YAKAP/Konsulta Package** | PhilHealth program knowledge | Awareness and understanding of YAKAP/Konsulta benefits |
| **D. NBB and ZBB Awareness** | Billing program knowledge | No Balance Billing and Zero Balance Billing awareness |
| **E. Expanded Health Programs** | BUCAS and GAMOT | Awareness of expanded programs |
| **F. Referrals and Satisfaction** | Referral system | Outbound/inbound referral experiences, satisfaction |
| **G. KAP on Professional Setting** | Charging and reimbursement | Knowledge, attitudes, practices on professional fees and PhilHealth reimbursement |
| **H. Task Sharing** | Workload distribution | Task sharing practices, willingness, barriers |
| **I. Facility Support** | Institutional support | Equipment, supplies, infrastructure support received |
| **J. Job Satisfaction** | Worker satisfaction | Compensation, professional development, working conditions |

## Skip Logic Notes

- Pharmacist/assistant pharmacist respondents have special routing (e.g., skip to Section E2 or Section F).
- Multiple "select all that apply" questions throughout.

## CAPI Development Notes

- Shortest of the four instruments (14 pages).
- Self-administered mode means the CAPI interface must be user-friendly for respondents who may not be familiar with tablets — **or** this module uses Google Forms instead of CSPro.
- The Inception Report specifies F2 as self-administered (Google Forms/paper), so CSPro CAPI may not be needed for this module. Clarify with team.

## Sources

- Part of Deliverable 1 submitted to [[wiki/entities/DOH-PMSMD|DOH-PMSMD]]
- Developed by [[wiki/entities/ASPSI|ASPSI]] consultant team
