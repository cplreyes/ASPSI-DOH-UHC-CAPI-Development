import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';
import { sections } from '../src/generated/items';

// Auto-derive a complete answer for every generated item so the section walk
// never trips a required-field gate, whatever the current spec revision looks
// like. Curated persona/branch answers below override these defaults.
function autoAnswers(): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const s of sections) {
    for (const item of s.items) {
      const first = item.choices?.[0]?.value;
      if (item.type === 'multi') out[item.id] = first ? [first] : [];
      else if (item.type === 'single') out[item.id] = first ?? 'Yes';
      else if (item.type === 'number') out[item.id] = 1;
      else if (item.type === 'date' || item.type === 'partial-date') out[item.id] = '2024';
      else out[item.id] = 'UAT test answer';
    }
  }
  return out;
}

// #1179/#1180/#1181 — regression + evidence run: mid-section preambles
// (professional-fee definition, battery instructions) must render when their
// carrier items are folded into a matrix group. Uses a Physician persona so
// the doctor/dentist-gated Section G fee block is visible.
const ANSWERS: Record<string, unknown> = {
  Q1_1: 'Dela Cruz', Q1_2: 'Juan', Q1_3: 'P',
  Q2: 'Regular',
  Q3: 'Female',
  Q4: 32,
  Q5: 'Physician/Doctor',
  Q7: 'No',
  Q9_1: 2, Q9_2: 6,
  Q10: 5,
  Q11: 8,
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
  Q31: 'Yes',
  Q32: ['Pap smear'],
  Q33: 'It is possible to register individual patients to YAKAP/Konsulta',
  Q34: 'Yes',
  Q38: 'Yes',
  Q41: 'Yes',
  Q44: 'Yes',
  Q48: 'Yes',
  Q53: 'Yes',
  Q56: ['Physical referral slip'],
  Q57: 'DOH standard referral form',
  Q58: 'Yes',
  Q59: 'Almost all patients are referred, very few walk-in/self-referred',
  Q60: ['Physical referral slip'],
  Q61: 'Very Satisfied: Minor improvements needed, patients are always referred appropriately',
  Q63: 'Yes',
  Q64: 'Yes',
  Q66: 'Yes',
  Q67: 'Yes',
  Q72: 'Yes',
  Q74: 'UAT test answer',
  Q77: '1', Q78: '1', Q79: '1', Q80: '1', Q81: '1',
  Q82: 'UAT test answer',
  Q83: 'Never', Q84: 'Never', Q85: 'Never',
  Q86: 'UAT test answer',
  Q90: 'UAT test answer',
  Q91: 'Everyday',
  Q92: 'I typically have to take on tasks that should be performed by only staff / more junior health care providers to me',
  Q93: ['Patient assessments'],
  Q94: 'We are short staffed, so I have to',
  Q95: 'Agree but for medical tasks only',
  Q96: 'Yes',
  Q98: 'Strongly Agree', Q99: 'Strongly Agree', Q100: 'Strongly Agree',
  Q101: 'Strongly Agree', Q102: 'Strongly Agree', Q103: 'Strongly Agree',
  Q104: 'Strongly Agree', Q105: 'Strongly Agree', Q106: 'Strongly Agree',
  Q107: 'Strongly Agree',
  // aug17 migration: Section J ids Q109-Q125 shifted to Q108-Q124 (the
  // Apr-20 Q108 PDF numbering gap closes in the Aug-17 rev) — re-keyed per
  // maps/F2-renames.csv, Task 3.4, 2026-08-18. Values unchanged.
  Q108: 'UAT test answer',
  Q109: ['Professional development opportunities'],
  Q110: ['Seminars, conferences, workshops'],
  Q111: ['Clinical audits'],
  Q112: ['Clinical audits'],
  Q113: 'Always', Q114: 'Always', Q115: 'Always', Q116: 'Always',
  Q117: 'Always', Q118: 'Always', Q119: 'Always', Q120: 'Always',
  Q122: "Yes, I've thought about it and have definite plans to leave",
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

test('preambles render above matrix groups in Sections G and J (#1179-#1181)', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);

  // The Model-C token gate verifies against the Worker's /verify-token —
  // answer it from the mock so enrollment proceeds against fixture state.
  await page.route('**/verify-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ok: true,
        claims: {
          facility_id: 'F001',
          exp: Math.floor(Date.now() / 1000) + 86400,
          tablet_id: 'TAB-E2E',
        },
      }),
    });
  });

  // The app re-parses claims from the stored JWT on every boot (spec §7.2),
  // so the pasted token must be structurally decodable — mint an unsigned
  // JWT whose payload matches the mocked /verify-token claims.
  const b64url = (o: object) =>
    Buffer.from(JSON.stringify(o)).toString('base64url');
  const e2eToken = `${b64url({ alg: 'HS256', typ: 'JWT' })}.${b64url({
    facility_id: 'F001',
    tablet_id: 'TAB-E2E',
    exp: Math.floor(Date.now() / 1000) + 86400,
  })}.e2e-sig`;

  await page.goto('/');
  await expect(page.getByRole('heading', { name: /enroll/i })).toBeVisible();
  await page.getByLabel(/tablet token/i).fill(e2eToken);
  await page.getByRole('button', { name: /verify token/i }).click();
  await page.getByLabel(/HCW ID/i).fill('UAT-DOC-01');
  await page.getByRole('button', { name: /^Enroll$/i }).click();

  // Informed Consent gate (added post-golden-path): agree, then continue.
  await expect(page.getByRole('heading', { name: /informed consent/i })).toBeVisible({ timeout: 5000 });
  await page.getByRole('radio', { name: /voluntarily agree to participate/i }).check();
  await page.getByRole('button', { name: /^Continue$/i }).click();

  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  await seedDraft(page, { ...autoAnswers(), ...ANSWERS });
  await page.reload();

  // Seeding replaced the draft wholesale, so the consent flag went with it —
  // the gate reappears after reload. Agree again.
  await expect(page.getByRole('heading', { name: /informed consent/i })).toBeVisible({ timeout: 5000 });
  await page.getByRole('radio', { name: /voluntarily agree to participate/i }).check();
  await page.getByRole('button', { name: /^Continue$/i }).click();

  await expect(page.getByRole('heading', { name: /Section A/i })).toBeVisible({ timeout: 5000 });

  // Walk A → F, then land on G
  for (const id of ['A', 'B', 'C', 'D', 'E', 'F']) {
    await expect(page.getByRole('heading', { name: new RegExp(`Section ${id}`) })).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: 'Next section' }).click();
  }

  // Section G: the professional-fee definition renders as subtext (#1179)
  await expect(page.getByRole('heading', { name: /Section G/ })).toBeVisible({ timeout: 5000 });
  await expect(
    page.getByText(/negotiable, and personalized fee/).first(),
  ).toBeVisible({ timeout: 5000 });
  await page.screenshot({ path: 'e2e-evidence-1179-section-g.png', fullPage: false });

  // Walk G → I, land on J
  for (const id of ['G', 'H', 'I']) {
    await expect(page.getByRole('heading', { name: new RegExp(`Section ${id}`) })).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: 'Next section' }).click();
  }

  // Section J: the battery instruction renders above both matrices (#1180/#1181)
  await expect(page.getByRole('heading', { name: /Section J/ })).toBeVisible({ timeout: 5000 });
  const note = page.getByText(/Please think about your experience in this post/);
  await expect(note.first()).toBeVisible({ timeout: 5000 });
  await page.screenshot({ path: 'e2e-evidence-1180-section-j-top.png', fullPage: false });
  // Scroll to the second battery (Q114-Q120 display range, aug17-renumbered) and capture it too
  await note.last().scrollIntoViewIfNeeded();
  await expect(note.last()).toBeVisible();
  await page.screenshot({ path: 'e2e-evidence-1181-section-j-battery2.png', fullPage: false });
});
