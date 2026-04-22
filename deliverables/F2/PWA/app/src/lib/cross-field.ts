import type { FormValues } from './skip-logic';

export type Severity = 'info' | 'warn' | 'clean' | 'error';

export interface Warning {
  id: string;
  severity: Severity;
  message: { key: string; values?: Record<string, unknown> };
  fields: string[];
  derived?: Record<string, string>;
}

const BUCKET_CD = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
]);

const DOCTOR_DENTIST = new Set(['Physician/Doctor', 'Dentist']);

const SECTION_G_FIELDS = [
  'Q63',
  'Q64',
  'Q65',
  'Q66',
  'Q67',
  'Q68',
  'Q69',
  'Q70',
  'Q71',
  'Q72',
  'Q73',
  'Q74',
  'Q75',
  'Q76',
  'Q77',
  'Q78',
  'Q79',
  'Q80',
  'Q81',
  'Q82',
  'Q83',
  'Q84',
  'Q85',
  'Q86',
  'Q87',
  'Q88',
  'Q89',
  'Q90',
];

const SECTION_CD_FIELDS = [
  'Q31',
  'Q32',
  'Q33',
  'Q34',
  'Q35',
  'Q36',
  'Q37',
  'Q38',
  'Q39',
  'Q40',
  'Q41',
  'Q42',
  'Q43',
  'Q44',
  'Q45',
  'Q46',
];

function isFilled(v: unknown): boolean {
  if (v === undefined || v === null) return false;
  if (typeof v === 'string') return v.trim().length > 0;
  if (Array.isArray(v)) return v.length > 0;
  return true;
}

function anyFilled(values: FormValues, fields: string[]): boolean {
  return fields.some((f) => isFilled(values[f]));
}

export function evaluateCrossField(values: FormValues): Warning[] {
  const out: Warning[] = [];

  const age = typeof values.Q4 === 'number' ? values.Q4 : Number(values.Q4);
  const tenureYears = typeof values.Q9_1 === 'number' ? values.Q9_1 : Number(values.Q9_1);
  if (Number.isFinite(age) && Number.isFinite(tenureYears) && tenureYears > age - 15) {
    out.push({
      id: 'PROF-01',
      severity: 'warn',
      message: {
        key: 'crossField.tenureImplausible',
        values: { years: tenureYears, age },
      },
      fields: ['Q4', 'Q9_1'],
    });
  }

  const role = typeof values.Q5 === 'string' ? values.Q5 : '';
  const specialty = typeof values.Q6 === 'string' ? values.Q6 : '';
  if (role && !DOCTOR_DENTIST.has(role) && specialty && specialty !== 'No specialty') {
    out.push({
      id: 'PROF-02',
      severity: 'warn',
      message: {
        key: 'crossField.specialtyMismatch',
        values: { role, specialty },
      },
      fields: ['Q5', 'Q6'],
    });
  }

  const hours = typeof values.Q11 === 'number' ? values.Q11 : Number(values.Q11);
  if (Number.isFinite(hours)) {
    out.push({
      id: 'PROF-03',
      severity: 'info',
      message: {
        key: 'crossField.employmentClassDerived',
        values: { employmentClass: hours >= 8 ? 'full-time' : 'part-time' },
      },
      fields: ['Q11'],
      derived: { employment_class: hours >= 8 ? 'full-time' : 'part-time' },
    });
  }

  const days = typeof values.Q10 === 'number' ? values.Q10 : Number(values.Q10);
  if (Number.isFinite(days) && Number.isFinite(hours) && days * hours > 80) {
    out.push({
      id: 'PROF-04',
      severity: 'warn',
      message: {
        key: 'crossField.workloadExceeds80',
        values: { days, hours, total: days * hours },
      },
      fields: ['Q10', 'Q11'],
    });
  }

  if (role && !DOCTOR_DENTIST.has(role) && anyFilled(values, SECTION_G_FIELDS)) {
    out.push({
      id: 'GATE-02',
      severity: 'clean',
      message: {
        key: 'crossField.sectionGRoleMismatch',
        values: { role },
      },
      fields: ['Q5', ...SECTION_G_FIELDS.filter((f) => isFilled(values[f]))],
    });
  }

  if (role && !BUCKET_CD.has(role) && anyFilled(values, SECTION_CD_FIELDS)) {
    out.push({
      id: 'GATE-05',
      severity: 'clean',
      message: {
        key: 'crossField.sectionsCDRoleMismatch',
        values: { role },
      },
      fields: ['Q5', ...SECTION_CD_FIELDS.filter((f) => isFilled(values[f]))],
    });
  }

  return out;
}
