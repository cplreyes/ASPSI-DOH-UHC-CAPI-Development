export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

const ROLES_WITH_SPECIALTY = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
]);

const isYes = (v: unknown) => v === 'Yes';

const isDissatisfied = (v: unknown) => {
  if (typeof v !== 'string') return false;
  return v.startsWith('Dissatisfied') || v.startsWith('Very Dissatisfied');
};

const q123IsYes = (v: unknown) => typeof v === 'string' && v.startsWith('Yes,');

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    Q14: (v) => typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
  },
  C: {
    Q36: (v) => v.Q34 === 'Yes',
  },
  D: {
    Q42: (v) => isYes(v.Q41),
    Q43: (v) => isYes(v.Q41),
    Q45: (v) => isYes(v.Q44),
    Q46: (v) => isYes(v.Q44),
  },
  E: {
    Q50: (v) => isYes(v.Q48) && isYes(v.Q49),
    Q51: (v) => isYes(v.Q48) && isYes(v.Q49),
    Q52: (v) => isYes(v.Q48) && isYes(v.Q49),
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
    Q71: (v) => isYes(v['Q69']) || isYes(v['Q70']),
    Q73: (v) => v.Q72 === 'No',
    Q89: (v) => isYes(v['Q87']) || isYes(v['Q88']),
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
