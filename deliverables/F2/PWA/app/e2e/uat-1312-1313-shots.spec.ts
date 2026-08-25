// Evidence capture for UAT R7 #1312 (Q24.2 DOH option list) and #1313 (ICF text).
// Not a regression test — writes PNGs to uat-shots/ against the mock backend.
// Entry path mirrors cadre-routing-evidence.spec.ts (Model C landing: seed IndexedDB, reload).
import { test } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';
import {
  sectionA, sectionB, sectionC, sectionD, sectionE,
  sectionF, sectionG, sectionH, sectionI, sectionJ,
} from '../src/generated/items';
import * as fs from 'fs';

const SECTIONS = [sectionA, sectionB, sectionC, sectionD, sectionE, sectionF, sectionG, sectionH, sectionI, sectionJ];
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

async function seedEnrollment(page: import('@playwright/test').Page) {
  await page.evaluate(async () => {
    const b64u = (o: object) =>
      btoa(JSON.stringify(o)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const exp = Math.floor(Date.now() / 1000) + 365 * 24 * 3600;
    const jwt = `${b64u({ alg: 'HS256', typ: 'JWT' })}.${b64u({ sub: 'UAT-EVIDENCE', exp })}.sig`;
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
      id: 'singleton', hcw_id: 'UAT-EVIDENCE', facility_id: 'F001',
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
    await new Promise<void>((res, rej) => {
      const tx = idb.transaction('drafts', 'readwrite');
      const req = tx.objectStore('drafts').put({ id: draftId, hcw_id: 'UAT-EVIDENCE', updated_at: Date.now(), values: vals });
      req.onsuccess = () => res(); req.onerror = () => rej(req.error);
    });
  }, values);
}

async function passConsent(page: import('@playwright/test').Page, shotPath?: string) {
  await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
  const radios = page.getByRole('radio');
  if ((await radios.count()) === 2) {
    if (shotPath) await page.screenshot({ path: shotPath, fullPage: true });
    await radios.first().check();
    await page.getByRole('button', { name: /Continue|Magpatuloy/i }).click();
    await page.waitForTimeout(800);
    const proceed = page.getByRole('button', { name: /proceed|yes|continue without/i }).last();
    if ((await proceed.count()) > 0 && (await proceed.isVisible().catch(() => false))) {
      await proceed.click(); await page.waitForTimeout(800);
    }
  }
  await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
}

test.use({ viewport: { width: 1280, height: 1600 } });

test('capture consent screen (#1313) and Section B Q24.2 (#1312)', async ({ page }) => {
  const out = 'uat-shots'; fs.mkdirSync(out, { recursive: true });
  await installMockBackend(page, defaultState());
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(800);
  await seedEnrollment(page);
  await page.reload();
  await passConsent(page, `${out}/1313-consent-screen.png`);
  console.log('after consent H2:', await page.getByRole('heading', { level: 2 }).first().textContent());

  const answers = buildAnswers();
  answers.Q5 = 'Physician/Doctor'; answers.Q7 = 'No';
  answers.Q4 = 40; // tenure-vs-age cross-check: min age (18) fails Section A validation
  answers.Q12 = 'Yes'; answers.Q24 = 'Yes';
  answers.Q24_1 = 'Implemented as a direct result of the UHC Act';
  answers.Q24_2 = ['Patient or Client satisfaction survey', 'Quality Assurance Plan (QAP)'];
  await seedDraft(page, answers);
  await page.reload();
  await passConsent(page);

  // Sidebar → Section B (desktop rail), fallback to "Next section".
  const rail = page.locator('aside').first().getByRole('button', { name: /Section B|^B\b|UHC Awareness/i });
  if ((await rail.count()) > 0) { await rail.first().click(); }
  else { await page.getByRole('button', { name: 'Next section' }).click(); }
  await page.waitForTimeout(900);
  await page.getByRole('heading', { name: /Section B/i }).waitFor({ timeout: 10000 });
  console.log('Section B H2:', await page.getByRole('heading', { level: 2 }).first().textContent());
  await page.screenshot({ path: `${out}/1312-section-b-full.png`, fullPage: true });

  const q = page.getByText(/primary care quality measures are you implementing/i).first();
  await q.waitFor({ timeout: 10000 });
  const block = q.locator('xpath=ancestor::*[self::fieldset or self::section or contains(@class,"space-y")][1]');
  if ((await block.count()) > 0) await block.first().screenshot({ path: `${out}/1312-q24-2-options.png` });
  const labels = await page.getByRole('checkbox').evaluateAll((els) => els.map((e) => (e as HTMLInputElement).closest('label')?.textContent?.trim() ?? ''));
  console.log('checkbox labels on Section B:', JSON.stringify(labels.filter(Boolean)));
});
