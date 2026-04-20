import { test } from '@playwright/test';

test.skip('enrollment → form → submit → sync', async () => {
  // Deferred: requires form-schema-aware helpers to answer each section's required
  // questions before the Next button enables. Walk this path manually via the QA
  // checklist for now. See ../2026-04-18-cross-platform-qa-checklist.md.
});
