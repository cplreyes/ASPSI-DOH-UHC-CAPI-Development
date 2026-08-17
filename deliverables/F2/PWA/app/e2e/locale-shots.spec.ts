import { test } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';
import * as fs from 'fs';

// Mirror of SUPPORTED_LOCALES — src/i18n evaluates import.meta.env at module
// scope, which Playwright's node-side loader cannot execute.
const SUPPORTED_LOCALES = ['en', 'fil', 'ceb', 'bis', 'ilo', 'hil', 'war', 'bcl'] as const;

// Translation-coverage evidence: the SAME survey screen (Section A top — section
// header + first questions incl. the Q2 employment single-choice options) captured
// once per locale, switched exactly the way the app itself persists a choice
// (f2_locale in localStorage; READY_LOCALES gates what the switcher offers).

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

test.use({ viewport: { width: 1280, height: 1600 } });

test('capture Section A in every locale', async ({ page }) => {
  const state = defaultState();
  await installMockBackend(page, state);
  await page.goto('/');
  // EnrollmentScreen now lives behind /enroll (Model C landing) — we seed the
  // IndexedDB directly, so we only need the app booted, whatever screen shows.
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(800);
  await seedEnrollment(page);
  await page.reload();
  await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });

  const outdir = 'locale-shots';
  fs.mkdirSync(outdir, { recursive: true });
  for (const loc of SUPPORTED_LOCALES) {
    await page.evaluate((l) => localStorage.setItem('f2_locale', l), loc);
    await page.reload();
    await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
    await page.waitForTimeout(600);
    // The ICF consent gate precedes Section A. Capture it once (fil) as evidence
    // that the consent body renders English in a dialect locale, then pass it.
    const consentRadio = page.getByRole('radio').first();
    if ((await consentRadio.count()) > 0 && (await page.getByRole('radio').count()) === 2) {
      if (loc === 'fil') {
        await page.screenshot({ path: `${outdir}/f2_consent_${loc}.png`, fullPage: false });
      }
      await consentRadio.check();
      await page.getByRole('button', { name: /Continue|Magpatuloy/i }).click();
      await page.waitForTimeout(800);
      // No raffle number entered -> inline confirm ("Do you want to proceed?").
      const proceed = page.getByRole('button', { name: /proceed|yes|continue without/i }).last();
      if ((await proceed.count()) > 0 && (await proceed.isVisible().catch(() => false))) {
        await proceed.click();
        await page.waitForTimeout(800);
      }
    }
    await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
    await page.screenshot({ path: `${outdir}/f2_secA_${loc}.png`, fullPage: false });
  }
  console.log('Captured locales:', SUPPORTED_LOCALES.join(', '));
});
