// Self-destructing service worker. The old PWA's workbox SW serves the app shell
// from cache without touching the network, so a returning tester never sees the
// _redirects 301 — the browser's SW update check fetches THIS file (same URL the
// app registered: /sw.js, scope /), byte-diff installs it, and activation nukes
// every cache, unregisters, and walks all open tabs to the new origin.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
    await self.registration.unregister();
    const clients = await self.clients.matchAll({ type: 'window' });
    for (const c of clients) c.navigate('https://uhc-hcw.asiansocial.org/');
  })());
});
