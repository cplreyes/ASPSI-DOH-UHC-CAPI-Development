import { test } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';
import * as fs from 'fs';

// One-shot masthead evidence: the gov logo strip + PSA/SJREB clearance block
// (RA-approved layout, 2026-08-17) clipped from the top of the page.
test.use({ viewport: { width: 1280, height: 800 } });

test('capture the masthead', async ({ page }) => {
  await installMockBackend(page, defaultState());
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(800);
  await page.evaluate(() => window.scrollTo(0, 0));
  fs.mkdirSync('locale-shots', { recursive: true });
  await page.screenshot({
    path: 'locale-shots/f2_masthead.png',
    clip: { x: 0, y: 0, width: 1280, height: 240 },
  });
});
