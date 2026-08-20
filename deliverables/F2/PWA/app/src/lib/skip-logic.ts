export type FormValues = Record<string, unknown>;
type Predicate = (values: FormValues) => boolean;

// #539: Section G is restricted to physicians and dentists only. The R2-#114
// list also included 'Physician assistant'; the updated tester-guide spec
// excludes it ("Only Physicians/Doctors, and Dentist should answer Section G").
const SECTION_G_ROLES = new Set(['Physician/Doctor', 'Dentist']);

// Sections C/D/E are role-gated to patient-care roles. shouldShowSection gates
// C/D on SECTION_CDE_ROLES and E on SECTION_E_ROLES; the E2 (GAMOT) half adds
// pharmacists/dispensers, who skip E1 (Q48–Q52) but answer E2 (Q53–Q55) via the
// item-level gates below.
//
// Per the updated tester-guide spec (#539 — supersedes the R2-#114 list):
//   - C/D/E1: Administrator, Physician/Doctor, Nurse, Midwife, Dentist.
//   - E2 only: Pharmacist/Dispenser (skip C/D/E1, answer the E2 GAMOT half).
//   - None of C/D/E — proceed to F: Physician assistant, Nursing assistant,
//            Laboratory technician, Medical/radiologic technologist, Health
//            promotion officer, Nutrition action officer/coordinator, Physical
//            Therapist, Dentist aide, Barangay Health Worker, Other.
//
// #539: 'Physician assistant' and 'Nutrition action officer/ coordinator' were
// in the R2-#114 set; the new spec excludes both. They leaked C/D/E to those
// two personas (Aidan re-test 2026-06-16) until removed here.
// R6 #820 (2026-07-02) SUPERSEDES #539 for the Nutrition role only: the role
// routes with Administrator/Nurse/Midwife again (C/D/E1/E2; still not G) —
// the paper's own C/D/E1 gates include nutritionists-dieticians.
// 'Physician assistant' stays excluded.
// aug17 migration (R12, Task 3.2, 2026-08-19): the Nutrition and Pharmacist
// role VALUES below are reworded to the Aug-17 paper's verbatim Q5 print
// order/wording ('Nutrition action officer/coordinator/Nutritionist-Dietician',
// 'Pharmacist/Dispenser/Assistant Pharmacist') — was
// 'Nutrition-Dietician or Nutrition Action Officer/Coordinator' /
// 'Pharmacist/Dispenser or Assistant Pharmacist' (Apr-20 build wording, kept
// through Task 3.1 to avoid breaking gating mid-spec-rewrite). Role
// MEMBERSHIP is unchanged — same 6 roles in C/D/E1, same +1 pharmacist in E2
// — only the string values change. See spec/F2-Spec.md Q5 row +
// aug17-approved-divergences.md is NOT touched here since post-rename the
// build's Q5 values now match the paper exactly (no divergence to register).
// Exported so cross-field.ts (the C/D data-quality gate, GATE-05) shares one
// source of truth and can't drift from the section gate — the drift that let
// #539 slip in.
export const SECTION_CDE_ROLES = new Set([
  'Administrator',
  'Physician/Doctor',
  'Nurse',
  'Midwife',
  'Dentist',
  // R6 #820: routed like Administrator/Nurse/Midwife (supersedes #539 for
  // this one role). Value reworded R12/Task 3.2 — see comment block above.
  'Nutrition action officer/coordinator/Nutritionist-Dietician',
]);
const SECTION_E_ROLES = new Set([
  ...SECTION_CDE_ROLES,
  // R6 #820: renamed from 'Pharmacist/Dispenser'. Value reworded R12/Task
  // 3.2 — see comment block above.
  'Pharmacist/Dispenser/Assistant Pharmacist',
]);

const ROLES_WITH_SPECIALTY = new Set([
  'Administrator',
  'Physician/Doctor',
  'Physician assistant',
  'Nurse',
  'Midwife',
  'Dentist',
  // R6 #820: same Section A treatment as Administrator/Nurse/Midwife (the
  // Q6 choice filter still limits non-MD roles to the role-agnostic
  // options). Value reworded R12/Task 3.2 — see comment block above.
  'Nutrition action officer/coordinator/Nutritionist-Dietician',
]);

// Q6 specialty list filter — roles whose specialties match the medical-doctor list (Q6's
// current choice set: Anesthesia, Dermatology, Internal Medicine, etc.). Other roles in
// ROLES_WITH_SPECIALTY get only the role-agnostic options ("No specialty", "Others (specify)").
const MD_SPECIALTY_ROLES = new Set(['Physician/Doctor', 'Physician assistant']);
const ROLE_AGNOSTIC_SPECIALTY_VALUES = new Set(['No specialty', 'Others (specify)']);

