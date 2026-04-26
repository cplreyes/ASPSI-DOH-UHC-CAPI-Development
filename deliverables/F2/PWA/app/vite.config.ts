import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'node:path';
import pkg from './package.json' with { type: 'json' };

export default defineConfig({
  plugins: [
    react(),
    process.env.BUNDLE_VISUALIZE === '1'
      ? visualizer({ filename: 'dist/bundle.html', gzipSize: true, brotliSize: true, open: false })
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
});
