import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

// Complete answer set for a Nurse persona.
// Chosen to satisfy all visible required fields across all 10 sections
// without triggering optional conditional branches unnecessarily.
const COMPLETE_ANSWERS: Record<string, unknown> = {
  // Section A — Healthcare Worker Profile
  Q1_1: 'Dela Cruz', Q1_2: 'Juan', Q1_3: 'P',
  Q2: 'Regular',
  Q3: 'Female',
  Q4: 32,
  Q5: 'Nurse',
  Q7: 'No',
  Q9_1: 2, Q9_2: 6,
  Q10: 5,
  Q11: 8,

  // Section B — UHC Awareness
  Q12: 'Yes',
  Q13: 'Yes, this was implemented as a direct result of the UHC Act',
  Q15: 'Yes, this was implemented as a direct result of the UHC Act',
  Q17: 'Yes, this was implemented as a direct result of the UHC Act',
  Q18: 'Yes, this was implemented as a direct result of the UHC Act',
  Q19: 'Yes, this was implemented as a direct result of the UHC Act',
  Q20: 'Yes, this was implemented as a direct result of the UHC Act',
  Q21: 'Yes, this was implemented as a direct result of the UHC Act',
  Q22: 'Yes, this was implemented as a direct result of the UHC Act',
  Q23: 'Yes, this was implemented as a direct result of the UHC Act',
  Q24: 'Yes, this was implemented as a direct result of the UHC Act',
  Q25: ['Salary'],

  // Section C — YAKAP/Konsulta
  Q31: 'Yes',
  Q32: ['Pap smear'],
  Q33: 'It is possible to register individual patients to YAKAP/Konsulta',
  Q34: 'Yes',
  Q38: 'Yes',

  // Section D — No Balance Billing
  Q41: 'Yes',
  Q44: 'Yes',

  // Section E — BUCAS and GAMOT
  Q48: 'Yes',
  Q53: 'Yes',

  // Section F — Referrals and Satisfaction
  Q56: ['Physical referral slip'],
  Q57: 'DOH standard referral form',
  Q58: 'Yes',
  Q59: 'Almost all patients are referred, very few walk-in/self-referred',
  Q60: ['Physical referral slip'],
  Q61: 'Very Satisfied: Minor improvements needed, patients are always referred appropriately',

  // Section G — KAP on Professional Setting
  Q63: 'Yes',
  Q66: 'Yes',
  Q72: 'Yes',
  Q74: 'UAT test answer',
  Q77: '1', Q78: '1', Q79: '1', Q80: '1', Q81: '1',
  Q82: 'UAT test answer',
  Q83: 'Never', Q84: 'Never', Q85: 'Never',
  Q86: 'UAT test answer',
  Q90: 'UAT test answer',

  // Section H — Task Sharing
  Q91: 'Everyday',
  Q92: 'I typically have to take on tasks that should be performed by only staff / more junior health care providers to me',
  Q93: ['Patient assessments'],
  Q94: 'We are short staffed, so I have to',
  Q95: 'Agree but for medical tasks only',

  // Section I — Facility Support
  Q96: 'Yes',

  // Section J — Job Satisfaction
  Q98: 'Strongly Agree', Q99: 'Strongly Agree', Q100: 'Strongly Agree',
  Q101: 'Strongly Agree', Q102: 'Strongly Agree', Q103: 'Strongly Agree',
  Q104: 'Strongly Agree', Q105: 'Strongly Agree', Q106: 'Strongly Agree',
  Q107: 'Strongly Agree',
  Q109: 'UAT test answer',
  Q110: ['Professional development opportunities'],
  Q111: ['Seminars, conferences, workshops'],
  Q112: ['Clinical audits'],
  Q113: ['Clinical audits'],
  Q114: 'Always', Q115: 'Always', Q116: 'Always', Q117: 'Always',
  Q118: 'Always', Q119: 'Always', Q120: 'Always', Q121: 'Always',
  Q123: "Yes, I've thought about it and have definite plans to leave",
};

