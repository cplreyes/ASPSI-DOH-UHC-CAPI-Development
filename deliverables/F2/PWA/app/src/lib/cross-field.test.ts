import { describe, it, expect } from 'vitest';
import { evaluateCrossField, type Warning } from './cross-field';

describe('evaluateCrossField', () => {
  it('returns no warnings on a clean nurse profile', () => {
    expect(evaluateCrossField({ Q4: 30, Q5: 'Nurse', Q9_1: 5, Q10: 5, Q11: 8 })).toEqual([
      {
        id: 'PROF-03',
        severity: 'info',
        message: {
          key: 'crossField.employmentClassDerived',
          values: { employmentClass: 'full-time' },
        },
        fields: ['Q11'],
        derived: { employment_class: 'full-time' },
      },
    ]);
  });

  it('flags PROF-01 when tenure exceeds age − 15', () => {
    const out = evaluateCrossField({ Q4: 25, Q5: 'Nurse', Q9_1: 15 });
    expect(out.map((w) => w.id)).toContain('PROF-01');
  });

  it('flags PROF-02 when a non-doctor reports a specialty', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q6: 'Pediatrics' });
    expect(out.map((w) => w.id)).toContain('PROF-02');
  });

  it('does not flag PROF-02 when Q6 is "No specialty"', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q6: 'No specialty' });
    expect(out.map((w) => w.id)).not.toContain('PROF-02');
  });

  it('does not flag PROF-02 when Q5 is Physician/Doctor', () => {
    const out = evaluateCrossField({ Q5: 'Physician/Doctor', Q6: 'Pediatrics' });
    expect(out.map((w) => w.id)).not.toContain('PROF-02');
  });

  it('emits PROF-03 derived employment_class=full-time for Q11 >= 8', () => {
    const out = evaluateCrossField({ Q11: 8 });
    const w = out.find((x) => x.id === 'PROF-03');
    expect(w?.severity).toBe('info');
    expect(w?.derived).toEqual({ employment_class: 'full-time' });
  });

  it('emits PROF-03 derived employment_class=part-time for Q11 < 8', () => {
    const w = evaluateCrossField({ Q11: 6 }).find((x) => x.id === 'PROF-03');
    expect(w?.derived).toEqual({ employment_class: 'part-time' });
  });

  it('flags PROF-04 when Q10 × Q11 exceeds 80 weekly hours', () => {
    const out = evaluateCrossField({ Q10: 7, Q11: 13 });
    expect(out.map((w) => w.id)).toContain('PROF-04');
  });

  it('flags GATE-02 when a nurse has answered Section G items', () => {
    const out = evaluateCrossField({ Q5: 'Nurse', Q56: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-02');
  });

  it('does not flag GATE-02 for doctors who answered Section G', () => {
    const out = evaluateCrossField({ Q5: 'Physician/Doctor', Q56: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-02');
  });

  it('flags GATE-05 when a pharmacist has answered Section C items', () => {
    const out = evaluateCrossField({ Q5: 'Pharmacist/Dispenser', Q27: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-05');
  });

  it('does not flag GATE-05 for administrators (in BUCKET-CD)', () => {
    const out = evaluateCrossField({ Q5: 'Administrator', Q27: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-05');
  });

  it('warning has a human-readable message and lists involved fields', () => {
    const out = evaluateCrossField({ Q4: 25, Q5: 'Nurse', Q9_1: 15 });
    const prof01 = out.find((w): w is Warning => w.id === 'PROF-01');
    expect(prof01?.message).toEqual({
      key: 'crossField.tenureImplausible',
      values: { years: 15, age: 25 },
    });
    expect(prof01?.fields).toEqual(['Q4', 'Q9_1']);
  });
});
