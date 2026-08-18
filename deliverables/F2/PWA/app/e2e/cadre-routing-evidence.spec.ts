import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

// Task 3.4 (aug17 migration, 2026-08-18): desk/browser evidence that Section
// C/D/E/G routing (shouldShowSection, skip-logic.ts) resolves correctly per
// Q5 cadre, post-renumber. F2 is web-native (self-admin PWA, no enumerator
// tablet role) — per R3, desk+browser evidence substitutes for the tablet
// capture convention used by F1/F3/F4.
//
// Reuses locale-shots.spec.ts's proven seedEnrollment pattern (the
// EnrollmentScreen now lives behind /enroll — Model C landing — so direct
// `goto('/')` + HCW-ID-field flow used by golden-path.spec.ts/
// preamble-evidence.spec.ts/f2-shots.spec.ts is stale and fails before
// reaching the survey; NOT an Aug-17 regression, pre-existing, flagged
// separately in task-3.4-report.md, out of this task's scope to fix).

test.use({ viewport: { width: 1280, height: 1600 } });

async function seedEnrollmentAndDraft(page: import('@playwright/test').Page, role: string) {
  await page.evaluate(async (r) => {
    const b64u = (o: object) =>
      btoa(JSON.stringify(o)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const exp = Math.floor(Date.now() / 1000) + 365 * 24 * 3600;
    const jwt = `${b64u({ alg: 'HS256', typ: 'JWT' })}.${b64u({ sub: `UAT-${r}`, exp })}.sig`;
    const dbReq = indexedDB.open('f2_pwa');
    const idb: IDBDatabase = await new Promise((res, rej) => {
      dbReq.onsuccess = () => res(dbReq.result);
      dbReq.onerror = () => rej(dbReq.error);
    });
    const put = (store: string, value: unknown) =>
      new Promise<void>((res, rej) => {
        const tx = idb.transaction(store, 'readwrite');
        const req = tx.objectStore(store).put(value);
        req.onsuccess = () => res();
        req.onerror = () => rej(req.error);
      });
    await put('facilities', {
      facility_id: 'F001', facility_name: 'Test Facility A', facility_type: 'Urban Health Center',
      region: 'NCR', province: 'Metro Manila', city_mun: 'Manila', barangay: 'B1',
    });
    await put('enrollment', {
      id: 'singleton', hcw_id: `UAT-${r}`, facility_id: 'F001',
      facility_type: 'Urban Health Center', device_token: jwt,
    });
  }, role);
}

/** Past the ICF consent gate + optional raffle-number confirm, same steps
 * locale-shots.spec.ts already exercises successfully. */
async function passConsent(page: import('@playwright/test').Page) {
  await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
  const consentRadio = page.getByRole('radio').first();
  if ((await consentRadio.count()) > 0 && (await page.getByRole('radio').count()) === 2) {
    await consentRadio.check();
    await page.getByRole('button', { name: /Continue|Magpatuloy/i }).click();
    await page.waitForTimeout(800);
    const proceed = page.getByRole('button', { name: /proceed|yes|continue without/i }).last();
    if ((await proceed.count()) > 0 && (await proceed.isVisible().catch(() => false))) {
      await proceed.click();
      await page.waitForTimeout(800);
    }
  }
  await page.getByRole('heading', { level: 2 }).first().waitFor({ timeout: 10000 });
}

/** Sets Q5 through the live Section A form (not IndexedDB) so
 * shouldShowSection's `values.Q5` reflects it exactly the way a real
 * respondent's answer would, then reads back the desktop sidebar's list of
 * visible section names. */
async function readVisibleSections(page: import('@playwright/test').Page, role: string): Promise<string[]> {
  await page.getByLabel(/What is your role at this health facility/i).selectOption({ label: role }).catch(async () => {
    // Radio-group rendering fallback if this isn't a <select>.
    await page.getByRole('radio', { name: role }).check();
  });
  await page.waitForTimeout(300);
  const items = page.locator('aside').first().getByRole('button');
  const count = await items.count();
  const names: string[] = [];
  for (let i = 0; i < count; i++) {
    names.push((await items.nth(i).innerText()).trim());
  }
  return names;
}

// Sidebar buttons render the section's own title text (from items.ts), not
// a "Section X" label — match on distinctive title substrings instead.
const SEC_C = 'YAKAP/Konsulta Package';
const SEC_D = 'No Balance Billing';
const SEC_E = 'Expanded Health Programs';
const SEC_G = 'Professional Setting, Charging';

const CADRES: Array<{ role: string; expectSections: string[]; skipSections: string[] }> = [
  {
    role: 'Physician/Doctor',
    expectSections: [SEC_C, SEC_D, SEC_E, SEC_G],
    skipSections: [],
  },
  {
    role: 'Nurse',
    expectSections: [SEC_C, SEC_D, SEC_E],
    skipSections: [SEC_G],
  },
  {
    role: 'Pharmacist',
    expectSections: [SEC_E],
    skipSections: [SEC_C, SEC_D, SEC_G],
  },
  {
    role: 'Dentist aide',
    expectSections: [],
    skipSections: [SEC_C, SEC_D, SEC_E, SEC_G],
  },
];

for (const cadre of CADRES) {
  test(`cadre routing: ${cadre.role} sees the correct section set`, async ({ page }) => {
    const state = defaultState();
    await installMockBackend(page, state);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    await seedEnrollmentAndDraft(page, cadre.role.replace(/[^A-Za-z]/g, ''));
    await page.reload();
    await passConsent(page);

    const roleSelect = page.getByLabel(/What is your role at this health facility/i);
    await expect(roleSelect).toBeVisible({ timeout: 10000 });
    const names = await readVisibleSections(page, cadre.role);

    for (const expected of cadre.expectSections) {
      expect(names.some((n) => n.includes(expected))).toBe(true);
    }
    for (const skipped of cadre.skipSections) {
      expect(names.some((n) => n.includes(skipped))).toBe(false);
    }

    await page.screenshot({
      path: `docs/uat-fix-evidence-cadre-routing/${cadre.role.replace(/[^A-Za-z]/g, '-')}.png`,
      fullPage: false,
    });
  });
}
