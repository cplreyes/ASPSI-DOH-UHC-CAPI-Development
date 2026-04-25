import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

// ---------------------------------------------------------------------------
// TODO (un-skip): There is no window.__e2eShortcut / window.__e2e helper in
// this codebase.  main.tsx does not expose any VITE_E2E_SHORTCUTS shortcut.
//
// The approved pattern for "pre-fill all sections" is the seedDraft() helper
// used in golden-path.spec.ts — it writes answers directly into IndexedDB so
// the app loads Section A already complete, and you click Next through each
// section.
//
// To activate this test:
//   1. Extract (or inline) the seedDraft() helper from golden-path.spec.ts.
//   2. Add Physician/Doctor-profile answers for Sections A–I to a
//      PHYSICIAN_ANSWERS constant (Q5: 'Physician/Doctor', plus whatever
//      fields are required for that persona).
//   3. Replace the test.skip block below with the real test body that:
//      a. Installs mock-backend (installMockBackend + defaultState).
//      b. Enrolls (HCW ID + facility select + Enroll button).
//      c. Seeds the draft via seedDraft() + page.reload().
//      d. Clicks "Next section" through A → I (9 clicks).
//      e. Asserts Section J is visible and contains exactly 2 <table> elements
//         (Grid #1 Agreement + Grid #2 Frequency).
//      f. Fills every radio in each matrix row (nth(2) = middle option).
//      g. Clicks "Next section" and expects the Review heading.
//      h. Asserts the compact mini-table inside the "Section J" review block.
// ---------------------------------------------------------------------------

test.skip('Section J renders Grid #1 + Grid #2 as matrix tables', async ({ page }) => {
  // Stub — body intentionally empty until the seedDraft path is wired up.
  // See TODO above for the full implementation plan.
  void page;
  void installMockBackend;
  void defaultState;
  void expect;
});
