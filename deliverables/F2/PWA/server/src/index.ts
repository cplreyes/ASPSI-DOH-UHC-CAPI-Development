/**
 * f2-api bootstrap. Secrets/config via env only (names in .env.example —
 * values are Carl-placed on the box, never in the repo).
 *
 * Env (all optional except the two FATAL checks):
 *   JWT_SIGNING_KEY  — base64url HMAC key shared with the Worker era (FATAL if unset)
 *   F2_DB_PASSWORD   — MySQL password for the f2api user (FATAL if unset)
 *   F2_DB_HOST/PORT/USER/NAME — MySQL connection (defaults in store.ts)
 *   F2_FILES_DIR     — admin file uploads dir (default /opt/app/f2-files)
 *   F2_WWW_DIR       — PWA static build dir (P3); unset = API-only (P2 dark)
 *   PWA_ORIGIN       — public PWA origin for enroll_url QR links
 *   PWA_VERSION / PWA_BUILD_SHA / API_VERSION / API_DEPLOYED_AT — Versioning panel
 *   identifiers, stamped into the container env by deploy_model_c_full.sh
 */
import { serve } from '@hono/node-server';
import { createApp } from './app.js';
import { createMySqlPool, MySqlStore } from './store.js';
import { LocalFileStore, MySqlAdminStore } from './admin/store.js';

const jwtSigningKey = process.env.JWT_SIGNING_KEY;
if (!jwtSigningKey) {
  console.error('FATAL: JWT_SIGNING_KEY is not set');
  process.exit(1);
}
if (!process.env.F2_DB_PASSWORD) {
  console.error('FATAL: F2_DB_PASSWORD is not set');
  process.exit(1);
}

const pool = createMySqlPool(process.env);
const app = createApp({
  jwtSigningKey,
  store: new MySqlStore(pool),
  ...(process.env.F2_WWW_DIR ? { staticDir: process.env.F2_WWW_DIR } : {}),
  admin: {
    adminStore: new MySqlAdminStore(pool),
    fileStore: new LocalFileStore(process.env.F2_FILES_DIR || '/opt/app/f2-files'),
    pwaOrigin: process.env.PWA_ORIGIN || 'https://uhc-hcw.asiansocial.org',
    pwaVersion: process.env.PWA_VERSION || '',
    pwaBuildSha: process.env.PWA_BUILD_SHA || '',
    apiVersion: process.env.API_VERSION || '',
    apiDeployedAt: process.env.API_DEPLOYED_AT || '',
  },
});
const port = Number(process.env.PORT || 8787);
serve({ fetch: app.fetch, port, hostname: '0.0.0.0' }, (info) => {
  console.log(`f2-api listening on :${info.port}`);
});
