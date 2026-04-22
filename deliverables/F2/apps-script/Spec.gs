/**
 * F2 Spec — 124 actual items (numbered Q1..Q125 with Q108 as a PDF numbering gap),
 * verbatim labels per project rule.
 *
 * Source: deliverables/F2/F2-Spec.md (Apr 20, 2026 PDF rev).
 * Routing: deliverables/F2/F2-Skip-Logic.md (Apr 20 rev).
 * Validation: deliverables/F2/F2-Validation.md (Apr 20 rev).
 * Cross-field: deliverables/F2/F2-Cross-Field.md (Apr 20 rev).
 *
 * Supersedes: draft-2026-04-15 (April 8 PDF, 114 items).
 *
 * Apr 08 → Apr 20 deltas baked in here:
 *   - Section B: +4 new UHC-implementation items (Q21 DOH licensing, Q22 PhilHealth
 *     accreditation, Q23 service delivery, Q24 primary care quality).
 *   - Section B: Q25 is a multi-select filter; Q26–Q30 are gated on Q25 selections
 *     (Forms cannot gate grid rows on multi-select — handled in POST, see GATE-06).
 *   - Section D: +Q47 ZBB challenges (gated on Q44 = Yes).
 *   - Section E1: +Q50 BUCAS utilization factors, +Q51 BUCAS efficacy opinion.
 *   - Section G: three ZBB/NBB sibling pairs — Q69/Q70 implications, Q75/Q76 fairness
 *     scales, Q87/Q88 balance billing — replacing Apr 08's ZBB-with-.1-NBB pattern.
 *   - Section J: grid-lift shifted from Q103 → Q114 (standalone single so Q122
 *     skip-if-Never survives); Q108 is a PDF numbering gap (no item emitted).
 *   - Terminal branch driver: Q123 (was Q112).
 *
 * Sections use section IDs (SEC-A, SEC-B, ..., SEC-END) as routing keys.
 * Items with `branchTo: {choice: sectionId}` must be the last item of their
 * section for Forms' per-answer navigation to work. See FormBuilder.wireRouting_.
 *
 * Rule of thumb: one branching question = one dedicated section ending with
 * that question. Everything else groups within the same section.
 */

// ---------- shared choice sets ----------

var UHC_CHANGE_CHOICES = [
  'Yes, this was implemented as a direct result of the UHC Act',
  'Yes, this was pre-existing, but it has significantly improved due to the UHC Act',
  'Yes, this has been implemented or improved recently, but not due to the UHC Act',
  'Yes, specify other reason',
  'No, this has not been implemented yet, but we plan to in the next 1-2 years',
  'No, and we have no plans to do this in the next 1-2 years',
  'No, specify other reason',
  'I don’t know'
];

var INFO_SOURCE_CHOICES = [
  'News', 'Legislation', 'Social Media', 'Friends/Family',
  'Health center/facility', 'LGU/Barangay', 'I don’t know', 'Other (specify)'
];

var NBB_UNDERSTANDING_CHOICES = [
  'Patient does not pay any hospital bill',
  'PhilHealth will cover cost of treatment',
  'Medicine and service are already included',
  'No cash payment required upon discharge',
  'Applies only to PhilHealth members and DOH-run hospitals',
  'Bills are settled between the hospital and PhilHealth',
  'Patients should not be charged extra fees',
  'Applies only to PhilHealth members and any public hospital',
  'Applies only to PhilHealth members and any public and private hospital',
  'I don’t know',
  'Other (Specify)'
];

var ROLE_CHOICES = [
  'Administrator','Physician/Doctor','Physician assistant','Nurse','Nursing assistant',
  'Pharmacist/Dispenser','Midwife','Laboratory technician','Medical/radiologic technologist',
  'Health promotion officer','Nutrition action officer/coordinator','Physical Therapist',
  'Dentist','Dentist aide','Barangay Health Worker','Other (specify)'
];

var SPECIALTY_CHOICES = [
  'No specialty','Anesthesia','Dermatology','Emergency Medicine','Family Medicine',
  'General Surgery','Internal Medicine','Neurology','Nuclear Medicine',
  'Obstetrics and Gynecology','Occupational Medicine','Ophthalmology','Orthopedics',
  'Otorhinolaryngology (ENT)','Pathology','Pediatrics','Physical and Rehabilitation Medicine',
  'Psychiatry','Public health','Radiology','Research','Others (specify)'
];

var EMPLOYMENT_CHOICES = [
  'Regular','Casual','Seasonal','Probationary','Project','Fixed-term','Other, specify'
];

var AGREE_5 = ['Strongly Agree','Agree','Neither Agree nor Disagree','Disagree','Strongly Disagree'];
var FREQ_5  = ['Always','Often','Sometimes','Seldom','Never'];
var CHARGE_5 = ['Never','Rarely','Sometimes','Often','Always'];
var CHANGE_DIR = ['Higher','Lower','I don’t know'];

var ZBB_CHALLENGE_CHOICES = [
  'Lack/Insufficient medicines/supplies',
  'Limited diagnostic services',
  'High patient volume/workload',
  'Documentation/compliance issues',
  'ICT/system limitations',
  'Patient-related concerns',
  'Other (specify)'
];

var BUCAS_FACTOR_CHOICES = [
  'Patient awareness',
  'Referral patterns',
  'Availability of staff/services',
  'Facility location and accessibility',
  'PhilHealth coverage and reimbursement',
  'Other (specify)'
];

var BUCAS_IMPACT_CHOICES = [
  'Improved access to care',
  'Improved quality of care',
  'Reduced patient congestion',
  'No significant impact',
  'Other (specify)'
];

