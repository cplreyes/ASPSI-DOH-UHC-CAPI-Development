import { test, expect } from '@playwright/test';
import { installMockBackend, defaultState } from './fixtures/mock-backend';

test('min_accepted_spec_version > local triggers forced-update modal', async ({ page }) => {
  const state = defaultState();
  state.config.min_accepted_spec_version = '2099-01-01-final';
  await installMockBackend(page, state);

  await page.goto('/');

  await expect(page.getByRole('alertdialog')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('alertdialog')).toContainText(/update required/i);
  await expect(page.getByRole('button', { name: /reload/i })).toBeVisible();
});
