# Runbook — F2 backend secrets rotation policy

**Created:** 2026-05-12
**Closes:** #172 (E4-PWA-010 — backend secrets rotation policy documented)
**Owner:** Carl (hands-on Cloudflare + Google Workspace + Gmail credential access — can't be delegated)
**Cadence:** See per-secret tables below; emergency rotation on any suspected compromise

---

## Context

The F2 PWA backend uses 6 distinct secret-bearing surfaces. This runbook defines what each is, when to rotate, how to rotate, and what breaks if you skip it.

| Secret | Layer | Default cadence | Emergency trigger |
|---|---|---|---|
| `JWT_SIGNING_KEY` | Worker (`wrangler secret`) | Annual | Suspected leak, departing operator, post-incident |
| `APPS_SCRIPT_HMAC` / `PROP_HMAC_SECRET` | Worker secret + AS Script Property | Annual + on AS deploy ID rotation | Same |
| `APPS_SCRIPT_URL` (deploy ID) | Worker secret + AS deployment | When AS code changes materially | Same |
| Cloudflare R2 access keys | Account-level (Cloudflare dashboard) | Annual | Same |
| `aspsi.doh.uhc.survey2.data@gmail.com` password | Google Workspace | Quarterly | Same |
| Admin user passwords (`F2_Users.password_hash`) | F2 Admin Portal — per-user | Per user, on demand (forced rotation on role change) | Suspected leak, role change, departure |

**Order of operations on a multi-secret rotation:** rotate the password (Gmail) first, then everything downstream that depends on access to the AS / Cloudflare dashboard. JWT + HMAC last because they require coordinated worker + AS deploys.

---

## 1. `JWT_SIGNING_KEY` (Worker)

**What it does:** signs every enrollment-token JWT minted for HCW tablets and every admin session JWT. Rotation invalidates all currently-active sessions and tokens — testers/HCWs need new tokens.

**When to rotate:**
- Annual (calendar reminder: every May 1)
- Immediately if leaked (e.g., committed to git, leaked in a screenshot, exposed in a log)
- After any operator with prod Cloudflare access leaves

**How to rotate:**

1. Generate new key:
   ```sh
   openssl rand -base64 32 | tr -d '=' | tr '+/' '-_'
   ```
2. Set on Worker (do staging first):
   ```sh
   cd deliverables/F2/PWA/worker
   wrangler secret put JWT_SIGNING_KEY --env staging
   # paste the new key, hit enter
   wrangler secret put JWT_SIGNING_KEY
   # paste the same new key for prod
   ```
3. Re-mint all active enrollment tokens. Open Admin Portal → Data → HCWs → for each row with `status='enrolled'`, click **REISSUE**. (For >50 HCWs, file a follow-up to add a bulk-reissue script.)
4. Force-logout all active admin sessions: open Admin Portal → Users → for each row, click the menu → **Revoke active sessions**. (No bulk button yet.)
5. Notify Shan + Kidd + Marriz in `#f2-pwa-uat` that they need to re-login and re-enroll their test devices.

**What breaks if you skip:** key compromise → arbitrary token forgery → unauthorized admin access OR unauthorized survey submission with stolen HCW identity.

---

## 2. `APPS_SCRIPT_HMAC` / `PROP_HMAC_SECRET`

**What it does:** the Worker signs every request to Apps Script with HMAC-SHA256 over the request body using this shared secret. AS verifies the signature before executing. Rotating requires the Worker secret + the AS Script Property to update **simultaneously** — there's no graceful overlap.

**When to rotate:**
- Annual (calendar reminder: every May 1, paired with `JWT_SIGNING_KEY`)
- Immediately if leaked
- Whenever the Apps Script deploy ID rotates (see §3)

**How to rotate (paired update — coordinate timing carefully):**

1. Generate new HMAC secret:
   ```sh
   openssl rand -base64 32 | tr -d '=' | tr '+/' '-_'
   ```
2. Open the F2-PWA-Backend Apps Script project. Project Settings → Script Properties → set `PROP_HMAC_SECRET` to the new value. **Do NOT save yet.**
3. In a separate shell, queue the Worker secret update:
   ```sh
   cd deliverables/F2/PWA/worker
   wrangler secret put APPS_SCRIPT_HMAC --env staging
   # paste new value
   ```
4. Click **Save** on the AS Script Property → immediately complete the wrangler `secret put` for staging by hitting enter.
5. Smoke-test staging: open `https://f2-pwa-worker-staging.hcw.workers.dev/health` → expect 200. Submit a test enrollment via `/admin/login` (staging). If 503 errors with HMAC mismatch in logs, you mistimed the swap — repeat steps 2–4 carefully.
6. Repeat for prod:
   ```sh
   wrangler secret put APPS_SCRIPT_HMAC
   ```
   Run AS Script Property update in lockstep on the prod AS project (not the staging one — they're separate AS projects per `2026-05-01-ap0-apps-script-staging-setup.md`).
7. Smoke prod via Admin Portal → Data → Responses (should load).

**Disruption window:** 1–3 minutes if you do it carefully; up to 10 minutes if you flub the timing and have to repeat. Run it in a low-traffic window (early AM PHT).

**What breaks if you skip:** HMAC compromise → an attacker who knows the secret can call Apps Script directly and bypass Worker auth, manipulating sheet data without going through the Admin Portal.

---

## 3. `APPS_SCRIPT_URL` (deployment ID)

**What it does:** the Worker `fetch`-es Apps Script at this exact URL. Each AS deployment has a unique URL containing the deploy ID. Rotating means re-deploying AS and updating the Worker secret.

**When to rotate:**
- Whenever you make material AS code changes that need to atomically activate (rare — most AS updates use the existing deployment via `clasp push` which updates the same deploy ID).
- If the deploy ID is somehow leaked alongside the HMAC (combined leak = full bypass).

**How to rotate:**

1. In the AS editor: **Deploy → New deployment** (NOT "Manage deployments" → edit). Copy the new Web app URL.
2. Update Worker secret:
   ```sh
   cd deliverables/F2/PWA/worker
   wrangler secret put APPS_SCRIPT_URL --env staging
   wrangler secret put APPS_SCRIPT_URL
   ```
3. Smoke as in §2 step 5.
4. **Archive the old deployment** in AS (Manage deployments → Archive). Don't delete — keep for audit trail.

**What breaks if you skip:** AS deployment URL stays callable indefinitely after a code change; old code keeps running for any caller who hasn't updated their URL. Mostly an issue if you forgot to update AS Script Properties at the same time and prod is still hitting the old deploy.

---

## 4. Cloudflare R2 access keys

**What they do:** R2 buckets are bound to the Worker via `[[r2_buckets]]` config (binding: `F2_ADMIN_R2`); the Worker uses bucket-binding API, not S3-compatible access keys, so there are no per-Worker R2 access keys to rotate. **However**, if you've created S3-compatible access keys at the account level for `wrangler r2 object get` backup runs (per `2026-05-12-f2-pwa-backup-restore.md`), those need annual rotation.

**When to rotate:**
- Annual
- Immediately if the access-key CSV is leaked

**How to rotate:**

1. Cloudflare dashboard → R2 → Manage R2 API tokens → revoke the existing token.
2. Create a new token with the same scope (read + write on `f2-admin`, `f2-admin-staging`, both `-preview` variants).
3. Update local credentials file (`~/.cloudflare/r2-credentials` or wherever your backup script reads from).
4. Re-run a backup smoke (one bucket): `wrangler r2 object list f2-admin` → expect non-error.

**What breaks if you skip:** worst-case, leaked access key lets an attacker enumerate + delete + replace bucket objects. Backup files would be the highest-value target.

---

## 5. Project Gmail password

**What it does:** the project mailbox `aspsi.doh.uhc.survey2.data@gmail.com` is the operator account for everything Cloudflare + Apps Script + Drive (sheet) is bound to. Compromise = full system takeover.

**When to rotate:**
- Quarterly (calendar reminder: 1st of Feb / May / Aug / Nov)
- Immediately on any operator transition (Carl handoff, ASPSI ops change)
- Immediately on any phishing/malware suspicion

**How to rotate:**

1. Sign in via Google Account → Security → Password → change.
2. Update password manager (1Password / Bitwarden — wherever the credential is stored for cross-operator handoff).
3. Re-authenticate any active wrangler / clasp sessions:
   ```sh
   wrangler logout
   wrangler login
   clasp logout
   clasp login
   ```
4. Verify 2FA is still enabled and recovery codes are still trusted.

**What breaks if you skip:** password compromise → attacker logs into Gmail → accesses every connected service → full data exfiltration possible.

---

## 6. Admin user passwords (`F2_Users.password_hash`)

**What they are:** per-user passwords for ASPSI ops staff using the Admin Portal. PBKDF2-hashed (100k iters per `worker/src/admin/auth.ts:18`).

**When to rotate:**
- On role change (forced by role_version bump — user is bounced to login on next request)
- On suspected leak
- Annual recommended (no automatic enforcement yet)
- On staff departure (delete the user, don't just rotate)

**How to rotate (user-initiated):**

1. User logs into Admin Portal → click their username at sidebar bottom → Change password.
2. Enter old + new (≥ 8 chars, ≥ 1 number, ≥ 1 letter).
3. New password takes effect on next request; existing JWT continues to work until session expiry (60 min) — they can keep working.

**How to rotate (admin-forced):**

1. Admin Portal → Users → find user → click menu → **Reset password**.
2. Modal returns a one-time temporary password. Hand to user out-of-band (Slack DM, in-person — NOT email).
3. User logs in with temp password → forced password change on next auth (`password_must_change=true`).

**What breaks if you skip:** standard credential-stuffing risk; one stale departed-operator account is one open door.

---

## Annual rotation checklist (run May 1 each year)

- [ ] §1: rotate `JWT_SIGNING_KEY` on staging + prod, re-mint all enrollment tokens, force-logout admin sessions
- [ ] §2: rotate `APPS_SCRIPT_HMAC` / `PROP_HMAC_SECRET` (paired) on staging + prod
- [ ] §4: rotate Cloudflare R2 access tokens used by backup tooling
- [ ] §5 (if not done in last quarter): rotate Gmail password, re-auth wrangler + clasp
- [ ] §6: send "annual password rotation" Slack reminder to all admin users; track non-compliance after 14 days

Document each rotation in `log.md` with date + ticket reference.

---

## Emergency rotation (any secret leaked)

1. **Stop writes** (if compromise scope is unclear): Apps Script editor → pause cron triggers + open Admin Portal → toggle the kill-switch (Apps & Settings → Kill switch — if implemented; if not, manually set `OPS_KILL_SWITCH=true` script property).
2. Rotate the leaked secret per the relevant section above.
3. Audit: open Admin Portal → Data → Audit → filter by suspicious actor / time window. Look for unexpected mutations during the leak window.
4. **Resume writes** once rotation is verified.
5. File an incident issue documenting: what leaked, how, scope of audit, mitigation taken.
