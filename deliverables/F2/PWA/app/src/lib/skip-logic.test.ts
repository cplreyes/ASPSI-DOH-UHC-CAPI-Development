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
      expect(shouldShow('B', 'Q14', { Q13: 'No, and no plans in next 1–2 years' })).toBe(false);
    });

    it('shows Q14 when Q13 starts with Yes', () => {
      expect(shouldShow('B', 'Q14', { Q13: 'Yes, direct result of UHC Act' })).toBe(true);
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

  describe('Section D', () => {
    it('hides Q38 and Q39 when Q37 is No', () => {
      expect(shouldShow('D', 'Q38', { Q37: 'No' })).toBe(false);
      expect(shouldShow('D', 'Q39', { Q37: 'No' })).toBe(false);
    });

    it('shows Q38 and Q39 when Q37 is Yes', () => {
      expect(shouldShow('D', 'Q38', { Q37: 'Yes' })).toBe(true);
      expect(shouldShow('D', 'Q39', { Q37: 'Yes' })).toBe(true);
    });

    it('hides Q41 and Q42 when Q40 is No', () => {
      expect(shouldShow('D', 'Q41', { Q40: 'No' })).toBe(false);
      expect(shouldShow('D', 'Q42', { Q40: 'No' })).toBe(false);
    });

    it('shows Q41 and Q42 when Q40 is Yes', () => {
      expect(shouldShow('D', 'Q41', { Q40: 'Yes' })).toBe(true);
      expect(shouldShow('D', 'Q42', { Q40: 'Yes' })).toBe(true);
    });
  });

  describe('Section E1', () => {
    it('hides Q45 when Q43 is No', () => {
      expect(shouldShow('E1', 'Q45', { Q43: 'No', Q44: 'Yes' })).toBe(false);
    });

    it("hides Q45 when Q44 is No or I don't know", () => {
      expect(shouldShow('E1', 'Q45', { Q43: 'Yes', Q44: 'No' })).toBe(false);
      expect(shouldShow('E1', 'Q45', { Q43: 'Yes', Q44: "I don't know" })).toBe(false);
    });

    it('shows Q45 when both Q43 and Q44 are Yes', () => {
      expect(shouldShow('E1', 'Q45', { Q43: 'Yes', Q44: 'Yes' })).toBe(true);
    });
  });

  describe('Section E2', () => {
    it('hides Q48 when Q46 is No', () => {
      expect(shouldShow('E2', 'Q48', { Q46: 'No', Q47: 'Yes' })).toBe(false);
    });

    it('hides Q48 when Q47 is No', () => {
      expect(shouldShow('E2', 'Q48', { Q46: 'Yes', Q47: 'No' })).toBe(false);
    });

    it('shows Q48 when both Q46 and Q47 are Yes', () => {
      expect(shouldShow('E2', 'Q48', { Q46: 'Yes', Q47: 'Yes' })).toBe(true);
    });
  });

  describe('Section F', () => {
    it('hides Q55 when Q54 is a satisfied variant', () => {
      expect(shouldShow('F', 'Q55', { Q54: 'Very Satisfied: Minor improvements needed…' })).toBe(
        false,
      );
      expect(shouldShow('F', 'Q55', { Q54: 'Satisfied: Some improvements needed…' })).toBe(false);
      expect(
        shouldShow('F', 'Q55', {
          Q54: 'Neither Satisfied nor Dissatisfied: Improvements needed, but generally functional',
        }),
      ).toBe(false);
    });

    it('shows Q55 when Q54 is Dissatisfied or Very Dissatisfied', () => {
      expect(shouldShow('F', 'Q55', { Q54: 'Dissatisfied: Moderate improvements needed…' })).toBe(
        true,
      );
      expect(shouldShow('F', 'Q55', { Q54: 'Very Dissatisfied: Major improvements needed…' })).toBe(
        true,
      );
    });
  });

  describe('Section G', () => {
    it('shows Q57 when Q56 is Yes and hides otherwise', () => {
      expect(shouldShow('G', 'Q57', { Q56: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q57', { Q56: 'No' })).toBe(false);
    });

    it('shows Q58 only when Q57 is No', () => {
      expect(shouldShow('G', 'Q58', { Q57: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q58', { Q57: 'Yes' })).toBe(false);
    });

    it('shows Q60 when Q59 is Yes', () => {
      expect(shouldShow('G', 'Q60', { Q59: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q60', { Q59: 'No' })).toBe(false);
    });

    it('shows Q61 only when Q60 is No', () => {
      expect(shouldShow('G', 'Q61', { Q60: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q61', { Q60: 'Yes' })).toBe(false);
    });

    it('shows Q63 when either Q62 or Q62.1 is Yes', () => {
      expect(shouldShow('G', 'Q63', { Q62: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q63', { 'Q62.1': 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q63', { Q62: 'No', 'Q62.1': 'No' })).toBe(false);
    });

    it('shows Q65 only when Q64 is No', () => {
      expect(shouldShow('G', 'Q65', { Q64: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q65', { Q64: 'Yes' })).toBe(false);
    });

    it('shows Q79 when either Q78 or Q78.1 is Yes', () => {
      expect(shouldShow('G', 'Q79', { Q78: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q79', { 'Q78.1': 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q79', { Q78: 'No', 'Q78.1': 'No' })).toBe(false);
    });
  });

  describe('Section I', () => {
    it('hides Q87 when Q86 is Yes', () => {
      expect(shouldShow('I', 'Q87', { Q86: 'Yes' })).toBe(false);
    });

    it('shows Q87 when Q86 is No', () => {
      expect(shouldShow('I', 'Q87', { Q86: 'No' })).toBe(true);
    });
  });

  describe('Section J', () => {
    it('hides Q111 when Q103 is Never', () => {
      expect(shouldShow('J', 'Q111', { Q103: 'Never' })).toBe(false);
    });

    it('shows Q111 when Q103 is any other frequency', () => {
      expect(shouldShow('J', 'Q111', { Q103: 'Always' })).toBe(true);
      expect(shouldShow('J', 'Q111', { Q103: 'Seldom' })).toBe(true);
    });

    it('hides Q113 and Q114 when Q112 is No', () => {
      expect(shouldShow('J', 'Q113', { Q112: "No, I haven't thought about it" })).toBe(false);
      expect(shouldShow('J', 'Q114', { Q112: "No, I haven't thought about it" })).toBe(false);
    });

    it('shows Q113 and Q114 when Q112 starts with Yes,', () => {
      const yes = "Yes, I've thought about it and have definite plans to leave";
      expect(shouldShow('J', 'Q113', { Q112: yes })).toBe(true);
      expect(shouldShow('J', 'Q114', { Q112: yes })).toBe(true);
    });
  });
});
