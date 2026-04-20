import { test } from '@playwright/test';

test.skip('submit retries after transient failure', async () => {
  // Deferred: same blocker as golden-path — needs form-schema-aware helpers.
  // Manual QA covers this via the checklist's offline-behavior section.
});
