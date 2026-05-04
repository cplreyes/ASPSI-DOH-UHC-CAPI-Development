import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import './lib/zod-error-map';
import { registerSW } from 'virtual:pwa-register';

// FX-016 (2026-05-04): the F2 Admin Portal at /admin/* is a non-offline
// operations console — it has no use case for the SW (no offline submit, no
// install-to-home-screen pattern). When the SW is active and intercepts
// /admin/* navigations, it produces blank pages on full-page navigations
// (typed URLs, fresh tabs, soft reloads) even with `navigateFallbackDenylist`
// in place — the denylist exempts the navigateFallback handler but doesn't
// fully isolate /admin/* from the SW's other interception paths. Skipping
// SW registration entirely on /admin/* paths bypasses the issue cleanly.
// HCW survey routes ('/', '/enroll', '/survey/...') still get the SW for
// offline + install support.
const isAdminRoute = window.location.pathname.startsWith('/admin');

if (!isAdminRoute) {
  // Prompt-style SW registration. Full update UX lands in M11.
  registerSW({
    onNeedRefresh() {
      console.info('[PWA] New content available. Reload to update.');
    },
    onOfflineReady() {
      console.info('[PWA] Ready to work offline.');
    },
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
