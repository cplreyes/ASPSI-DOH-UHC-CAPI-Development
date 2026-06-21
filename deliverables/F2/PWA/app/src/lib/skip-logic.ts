export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

// #539: Section G is restricted to physicians and dentists only. The R2-#114
// list also included 'Physician assistant'; the updated tester-guide spec
// excludes it ("Only Physicians/Doctors, and Dentist should answer Section G").
const SECTION_G_ROLES = new Set(['Physician/Doctor', 'Dentist']);

// Sections C/D/E are role-gated to patient-care roles. shouldShowSection gates
// C/D on SECTION_CDE_ROLES and E on SECTION_E_ROLES; the E2 (GAMOT) half adds
// pharmacists/dispensers, who skip E1 (Q48–Q52) but answer E2 (Q53–Q55) via the
// item-level gates below.
//
// Per the updated tester-guide spec (#539 — supersedes the R2-#114 list):
//   - C/D/E1: Administrator, Physician/Doctor, Nurse, Midwife, Dentist.
//   - E2 only: Pharmacist/Dispenser (skip C/D/E1, answer the E2 GAMOT half).
//   - None of C/D/E — proceed to F: Physician assistant, Nursing assistant,
//            Laboratory technician, Medical/radiologic technologist, Health
//            promotion officer, Nutrition action officer/coordinator, Physical
//            Therapist, Dentist aide, Barangay Health Worker, Other.
//
// #539: 'Physician assistant' and 'Nutrition action officer/ coordinator' were
// in the R2-#114 set; the new spec excludes both. They leaked C/D/E to those
// two personas (Aidan re-test 2026-06-16) until removed here.
// Exported so cross-field.ts (the C/D data-quality gate, GATE-05) shares one
// source of truth and can't drift from the section gate — the drift that let
// #539 slip in.
export const SECTION_CDE_ROLES = new Set([
  'Administrator',
  'Physician/Doctor',
  'Nurse',
  'Midwife',
  'Dentist',
]);
const SECTION_E_ROLES = new Set([...SECTION_CDE_ROLES, 'Pharmacist/Dispenser']);

const ROLES_WITH_SPECIALTY = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
]);

// Q6 specialty list filter — roles whose specialties match the medical-doctor list (Q6's
// current choice set: Anesthesia, Dermatology, Internal Medicine, etc.). Other roles in
// ROLES_WITH_SPECIALTY get only the role-agnostic options ("No specialty", "Others (specify)").
const MD_SPECIALTY_ROLES = new Set(['Physician/Doctor', 'Physician assistant']);
const ROLE_AGNOSTIC_SPECIALTY_VALUES = new Set(['No specialty', 'Others (specify)']);

const isYes = (v: unknown) => v === 'Yes';

const isDissatisfied = (v: unknown) => {
  if (typeof v !== 'string') return false;
  return v.startsWith('Dissatisfied') || v.startsWith('Very Dissatisfied');
};

const q123IsYes = (v: unknown) => typeof v === 'string' && v.startsWith('Yes,');

