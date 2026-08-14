import '@testing-library/jest-dom/vitest';
import 'fake-indexeddb/auto';
import { afterEach } from 'vitest';

import.meta.env.VITE_F2_PROXY_URL = 'https://test.invalid';

afterEach(async () => {
  const dbs = await indexedDB.databases();
  await Promise.all(
    dbs.map(
      ({ name }) =>
        name &&
        new Promise<void>((resolve, reject) => {
          const req = indexedDB.deleteDatabase(name);
          req.onsuccess = () => resolve();
          req.onerror = () => reject(req.error);
          req.onblocked = () => resolve();
        }),
    ),
  );
  localStorage.clear();
  // The admin portal keeps its session here (src/admin/lib/auth-storage.ts);
  // without this, one test's login leaks into the next test's "starts logged
  // out" assumption.
  sessionStorage.clear();
});

import '@/i18n';
