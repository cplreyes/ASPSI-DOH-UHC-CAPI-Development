import { describe, it, expect } from 'vitest';
import { shouldShow } from './skip-logic';

describe('shouldShow', () => {
  it('returns true when no predicate is registered for the item', () => {
    expect(shouldShow('A', 'Q3', { Q5: 'Nurse' })).toBe(true);
  });

  describe('Section A', () => {
    it('hides Q6 when Q5 is not a role with specialty', () => {
      expect(shouldShow('A', 'Q6', { Q5: 'Pharmacist/Dispenser' })).toBe(false);
    });

    it('shows Q6 when Q5 is Physician/Doctor', () => {
      expect(shouldShow('A', 'Q6', { Q5: 'Physician/Doctor' })).toBe(true);
    });

    it('hides Q8 when Q7 is No', () => {
      expect(shouldShow('A', 'Q8', { Q7: 'No' })).toBe(false);
    });

    it('shows Q8 when Q7 is Yes', () => {
      expect(shouldShow('A', 'Q8', { Q7: 'Yes' })).toBe(true);
    });
  });

  describe('Section B', () => {
    it('hides Q14 when Q13 is a No variant', () => {
      expect(
        shouldShow('B', 'Q14', { Q13: 'No, and no plans in next 1–2 years' }),
      ).toBe(false);
    });

    it('shows Q14 when Q13 starts with Yes', () => {
      expect(
        shouldShow('B', 'Q14', { Q13: 'Yes, direct result of UHC Act' }),
      ).toBe(true);
    });

    it('hides Q14 when Q13 is unanswered', () => {
      expect(shouldShow('B', 'Q14', {})).toBe(false);
    });
  });

  describe('Section C', () => {
    it('hides Q32 when Q30 is not Yes', () => {
      expect(shouldShow('C', 'Q32', { Q30: 'No' })).toBe(false);
    });

    it('shows Q32 when Q30 is Yes', () => {
      expect(shouldShow('C', 'Q32', { Q30: 'Yes' })).toBe(true);
    });
  });
});