var GAMOT_FACTOR_CHOICES = [
  'Availability of GAMOT medicines',
  'Patient awareness of the program',
  'Prescribing practices of physicians',
  'Pharmacy capacity',
  'PhilHealth eligibility and reimbursement processes',
  'Other (specify)'
];

var EXPECT_CHANGE_MULTI_CHOICES = [
  'Salary','Number of patients','Working hours','Standards to follow',
  'Preventative health care','Patients seek healthcare in different ways',
  'I don’t know','Other (specify)'
];

var BUCKET_CD    = 'BUCKET-CD';    // admins, doctors, nurses, midwives, dentists, nutrition/dietitian
var BUCKET_PHARM = 'BUCKET-PHARM'; // pharmacist, assistant pharmacist
var BUCKET_OTHER = 'BUCKET-OTHER';

// ---------- full spec ----------

var F2_SPEC = { sections: [

  // =============================================================
  // Cover
  // =============================================================
  { id: 'SEC-COVER', title: 'Cover — Consent and Facility Confirmation',
    description: 'Before you begin, please confirm your consent and facility details. ' +
      'This survey takes about 30 minutes (124 items). You may save and resume within 3 days.',
    items: [
      { type: 'single', label: 'I have read the information above and I consent to participate in this survey.',
        required: true, choices: ['Yes, I consent','No, I do not consent'],
        branchTo: {'Yes, I consent': 'SEC-COVER2', 'No, I do not consent': 'SEC-DECLINE'} }
    ] },

  { id: 'SEC-DECLINE', title: 'Thank you',
    description: 'Thank you for your time. Your response has been recorded as declined. ' +
                 'You may close this window.', items: [] },

  { id: 'SEC-COVER2', title: 'Facility confirmation',
    description: 'The fields below were pre-filled from your facility link. Please confirm they are correct.',
    items: [
      { type: 'text', label: 'facility_id', required: false, help: 'Pre-filled from your link.' },
      { type: 'single', label: 'Please confirm your facility type', required: true,
        choices: ['DOH-retained hospital','Public hospital (non-DOH-retained)','Private facility','RHU / Health center','Other public facility'] },
      { type: 'single', label: 'Does your facility have a BUCAS Center?', required: true,
        choices: ['Yes','No'] },
      { type: 'single', label: 'Does your facility have a GAMOT Pharmacy?', required: true,
        choices: ['Yes','No'] },
      { type: 'text', label: 'response_source', required: false,
        help: 'Auto-set by the link: self / staff_encoded / paper_mirror. Do not edit.' }
    ] },

  // =============================================================
  // Section A — Profile (Q1–Q11)
  // =============================================================
  { id: 'SEC-A', title: 'Section A — Healthcare Worker Profile',
    description: 'The following questions ask about your profile. Please put your answer/s in the space provided or check the box of your answer.',
    items: [
      { type: 'text',  label: 'Q1a. Last Name',      required: false, help: 'Optional. Used only for the raffle draw.' },
      { type: 'text',  label: 'Q1b. First Name',     required: false },
      { type: 'text',  label: 'Q1c. Middle Initial', required: false },
      { type: 'single', label: 'Q2. What type of employment do you have at this health facility?',
        required: false, choices: EMPLOYMENT_CHOICES },
      { type: 'text',  label: 'Q2.other. If "Other, specify", please specify.', required: false },
      { type: 'single', label: 'Q3. What is your sex at birth?',
        required: false, choices: ['Male','Female'] },
      { type: 'number', label: 'Q4. How old are you as of your last birthday (in years)?',
        required: false, min: 18, max: 80 },
      { type: 'single', label: 'Q5. What is your role at this health facility?',
        required: true, choices: ROLE_CHOICES },
      { type: 'text',  label: 'Q5.other. If "Other (specify)", please specify.', required: false },
      { type: 'single', label: 'Q6. What is your specialty, if any?',
        required: false, choices: SPECIALTY_CHOICES },
      { type: 'text',  label: 'Q6.other. If "Others (specify)", please specify.', required: false },
      { type: 'single', label: 'Q7. Do you practice at any private facility/clinic?',
        required: false, choices: ['Yes','No'] },
      { type: 'single', label: 'Q8. How do you divide your time between public and private practice? (only if you practice in both)',
        required: false,
        choices: ['I spend all of my time in private practice',
                  'I spend over half, but not all of my time in private practice',
                  'I spend my time equally in private and public practice',
                  'I spend over half, but not all of my time in public practice',
                  'I spend all of my time in public practice',
                  'I don’t know'] },
      { type: 'number', label: 'Q9a. In your current position, how many YEARS have you worked at this health facility?',
        required: false, min: 0, max: 60 },
      { type: 'number', label: 'Q9b. And how many additional MONTHS beyond whole years?',
        required: false, min: 0, max: 11 },
      { type: 'number', label: 'Q10. How many days in a week do you work at this health facility?',
        required: false, min: 1, max: 7 },
      { type: 'number', label: 'Q11. On average, how many hours do you work per day?',
        required: false, min: 1, max: 24,
        help: 'According to DOLE, typically full-time is 8 hours per day, part-time is less than that.' }
    ] },

  // =============================================================
  // Section B — UHC Awareness (Q12–Q30)
  // Apr 20: +4 new implementation items Q21–Q24; Q25 is multi filter; Q26–Q30 per-domain conditionals
  // =============================================================
  { id: 'SEC-B0', title: 'Section B — Universal Health Care (UHC) Awareness',
    description: 'The following questions ask about your awareness of UHC and the changes which may have occurred due to its implementation. Please check the box/es of your answer.',
    items: [
      { type: 'single', label: 'Q12. Have you heard about Universal Health Care (UHC) prior to this survey?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-B1', 'No': 'SEC-C-gate'} }
    ] },

  { id: 'SEC-B1', title: 'Section B — UHC implementation since 2019',
    items: [
      { type: 'single', label: 'Q13. Has the increase in equipment been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q13.other. If "Yes, specify other reason" or "No, specify other reason", please specify.', required: false },
      { type: 'paragraph', label: 'Q14. What are these pieces of equipment? (Specify the equipment)', required: false },
      { type: 'single', label: 'Q15. Has the increase in supplies been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q15.other. Please specify if "other reason".', required: false },
      { type: 'paragraph', label: 'Q16. What are these supplies? (Specify the supplies)', required: false },
      { type: 'single', label: 'Q17. Has the use of electronic medical records at the facility been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q17.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q18. Have the changes to the referral system (inbound or outbound) been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q18.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q19. Have the changes in staffing been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q19.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q20. Have the improved clinical practice guidelines been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q20.other. Please specify if "other reason".', required: false },
      // --- Apr 20 NEW items: Q21–Q24 ---
      { type: 'single', label: 'Q21. Have the DOH licensing standards been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q21.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q22. Have the PhilHealth accreditation requirements been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q22.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q23. Have the service delivery protocols been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q23.other. Please specify if "other reason".', required: false },
      { type: 'single', label: 'Q24. Have the primary care quality measures been implemented since the UHC Act was passed in 2019 and was it a result of the UHC Act?',
        required: false, choices: UHC_CHANGE_CHOICES },
      { type: 'text',   label: 'Q24.other. Please specify if "other reason".', required: false }
    ] },

  { id: 'SEC-B2', title: 'Section B — Expected changes under UHC',
    description: 'The next question asks which aspects of your work you expect to change under UHC. The follow-up grid (Q26–Q30) asks the direction of change.',
    items: [
      { type: 'multi',  label: 'Q25. Which of the following do you expect to change in your personal work as a health worker under UHC?',
        required: false, choices: EXPECT_CHANGE_MULTI_CHOICES },
      { type: 'text',   label: 'Q25.other. Please specify if "Other".', required: false },
      // Q26–Q30 per-domain direction questions. Forms cannot gate on multi-select answers, so
      // we always display these and handle Q25 × Q26–Q30 integrity in POST (see GATE-06).
      { type: 'single', label: 'Q26. How do you expect Salary to change?',
        required: false, choices: CHANGE_DIR,
        help: 'If you did not select "Salary" in Q25, choose "I don’t know".' },
      { type: 'single', label: 'Q27. How do you expect Number of patients to change?',
        required: false, choices: CHANGE_DIR,
        help: 'If you did not select "Number of patients" in Q25, choose "I don’t know".' },
      { type: 'single', label: 'Q28. How do you expect Working hours to change?',
        required: false, choices: ['Longer','Shorter','I don’t know'],
        help: 'If you did not select "Working hours" in Q25, choose "I don’t know".' },
      { type: 'single', label: 'Q29. How do you expect Standards to follow to change?',
        required: false, choices: ['More stringent','Less stringent','I don’t know'],
        help: 'If you did not select "Standards to follow" in Q25, choose "I don’t know".' },
      { type: 'single', label: 'Q30. How do you expect Preventive healthcare to change?',
        required: false, choices: ['More','Less','I don’t know'],
        help: 'If you did not select "Preventative health care" in Q25, choose "I don’t know".' }
    ] },

  // =============================================================
  // Role-bucket gate — re-ask Q5 bucket since Forms has no cross-section memory
  // =============================================================
  { id: 'SEC-C-gate', title: 'Role confirmation',
    description: 'To route you to the right questions, please confirm which group best matches your role.',
    items: [
      { type: 'single', label: 'Role group (routing)', required: true,
        choices: [
          'Administrator / Doctor / Nurse / Midwife / Dentist / Nutritionist-Dietitian',
          'Pharmacist / Dispenser / Assistant Pharmacist',
          'Other role'
        ],
        branchTo: {
          'Administrator / Doctor / Nurse / Midwife / Dentist / Nutritionist-Dietitian': 'SEC-C',
          'Pharmacist / Dispenser / Assistant Pharmacist': 'SEC-E2',
          'Other role': 'SEC-F'
        } }
    ] },

  // =============================================================
  // Section C — YAKAP/Konsulta (Q31–Q40) — BUCKET-CD only
  // Apr 20 skip-logic fix: Q36 all-answers → Q41 (skip C-tail for already-accredited)
  // =============================================================
  { id: 'SEC-C', title: 'Section C — YAKAP/Konsulta Package',
    description: 'The following questions ask about your awareness of the YAKAP/Konsulta package of PhilHealth.',
    items: [
      { type: 'single', label: 'Q31. Have you heard of the PhilHealth YAKAP/Konsulta package?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-C1', 'No': 'SEC-D'} }
    ] },

  { id: 'SEC-C1', title: 'Section C — YAKAP details',
    items: [
      { type: 'multi',  label: 'Q32. Which of the following are included in the YAKAP/Konsulta package?',
        required: false,
        choices: ['Pap smear','Mammogram','Lipid profile','Thyroid function test','Chest X-ray',
                  'Low-dose Chest CT scan','Dental services','All of the above','I don’t know'] },
      { type: 'single', label: 'Q33. Which of the following statements is true with regard to registering patients to YAKAP/Konsulta?',
        required: false,
        choices: ['It is possible to register individual patients to YAKAP/Konsulta',
                  'It is possible to register whole families to YAKAP/Konsulta',
                  'It is possible to register both individual patients and their family members together to YAKAP/Konsulta',
                  'None of the above are true',
                  'I don’t know'] },
      { type: 'single', label: 'Q34. Are you part of a health facility that is an accredited PhilHealth YAKAP/Konsulta provider?',
        required: false,
        choices: ['Yes','No','I don’t know what PhilHealth YAKAP/Konsulta package accreditation is','Other (specify)'],
        branchTo: {
          'Yes': 'SEC-C2-yes',
          'No':  'SEC-C2-no',
          'I don’t know what PhilHealth YAKAP/Konsulta package accreditation is': 'SEC-C2-no',
          'Other (specify)': 'SEC-C2-no'
        } },
      { type: 'text', label: 'Q34.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-C2-yes', title: 'Section C — Accredited provider details',
    items: [
      { type: 'date',   label: 'Q35. Since when? (accreditation start date)', required: false },
      { type: 'single', label: 'Q36. Why is your facility applying to become an accredited YAKAP/Konsulta provider?',
        required: false,
        choices: ['Predictable revenue due to capitation','YAKAP is more comprehensive',
                  'High volume of patients','Other (specify)'],
        branchTo: {
          'Predictable revenue due to capitation': 'SEC-D',
          'YAKAP is more comprehensive': 'SEC-D',
          'High volume of patients': 'SEC-D',
          'Other (specify)': 'SEC-D'
        } },
      { type: 'text',   label: 'Q36.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-C2-no', title: 'Section C — Non-accredited reasons',
    items: [
      { type: 'multi',  label: 'Q37. Why is your facility not accredited?',
        required: false, choices: ['No time','Ongoing application','Other (specify)'] },
      { type: 'text',   label: 'Q37.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-C3', title: 'Section C — Considering accreditation',
    items: [
      { type: 'single', label: 'Q38. Under UHC, there is a thrust towards primary health care. Part of this is the implementation of the YAKAP/Konsulta or primary care package. Would your facility consider becoming accredited as a YAKAP/Konsulta or primary care provider?',
        required: false, choices: ['Yes','No','Not a physician/dentist'],
        branchTo: {'Yes': 'SEC-C4', 'No': 'SEC-C5', 'Not a physician/dentist': 'SEC-D'} }
    ] },

  { id: 'SEC-C4', title: 'Section C — Reasons to consider',
    items: [
      { type: 'multi',  label: 'Q39. Why would your facility consider it?',
        required: false,
        choices: ['Predictable revenue due to capitation','YAKAP is more comprehensive',
                  'High volume of patients','Other, specify','Not a physician/dentist'] },
      { type: 'text',   label: 'Q39.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-C5', title: 'Section C — Open feedback',
    items: [
      { type: 'paragraph', label: 'Q40. What might convince your facility to become a primary care provider?', required: false }
    ] },

  // =============================================================
  // Section D — NBB/ZBB Awareness (Q41–Q47) — BUCKET-CD only
  // Apr 20: +Q47 ZBB challenges
  // =============================================================
  { id: 'SEC-D', title: 'Section D — Awareness on No Balance Billing (NBB) and Zero Balance Billing (ZBB)',
    items: [
      { type: 'single', label: 'Q41. Have you heard about the No Balance Billing (NBB)?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-D1', 'No': 'SEC-D2'} }
    ] },

  { id: 'SEC-D1', title: 'Section D — NBB details',
    items: [
      { type: 'multi', label: 'Q42. What are your sources of information about NBB?',
        required: false, choices: INFO_SOURCE_CHOICES },
      { type: 'text',  label: 'Q42.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q43. What is your understanding about the No Balance Billing (NBB)?',
        required: false, choices: NBB_UNDERSTANDING_CHOICES },
      { type: 'text',  label: 'Q43.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-D2', title: 'Section D — ZBB awareness',
    items: [
      { type: 'single', label: 'Q44. Have you heard about the Zero Balance Billing (ZBB)?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-D3', 'No': 'SEC-E1'} }
    ] },

  { id: 'SEC-D3', title: 'Section D — ZBB details',
    items: [
      { type: 'multi', label: 'Q45. What are your sources of information about ZBB?',
        required: false, choices: INFO_SOURCE_CHOICES },
      { type: 'text',  label: 'Q45.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q46. What is your understanding about the Zero Balance Billing (ZBB)?',
        required: false, choices: NBB_UNDERSTANDING_CHOICES },
      { type: 'text',  label: 'Q46.other. Please specify if "Other".', required: false },
      // --- Apr 20 NEW: Q47 ZBB challenges ---
      { type: 'multi', label: 'Q47. What challenges do you commonly encounter for patients covered by ZBB?',
        required: false, choices: ZBB_CHALLENGE_CHOICES },
      { type: 'text',  label: 'Q47.other. Please specify if "Other".', required: false }
    ] },

  // =============================================================
  // Section E1 — BUCAS (Q48–Q52)
  // Apr 20: +Q50 utilization factors, +Q51 efficacy opinion
  // =============================================================
  { id: 'SEC-E1', title: 'Section E1 — Awareness of and perceptions on BUCAS',
    description: 'If your facility does not have a BUCAS Center, you may skip this section.',
    items: [
      { type: 'single', label: 'Q48. Have you heard about the Bagong Urgent Care and Ambulatory Service (BUCAS) center?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-E1b', 'No': 'SEC-E2'} }
    ] },

  { id: 'SEC-E1b', title: 'Section E1 — BUCAS in your facility',
    items: [
      { type: 'single', label: 'Q49. Do you have a BUCAS Center?',
        required: false, choices: ['Yes','No','I don’t know'],
        branchTo: {'Yes': 'SEC-E1c', 'No': 'SEC-E2', 'I don’t know': 'SEC-E2'} }
    ] },

  { id: 'SEC-E1c', title: 'Section E1 — BUCAS factors, efficacy, and impact',
    items: [
      // --- Apr 20 NEW: Q50 factors ---
      { type: 'multi', label: 'Q50. In your assessment, what are the main factors affecting the utilization of BUCAS in your facility?',
        required: false, choices: BUCAS_FACTOR_CHOICES },
      { type: 'text', label: 'Q50.other. Please specify if "Other".', required: false },
      // --- Apr 20 NEW: Q51 efficacy ---
      { type: 'single', label: 'Q51. Do you feel BUCAS improves patient management efficiently?',
        required: false, choices: ['Yes','No'] },
      // Q52 (was Q45 in Apr 08 — BUCAS impact; reformatted)
      { type: 'multi', label: 'Q52. In your opinion, BUCAS Centers have:',
        required: false, choices: BUCAS_IMPACT_CHOICES },
      { type: 'text', label: 'Q52.other. Please specify if "Other".', required: false }
    ] },

  // =============================================================
  // Section E2 — GAMOT (Q53–Q55)
  // =============================================================
  { id: 'SEC-E2', title: 'Section E2 — Awareness of GAMOT Package',
    description: 'If your facility does not have a GAMOT pharmacy, you may skip this section.',
    items: [
      { type: 'single', label: 'Q53. Have you heard about the Guaranteed and Accessible Medications for Outpatient Treatment (GAMOT) package?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-E2b', 'No': 'SEC-F'} }
    ] },

  { id: 'SEC-E2b', title: 'Section E2 — GAMOT accreditation',
    items: [
      { type: 'single', label: 'Q54. Is your facility an accredited GAMOT provider?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-E2c', 'No': 'SEC-F'} }
    ] },

  { id: 'SEC-E2c', title: 'Section E2 — GAMOT factors',
    items: [
      { type: 'multi', label: 'Q55. In your assessment, what are the main factors affecting the utilization of the GAMOT package in your facility?',
        required: false, choices: GAMOT_FACTOR_CHOICES },
      { type: 'text', label: 'Q55.other. Please specify if "Other".', required: false }
    ] },

  // =============================================================
  // Section F — Outbound & Inbound Referrals and Satisfaction (Q56–Q62)
  // =============================================================
  { id: 'SEC-F', title: 'Section F — Outbound & Inbound Referrals and Satisfaction',
    description: 'The following questions will ask about your outbound and inbound referrals as well as your satisfaction with the referral system.',
    items: [
      { type: 'multi', label: 'Q56. What is/are the most common way/s you send referrals to higher level facilities?',
        required: false,
        choices: ['Physical referral slip','E-referral','Referring facility calls receiving facility','Other (specify)'] },
      { type: 'text',  label: 'Q56.other. Please specify if "Other".', required: false },
      { type: 'single', label: 'Q57. What type of referral form do you use to send to higher level facilities?',
        required: false,
        choices: ['DOH standard referral form','Facility’s standard referral form',
                  'Province’s standard referral form','City / LGU standard referral form',
                  'No standard referral form','Other (specify)'] },
      { type: 'text',  label: 'Q57.other. Please specify if "Other".', required: false },
      { type: 'single', label: 'Q58. Do you have a network of specialist providers to refer patients to, if needed?',
        required: false, choices: ['Yes','No','I’ve never heard of it','I don’t know'] },
      { type: 'single', label: 'Q59. Considering all patients who come to this facility for the past 6 months, what proportion of patients coming to this facility are referred from another facility compared to walk-ins?',
        required: false,
        choices: ['Almost all patients are referred, very few walk-in/self-referred',
                  'Majority of patients are referred, some walk-in/self-referred',
                  'The proportion of referrals is about equal to walk-ins',
                  'Majority of patients walk-in/self-referred, some are referred',
                  'Almost all patients walk-in/self-referred, very few are referred',
                  'I am unsure about the typical ratio of referrals to walk-ins'] },
      { type: 'multi', label: 'Q60. Of those referred, what is/are the most common way/s you receive referrals from lower-level facilities?',
        required: false,
        choices: ['Physical referral slip','E-referral','Referring facility calls receiving facility','Other (specify)'] },
      { type: 'text',  label: 'Q60.other. Please specify if "Other".', required: false },
      { type: 'single', label: 'Q61. How would you rate your satisfaction with your current referral system?',
        required: false,
        choices: [
          'Very Satisfied: Minor improvements needed, patients are always referred appropriately',
          'Satisfied: Some improvements needed, patients are generally referred appropriately',
          'Neither Satisfied nor Dissatisfied: Improvements needed, but generally functional',
          'Dissatisfied: Moderate improvements needed, a number of patients are referred to the wrong specialists or do not receive appropriate follow-up care',
          'Very Dissatisfied: Major improvements needed, many patients are referred to the wrong specialists or do not receive appropriate follow-up care'
        ] },
      { type: 'multi', label: 'Q62. (If dissatisfied) Why are you not satisfied with the current referral system?',
        required: false,
        choices: ['Facilities are overcrowded or operating beyond capacity and do not accept the health care provider’s patient referrals',
                  'The referral process is slow',
                  'There is poor coordination between our facility and referred facilities (e.g. We do not get information back from the facility about the patients we referred to them.)',
                  'Other (specify)'],
        help: 'Only answer if you rated Dissatisfied or Very Dissatisfied in Q61.' },
      { type: 'text', label: 'Q62.other. Please specify if "Other".', required: false }
    ] },

  // End-of-F router: doctors/dentists → Section G; others → Section H
  { id: 'SEC-F-router', title: 'Role confirmation for Section G',
    description: 'Section G is asked only of physicians and dentists. Please confirm your role.',
    items: [
      { type: 'single', label: 'Are you a physician/doctor or dentist?', required: true,
        choices: ['Yes — physician/doctor or dentist','No — other role'],
        branchTo: {
          'Yes — physician/doctor or dentist': 'SEC-G1',
          'No — other role': 'SEC-H'
        } }
    ] },

  // =============================================================
  // Section G — KAP on Fees (Q63–Q90) — physicians/dentists only
  // Apr 20: three ZBB/NBB sibling pairs (Q69/Q70, Q75/Q76, Q87/Q88)
  // =============================================================
  { id: 'SEC-G1', title: 'Section G — KAP on Fees (Part 1)',
    description: 'A doctor’s professional fee is a negotiable and personalized fee that takes into account both the difficulty of the case and the patient’s capacity to pay, while adhering to ethical standards.',
    items: [
      { type: 'single', label: 'Q63. Are you aware of the facility-level professional fee policies in setting your professional fees?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-G2', 'No': 'SEC-G3'} }
    ] },

  { id: 'SEC-G2', title: 'Section G — Facility-level fee policies (cont.)',
    items: [
      { type: 'single', label: 'Q64. If yes, do you consider them in setting your professional fees?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-G3', 'No': 'SEC-G2b'} }
    ] },

  { id: 'SEC-G2b', title: 'Section G — Reasons',
    items: [
      { type: 'paragraph', label: 'Q65. If no, why not?', required: false }
    ] },

  { id: 'SEC-G3', title: 'Section G — PhilHealth coverage rules',
    items: [
      { type: 'single', label: 'Q66. Are you aware of the PhilHealth coverage rules in setting your professional fees?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-G3b', 'No': 'SEC-G4'} }
    ] },

  { id: 'SEC-G3b', title: 'Section G — PhilHealth rules (cont.)',
    items: [
      { type: 'single', label: 'Q67. Do you consider these in setting professional fees?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-G4', 'No': 'SEC-G3c'} }
    ] },

  { id: 'SEC-G3c', title: 'Section G — Reasons',
    items: [
      { type: 'paragraph', label: 'Q68. If no, why not?', required: false }
    ] },

  { id: 'SEC-G4', title: 'Section G — ZBB / NBB implications (Q69/Q70 facility-type-gated)',
    description: 'Answer whichever policy applies to your facility. Non-applicable answers are cleaned in post-processing. Apr 20: Q70 is a new NBB sibling to the Q69 ZBB item.',
    items: [
      { type: 'single', label: 'Q69. (ZBB — DOH-retained facilities only) Do you know the implications of the ZBB policy for professional fee charging?',
        required: false, choices: ['Yes','No'] },
      { type: 'single', label: 'Q70. (NBB — public facilities including DOH-retained) Do you know the implications of the NBB policy for professional fee charging?',
        required: false, choices: ['Yes','No'] },
      { type: 'paragraph', label: 'Q71. If yes, what are the implications? (ZBB and/or NBB — answer whichever applies)', required: false }
    ] },

  { id: 'SEC-G5', title: 'Section G — RVU-based pricing',
    items: [
      { type: 'single', label: 'Q72. Are you familiar with the Relative Value Unit (RVU)-based pricing?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-G5b', 'No': 'SEC-G5a'} }
    ] },

  { id: 'SEC-G5a', title: 'Section G — Reasons',
    items: [
      { type: 'paragraph', label: 'Q73. If no, why not?', required: false }
    ] },

  { id: 'SEC-G5b', title: 'Section G — Other factors',
    items: [
      { type: 'paragraph', label: 'Q74. Aside from above policies, what other factors do you consider in setting your professional fee?', required: false }
    ] },

  { id: 'SEC-G6', title: 'Section G — Fairness and adequacy (scale 1–5)',
    description: 'For each question, 1 = lowest, 5 = highest. Answer whichever ZBB/NBB variant applies. Apr 20: Q76 is a new NBB sibling to the Q75 ZBB scale.',
    items: [
      { type: 'scale', label: 'Q75. (ZBB) On a scale of 1-5 with 5 as highest, how fair is your professional fee reimbursement compared to colleagues in other specialties with similar years of training who practice in facilities which are not ZBB accredited?',
        required: false, min: 1, max: 5, minLabel: 'Very unfair', maxLabel: 'Very fair' },
      { type: 'scale', label: 'Q76. (NBB) On a scale of 1-5 with 5 as highest, how fair is your professional fee reimbursement compared to colleagues in other specialties with similar years of training who practice in facilities which are not NBB accredited?',
        required: false, min: 1, max: 5, minLabel: 'Very unfair', maxLabel: 'Very fair' },
      { type: 'scale', label: 'Q77. On a scale of 1-5 with 5 as highest, how adequate is your professional fee given your specialization and expertise?',
        required: false, min: 1, max: 5 },
      { type: 'scale', label: 'Q78. On a scale of 1-5 with 5 as highest, do you agree that the current reimbursement rates accurately reflect the complexity and cognitive effort required for your most frequent procedures?',
        required: false, min: 1, max: 5 },
      { type: 'scale', label: 'Q79. On a scale of 1-5 with 5 as highest, does your professional fee compensate for the medico-legal risks associated with your specific field?',
        required: false, min: 1, max: 5 },
      { type: 'scale', label: 'Q80. On a scale of 1-5 with 5 as highest, do reimbursement rates influence your practice’s pricing strategy?',
        required: false, min: 1, max: 5 },
      { type: 'scale', label: 'Q81. On a scale of 1-5 with 5 as highest, how acceptable is the professional fee regulation or standardization under UHC?',
        required: false, min: 1, max: 5 },
      { type: 'paragraph', label: 'Q82. What is your opinion on the policy of charging different professional fees based on the patient’s ability to pay?',
        required: false }
    ] },

  { id: 'SEC-G7', title: 'Section G — Charging behavior',
    items: [
      { type: 'single', label: 'Q83. How often do you charge your patients?',
        required: false, choices: CHARGE_5 },
      { type: 'single', label: 'Q84. How often do you waive your professional fee?',
        required: false, choices: CHARGE_5 },
      { type: 'single', label: 'Q85. How often do you give discounts/adjustments on your professional fee?',
        required: false, choices: CHARGE_5 },
      { type: 'paragraph', label: 'Q86. What coping strategies have you adapted when reimbursement is perceived as insufficient?',
        required: false }
    ] },

  { id: 'SEC-G8', title: 'Section G — Balance billing experience',
    description: 'Apr 20: Q88 is a new NBB sibling to the Q87 ZBB item.',
    items: [
      { type: 'single', label: 'Q87. (ZBB — DOH-retained facilities only) Have you experienced professional fee balance billing despite the insurance/ZBB?',
        required: false, choices: ['Yes','No'] },
      { type: 'single', label: 'Q88. (NBB — public facilities including DOH-retained) Have you experienced professional fee balance billing despite the insurance/NBB?',
        required: false, choices: ['Yes','No'] },
      { type: 'paragraph', label: 'Q89. If yes, what are those situations? (answer for whichever of Q87/Q88 you said Yes to)', required: false },
      { type: 'paragraph', label: 'Q90. What challenges do you face in maintaining fair and sustainable professional fees?', required: false }
    ] },

  // =============================================================
  // Section H — Task Sharing (Q91–Q95)
  // =============================================================
  { id: 'SEC-H', title: 'Section H — Task Sharing',
    description: 'We understand that in a health facility, it’s often necessary to perform tasks outside of your job description to ensure that high quality patient care is maintained. All information here will be kept confidential and anonymous.',
    items: [
      { type: 'single', label: 'Q91. In your day-to-day work, how often do you have to perform tasks that should be performed by a different role?',
        required: false,
        choices: ['Everyday','More than once a week, but not everyday','Around once a week',
                  'Less than once a week, but at least once a month','Very rarely (can think of a few times only)',
                  'This has never happened to me'] },
      { type: 'single', label: 'Q92. When this happens, which of the following best applies to you?',
        required: false,
        choices: [
          'I typically have to take on tasks that should be performed by only staff / more junior health care providers to me',
          'I typically have to take on tasks that should be performed only by staff / more senior health care providers to me',
          'I have to take on tasks that should be performed by staff that are not health workers (e.g., cleaners, drivers, IT)',
          'Other (specify)'
        ] },
      { type: 'text', label: 'Q92.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q93. What are the most common tasks you do in your daily work that you could delegate to a more junior staff or different staff member?',
        required: false,
        choices: [
          'Patient assessments',
          'Clinical tasks (e.g. taking vital signs, drawing blood, hanging medicines)',
          'Patient self-care support (e.g., cleaning patients, assisting with toilet)',
          'Explaining treatment plans to patients and relatives',
          'Administrative tasks (e.g. writing notes, requesting tests, encoding)',
          'Other (specify)'
        ] },
      { type: 'text', label: 'Q93.other. Please specify if "Other".', required: false },
      { type: 'single', label: 'Q94. Which best explains why you take on these tasks?',
        required: false,
        choices: [
          'We are short staffed, so I have to',
          'I am capable of the task, I just haven’t completed official certification yet',
          'I think that someone of my role should be responsible for these tasks',
          'Other (specify)'
        ] },
      { type: 'text', label: 'Q94.other. Please specify if "Other".', required: false },
      { type: 'single', label: 'Q95. Do you agree or disagree with this statement: I think it’s okay that health workers share tasks across roles even if they are beyond their job description.',
        required: false,
        choices: ['Agree but for medical tasks only','Agree but for clerical tasks only',
                  'Agree for both medical and clerical tasks','Disagree for both medical and clerical tasks'] }
    ] },

  // =============================================================
  // Section I — Facility Support (Q96–Q97)
  // =============================================================
  { id: 'SEC-I', title: 'Section I — Facility Support',
    description: 'These questions ask about your satisfaction with the support you receive from your facility.',
    items: [
      { type: 'single', label: 'Q96. Are you satisfied with the support you receive from your facility to implement UHC reforms?',
        required: false, choices: ['Yes','No'],
        branchTo: {'Yes': 'SEC-J1', 'No': 'SEC-I-no'} }
    ] },

  { id: 'SEC-I-no', title: 'Section I — Reasons',
    items: [
      { type: 'multi', label: 'Q97. Why not?',
        required: false,
        choices: ['Insufficient support given','Hard to coordinate','Support is not targeted','Other (specify)'] },
      { type: 'text', label: 'Q97.other. Please specify if "Other".', required: false }
    ] },

  // =============================================================
  // Section J — Job Satisfaction (Q98–Q125; Q108 is a PDF numbering gap)
  // Apr 20: grid-lift shifted from Q103 → Q114 (was Apr 08 Q103); terminal driver Q123 (was Q112)
  // =============================================================
  { id: 'SEC-J1', title: 'Section J — Job Satisfaction (Part 1)',
    description: 'The final section focuses on your satisfaction about your compensation, working environment, and professional development. Please think about your experience in this post for the past 6 months.',
    items: [
      { type: 'grid-single', label: 'Q98–Q107. For each statement, indicate your level of agreement.',
        required: false,
        rows: [
          'Q98. I am compensated fairly.',
          'Q99. All of my salary payments have arrived on time.',
          'Q100. All of my salary payments have arrived in the correct amount.',
          'Q101. The working environment is a fully supportive one.',
          'Q102. I am treated fairly at the workplace.',
          'Q103. My colleagues treat me with respect.',
          'Q104. My department/unit/practice provides a supportive environment for everyone regardless of background, beliefs, or identity.',
          'Q105. I have access to the resources I need to do my job well.',
          'Q106. In this post, I am given opportunities to develop my leadership skills relevant for my stage of training.',
          'Q107. I am satisfied with the professional development opportunities I have in my job.'
        ],
        columns: AGREE_5 },
      // NOTE: Q108 is a PDF numbering gap — no item emitted at this slot.
      { type: 'paragraph', label: 'Q109. In addition to your salary, what other benefits as an accredited healthcare provider do you receive?', required: false },
      { type: 'multi', label: 'Q110. What additional resources do you need to perform well in this job?',
        required: false,
        choices: ['Professional development opportunities','Better compensation policies','Better equipment/facilities','Other (specify)'] },
      { type: 'text', label: 'Q110.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q111. What opportunities to develop leadership skill/s would be useful to you?',
        required: false,
        choices: ['Seminars, conferences, workshops','Supervisory trainings','More training related to my job post','Other (specify)'] },
      { type: 'text', label: 'Q111.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q112. Which of the following professional development opportunity/ies is/are currently provided to you by your facility? (Check all that apply)',
        required: false,
        choices: ['Clinical audits','Surgical audits','Quality assurance meetings','Seminars, conferences, workshops',
                  'Support for independent professional development: scholarships',
                  'Support for independent professional development: research grants','None'] },
      { type: 'multi', label: 'Q113. Which of the following professional development opportunity/ies would be most useful to you?',
        required: false,
        choices: ['Clinical audits','Surgical audits','Quality assurance meetings','Seminars, conferences, workshops',
                  'Support for independent professional development: scholarships',
                  'Support for independent professional development: research grants','Other (specify)'] },
      { type: 'text', label: 'Q113.other. Please specify if "Other".', required: false },
      // Q114 lifted out of Grid #2 so Q122 skip-if-Never can route. Apr 20: was Q103 in Apr 08.
      { type: 'single', label: 'Q114. In the past month, I have worked beyond my scheduled hours.',
        required: false, choices: FREQ_5,
        branchTo: {
          'Always': 'SEC-J2', 'Often': 'SEC-J2', 'Sometimes': 'SEC-J2', 'Seldom': 'SEC-J2', 'Never': 'SEC-J3'
        } }
    ] },

  { id: 'SEC-J2', title: 'Section J — Frequency grid + overtime pattern',
    description: 'Please think about your experience in this post for the past 6 months.',
    items: [
      { type: 'grid-single', label: 'Q115–Q121. For each statement, indicate how often it applies.',
        required: false,
        rows: [
          'Q115. I have been compensated for working overtime.',
          'Q116. My work is emotionally exhausting.',
          'Q117. My work frustrates me.',
          'Q118. I feel worn out at the end of a working day.',
          'Q119. I feel exhausted every morning at the thought of another day at work.',
          'Q120. I feel that every working hour is tiring for me.',
          'Q121. I have enough energy for family and friends during leisure time.'
        ],
        columns: FREQ_5 },
      { type: 'single', label: 'Q122. I have worked overtime for:',
        required: false,
        choices: ['Once or twice in the past month','Once or twice a week',
                  'Three or four days every week','Almost everyday','Everyday'] }
    ] },

  { id: 'SEC-J3', title: 'Section J — Frequency grid (no overtime)',
    description: 'Please think about your experience in this post for the past 6 months.',
    items: [
      { type: 'grid-single', label: 'Q115–Q121. For each statement, indicate how often it applies.',
        required: false,
        rows: [
          'Q115. I have been compensated for working overtime.',
          'Q116. My work is emotionally exhausting.',
          'Q117. My work frustrates me.',
          'Q118. I feel worn out at the end of a working day.',
          'Q119. I feel exhausted every morning at the thought of another day at work.',
          'Q120. I feel that every working hour is tiring for me.',
          'Q121. I have enough energy for family and friends during leisure time.'
        ],
        columns: FREQ_5 }
      // Q122 not shown when Q114 = Never
    ] },

  { id: 'SEC-J4', title: 'Section J — Closing',
    items: [
      { type: 'single', label: 'Q123. Have you considered leaving this facility?',
        required: true,
        choices: [
          'Yes, I’ve thought about it and have definite plans to leave',
          'Yes, I’ve thought about it and am actively exploring other opportunities, but no firm plans yet',
          'Yes, I’ve thought about it, but I’m not actively exploring nor have I made any firm plans yet',
          'No, I haven’t thought about it'
        ],
        branchTo: {
          'Yes, I’ve thought about it and have definite plans to leave': 'SEC-J5',
          'Yes, I’ve thought about it and am actively exploring other opportunities, but no firm plans yet': 'SEC-J5',
          'Yes, I’ve thought about it, but I’m not actively exploring nor have I made any firm plans yet': 'SEC-J5',
          'No, I haven’t thought about it': 'SEC-END'
        } }
    ] },

  { id: 'SEC-J5', title: 'Section J — Leaving intent',
    items: [
      { type: 'multi', label: 'Q124. Why are you planning on leaving this facility?',
        required: false,
        choices: ['Poor compensation','Lack of opportunities','Burnt out',
                  'Moving to another part of the country','Moving to another country','Other (specify)'] },
      { type: 'text', label: 'Q124.other. Please specify if "Other".', required: false },
      { type: 'multi', label: 'Q125. What are you planning to do after leaving this facility?',
        required: false,
        choices: ['Transfer to a new facility with the same role',
                  'Change training/specialization within healthcare',
                  'Change profession','Take an extended leave from work',
                  'Take a position as a health worker in another country',
                  'Retire','Other (specify)'] },
      { type: 'text', label: 'Q125.other. Please specify if "Other".', required: false }
    ] },

  { id: 'SEC-END', title: 'End of survey',
    description: 'Thank you for completing the F2 Healthcare Worker Survey. Your responses have been recorded. ' +
                 'If you included your name for the raffle, you will be contacted if you are a winner.',
    items: [] }

] };