const q25Includes = (v: FormValues, choice: string) =>
  Array.isArray(v.Q25) && (v.Q25 as string[]).includes(choice);

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    // Q12=No → skip to Section C (Q31); entire Q13–Q30 block hidden
    Q13: (v) => v.Q12 === 'Yes',
    Q14: (v) => v.Q12 === 'Yes' && typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
    Q15: (v) => v.Q12 === 'Yes',
    Q16: (v) => v.Q12 === 'Yes' && typeof v.Q15 === 'string' && v.Q15.startsWith('Yes'),
    Q17: (v) => v.Q12 === 'Yes',
    Q18: (v) => v.Q12 === 'Yes',
    Q19: (v) => v.Q12 === 'Yes',
    Q20: (v) => v.Q12 === 'Yes',
    Q21: (v) => v.Q12 === 'Yes',
    Q22: (v) => v.Q12 === 'Yes',
    Q23: (v) => v.Q12 === 'Yes',
    Q24: (v) => v.Q12 === 'Yes',
    Q25: (v) => v.Q12 === 'Yes',
    // Q26–Q30 show only for their respective Q25 selection
    Q26: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Salary'),
    Q27: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Number of patients'),
    Q28: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Working hours'),
    Q29: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Standards to follow'),
    Q30: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Preventative health care'),
  },
  C: {
    // Q31=No → skip to Section D (Q41); Q32–Q40 hidden
    Q32: (v) => v.Q31 === 'Yes',
    Q33: (v) => v.Q31 === 'Yes',
    Q34: (v) => v.Q31 === 'Yes',
    Q35: (v) => v.Q31 === 'Yes' && v.Q34 === 'Yes',
    Q36: (v) => v.Q31 === 'Yes' && v.Q34 === 'Yes',
    Q37: (v) => v.Q31 === 'Yes' && v.Q34 === 'No',
    // R3 #308: per F2-Skip-Logic "Apr 20 improvement", Q34=Yes (already
    // accredited) skips the whole C tail (Q37–Q40) → Q41. Q38 ("would you
    // consider becoming accredited?") only makes sense for the not-yet-
    // accredited path, so gate it on Q34=No like Q37.
    Q38: (v) => v.Q31 === 'Yes' && v.Q34 === 'No',
    Q39: (v) => v.Q31 === 'Yes' && v.Q38 === 'Yes',
    Q40: (v) => v.Q31 === 'Yes' && v.Q38 === 'No',
  },
  D: {
    Q42: (v) => isYes(v.Q41),
    Q43: (v) => isYes(v.Q41),
    Q45: (v) => isYes(v.Q44),
    Q46: (v) => isYes(v.Q44),
    Q47: (v) => isYes(v.Q44),
  },
  // R2-#117: Section E sub-divides into two role-segregated halves.
  // E1 (BUCAS) = Q48-Q52, restricted to SECTION_CDE_ROLES.
  // E2 (GAMOT) = Q53-Q55, available to SECTION_E_ROLES (CDE + pharmacist).
  // Pre-fix Q48 always showed within Section E for any role that reached
  // the section, so pharmacists answered BUCAS questions despite being
  // outside the patient-care role set for E1. Tester (Shan, 2026-05-07)
  // suggested splitting: "for pharmacists/dispensers and assistant
  // pharmacists, the form should proceed directly to Section E2 -
  // Question 53." Implemented as item-level role gates inside Section
  // E rather than a structural section split (the latter would touch
  // SECTIONS array + 2 schemas + section-numbering across the app).
  E: {
    Q48: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5),
    Q49: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48),
    Q50: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q51: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q52: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q54: (v) => isYes(v.Q53),
    Q55: (v) => isYes(v.Q53) && isYes(v.Q54),
  },
  F: {
    Q62: (v) => isDissatisfied(v.Q61),
  },
  G: {
    Q64: (v) => isYes(v.Q63),
    Q65: (v) => v.Q64 === 'No',
    Q67: (v) => isYes(v.Q66),
    Q68: (v) => v.Q67 === 'No',
    Q70: (v) => isYes(v.Q69),
    Q71: (v) => isYes(v['Q69']) || isYes(v['Q70']),
    Q73: (v) => v.Q72 === 'No',
    Q88: (v) => isYes(v.Q87),
    Q89: (v) => isYes(v['Q87']) || isYes(v['Q88']),
  },
  H: {
    // Q91='This has never happened to me' → skip Q92–Q95
    Q92: (v) => v.Q91 !== 'This has never happened to me',
    Q93: (v) => v.Q91 !== 'This has never happened to me',
    Q94: (v) => v.Q91 !== 'This has never happened to me',
    Q95: (v) => v.Q91 !== 'This has never happened to me',
  },
  I: {
    Q97: (v) => v.Q96 === 'No',
  },
  J: {
    Q122: (v) => typeof v.Q114 === 'string' && v.Q114 !== 'Never',
    Q124: (v) => q123IsYes(v.Q123),
    Q125: (v) => q123IsYes(v.Q123),
  },
};

export function shouldShow(sectionId: string, itemId: string, values: FormValues): boolean {
  const p = predicates[sectionId]?.[itemId];
  return p ? p(values) : true;
}

// Section-level skip: returns false if the whole section should be skipped
export function shouldShowSection(sectionId: string, values: FormValues): boolean {
  const role = typeof values.Q5 === 'string' ? values.Q5 : null;
  if (sectionId === 'G') {
    return role !== null && SECTION_G_ROLES.has(role);
  }
  if (sectionId === 'C' || sectionId === 'D') {
    return role !== null && SECTION_CDE_ROLES.has(role);
  }
  if (sectionId === 'E') {
    return role !== null && SECTION_E_ROLES.has(role);
  }
  return true;
}

// Filter an item's choice list based on dependent form values. Returns the input list
// when no filter applies, so consumers can call this unconditionally without checking
// for a registered filter first.
export interface ChoiceLike {
  value: string;
}

export function filterChoices<T extends ChoiceLike>(
  sectionId: string,
  itemId: string,
  values: FormValues,
  choices: T[],
): T[] {
  // A.Q6 specialty filter — non-MD roles (Administrator, Nurse, Midwife, Dentist) only see
  // role-agnostic options. The full medical specialty list is shown only to Physician/Doctor
  // and Physician assistant.
  if (sectionId === 'A' && itemId === 'Q6') {
    const role = values.Q5;
    if (typeof role === 'string' && !MD_SPECIALTY_ROLES.has(role)) {
      return choices.filter((c) => ROLE_AGNOSTIC_SPECIALTY_VALUES.has(c.value));
    }
  }
  return choices;
}