const isYes = (v: unknown) => v === 'Yes';

const isDissatisfied = (v: unknown) => {
  if (typeof v !== 'string') return false;
  return v.startsWith('Dissatisfied') || v.startsWith('Very Dissatisfied');
};

// aug17 migration (Task 3.1, 2026-08-19): renamed from q123IsYes — the item
// this gates on is Q122 in the Aug-17 renumber (was Q123 pre-renumber; the
// Q108 gap retirement shifts every Section J id from the old Q109 onward
// down by one). Pure re-key, same predicate.
const q122IsYes = (v: unknown) => typeof v === 'string' && v.startsWith('Yes,');

const q25Includes = (v: FormValues, choice: string) =>
  Array.isArray(v.Q25) && (v.Q25 as string[]).includes(choice);

const predicates: Record<string, Record<string, Predicate>> = {
  A: {
    Q6: (v) => typeof v.Q5 === 'string' && ROLES_WITH_SPECIALTY.has(v.Q5),
    Q8: (v) => v.Q7 === 'Yes',
  },
  B: {
    // Q12=No → skip to Section C (Q31); entire Q13–Q30 block hidden
    Q13: (v) => v.Q12 === 'Yes',
    Q14: (v) => v.Q12 === 'Yes' && typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
    Q15: (v) => v.Q12 === 'Yes',
    Q16: (v) => v.Q12 === 'Yes' && typeof v.Q15 === 'string' && v.Q15.startsWith('Yes'),
    Q17: (v) => v.Q12 === 'Yes',
    Q18: (v) => v.Q12 === 'Yes',
    Q19: (v) => v.Q12 === 'Yes',
    Q20: (v) => v.Q12 === 'Yes',
    Q21: (v) => v.Q12 === 'Yes',
    Q22: (v) => v.Q12 === 'Yes',
    Q23: (v) => v.Q12 === 'Yes',
    Q24: (v) => v.Q12 === 'Yes',
    // aug17 migration (Task 3.2, 2026-08-19): the eleven new UHC-attribution
    // sub-items (spec.md's Section-B rewrite, Task 3.1) — each shows only when
    // its parent Yes/No stem was answered Yes.
    //
    // #1291 (UAT R7, 2026-08-20): these keys WERE quoted literal dots
    // ('Q13_1'), mirroring the paper's printed sub-item number. That is what
    // broke the battery: react-hook-form parses '.' as a nested path, so the
    // matching item id made register() address `values.Q13['1']` and destroy
    // the parent's answer. Ids are now underscored (parse-spec.ts rewrites
    // them; the printed number survives as displayNumber), so these keys are
    // plain identifiers. A side benefit: `loadConditionalItemKeys()` in
    // parse-spec.ts only matches UNQUOTED keys, so these eleven are now
    // auto-detected as conditional from here too, instead of relying solely on
    // each row's spec `required: conditional` column.
    Q13_1: (v) => v.Q12 === 'Yes' && typeof v.Q13 === 'string' && v.Q13.startsWith('Yes'),
    Q15_1: (v) => v.Q12 === 'Yes' && typeof v.Q15 === 'string' && v.Q15.startsWith('Yes'),
    Q17_1: (v) => v.Q12 === 'Yes' && typeof v.Q17 === 'string' && v.Q17.startsWith('Yes'),
    Q18_1: (v) => v.Q12 === 'Yes' && typeof v.Q18 === 'string' && v.Q18.startsWith('Yes'),
    Q19_1: (v) => v.Q12 === 'Yes' && typeof v.Q19 === 'string' && v.Q19.startsWith('Yes'),
    Q20_1: (v) => v.Q12 === 'Yes' && typeof v.Q20 === 'string' && v.Q20.startsWith('Yes'),
    Q21_1: (v) => v.Q12 === 'Yes' && typeof v.Q21 === 'string' && v.Q21.startsWith('Yes'),
    Q22_1: (v) => v.Q12 === 'Yes' && typeof v.Q22 === 'string' && v.Q22.startsWith('Yes'),
    Q23_1: (v) => v.Q12 === 'Yes' && typeof v.Q23 === 'string' && v.Q23.startsWith('Yes'),
    Q24_1: (v) => v.Q12 === 'Yes' && typeof v.Q24 === 'string' && v.Q24.startsWith('Yes'),
    // Q24's second sub-item (primary care quality measures) — same gate as
    // Q24_1, both fire off Q24=Yes independently (not chained on each other).
    Q24_2: (v) => v.Q12 === 'Yes' && typeof v.Q24 === 'string' && v.Q24.startsWith('Yes'),
    Q25: (v) => v.Q12 === 'Yes',
    // Q26–Q30 show only for their respective Q25 selection
    Q26: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Salary'),
    Q27: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Number of patients'),
    Q28: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Working hours'),
    Q29: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Standards to follow'),
    // aug17 migration (Task 3.2, 2026-08-19): matches Q25's actual choice
    // value ('Preventative health care'), not Q30's own printed gate text
    // ('Preventive healthcare' — F2-inventory.md anomaly #7, a paper-author
    // spelling/spacing mismatch between the two). Matching the literal Q30
    // text would never fire (that string isn't a real Q25 value), hiding
    // Q30 permanently — defect fix, single spelling matching the real
    // choice value. See aug17-approved-divergences.md.
    Q30: (v) => v.Q12 === 'Yes' && q25Includes(v, 'Preventative health care'),
  },
  C: {
    // Q31=No → skip to Section D (Q41); Q32–Q40 hidden
    Q32: (v) => v.Q31 === 'Yes',
    Q33: (v) => v.Q31 === 'Yes',
    Q34: (v) => v.Q31 === 'Yes',
    Q35: (v) => v.Q31 === 'Yes' && v.Q34 === 'Yes',
    Q36: (v) => v.Q31 === 'Yes' && v.Q34 === 'Yes',
    Q37: (v) => v.Q31 === 'Yes' && v.Q34 === 'No',
    // R3 #308: per F2-Skip-Logic "Apr 20 improvement", Q34=Yes (already
    // accredited) skips the whole C tail (Q37–Q40) → Q41. Q38 ("would you
    // consider becoming accredited?") only makes sense for the not-yet-
    // accredited path, so gate it on Q34=No like Q37.
    // aug17 migration (Task 3.2, 2026-08-19): Q34 also has "I don't know
    // what PhilHealth YAKAP/Konsulta accreditation is" and "Other (specify)"
    // options beyond Yes/No. F2-inventory.md's routing table (line 285)
    // documents the paper's printed per-option note for "I don't know" as
    // an explicit `<proceed to Q41>` — the whole C tail (Q35–Q40) is
    // skipped, not just Q37 as an incomplete read of the normalized CSV's
    // single `skip` cell might suggest (that cell only captured the "No"
    // note). The strict `=== 'No'` checks on Q37/Q38 already produce exactly
    // this: neither "I don't know" nor "Other (specify)" satisfies them, so
    // both fall straight through to Q41. Verified correct as-is — no change.
    // See aug17-approved-divergences.md for the register entry.
    Q38: (v) => v.Q31 === 'Yes' && v.Q34 === 'No',
    Q39: (v) => v.Q31 === 'Yes' && v.Q38 === 'Yes',
    Q40: (v) => v.Q31 === 'Yes' && v.Q38 === 'No',
  },
  D: {
    Q42: (v) => isYes(v.Q41),
    Q43: (v) => isYes(v.Q41),
    Q45: (v) => isYes(v.Q44),
    Q46: (v) => isYes(v.Q44),
    Q47: (v) => isYes(v.Q44),
  },
  // R2-#117: Section E sub-divides into two role-segregated halves.
  // E1 (BUCAS) = Q48-Q52, restricted to SECTION_CDE_ROLES.
  // E2 (GAMOT) = Q53-Q55, available to SECTION_E_ROLES (CDE + pharmacist).
  // Pre-fix Q48 always showed within Section E for any role that reached
  // the section, so pharmacists answered BUCAS questions despite being
  // outside the patient-care role set for E1. Tester (Shan, 2026-05-07)
  // suggested splitting: "for pharmacists/dispensers and assistant
  // pharmacists, the form should proceed directly to Section E2 -
  // Question 53." Implemented as item-level role gates inside Section
  // E rather than a structural section split (the latter would touch
  // SECTIONS array + 2 schemas + section-numbering across the app).
  E: {
    Q48: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5),
    Q49: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48),
    Q50: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q51: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q52: (v) => typeof v.Q5 === 'string' && SECTION_CDE_ROLES.has(v.Q5) && isYes(v.Q48) && isYes(v.Q49),
    Q54: (v) => isYes(v.Q53),
    Q55: (v) => isYes(v.Q53) && isYes(v.Q54),
  },
  F: {
    Q62: (v) => isDissatisfied(v.Q61),
  },
  G: {
    Q64: (v) => isYes(v.Q63),
    Q65: (v) => v.Q64 === 'No',
    Q67: (v) => isYes(v.Q66),
    Q68: (v) => v.Q67 === 'No',
    Q70: (v) => isYes(v.Q69),
    // R6 #817: Q71 split into the paper's 71a/71b — one box per parent policy.
    Q71a: (v) => isYes(v.Q69),
    Q71b: (v) => isYes(v.Q70),
    Q73: (v) => v.Q72 === 'No',
    // R6 #821 (still in force): Q88 (NBB) is asked regardless of Q87's answer.
    // That half is unchanged — and it was never a departure from the Aug-17
    // paper, which prints NO skip on Q87 (F2-inventory.md:152); only the
    // Apr-20 sheet did.
    //
    // #1293 (UAT R7, 2026-08-20) — the gate below WAS `isYes(Q87) || isYes(Q88)`.
    // The Aug-17 paper prints the skip on Q88 alone: "Q88 … Yes / No
    // `<proceed to Q90>`" (F2-inventory.md:153), and Q89's "If yes, what
    // situations?" refers to the question immediately above it. The OR gate
    // therefore asked Q89 of a Q87=Yes / Q88=No respondent, whom the paper routes
    // straight to Q90 — which is exactly what the reviewers filed. The spec was
    // self-contradictory on this point (its Q88 row already carried `No → Q90`
    // while its Q89 row carried the OR); the Q88 row and the paper agree, so the
    // OR is the part that goes.
    //
    // ACCEPTED TRADE-OFF, disclosed on #1293: a Q87=Yes / Q88=No respondent no
    // longer supplies a narrative, so a ZBB-only balance-billing account is not
    // captured. The paper accepts that, and Q89 was a single undifferentiated box
    // that could not be attributed to ZBB vs NBB anyway.
    Q89: (v) => isYes(v['Q88']),
  },
  H: {
    // Q91='This has never happened to me' → skip Q92–Q95
    Q92: (v) => v.Q91 !== 'This has never happened to me',
    Q93: (v) => v.Q91 !== 'This has never happened to me',
    Q94: (v) => v.Q91 !== 'This has never happened to me',
    Q95: (v) => v.Q91 !== 'This has never happened to me',
  },
  I: {
    Q97: (v) => v.Q96 === 'No',
  },
  // aug17 migration (Task 3.1, 2026-08-19): mechanical re-key per
  // maps/F2-renames.csv — the Q108 numbering gap retired, so every Section J
  // id from the old Q109 onward (both these keys and their v.Qnn
  // dependencies) shifts down by one. Zero logic change: Q121 still gates on
  // "did you work beyond scheduled hours" (was Q122←Q114, now Q121←Q113);
  // Q123/Q124 still gate on "are you planning to leave" (was Q124/Q125←Q123,
  // now Q123/Q124←Q122).
  J: {
    // Defect fix (Task 3.2, 2026-08-19): the Aug-17 paper's own printed note
    // for Q121 says "<Skip if you have answered 'Never' in Q114>", but Q114
    // is "I have been compensated for working overtime" — Q121 ("I have
    // worked overtime for:") logically gates on Q113 ("I have worked beyond
    // my scheduled hours") instead (F2-inventory.md anomaly #8 / open item
    // #3). Gates on Q113 here, not the paper's literal Q114 reference. See
    // aug17-approved-divergences.md.
    Q121: (v) => typeof v.Q113 === 'string' && v.Q113 !== 'Never',
    Q123: (v) => q122IsYes(v.Q122),
    Q124: (v) => q122IsYes(v.Q122),
  },
};

