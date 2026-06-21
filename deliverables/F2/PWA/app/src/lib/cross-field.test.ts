import { describe, it, expect } from 'vitest';
import { evaluateCrossField, sectionBlockingErrors, type Warning } from './cross-field';

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

  it('flags PROF-01 as an error when tenure is at or above age − 20 (R3 #305/3b)', () => {
    // age 25, threshold age − 20 = 5; tenure 15 ≥ 5 → block.
    const out = evaluateCrossField({ Q4: 25, Q5: 'Nurse', Q9_1: 15 });
    const prof01 = out.find((w) => w.id === 'PROF-01');
    expect(prof01?.severity).toBe('error');
  });

  it('flags PROF-01 at the exact age − 20 boundary (inclusive block)', () => {
    // age 40, threshold = 20; tenure exactly 20 → blocks (must be strictly <).
    const out = evaluateCrossField({ Q4: 40, Q5: 'Nurse', Q9_1: 20 });
    expect(out.map((w) => w.id)).toContain('PROF-01');
  });

  it('does not flag PROF-01 when tenure is below age − 20', () => {
    // age 40, threshold = 20; tenure 19 < 20 → clean.
    const out = evaluateCrossField({ Q4: 40, Q5: 'Nurse', Q9_1: 19 });
    expect(out.map((w) => w.id)).not.toContain('PROF-01');
  });

  it('flags PROF-05 (error) when both Q9 years and months are zero (#305/3a)', () => {
    const out = evaluateCrossField({ Q4: 30, Q5: 'Nurse', Q9_1: 0, Q9_2: 0 });
    expect(out.find((w) => w.id === 'PROF-05')?.severity).toBe('error');
  });

  it('allows years=0 with months ≥ 1 (valid sub-1-year tenure) — no PROF-05', () => {
    const out = evaluateCrossField({ Q4: 30, Q5: 'Nurse', Q9_1: 0, Q9_2: 6 });
    expect(out.map((w) => w.id)).not.toContain('PROF-05');
  });

  it('does not flag PROF-05 for normal tenure', () => {
    const out = evaluateCrossField({ Q4: 30, Q5: 'Nurse', Q9_1: 3, Q9_2: 0 });
    expect(out.map((w) => w.id)).not.toContain('PROF-05');
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
    const out = evaluateCrossField({ Q5: 'Nurse', Q63: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-02');
  });

  it('does not flag GATE-02 for doctors who answered Section G', () => {
    const out = evaluateCrossField({ Q5: 'Physician/Doctor', Q63: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-02');
  });

  it('flags GATE-05 when a pharmacist has answered Section C items', () => {
    const out = evaluateCrossField({ Q5: 'Pharmacist/Dispenser', Q31: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-05');
  });

  it('does not flag GATE-05 for administrators (in BUCKET-CD)', () => {
    const out = evaluateCrossField({ Q5: 'Administrator', Q31: 'Yes' });
    expect(out.map((w) => w.id)).not.toContain('GATE-05');
  });

  // #539: these two roles were removed from the C/D set; the data-quality gate
  // shares that set, so it must now flag C/D data from either of them.
  it('#539: flags GATE-05 for Physician assistant who answered Section C', () => {
    const out = evaluateCrossField({ Q5: 'Physician assistant', Q31: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-05');
  });

  it('#539: flags GATE-05 for Nutrition action officer/coordinator who answered Section C', () => {
    const out = evaluateCrossField({ Q5: 'Nutrition action officer/ coordinator', Q31: 'Yes' });
    expect(out.map((w) => w.id)).toContain('GATE-05');
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

// #587: inline section-exit gate — the error-severity findings whose fields
// belong to the section the respondent is leaving.
describe('sectionBlockingErrors', () => {
  // Section A owns the age (Q4) and tenure (Q9_1 years / Q9_2 months) fields.
  const sectionA = new Set(['Q4', 'Q9_1', 'Q9_2']);

  it('returns PROF-01 when tenure ≥ age − 20 and the field is in the section', () => {
    const out = sectionBlockingErrors({ Q4: 30, Q9_1: 15 }, sectionA);
    expect(out.map((w) => w.id)).toContain('PROF-01');
  });

  it('returns PROF-05 for the zero-tenure block', () => {
    const out = sectionBlockingErrors({ Q4: 30, Q9_1: 0, Q9_2: 0 }, sectionA);
    expect(out.map((w) => w.id)).toContain('PROF-05');
  });

  it('is empty when the tenure is plausible', () => {
    expect(sectionBlockingErrors({ Q4: 40, Q9_1: 5, Q9_2: 0 }, sectionA)).toEqual([]);
  });

  it('ignores error findings whose fields are outside the given section', () => {
    // A later section that does not own Q4/Q9 must not block on a tenure error.
    expect(sectionBlockingErrors({ Q4: 30, Q9_1: 15 }, new Set(['Q31', 'Q41']))).toEqual([]);
  });

  it('does not block on warn-severity findings (e.g. PROF-04 weekly workload)', () => {
    // Q10 × Q11 = 91 > 80 → PROF-04 (warn), not a hard block.
    const out = sectionBlockingErrors({ Q10: 7, Q11: 13 }, new Set(['Q10', 'Q11']));
    expect(out).toEqual([]);
  });
});
