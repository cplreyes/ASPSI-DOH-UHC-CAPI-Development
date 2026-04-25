/**
 * Frontend env access. After the auth re-arch (spec 2026-04-26-f2-pwa-auth-rearch-design.md),
 * the only secret-shaped value the PWA knows is the device JWT (per-tablet, stored in Dexie).
 *
 * VITE_F2_HMAC_SECRET no longer exists — the HMAC is held only by the Cloudflare Worker.
 */

export interface SyncEnv {
  /** Cloudflare Worker origin, e.g. https://f2-pwa-worker.<account>.workers.dev. Public, fine in bundle. */
  proxyUrl: string;
}

export function getSyncEnv(): SyncEnv {
  const proxyUrl = import.meta.env.VITE_F2_PROXY_URL;

  if (!proxyUrl) {
    throw new Error(
      'VITE_F2_PROXY_URL is not set. Copy .env.example to .env.local and fill in the Cloudflare Worker origin.',
    );
  }
  return { proxyUrl };
}
