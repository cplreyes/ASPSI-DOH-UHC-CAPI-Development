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
 * visible section names. Q5 renders as one radio input per choice, each
 * wrapped in its own <label> (Question.tsx, `case 'single'`) — no <select>,
 * so target the radio directly by its exact accessible name. */
async function readVisibleSections(page: import('@playwright/test').Page, role: string): Promise<string[]> {
  const radio = page.getByRole('radio', { name: role, exact: true });
  await expect(radio).toBeVisible({ timeout: 10000 });
  await radio.check({ force: true });
  await expect(radio).toBeChecked();
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

// `label` is the display name for the test title / evidence filename;
// `q5Value` is the EXACT Q5 choice text (items.ts) the radio's accessible
// name matches — several roles print longer than their common short name
// (e.g. Pharmacist's real Q5 option is the combined
// "Pharmacist/Dispenser/Assistant Pharmacist" string, R12/Task 3.2).
const CADRES: Array<{ label: string; q5Value: string; expectSections: string[]; skipSections: string[] }> = [
  {
    label: 'Physician-Doctor',
    q5Value: 'Physician/Doctor',
    expectSections: [SEC_C, SEC_D, SEC_E, SEC_G],
    skipSections: [],
  },
  {
    label: 'Nurse',
    q5Value: 'Nurse',
    expectSections: [SEC_C, SEC_D, SEC_E],
    skipSections: [SEC_G],
  },
  {
    label: 'Pharmacist',
    q5Value: 'Pharmacist/Dispenser/Assistant Pharmacist',
    expectSections: [SEC_E],
    skipSections: [SEC_C, SEC_D, SEC_G],
  },
  {
    label: 'Dentist-aide',
    q5Value: 'Dentist aide',
    expectSections: [],
    skipSections: [SEC_C, SEC_D, SEC_E, SEC_G],
  },
];

for (const cadre of CADRES) {
  test(`cadre routing: ${cadre.label} sees the correct section set`, async ({ page }) => {
    const state = defaultState();
    await installMockBackend(page, state);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(800);
    await seedEnrollmentAndDraft(page, cadre.label.replace(/[^A-Za-z]/g, ''));
    await page.reload();
    await passConsent(page);

    const names = await readVisibleSections(page, cadre.q5Value);
    console.log('DEBUG sidebar names for', cadre.label, ':', JSON.stringify(names));

    for (const expected of cadre.expectSections) {
      expect(names.some((n) => n.includes(expected))).toBe(true);
    }
    for (const skipped of cadre.skipSections) {
      expect(names.some((n) => n.includes(skipped))).toBe(false);
    }

    await page.screenshot({
      path: `docs/uat-fix-evidence-cadre-routing/${cadre.label}.png`,
      fullPage: false,
    });
  });
}