async function seedDraft(
  page: import('@playwright/test').Page,
  values: Record<string, unknown>,
) {
  await page.evaluate(async (vals) => {
    const draftId = localStorage.getItem('f2_current_draft_id');
    if (!draftId) throw new Error('No draft ID in localStorage');

    const dbReq = indexedDB.open('f2_pwa');
    const idb: IDBDatabase = await new Promise((res, rej) => {
      dbReq.onsuccess = () => res(dbReq.result);
      dbReq.onerror = () => rej(dbReq.error);
    });

    const hcwId: string = await new Promise((res, rej) => {
      const tx = idb.transaction('enrollment', 'readonly');
      const req = tx.objectStore('enrollment').get('singleton');
      req.onsuccess = () => res((req.result as { hcw_id: string })?.hcw_id ?? 'unknown');
      req.onerror = () => rej(req.error);
    });

    await new Promise<void>((res, rej) => {
      const tx = idb.transaction('drafts', 'readwrite');
      const req = tx.objectStore('drafts').put({
        id: draftId,
        hcw_id: hcwId,
        updated_at: Date.now(),
        values: vals,
      });
      req.onsuccess = () => res();
      req.onerror = () => rej(req.error);
    });
  }, values);
}

test('golden path: enrollment → all sections complete → review → submit', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);

  // 1. Enrollment
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /enroll/i })).toBeVisible();

  await page.getByLabel('HCW ID').fill('UAT-NURSE-01');
  await page.getByRole('button', { name: /refresh facility list/i }).click();
  await page.getByLabel('Facility').selectOption('F001');
  await page.getByRole('button', { name: /^Enroll$/i }).click();

  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  // 2. Seed all answers into IndexedDB, then reload so the app picks them up
  await seedDraft(page, COMPLETE_ANSWERS);
  await page.reload();
  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  // 3. Navigate through all 10 sections to the review screen.
  // Wait for each section heading before clicking Next to avoid race conditions.
  const sectionIds = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
  for (const id of sectionIds) {
    await expect(page.getByRole('heading', { name: new RegExp(`Section ${id}`) })).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: 'Next section' }).click();
  }

  await expect(page.getByText(/review your answers/i)).toBeVisible({ timeout: 8000 });

  // Review shows all 10 sections
  for (const id of ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']) {
    await expect(page.getByRole('heading', { name: new RegExp(`Section ${id}`, 'i') })).toBeVisible();
  }

  // 4. Submit
  await page.getByRole('button', { name: /^submit$/i }).click();
  await expect(page.getByText(/thank you/i)).toBeVisible({ timeout: 5000 });
  expect(state.submissions).toHaveLength(1);
});

test('section lock: cannot navigate to an unvisited section via tree', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);

  await page.goto('/');
  await page.getByLabel('HCW ID').fill('UAT-NURSE-01');
  await page.getByRole('button', { name: /refresh facility list/i }).click();
  await page.getByLabel('Facility').selectOption('F001');
  await page.getByRole('button', { name: /^Enroll$/i }).click();

  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  // Try to jump to Section J via the desktop sidebar (Section A is index 0, J is index 9)
  await page.locator('aside').first().getByRole('button', { name: /Job Satisfaction/i }).click();

  // Lock message should appear
  await expect(page.getByText(/complete sections in order/i)).toBeVisible({ timeout: 3000 });

  // Still on Section A
  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible();
});

test('language switch: form labels change without data loss', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);

  await page.goto('/');
  await page.getByLabel('HCW ID').fill('UAT-NURSE-01');
  await page.getByRole('button', { name: /refresh facility list/i }).click();
  await page.getByLabel('Facility').selectOption('F001');
  await page.getByRole('button', { name: /^Enroll$/i }).click();

  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  // Fill one field
  await page.getByLabel('Last Name').fill('Reyes');

  // Switch to Filipino
  await page.getByRole('button', { name: 'Filipino' }).click();

  // Value must survive the language toggle
  await expect(page.getByLabel('Last Name')).toHaveValue('Reyes');
});
