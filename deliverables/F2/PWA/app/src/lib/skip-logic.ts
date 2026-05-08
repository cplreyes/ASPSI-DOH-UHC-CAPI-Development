export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

const SECTION_G_ROLES = new Set(['Physician/Doctor', 'Physician assistant', 'Dentist']);

// R2-#114: sections C/D/E are role-gated to patient-care roles. Pre-fix
// shouldShowSection returned true for everything except G; tester saw
// C/D/E visible to Pharmacist/Dispenser, Physician/Doctor, and Dentist
// aide (1 of 3 should see them — Doctor only).
//
// Per UAT R2 tester guide spec:
//   - C/D/E: admin, doctor, physician assistant, nurse, midwife, dentist,
//            nutrition action officer/coordinator
//   - E only (E2 GAMOT half): pharmacists/dispensers — they should skip
//            E1 (Q48–Q52) but see E2 (Q53–Q55). Until #117 splits E1/E2,
//            pharmacists see all of E (acceptable trade for v2.0.1; the
//            E1 leak is #117's surface).
//   - All other roles (Nursing assistant, Lab tech, Med tech, Dentist
//            aide, BHW, Other): proceed straight to F.
const SECTION_CDE_ROLES = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
  'Nutrition action officer/ coordinator',
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
    Q38: (v) => v.Q31 === 'Yes',
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
