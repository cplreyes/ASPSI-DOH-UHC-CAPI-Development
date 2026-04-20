import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('kill_switch=true shows overlay on app open', async ({ page }) => {
  const state = defaultState();
  state.config.kill_switch = true;
  await installMockBackend(page, state);

  await page.goto('/');

  await expect(page.getByRole('alert')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('alert')).toContainText(/paused/i);
});
