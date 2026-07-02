import { test } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';
import {
  sectionA, sectionB, sectionC, sectionD, sectionE,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '../src/generated/items';
import * as fs from 'fs';

const SECTIONS = [sectionA, sectionB, sectionC, sectionD, sectionE, sectionF, sectionG, sectionH, sectionI, sectionJ];

// Build a complete, spec-accurate answer for every question (first choice /
// in-range number / etc.) so every section validates and unlocks — robust to
// spec drift (golden-path's hardcoded list went stale).
function buildAnswers(): Record<string, unknown> {
  const a: Record<string, unknown> = {};
  for (const s of SECTIONS as Array<{ items: Array<Record<string, unknown>> }>) {
    for (const item of s.items) {
      const choices = item.choices as Array<{ value: string }> | undefined;
      switch (item.type) {
        case 'single': if (choices?.length) a[item.id as string] = choices[0].value; break;
        case 'multi': if (choices?.length) a[item.id as string] = [choices[0].value]; break;
        case 'number': a[item.id as string] = (item.min as number) ?? 1; break;
        case 'long-text': a[item.id as string] = 'Test answer'; break;
        case 'partial-date': a[item.id as string] = '2024-06'; break;
        case 'multi-field':
          for (const sf of (item.subFields as Array<{ id: string; kind: string }>) ?? [])
            a[sf.id] = sf.kind === 'number' ? 1 : 'Test';
          break;
      }
    }
  }
  return a;
}
const COMPLETE_ANSWERS = buildAnswers();
// Persona override: 'Physician/Doctor' is the one role that surfaces ALL
// conditional sections — G (SECTION_G_ROLES) plus C/D/E (patient-care roles).
// First-choice default 'Administrator' hides G; 'Nurse' also hides G.
COMPLETE_ANSWERS.Q5 = 'Physician/Doctor';
COMPLETE_ANSWERS.Q7 = 'No';

async function seedEnrollment(page: import('@playwright/test').Page) {
  await page.evaluate(async () => {
    const b64u = (o: object) =>
      btoa(JSON.stringify(o)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const exp = Math.floor(Date.now() / 1000) + 365 * 24 * 3600;
    const jwt = `${b64u({ alg: 'HS256', typ: 'JWT' })}.${b64u({ sub: 'UAT-NURSE-01', exp })}.sig`;
    const dbReq = indexedDB.open('f2_pwa');
    const idb: IDBDatabase = await new Promise((res, rej) => {
      dbReq.onsuccess = () => res(dbReq.result); dbReq.onerror = () => rej(dbReq.error);
    });
    const put = (store: string, value: unknown) => new Promise<void>((res, rej) => {
      const tx = idb.transaction(store, 'readwrite');
      const req = tx.objectStore(store).put(value);
      req.onsuccess = () => res(); req.onerror = () => rej(req.error);
    });
    await put('facilities', {
      facility_id: 'F001', facility_name: 'Test Facility A', facility_type: 'Urban Health Center',
      region: 'NCR', province: 'Metro Manila', city_mun: 'Manila', barangay: 'B1',
    });
    await put('enrollment', {
      id: 'singleton', hcw_id: 'UAT-NURSE-01', facility_id: 'F001',
      facility_type: 'Urban Health Center', device_token: jwt,
    });
  });
}

async function seedDraft(page: import('@playwright/test').Page, values: Record<string, unknown>) {
  await page.evaluate(async (vals) => {
    const draftId = localStorage.getItem('f2_current_draft_id');
    if (!draftId) throw new Error('No draft ID in localStorage');
    const dbReq = indexedDB.open('f2_pwa');
    const idb: IDBDatabase = await new Promise((res, rej) => {
      dbReq.onsuccess = () => res(dbReq.result); dbReq.onerror = () => rej(dbReq.error);
    });
    const hcwId: string = await new Promise((res, rej) => {
      const tx = idb.transaction('enrollment', 'readonly');
      const req = tx.objectStore('enrollment').get('singleton');
      req.onsuccess = () => res((req.result as { hcw_id: string })?.hcw_id ?? 'unknown');
      req.onerror = () => rej(req.error);
    });
    await new Promise<void>((res, rej) => {
      const tx = idb.transaction('drafts', 'readwrite');
      const req = tx.objectStore('drafts').put({ id: draftId, hcw_id: hcwId, updated_at: Date.now(), values: vals });
      req.onsuccess = () => res(); req.onerror = () => rej(req.error);
    });
  }, values);
}

test.use({ viewport: { width: 1280, height: 900 } });

test('capture F2 section screenshots for the crosswalk', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);
  await page.goto('/');
  await page.getByRole('heading', { name: /Enroll/i }).waitFor({ timeout: 10000 });
  await seedEnrollment(page);
  await page.reload();
  await page.getByRole('heading', { name: /Section A/i }).waitFor({ timeout: 10000 });

  await seedDraft(page, COMPLETE_ANSWERS);
  await page.reload();
  await page.getByRole('heading', { name: /Section A/i }).waitFor({ timeout: 10000 });

  const outdir = 'section-shots';
  fs.mkdirSync(outdir, { recursive: true });
  // Adaptive: capture whatever section renders, in order, until the review
  // screen (no more "Next section"). Robust to conditionally-hidden sections.
  const seen: string[] = [];
  for (let i = 0; i < 14; i++) {
    const headingText = await page.getByRole('heading', { level: 2 }).first().textContent();
    const m = headingText?.match(/Section\s+([A-Z])\b/);
    if (!m) break;
    const id = m[1].toLowerCase();
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${outdir}/f2-web-section-${id}.png`, fullPage: true });
    seen.push(m[1]);
    const next = page.getByRole('button', { name: 'Next section' });
    if ((await next.count()) === 0) break;
    await next.click();
    await page.waitForTimeout(700);
  }
  console.log('Captured sections:', seen.join(', '));
});
