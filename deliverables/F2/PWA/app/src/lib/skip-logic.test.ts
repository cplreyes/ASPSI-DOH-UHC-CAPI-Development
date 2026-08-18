import { describe, it, expect } from 'vitest';
import { shouldShow, shouldShowSection } from './skip-logic';

describe('shouldShow', () => {
  it('returns true when no predicate is registered for the item', () => {
    expect(shouldShow('A', 'Q3', { Q5: 'Nurse' })).toBe(true);
  });

  describe('Section A', () => {
    it('hides Q6 when Q5 is not a role with specialty', () => {
      expect(shouldShow('A', 'Q6', { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist' })).toBe(false);
      // R6 #820: Nutrition-Dietician gets Q6 like Administrator/Nurse/Midwife.
      expect(shouldShow('A', 'Q6', { Q5: 'Nutrition action officer/coordinator/Nutritionist-Dietician' })).toBe(true);
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

    // aug17 migration (Task 3.2, 2026-08-19): the eleven new `.1`/`.2`
    // UHC-attribution sub-items. Q13/Q13.1 stands in as the representative
    // two-step battery pair (base No → probe hidden; base Yes → probe
    // visible) — the same shape repeats for Q15.1/Q17.1/.../Q24.1.
    describe('the .1/.2 UHC-attribution sub-items (new in Aug-17)', () => {
      it('hides Q13.1 when Q13 is No (two-step pair: base No → probe hidden)', () => {
        expect(shouldShow('B', 'Q13.1', { Q12: 'Yes', Q13: 'No' })).toBe(false);
      });

      it('shows Q13.1 when Q13 is Yes (two-step pair: base Yes → probe visible)', () => {
        expect(shouldShow('B', 'Q13.1', { Q12: 'Yes', Q13: 'Yes' })).toBe(true);
      });

      it('hides Q13.1 when Q13 is unanswered', () => {
        expect(shouldShow('B', 'Q13.1', { Q12: 'Yes' })).toBe(false);
      });

      it('hides Q13.1 when Q12 is No (outer Section-B gate still applies)', () => {
        expect(shouldShow('B', 'Q13.1', { Q12: 'No', Q13: 'Yes' })).toBe(false);
      });

      it('gates each sub-item on its own parent, not a sibling', () => {
        expect(shouldShow('B', 'Q15.1', { Q12: 'Yes', Q15: 'Yes', Q17: 'No' })).toBe(true);
        expect(shouldShow('B', 'Q17.1', { Q12: 'Yes', Q15: 'Yes', Q17: 'No' })).toBe(false);
        expect(shouldShow('B', 'Q18.1', { Q12: 'Yes', Q18: 'Yes' })).toBe(true);
        expect(shouldShow('B', 'Q19.1', { Q12: 'Yes', Q19: 'No' })).toBe(false);
        expect(shouldShow('B', 'Q20.1', { Q12: 'Yes', Q20: 'Yes' })).toBe(true);
        expect(shouldShow('B', 'Q21.1', { Q12: 'Yes', Q21: 'No' })).toBe(false);
        expect(shouldShow('B', 'Q22.1', { Q12: 'Yes', Q22: 'Yes' })).toBe(true);
        expect(shouldShow('B', 'Q23.1', { Q12: 'Yes', Q23: 'No' })).toBe(false);
      });

      it('Q24.1 and Q24.2 are independent siblings, both gated on Q24=Yes', () => {
        expect(shouldShow('B', 'Q24.1', { Q12: 'Yes', Q24: 'Yes' })).toBe(true);
        expect(shouldShow('B', 'Q24.2', { Q12: 'Yes', Q24: 'Yes' })).toBe(true);
        expect(shouldShow('B', 'Q24.1', { Q12: 'Yes', Q24: 'No' })).toBe(false);
        expect(shouldShow('B', 'Q24.2', { Q12: 'Yes', Q24: 'No' })).toBe(false);
      });
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

    // aug17 migration (Task 3.2, 2026-08-19): Q34 also has "I don't know…"
    // and "Other (specify)" options besides Yes/No. F2-inventory.md's fuller
    // routing table documents the paper's "I don't know" option as an
    // explicit <proceed to Q41> — skips the whole C tail like Q34=Yes does,
    // not just Q37 like Q34=No. See aug17-approved-divergences.md.
    it("hides Q37/Q38 (whole C tail) when Q34 is \"I don't know\" (paper's own routing note)", () => {
      const idk = "I don't know what PhilHealth YAKAP/Konsulta package accreditation is";
      expect(shouldShow('C', 'Q37', { Q31: 'Yes', Q34: idk })).toBe(false);
      expect(shouldShow('C', 'Q38', { Q31: 'Yes', Q34: idk })).toBe(false);
    });

    it('hides Q37/Q38 (whole C tail) when Q34 is Other (specify) (undocumented option, same fallthrough)', () => {
      expect(shouldShow('C', 'Q37', { Q31: 'Yes', Q34: 'Other (specify)' })).toBe(false);
      expect(shouldShow('C', 'Q38', { Q31: 'Yes', Q34: 'Other (specify)' })).toBe(false);
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
      expect(shouldShow('E', 'Q48', { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist' })).toBe(false);
    });

    it('R2-#117: hides Q52 for Pharmacist/Dispenser even with Q48/Q49=Yes', () => {
      expect(
        shouldShow('E', 'Q52', { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist', Q48: 'Yes', Q49: 'Yes' }),
      ).toBe(false);
    });

    it('shows Q48 (BUCAS gate) for the 5 patient-care CDE roles', () => {
      const cdeRoles = ['Administrator', 'Physician/Doctor', 'Nurse', 'Midwife', 'Dentist'];
      for (const role of cdeRoles) {
        expect(shouldShow('E', 'Q48', { Q5: role })).toBe(true);
      }
    });

    // #539 excluded Physician assistant and the Nutrition role from the CDE
    // set; R6 #820 restores the (renamed) Nutrition-Dietician role. Physician
    // assistant stays excluded.
    it('#539/#820: hides Q48 for Physician assistant; shows it for Nutrition-Dietician', () => {
      expect(shouldShow('E', 'Q48', { Q5: 'Physician assistant' })).toBe(false);
      expect(shouldShow('E', 'Q48', { Q5: 'Nutrition action officer/coordinator/Nutritionist-Dietician' })).toBe(true);
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

    it('R6 #817: shows Q71a only when Q69 (ZBB) is Yes', () => {
      expect(shouldShow('G', 'Q71a', { Q69: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q71a', { Q69: 'No', Q70: 'Yes' })).toBe(false);
      expect(shouldShow('G', 'Q71a', {})).toBe(false);
    });

    it('R6 #817: shows Q71b only when Q70 (NBB) is Yes', () => {
      expect(shouldShow('G', 'Q71b', { Q70: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q71b', { Q70: 'No', Q69: 'Yes' })).toBe(false);
      expect(shouldShow('G', 'Q71b', {})).toBe(false);
    });

    it('R6 #821: shows Q88 regardless of Q87 answer (skip removed)', () => {
      expect(shouldShow('G', 'Q88', { Q87: 'No' })).toBe(true);
      expect(shouldShow('G', 'Q88', { Q87: 'Yes' })).toBe(true);
      expect(shouldShow('G', 'Q88', {})).toBe(true);
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

  // aug17 migration (Task 3.1, 2026-08-19): mechanical re-key per
  // maps/F2-renames.csv — Q108 gap retired, Section J ids from the old Q109
  // onward shift down by one (Q122→Q121, Q124→Q123, Q125→Q124; dependency
  // refs Q114→Q113, Q123→Q122). Same predicates under the new ids.
  describe('Section J', () => {
    it('hides Q121 when Q113 is Never', () => {
      expect(shouldShow('J', 'Q121', { Q113: 'Never' })).toBe(false);
    });

    it('shows Q121 when Q113 is any other frequency', () => {
      expect(shouldShow('J', 'Q121', { Q113: 'Always' })).toBe(true);
      expect(shouldShow('J', 'Q121', { Q113: 'Seldom' })).toBe(true);
    });

    it('hides Q123 and Q124 when Q122 is No', () => {
      expect(shouldShow('J', 'Q123', { Q122: "No, I haven't thought about it" })).toBe(false);
      expect(shouldShow('J', 'Q124', { Q122: "No, I haven't thought about it" })).toBe(false);
    });

    it('shows Q123 and Q124 when Q122 starts with Yes,', () => {
      const yes = "Yes, I've thought about it and have definite plans to leave";
      expect(shouldShow('J', 'Q123', { Q122: yes })).toBe(true);
      expect(shouldShow('J', 'Q124', { Q122: yes })).toBe(true);
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

    it('hides G for Pharmacist/Dispenser/Assistant Pharmacist', () => {
      expect(shouldShowSection('G', { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist' })).toBe(false);
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
      'Nutrition action officer/coordinator/Nutritionist-Dietician', // R6 #820
    ])('shows C for %s', (role) => {
      expect(shouldShowSection('C', { Q5: role })).toBe(true);
    });

    it.each([
      'Pharmacist/Dispenser/Assistant Pharmacist',
      'Physician assistant', // #539
      'Nursing assistant',
      'Laboratory technician',
      'Medical/ radiologic technologist',
      'Health promotion officer',
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

    it('hides D for Pharmacist/Dispenser/Assistant Pharmacist', () => {
      expect(shouldShowSection('D', { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist' })).toBe(false);
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
      'Nutrition action officer/coordinator/Nutritionist-Dietician', // R6 #820
      'Pharmacist/Dispenser/Assistant Pharmacist', // E2 GAMOT half — sees E (item gates hide E1 Q48–Q52)
    ])('shows E for %s', (role) => {
      expect(shouldShowSection('E', { Q5: role })).toBe(true);
    });

    it.each([
      'Physician assistant', // #539
      'Nursing assistant',
      'Laboratory technician',
      'Medical/ radiologic technologist',
      'Health promotion officer',
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
    it('Pharmacist/Dispenser/Assistant Pharmacist sees A,B,E,F,H,I,J — not C,D,G', () => {
      const v = { Q5: 'Pharmacist/Dispenser/Assistant Pharmacist' };
      expect(shouldShowSection('A', v)).toBe(true);
      expect(shouldShowSection('B', v)).toBe(true);
      expect(shouldShowSection('C', v)).toBe(false); // was the bug
      expect(shouldShowSection('D', v)).toBe(false); // was the bug
      expect(shouldShowSection('E', v)).toBe(true); // E2 path
      expect(shouldShowSection('F', v)).toBe(true);
      expect(shouldShowSection('G', v)).toBe(false);
      expect(shouldShowSection('H', v)).toBe(true);
    });

    it('Physician/Doctor sees all sections (physician path — reaches G)', () => {
      const v = { Q5: 'Physician/Doctor' };
      for (const id of ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
    });

    // aug17 migration (Task 3.2, 2026-08-19): nurse path — one of the 6
    // SECTION_CDE_ROLES/SECTION_E_ROLES patient-care roles; sees C/D/E1/E2
    // (item-level Q48–Q52 gates admit it) but not G (physicians/dentists only).
    it('Nurse sees A,B,C,D,E,F,H,I,J — not G (nurse path, patient-care role)', () => {
      const v = { Q5: 'Nurse' };
      for (const id of ['A', 'B', 'C', 'D', 'E', 'F', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
      expect(shouldShowSection('G', v)).toBe(false);
      expect(shouldShow('E', 'Q48', v)).toBe(true); // reaches E1 (BUCAS), unlike the pharmacist path
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

    it('R6 #820 (supersedes #539): Nutrition-Dietician sees A,B,C,D,E,F,H,I,J — not G', () => {
      const v = { Q5: 'Nutrition action officer/coordinator/Nutritionist-Dietician' };
      expect(shouldShowSection('G', v)).toBe(false);
      for (const id of ['A', 'B', 'C', 'D', 'E', 'F', 'H', 'I', 'J']) {
        expect(shouldShowSection(id, v)).toBe(true);
      }
    });
  });
});
