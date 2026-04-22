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
    it('hides Q36 when Q34 is not Yes', () => {
      expect(shouldShow('C', 'Q36', { Q34: 'No' })).toBe(false);
    });

    it('shows Q36 when Q34 is Yes', () => {
      expect(shouldShow('C', 'Q36', { Q34: 'Yes' })).toBe(true);
    });
  });

  describe('Section D', () => {
    it('hides Q42 and Q43 when Q41 is No', () => {
      expect(shouldShow('D', 'Q42', { Q41: 'No' })).toBe(false);
      expect(shouldShow('D', 'Q43', { Q41: 'No' })).toBe(false);
    });

    it('shows Q42 and Q43 when Q41 is Yes', () => {
      expect(shouldShow('D', 'Q42', { Q41: 'Yes' })).toBe(true);
      expect(shouldShow('D', 'Q43', { Q41: 'Yes' })).toBe(true);
    });

    it('hides Q45 and Q46 when Q44 is No', () => {
      expect(shouldShow('D', 'Q45', { Q44: 'No' })).toBe(false);
      expect(shouldShow('D', 'Q46', { Q44: 'No' })).toBe(false);
    });

    it('shows Q45 and Q46 when Q44 is Yes', () => {
      expect(shouldShow('D', 'Q45', { Q44: 'Yes' })).toBe(true);
      expect(shouldShow('D', 'Q46', { Q44: 'Yes' })).toBe(true);
    });
  });

  describe('Section E (BUCAS half)', () => {
    it('hides Q52 when Q48 is No', () => {
      expect(shouldShow('E', 'Q52', { Q48: 'No', Q49: 'Yes' })).toBe(false);
    });

    it("hides Q52 when Q49 is No or I don't know", () => {
      expect(shouldShow('E', 'Q52', { Q48: 'Yes', Q49: 'No' })).toBe(false);
      expect(shouldShow('E', 'Q52', { Q48: 'Yes', Q49: "I don't know" })).toBe(false);
    });

    it('shows Q52 when both Q48 and Q49 are Yes', () => {
      expect(shouldShow('E', 'Q52', { Q48: 'Yes', Q49: 'Yes' })).toBe(true);
    });
  });

  describe('Section E (GAMOT half)', () => {
    it('hides Q55 when Q53 is No', () => {
      expect(shouldShow('E', 'Q55', { Q53: 'No', Q54: 'Yes' })).toBe(false);
    });

    it('hides Q55 when Q54 is No', () => {
      expect(shouldShow('E', 'Q55', { Q53: 'Yes', Q54: 'No' })).toBe(false);
    });

    it('shows Q55 when both Q53 and Q54 are Yes', () => {
      expect(shouldShow('E', 'Q55', { Q53: 'Yes', Q54: 'Yes' })).toBe(true);
    });
  });

  describe('Section F', () => {
    it('hides Q62 when Q61 is a satisfied variant', () => {
      expect(shouldShow('F', 'Q62', { Q61: 'Very Satisfied: Minor improvements needed…' })).toBe(
        false,
      );
      expect(shouldShow('F', 'Q62', { Q61: 'Satisfied: Some improvements needed…' })).toBe(false);
      expect(
        shouldShow('F', 'Q62', {
          Q61: 'Neither Satisfied nor Dissatisfied: Improvements needed, but generally functional',
        }),
      ).toBe(false);
    });

    it('shows Q62 when Q61 is Dissatisfied or Very Dissatisfied', () => {
      expect(shouldShow('F', 'Q62', { Q61: 'Dissatisfied: Moderate improvements needed…' })).toBe(
        true,
      );
      expect(shouldShow('F', 'Q62', { Q61: 'Very Dissatisfied: Major improvements needed…' })).toBe(
        true,
      );
    });
  });

  describe('Section G', () => {
    it('shows Q64 when Q63 is Yes and hides otherwise', () => {
      expect(shouldShow('G', 'Q64', { Q63: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q64', { Q63: 'No' })).toBe(false);
    });

    it('shows Q65 only when Q64 is No', () => {
      expect(shouldShow('G', 'Q65', { Q64: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q65', { Q64: 'Yes' })).toBe(false);
    });

    it('shows Q67 when Q66 is Yes', () => {
      expect(shouldShow('G', 'Q67', { Q66: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q67', { Q66: 'No' })).toBe(false);
    });

    it('shows Q68 only when Q67 is No', () => {
      expect(shouldShow('G', 'Q68', { Q67: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q68', { Q67: 'Yes' })).toBe(false);
    });

    it('shows Q71 when either Q69 or Q70 is Yes', () => {
      expect(shouldShow('G', 'Q71', { Q69: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q71', { 'Q70': 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q71', { Q69: 'No', 'Q70': 'No' })).toBe(false);
    });

    it('shows Q73 only when Q72 is No', () => {
      expect(shouldShow('G', 'Q73', { Q72: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q73', { Q72: 'Yes' })).toBe(false);
    });

    it('shows Q89 when either Q87 or Q88 is Yes', () => {
      expect(shouldShow('G', 'Q89', { Q87: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q89', { 'Q88': 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q89', { Q87: 'No', 'Q88': 'No' })).toBe(false);
    });
  });

  describe('Section I', () => {
    it('hides Q97 when Q96 is Yes', () => {
      expect(shouldShow('I', 'Q97', { Q96: 'Yes' })).toBe(false);
    });

    it('shows Q97 when Q96 is No', () => {
      expect(shouldShow('I', 'Q97', { Q96: 'No' })).toBe(true);
    });
  });

  describe('Section J', () => {
    it('hides Q122 when Q114 is Never', () => {
      expect(shouldShow('J', 'Q122', { Q114: 'Never' })).toBe(false);
    });

    it('shows Q122 when Q114 is any other frequency', () => {
      expect(shouldShow('J', 'Q122', { Q114: 'Always' })).toBe(true);
      expect(shouldShow('J', 'Q122', { Q114: 'Seldom' })).toBe(true);
    });

    it('hides Q124 and Q125 when Q123 is No', () => {
      expect(shouldShow('J', 'Q124', { Q123: "No, I haven't thought about it" })).toBe(false);
      expect(shouldShow('J', 'Q125', { Q123: "No, I haven't thought about it" })).toBe(false);
    });

    it('shows Q124 and Q125 when Q123 starts with Yes,', () => {
      const yes = "Yes, I've thought about it and have definite plans to leave";
      expect(shouldShow('J', 'Q124', { Q123: yes })).toBe(true);
      expect(shouldShow('J', 'Q125', { Q123: yes })).toBe(true);
    });
  });
});
