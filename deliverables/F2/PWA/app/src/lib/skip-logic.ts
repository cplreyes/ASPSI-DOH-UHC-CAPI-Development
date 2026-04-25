export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

const SECTION_G_ROLES = new Set(['Physician/Doctor', 'Physician assistant', 'Dentist']);

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
  E: {
    Q49: (v) => isYes(v.Q48),
    Q50: (v) => isYes(v.Q48) && isYes(v.Q49),
    Q51: (v) => isYes(v.Q48) && isYes(v.Q49),
    Q52: (v) => isYes(v.Q48) && isYes(v.Q49),
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
  if (sectionId === 'G') {
    return typeof values.Q5 === 'string' && SECTION_G_ROLES.has(values.Q5);
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
