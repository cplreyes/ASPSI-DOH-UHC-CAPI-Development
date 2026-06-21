import { describe, it, expect } from 'vitest';
import { shouldShow, shouldShowSection } from './skip-logic';

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
      expect(shouldShow('B', 'Q14', { Q12: 'Yes', Q13: 'No, and no plans in next 1–2 years' })).toBe(false);
    });

    it('shows Q14 when Q12 is Yes and Q13 starts with Yes', () => {
      expect(shouldShow('B', 'Q14', { Q12: 'Yes', Q13: 'Yes, direct result of UHC Act' })).toBe(true);
    });

    it('hides Q14 when Q13 is unanswered', () => {
      expect(shouldShow('B', 'Q14', { Q12: 'Yes' })).toBe(false);
    });

    it('hides Q14 when Q12 is No (entire Q13–Q30 block hidden)', () => {
      expect(shouldShow('B', 'Q14', { Q12: 'No', Q13: 'Yes, direct result of UHC Act' })).toBe(false);
    });
  });

  describe('Section C', () => {
    it('hides Q36 when Q34 is not Yes', () => {
      expect(shouldShow('C', 'Q36', { Q31: 'Yes', Q34: 'No' })).toBe(false);
    });

    it('shows Q36 when Q31 is Yes and Q34 is Yes', () => {
      expect(shouldShow('C', 'Q36', { Q31: 'Yes', Q34: 'Yes' })).toBe(true);
    });

    it('hides Q36 when Q31 is No (entire Q32–Q40 block hidden)', () => {
      expect(shouldShow('C', 'Q36', { Q31: 'No', Q34: 'Yes' })).toBe(false);
    });

    // R3 #308: F2-Skip-Logic "Apr 20 improvement" — an already-accredited
    // respondent (Q34=Yes) skips the entire Section C tail (Q37–Q40) to
    // Q41. Q38 "would you consider becoming accredited?" is nonsensical for
    // a facility that already is, so it must be hidden when Q34=Yes.
    it('hides Q38 when Q34 is Yes (already accredited — skip C tail)', () => {
      expect(shouldShow('C', 'Q38', { Q31: 'Yes', Q34: 'Yes' })).toBe(false);
    });

    it('shows Q38 when Q31=Yes and Q34=No (consider-accreditation path)', () => {
      expect(shouldShow('C', 'Q38', { Q31: 'Yes', Q34: 'No' })).toBe(true);
    });

    it('hides Q39/Q40 when Q34=Yes (gated behind the now-hidden Q38)', () => {
      expect(shouldShow('C', 'Q39', { Q31: 'Yes', Q34: 'Yes' })).toBe(false);
      expect(shouldShow('C', 'Q40', { Q31: 'Yes', Q34: 'Yes' })).toBe(false);
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
    // Tests use Q5='Nurse' (in SECTION_CDE_ROLES) so the R2-#117 role gate
    // doesn't suppress E1. The role-gating tests for Q48-Q52 live in the
    // shouldShowSection block below.
    it('hides Q52 when Q48 is No', () => {
      expect(shouldShow('E', 'Q52', { Q5: 'Nurse', Q48: 'No', Q49: 'Yes' })).toBe(false);
    });

    it("hides Q52 when Q49 is No or I don't know", () => {
      expect(shouldShow('E', 'Q52', { Q5: 'Nurse', Q48: 'Yes', Q49: 'No' })).toBe(false);
      expect(shouldShow('E', 'Q52', { Q5: 'Nurse', Q48: 'Yes', Q49: "I don't know" })).toBe(false);
    });

    it('shows Q52 when both Q48 and Q49 are Yes', () => {
      expect(shouldShow('E', 'Q52', { Q5: 'Nurse', Q48: 'Yes', Q49: 'Yes' })).toBe(true);
    });

    // R2-#117: Q48-Q52 hidden for Pharmacist/Dispenser even with Q48/Q49=Yes
    it('R2-#117: hides Q48 (BUCAS gate) for Pharmacist/Dispenser', () => {
      expect(shouldShow('E', 'Q48', { Q5: 'Pharmacist/Dispenser' })).toBe(false);
    });

    it('R2-#117: hides Q52 for Pharmacist/Dispenser even with Q48/Q49=Yes', () => {
      expect(
        shouldShow('E', 'Q52', { Q5: 'Pharmacist/Dispenser', Q48: 'Yes', Q49: 'Yes' }),
      ).toBe(false);
    });

    it('shows Q48 (BUCAS gate) for the 5 patient-care CDE roles', () => {
      const cdeRoles = ['Administrator', 'Physician/Doctor', 'Nurse', 'Midwife', 'Dentist'];
      for (const role of cdeRoles) {
        expect(shouldShow('E', 'Q48', { Q5: role })).toBe(true);
      }
    });

    // #539: Physician assistant and Nutrition action officer/coordinator were in
    // the R2 CDE set; the updated spec excludes them, so the E1 BUCAS gate must
    // hide Q48 for both.
    it('#539: hides Q48 for Physician assistant and Nutrition action officer/coordinator', () => {
      expect(shouldShow('E', 'Q48', { Q5: 'Physician assistant' })).toBe(false);
      expect(shouldShow('E', 'Q48', { Q5: 'Nutrition action officer/ coordinator' })).toBe(false);
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

// shouldShowSection gates which sections each Q5 role sees.
//
// Spec (updated tester-guide, #539 — supersedes the R2-#114 list):
//   C/D/E1:           Administrator, Physician/Doctor, Nurse, Midwife, Dentist.
//   E2 only:          Pharmacist/Dispenser — skips C/D/E1, answers E2 (Q53–Q55)
//                     via the item-level gates; Section E shows for them.
//   None of C/D/E:    Physician assistant, Nursing assistant, Lab tech, Med
//                     tech, Health promotion officer, Nutrition action
//                     officer/coordinator, Physical Therapist, Dentist aide,
//                     BHW, Other — proceed to F.
//   G:                Physician/Doctor, Dentist only.
//
// #539 (Aidan re-test 2026-06-16): Physician assistant and Nutrition action
// officer/coordinator were leaking C/D/E from the R2 list; Physician assistant
// was also leaking G. The fix removed all three from their respective sets.
describe('shouldShowSection', () => {
  describe('Section G — physicians and dentists only', () => {
    it('shows G for Physician/Doctor', () => {
      expect(shouldShowSection('G', { Q5: 'Physician/Doctor' })).toBe(true);
    });

    it('#539: hides G for Physician assistant', () => {
      expect(shouldShowSection('G', { Q5: 'Physician assistant' })).toBe(false);
    });

    it('shows G for Dentist', () => {
      expect(shouldShowSection('G', { Q5: 'Dentist' })).toBe(true);
    });

    it('hides G for Nurse', () => {
      expect(shouldShowSection('G', { Q5: 'Nurse' })).toBe(false);
    });

    it('hides G for Pharmacist/Dispenser', () => {
      expect(shouldShowSection('G', { Q5: 'Pharmacist/Dispenser' })).toBe(false);
    });

    it('hides G when Q5 is unset', () => {
      expect(shouldShowSection('G', {})).toBe(false);
    });
  });

  describe('Section C — patient-care roles only', () => {
    it.each([
      'Administrator',
      'Physician/Doctor',
      'Nurse',
      'Midwife',
      'Dentist',
    ])('shows C for %s', (role) => {
      expect(shouldShowSection('C', { Q5: role })).toBe(true);
    });

    it.each([
      'Pharmacist/Dispenser',
      'Physician assistant', // #539
      'Nursing assistant',
      'Laboratory technician',
      'Medical/ radiologic technologist',
      'Health promotion officer',
      'Nutrition action officer/ coordinator', // #539
      'Physical Therapist',
      'Dentist aide',
      'Barangay Health Worker',
      'Other (specify)',
    ])('hides C for %s', (role) => {
      expect(shouldShowSection('C', { Q5: role })).toBe(false);
    });

    it('hides C when Q5 is unset', () => {
      expect(shouldShowSection('C', {})).toBe(false);
    });
  });

  describe('Section D — patient-care roles only (same set as C)', () => {
    it('shows D for Nurse', () => {
      expect(shouldShowSection('D', { Q5: 'Nurse' })).toBe(true);
    });

    it('hides D for Pharmacist/Dispenser', () => {
      expect(shouldShowSection('D', { Q5: 'Pharmacist/Dispenser' })).toBe(false);
    });

    it('hides D for Dentist aide', () => {
      expect(shouldShowSection('D', { Q5: 'Dentist aide' })).toBe(false);
    });
  });

  describe('Section E — patient-care + pharmacists (broader than C/D)', () => {
    it.each([
      'Administrator',
      'Physician/Doctor',
      'Nurse',
      'Midwife',
      'Dentist',
      'Pharmacist/Dispenser', // E2 GAMOT half — sees E (item gates hide E1 Q48–Q52)
    ])('shows E for %s', (role) => {
      expect(shouldShowSection('E', { Q5: role })).toBe(true);
    });

    it.each([
      'Physician assistant', // #539
      'Nursing assistant',
      'Laboratory technician',
      'Medical/ radiologic technologist',
      'Health promotion officer',
      'Nutrition action officer/ coordinator', // #539
      'Physical Therapist',
      'Dentist aide',
      'Barangay Health Worker',
      'Other (specify)',
    ])('hides E for %s', (role) => {
      expect(shouldShowSection('E', { Q5: role })).toBe(false);
    });
  });

  describe('Always-shown sections', () => {
    it.each(['A', 'B', 'F', 'H', 'I', 'J'])('shows %s regardless of Q5', (sectionId) => {
      expect(shouldShowSection(sectionId, { Q5: 'Dentist aide' })).toBe(true);
      expect(shouldShowSection(sectionId, { Q5: 'Nurse' })).toBe(true);
      expect(shouldShowSection(sectionId, {})).toBe(true);
    });
  });

  describe('Persona section-visibility (R2 #114 + #539)', () => {
    it('Pharmacist/Dispenser sees A,B,E,F,H,I,J — not C,D,G', () => {
      const v = { Q5: 'Pharmacist/Dispenser' };
      expect(shouldShowSection('A', v)).toBe(true);
      expect(shouldShowSection('B', v)).toBe(true);
      expect(shouldShowSection('C', v)).toBe(false); // was the bug
      expect(shouldShowSection('D', v)).toBe(false); // was the bug
      expect(shouldShowSection('E', v)).toBe(true); // E2 path
      expect(shouldShowSection('F', v)).toBe(true);
      expect(shouldShowSection('G', v)).toBe(false);
      expect(shouldShowSection('H', v)).toBe(true);
    });

    it('Physician/Doctor sees all sections', () => {
      const v = { Q5: 'Physician/Doctor' };
      for (const id of ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
    });

    it('Dentist aide sees A,B,F,H,I,J — not C,D,E,G (skip to F)', () => {
      const v = { Q5: 'Dentist aide' };
      expect(shouldShowSection('A', v)).toBe(true);
      expect(shouldShowSection('B', v)).toBe(true);
      expect(shouldShowSection('C', v)).toBe(false); // was the bug
      expect(shouldShowSection('D', v)).toBe(false); // was the bug
      expect(shouldShowSection('E', v)).toBe(false); // was the bug
      expect(shouldShowSection('F', v)).toBe(true);
      expect(shouldShowSection('G', v)).toBe(false);
    });

    // #539 (Aidan re-test 2026-06-16): these two roles leaked C/D/E.
    it('#539: Physician assistant sees A,B,F,H,I,J — not C,D,E,G', () => {
      const v = { Q5: 'Physician assistant' };
      expect(shouldShowSection('C', v)).toBe(false);
      expect(shouldShowSection('D', v)).toBe(false);
      expect(shouldShowSection('E', v)).toBe(false);
      expect(shouldShowSection('G', v)).toBe(false);
      for (const id of ['A', 'B', 'F', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
    });

    it('#539: Nutrition action officer/coordinator sees A,B,F,H,I,J — not C,D,E,G', () => {
      const v = { Q5: 'Nutrition action officer/ coordinator' };
      expect(shouldShowSection('C', v)).toBe(false);
      expect(shouldShowSection('D', v)).toBe(false);
      expect(shouldShowSection('E', v)).toBe(false);
      expect(shouldShowSection('G', v)).toBe(false);
      for (const id of ['A', 'B', 'F', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
    });
  });
});
