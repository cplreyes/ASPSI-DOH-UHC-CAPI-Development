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

const q112IsYes = (v: unknown) => typeof v === 'string' && v.startsWith('Yes,');

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    Q14: (v) => typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
  },
  C: {
    Q32: (v) => v.Q30 === 'Yes',
  },
  D: {
    Q38: (v) => isYes(v.Q37),
    Q39: (v) => isYes(v.Q37),
    Q41: (v) => isYes(v.Q40),
    Q42: (v) => isYes(v.Q40),
  },
  E1: {
    Q45: (v) => isYes(v.Q43) && isYes(v.Q44),
  },
  E2: {
    Q48: (v) => isYes(v.Q46) && isYes(v.Q47),
  },
  F: {
    Q55: (v) => isDissatisfied(v.Q54),
  },
  G: {
    Q57: (v) => isYes(v.Q56),
    Q58: (v) => v.Q57 === 'No',
    Q60: (v) => isYes(v.Q59),
    Q61: (v) => v.Q60 === 'No',
    Q63: (v) => isYes(v['Q62']) || isYes(v['Q62.1']),
    Q65: (v) => v.Q64 === 'No',
    Q79: (v) => isYes(v['Q78']) || isYes(v['Q78.1']),
  },
  I: {
    Q87: (v) => v.Q86 === 'No',
  },
  J: {
    Q111: (v) => typeof v.Q103 === 'string' && v.Q103 !== 'Never',
    Q113: (v) => q112IsYes(v.Q112),
    Q114: (v) => q112IsYes(v.Q112),
  },
};

export function shouldShow(sectionId: string, itemId: string, values: FormValues): boolean {
  const p = predicates[sectionId]?.[itemId];
  return p ? p(values) : true;
}
