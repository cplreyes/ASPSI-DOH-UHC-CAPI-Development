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
};

export function shouldShow(
  sectionId: string,
  itemId: string,
  values: FormValues,
): boolean {
  const p = predicates[sectionId]?.[itemId];
  return p ? p(values) : true;
}
