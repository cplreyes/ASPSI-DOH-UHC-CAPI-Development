# Runbook — Per-tester admin accounts + ADMIN_PASSWORD_HASH sunset (prod)

**Created:** 2026-05-09
**Closes:** #64 (E4-APRT-042) + #65 (E4-APRT-043)
**Owner:** Carl (hands-on prod secrets — can't be delegated)
**Prereq:** PR #136 merged to main, deployed to prod, smoke-verified.

---

## Context

Two paired prod-ops items deferred from Sprint 004:

- **#64** — UAT testers (Shan, Kidd, optional `data_reader_uat`) currently share `carl_admin`, which collapses audit attribution. The Users dashboard shipped in PR #136 makes this a click-through, no scripts needed.
- **#65** — Prod-side completion of the M10 legacy auth sunset that staging finished 2026-05-04 under E4-APRT-039. Removes the now-unused `ADMIN_PASSWORD_HASH` secret from prod and deletes the dead `src/admin.ts` legacy route.

Order: **do #64 first**, then **#65**. Reason: confirming new admin accounts work end-to-end against the new `/admin/api/login` path before deleting the legacy fallback gives a 30-second rollback window if something's off.

---

## #64 — Per-tester admin accounts on prod

### Prereqs

- PR #136 merged to `main`. Wait for the cf-pages-deploy workflow + worker deploy to finish (~3 min).
- You have prod `carl_admin` credentials.
- Memory `[F2 Admin Portal — staging credentials]` lists the staging shape; prod uses your separate prod credentials.

### Steps

1. Open `https://f2-pwa.pages.dev/admin/login` in your browser.
2. Log in as `carl_admin` (prod credentials).
3. Navigate to **Users** in the sidebar.
4. For each tester, click **+ Add user** and fill:

   | username | role_name | first_name | last_name | email | initial password |
   |---|---|---|---|---|---|
   | `shan_admin` | `Administrator` | Shan | (last) | (email) | one-time, ≥8 chars, hand to Shan |
   | `kidd_admin` | `Administrator` | Kidd | (last) | (email) | one-time, ≥8 chars, hand to Kidd |
   | `data_reader_uat` | `Standard User` | Data Reader | UAT | — | one-time, ≥8 chars |

   The Create form sets `password_must_change=true` automatically (line 320 in `worker/src/admin/handlers/users.ts`). With #57 server-enforced, each tester's first login redirects them to `/admin/me/change-password` and they MUST rotate before any other endpoint responds.

5. Hand each tester their initial credential out-of-band (1Password share / Signal / etc — NOT email if the org policy forbids).
6. Watch each tester's first login complete. After they rotate, F2_Audit shows:
   - `admin_login` row with `actor_username = shan_admin` (theirs, not yours)
   - `admin_password_change` row immediately after (R2-#134 audit event)

### Verification (per acceptance criteria)

- [ ] `https://f2-pwa.pages.dev/admin/users` shows `shan_admin`, `kidd_admin`, `data_reader_uat` rows
- [ ] Each row's `password_must_change` column flips to false after the tester completes their first login
- [ ] F2_Audit table shows `actor_username` distinct per tester (no more shared `carl_admin` for their actions)
- [ ] Testers can read /admin/data without 403 (Administrator role grants `dash_data`); `data_reader_uat` can read but not mutate

### Rollback

Each row is independently revocable via the Users dashboard's **Revoke** action (force-logout) or **Delete**. With #133 shipped, the dashboard refuses to delete the last Administrator and refuses self-delete — you can't accidentally lock yourself out.

### Onboarding loop (future testers)

Same flow. Document the credential delivery channel in your team's onboarding ticket template. The Users dashboard + bulk import (#100) are the two surfaces to use; CSV bulk import is overkill for ≤3 accounts.

---

## #65 — Prod ADMIN_PASSWORD_HASH deletion

### Prereqs

- #64 complete: at least one non-Administrator-role user (`data_reader_uat`) and at least two Administrator users exist on prod (you + Shan or Kidd).
- You can run `wrangler` against the prod env from this machine.

### Steps

1. **Confirm legacy route is dead in prod**:
   ```sh
   curl -i -X POST https://f2-pwa-worker.<account>.workers.dev/admin/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"carl_admin","password":"<bogus>"}'
   ```
   Expect **HTTP 500** (mirroring staging pre-deletion). The route handler in `src/admin.ts` reads `env.ADMIN_PASSWORD_HASH` directly; if the secret is still set it'll respond 401, if missing it 500s. Either way the legacy path is dead — but if you see 200 here, **STOP** and investigate; something's still wired.

2. **Delete the secret**:
   ```sh
   cd deliverables/F2/PWA/worker
   cmd.exe //c "wrangler secret delete ADMIN_PASSWORD_HASH --env production"
   ```
   Confirm the prompt. Wrangler propagates the deletion within ~30s.

3. **Smoke the new path**:
   ```sh
   curl -i -X POST https://f2-pwa-worker.<account>.workers.dev/admin/api/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"carl_admin","password":"<your prod password>"}'
   ```
   Expect **HTTP 200** + `{ token, role, role_version, expires_at, password_must_change }`. The new path reads from F2_Users (PBKDF2 verify) and doesn't touch the deleted secret.

4. **Remove the dead source**:
   - Delete `worker/src/admin.ts` (or the M10 legacy route block within it — depends on the file shape; check before deleting wholesale).
   - Update `worker/src/index.ts` to drop the import + dispatch.
   - Run `npm run typecheck && npm test` in `worker/`. Expect green.
   - Commit on `main`:
     ```sh
     git checkout main
     git pull
     git rm worker/src/admin.ts  # or use git diff to confirm scope
     git commit -m "chore(F2-admin): remove dead M10 legacy auth route (#65)"
     git push
     ```
   The cf-pages-deploy workflow + worker deploy run automatically.

5. **Final smoke**:
   - Re-login at `f2-pwa.pages.dev/admin/login` as `carl_admin`. Expect normal session.
   - Re-run the 401 curl from step 1 against `/admin/login` — expect **HTTP 404** now (route removed entirely, no longer 500).

### Verification (per acceptance criteria)

- [ ] `wrangler secret list --env production` no longer lists `ADMIN_PASSWORD_HASH`
- [ ] `/admin/api/login` returns 200 for valid creds
- [ ] `/admin/login` returns 404 (legacy route removed) — distinct from 500 (route present, secret missing)
- [ ] No commit references `ADMIN_PASSWORD_HASH` in `worker/src/`
- [ ] Memory entry `project_admin_password_rotation_pending.md` updated to "completed" or removed

### Rollback

If step 3 smoke fails (login broken), the legacy route was a hard-coded fallback. Restore by:

```sh
echo '<old hash value from team password manager>' | cmd.exe //c "wrangler secret put ADMIN_PASSWORD_HASH --env production"
```

You'll need the original hash value from your team password manager — gstack-worktree-handoff history has it under the M10 cutover entry. If lost, generate a fresh one with PBKDF2 + a known password and reset.

If step 4 build fails (something still imports from `src/admin.ts`), revert the rm and address the imports first.

---

## After both done

- Close #64 and #65 with a comment linking this runbook + the per-step verification screenshots.
- Update memory `project_admin_password_rotation_pending.md` to mark complete (or delete it).
- The `[E4-APRT-039 M10 sunset soak]` runbook (`2026-05-04-e4-aprt-039-m10-sunset-soak-open.md`) can be archived.

---

## Why this lives here, not in scrum/runbooks

`docs/superpowers/runbooks/` is the established home for project runbooks — see `2026-05-02-f2-admin-portal-prod-cutover.md` for the Phase F precedent. Filename matches that convention (`YYYY-MM-DD-<id>-<short>.md`).
