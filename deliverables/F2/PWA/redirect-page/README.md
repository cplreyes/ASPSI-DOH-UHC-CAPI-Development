# CF Pages redirect deployment (P6 §3.1)

Replaces the dead-but-alive-looking old build on `f2-pwa.pages.dev` (and staging)
with a redirect to the new origin. Three files, all load-bearing:

- `_redirects` — 301 every path to `https://uhc-hcw.asiansocial.org/:splat` (network hits)
- `sw.js` — self-destructing service worker: the old workbox SW serves the cached app
  shell without hitting the network, so the 301 alone never reaches returning testers.
  The browser's SW update check (bypasses HTTP cache for the script by default) picks
  this up, clears all caches, unregisters, and navigates open tabs to the new origin.
- `index.html` — visible fallback + JS redirect for anything that still renders

Deploy (needs `npx wrangler login`; run AFTER the P5 pass + HMAC rotation, per the
P6 order — keep the deployment ~30 days, then delete the Pages projects):

```bash
cd deliverables/F2/PWA/redirect-page
npx wrangler pages deploy . --project-name f2-pwa --branch main --commit-dirty=true
npx wrangler pages deploy . --project-name f2-pwa-staging --branch staging --commit-dirty=true
```

Verify: `curl -sI https://f2-pwa.pages.dev/enroll | grep -i location` → uhc-hcw;
open the old URL in a browser that used the PWA → lands on uhc-hcw within one reload.
