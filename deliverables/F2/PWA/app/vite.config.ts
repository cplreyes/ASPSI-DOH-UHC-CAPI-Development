import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'node:path';
import pkg from './package.json' with { type: 'json' };

// Build-time guard for required env vars (Issue #45). Production builds without
// VITE_F2_PROXY_URL silently embed an unset value and the deployed PWA renders
// a "VITE_F2_PROXY_URL is not set" error at the enrollment screen — broken for
// every user. Caught at build now so it can't slip through to deploy.
function assertRequiredEnv(mode: string): void {
  if (mode !== 'production') return;
  const env = loadEnv(mode, __dirname, '');
  if (!env.VITE_F2_PROXY_URL || env.VITE_F2_PROXY_URL.includes('REPLACE_ME')) {
    throw new Error(
      'VITE_F2_PROXY_URL is required for production builds and is unset (or still ' +
        'the .env.example placeholder). Set it in .env.local OR pass inline:\n\n' +
        '  VITE_F2_PROXY_URL=https://f2-pwa-worker.<account>.workers.dev npm run build\n\n' +
        'See .env.example for the canonical worker-origin shape.',
    );
  }
}

export default defineConfig(({ mode }) => {
  assertRequiredEnv(mode);
  return {
    plugins: [
      react(),
      process.env.BUNDLE_VISUALIZE === '1'
        ? visualizer({
            filename: 'dist/bundle.html',
            gzipSize: true,
            brotliSize: true,
            open: false,
          })
        : null,
      VitePWA({
        registerType: 'prompt',
        injectRegister: false,
        includeAssets: ['icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable.png'],
        manifest: {
          name: 'UHC Survey Y2 — Healthcare Worker Survey Questionnaire',
          short_name: 'UHC Survey Y2 - HCW',
          description: 'Offline-capable self-administered survey for healthcare workers.',
          start_url: '/',
          scope: '/',
          display: 'standalone',
          orientation: 'portrait',
          theme_color: '#006B3F',
          background_color: '#F2F5EE',
          lang: 'en',
          icons: [
            { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
            {
              src: '/icons/icon-maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
        workbox: {
          globPatterns: ['**/*.{js,css,html,svg,png,ico,webmanifest}'],
          navigateFallback: '/index.html',
          // FX-011 (2026-05-03): admin portal routes must NOT be served from
          // the cached HCW-PWA shell. Workbox's navigateFallback otherwise
          // serves the previous deploy's `/index.html` to admin nav requests,
          // and that stale shell can reference a JS bundle whose route table
          // lacks `/admin/*` — React mounts nothing, page goes blank with no
          // console error. CF Pages already SPA-routes /admin/* to the live
          // index.html, so denying the SW fallback for admin routes lets the
          // browser fetch fresh HTML pointing at the current bundle hash.
          navigateFallbackDenylist: [/^\/admin(\/|$)/],
          // FX-011 follow-up (2026-05-04): the denylist alone doesn't help
          // users who already have a stale SW (no-denylist) registered from
          // an earlier deploy — `registerType: 'prompt'` keeps the old SW in
          // control until tabs close OR the user accepts an update prompt
          // that workbox-window never auto-shows. skipWaiting+clientsClaim
          // makes the new SW take control immediately on activation, so
          // every page load past install gets the latest precache manifest
          // and routing rules. Safe for the HCW PWA (no offline submit-queue
          // state survives across SW versions in any case — the PWA submits
          // on online + retries on next online).
          skipWaiting: true,
          clientsClaim: true,
          cleanupOutdatedCaches: true,
          // Verde Manual fonts. See DESIGN.md. CDN now, self-host follow-up.
          // CSS = StaleWhileRevalidate (refresh when online); woff2 = CacheFirst.
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/fonts\.bunny\.net\/css/,
              handler: 'StaleWhileRevalidate',
              options: {
                cacheName: 'bunny-fonts-css',
                expiration: { maxEntries: 5, maxAgeSeconds: 60 * 60 * 24 * 365 },
              },
            },
            {
              urlPattern: /^https:\/\/fonts\.bunny\.net\/.*\.(woff2?|ttf|otf)$/,
              handler: 'CacheFirst',
              options: {
                cacheName: 'bunny-fonts-files',
                expiration: { maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 365 },
                cacheableResponse: { statuses: [0, 200] },
              },
            },
          ],
        },
        devOptions: {
          enabled: false,
        },
      }),
    ],
    define: {
      __APP_VERSION__: JSON.stringify(pkg.version),
    },
    resolve: {
      alias: { '@': path.resolve(__dirname, './src') },
    },
    // Dev-only proxy. /admin/api/* is forwarded to the staging Worker so
    // localhost:5173/admin/login can dogfood the portal end-to-end without
    // running into CORS (admin routes are deliberately not CORS-enabled —
    // they're meant to be same-origin with the PWA in production).
    //
    // Override the staging URL via VITE_ADMIN_PROXY_TARGET in .env.local
    // when running against a different worker (e.g., production).
    server: {
      proxy: {
        '/admin/api': {
          target:
            process.env.VITE_ADMIN_PROXY_TARGET || 'https://f2-pwa-worker-staging.hcw.workers.dev',
          changeOrigin: true,
          secure: true,
        },
      },
    },
  };
});