export function shouldShow(sectionId: string, itemId: string, values: FormValues): boolean {
  const p = predicates[sectionId]?.[itemId];
  return p ? p(values) : true;
}

// Section-level skip: returns false if the whole section should be skipped
export function shouldShowSection(sectionId: string, values: FormValues): boolean {
  const role = typeof values.Q5 === 'string' ? values.Q5 : null;
  if (sectionId === 'G') {
    return role !== null && SECTION_G_ROLES.has(role);
  }
  if (sectionId === 'C' || sectionId === 'D') {
    return role !== null && SECTION_CDE_ROLES.has(role);
  }
  if (sectionId === 'E') {
    return role !== null && SECTION_E_ROLES.has(role);
  }
  return true;
}

// Filter an item's choice list based on dependent form values. Returns the input list
// when no filter applies, so consumers can call this unconditionally without checking
// for a registered filter first.
export interface ChoiceLike {
  value: string;
}

export function filterChoices<T extends ChoiceLike>(
  sectionId: string,
  itemId: string,
  values: FormValues,
  choices: T[],
): T[] {
  // A.Q6 specialty filter — non-MD roles (Administrator, Nurse, Midwife, Dentist) only see
  // role-agnostic options. The full medical specialty list is shown only to Physician/Doctor
  // and Physician assistant.
  if (sectionId === 'A' && itemId === 'Q6') {
    const role = values.Q5;
    if (typeof role === 'string' && !MD_SPECIALTY_ROLES.has(role)) {
      return choices.filter((c) => ROLE_AGNOSTIC_SPECIALTY_VALUES.has(c.value));
    }
  }
  return choices;
}
