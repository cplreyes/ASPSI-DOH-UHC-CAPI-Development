# FX-002 — Backend permission-set surface for role-aware nav gating

**Issue:** #324 (ADMIN PORTAL 5A.15) · **Date:** 2026-06-02 · **Status:** Design — ready to build
**Scope:** Unblock the cosmetic "hide controls the current role can't use" enhancement (FX-002) by deciding what the backend surfaces so the frontend can role-gate the sidebar.

---

## 1. Summary & decision

**Decision: return the user's resolved permission set in the login response body** (and the change-password re-mint response), store it in the in-memory admin auth context, and filter `NAV_GROUPS` against it in `Layout.tsx`. **No JWT change, no new endpoint, no AS change, no migration.**

The permission set is **advisory UI-only**. The Worker's `requirePerm` (`rbac.ts`) remains the sole authorization boundary and is untouched. Nav gating **fails open** (show the item when in doubt) while enforcement **fails closed** (server returns 403). A user who tampers with their in-memory perm map to reveal a hidden link gains nothing — the actual request is still rejected server-side.

---

## 2. Problem & why it was blocked

`Layout.tsx` `NAV_GROUPS` renders **every** nav item to every authenticated user (documented at `Layout.tsx:32-33`: *"Role-aware filtering still TBD (FX-002 follow-up). Today every link is visible to every authenticated user; Worker enforces 403 on actual access."*). A user whose role lacks `dash_users` still sees the **Users** link; clicking it 401/403s and bounces — functional, but confusing.

It was design-blocked because **custom roles exist** (admins define roles in `F2_Roles`). The frontend cannot hardcode which items a role may see — it must learn the current user's resolved permissions from the backend. The unmade decision was: **in what shape, and surfaced where?**

---

## 3. Chosen approach & rationale

**Surface the perm set in the login response body.** `handleLogin` (`worker/src/admin/handlers/auth.ts`) *already* fetches `admin_roles_list` and resolves the user's full `F2_Roles` row to read `role.version` for the JWT. The perm columns are sitting right there — projecting them into a map is near-zero extra cost.

Why this wins over the alternatives:

| Option | Verdict |
|---|---|
| **(A) Perms in login response body** ✅ chosen | The role object is already in hand; the admin JWT is in-memory only, so a perm map in auth-context has the *exact same lifecycle* as the token (cleared on reload/logout). Zero new round-trips, zero JWT bloat, custom roles "just work." |
| (B) Perms as a JWT claim | Rejected. The JWT is sent on every request → bloat for data that's only read once at app load. The in-memory JWT gives a claim **no persistence advantage** over the response body. Larger attack surface (claim tampering is meaningless for an advisory map, but it muddies the "JWT = identity, not UI state" line). |
| (C) Dedicated `GET /admin/api/me/permissions` | Rejected for now. An extra round-trip for data login already has. Useful only if perms must refresh mid-session without re-login — but `role_version` invalidation (below) already bounds staleness. Noted as the natural extension point if live-refresh is ever needed. |

---

## 4. Backend changes

**No Apps Script change.** `admin_roles_list` already returns each role row with all perm columns; `handleLogin` already resolves the user's role from it. **No migration.** **JWT untouched.**

### 4.1 `worker/src/admin/handlers/auth.ts`

Add an explicit perm-key allowlist (auditable; won't leak `name`/`version`/`created_by`/`created_at`/`is_builtin`, and won't accidentally expose a future non-perm column):

```ts
// The RBAC permission columns on F2_Roles, in display order. The single
// source of truth for what the client may learn about its own role. Keep in
// sync with the F2_Roles schema (Migrations.js) and rbac.ts perm checks.
export const PERM_KEYS = [
  'dash_data', 'dash_report', 'dash_apps', 'dash_users', 'dash_roles',
  'dict_self_admin_up', 'dict_self_admin_down',
  'dict_paper_encoded_up', 'dict_paper_encoded_down',
  'dict_capi_up', 'dict_capi_down',
] as const;

export type PermissionSet = Record<string, boolean>;

/** Project a resolved F2_Roles row into a boolean perm map (advisory, UI-only). */
export function projectPermissions(role: Record<string, unknown>): PermissionSet {
  const out: PermissionSet = {};
  for (const k of PERM_KEYS) out[k] = !!role[k];
  return out;
}
```

Extend the success contract:

```ts
interface LoginSuccess {
  token: string;
  role: string;
  role_version: number;
  expires_at: number;
  password_must_change: boolean;
  permissions: PermissionSet; // NEW — advisory nav-gating hint
}
```

In `handleLogin`, after the role is resolved (the `role` object already exists for `role.version`), set `permissions: projectPermissions(role)` on the returned `success`.

In `handleChangeMyPassword`, the same `LoginSuccess` is returned after the JWT re-mint and the role is re-resolved (`rolesResp` → `role`); set `permissions: projectPermissions(role)` there too, so a post-rotation client keeps a consistent perm map without a re-login.

> Both handlers already fetch roles and find the role row; this adds one pure projection call and one response field. ~15 lines total.

### 4.2 Worker tests (`test/admin/handlers/auth.test.ts`)
- `handleLogin` returns `permissions` reflecting the role's columns for a **built-in** role (e.g. Administrator → all true) **and** a **custom** role (e.g. a role with only `dash_data` true → `{dash_data:true, dash_report:false, …}`).
- `handleChangeMyPassword` returns `permissions` for the resolved role.
- `projectPermissions` unit: ignores non-perm columns, coerces truthy/falsy to boolean.

---

## 5. Frontend changes

### 5.1 `app/src/admin/lib/auth-context.tsx`
- `AdminLoginResponse` gains `permissions?: Record<string, boolean>` (optional → backward-compatible with an old Worker).
- `AdminAuthState` gains `permissions: Record<string, boolean> | null` (default `null` in `INITIAL_STATE`).
- `setAuth` stores `resp.permissions ?? null`.
- `useAdminAuth()` already spreads state, so `permissions` is exposed automatically.

### 5.2 `app/src/admin/Layout.tsx`

Add `requiredPerm` to `NavItemSpec` and tag each item (Help omits it → always visible):

```ts
interface NavItemSpec { to: string; label: string; description: string;
  icon: (props: SVGProps<SVGSVGElement>) => JSX.Element; requiredPerm?: string; }
```

| Nav item | `to` | `requiredPerm` |
|---|---|---|
| Data | `/admin/data` | `dash_data` |
| Reports | `/admin/report` | `dash_report` |
| Encode | `/admin/encode` | `dict_paper_encoded_up` |
| Apps & Settings | `/admin/apps` | `dash_apps` |
| Users | `/admin/users` | `dash_users` |
| Roles | `/admin/roles` | `dash_roles` |
| Help | `/admin/help` | *(none — always visible)* |

Filter at the render callsite, with the **graceful-degradation default**:

```ts
const { permissions } = useAdminAuth();
const canSee = (item: NavItemSpec) =>
  !item.requiredPerm ||           // Help, etc. — always visible
  permissions === null ||         // old client / Worker didn't send perms → show all
  permissions[item.requiredPerm]; // role grants it
// ...
NAV_GROUPS
  .map((g) => ({ ...g, items: g.items.filter(canSee) }))
  .filter((g) => g.items.length > 0)   // hide a group whose eyebrow header would be orphaned
  .map((group) => ( /* existing render */ ))
```

The mobile `FLAT_NAV` strip applies the same `canSee` filter.

### 5.3 Frontend tests (`Layout.test.tsx`)
- Renders only items whose `requiredPerm` is `true` in `permissions`; an item whose perm is `false` is **absent**.
- **Help is always rendered**, regardless of perms.
- `permissions === null` → **all** items render (graceful degradation).
- A group whose items all filter out → its eyebrow header is **not** rendered.

---

## 6. Security posture

- **Advisory only.** The perm map gates *visibility*, never *access*. `rbac.ts requirePerm` is unchanged and remains the sole authorization gate; every protected route still calls it.
- **Fail-open nav / fail-closed enforcement.** Missing/null/tampered perms → the nav shows the item (no worse than today). The server still 403s the actual request. There is no path where hiding fails *open* on enforcement.
- **No new trust.** The client already receives `role` + `role_version`; it now also receives the boolean projection of that role's perm columns — strictly less sensitive than the role name it already holds. Nothing secret is exposed.

---

## 7. Edge cases

- **Custom roles** — handled natively: `permissions` is the projection of the *resolved* role row, not a built-in assumption.
- **Demoted mid-session** — the nav reflects login-time perms. When a role's perms change, `F2_Roles.version` bumps; the stale-`role_version` JWT is rejected (`E_AUTH_EXPIRED`) on the next gated request or within the 5-min `RoleVersionCache` TTL → re-login → fresh perm map. The menu does **not** live-update (a demoted user briefly still sees, e.g., the Users link), but clicking it 403s and redirects — **cosmetic lag, no security impact**. This is the accepted behavior from the issue's first triage (option 1); live menu refresh would be the `/me/permissions` follow-up.
- **JWT** — untouched (size, claims, verify path all unchanged).
- **Old client / version skew** — fully backward-compatible **both** directions. New Worker + old frontend: extra field ignored, shows all (today's behavior). New frontend + old Worker: `permissions` absent → `null` → shows all.
- **Unauthenticated** — unchanged. The existing Help-only branch renders only Help; the filter runs only on the authenticated branch.

---

## 8. Scope

**IN:** coarse **top-level** nav gating — one `requiredPerm` per sidebar item.

**OUT (clearly-scoped follow-up):** intra-page **sub-tab** gating. The **Data** page aggregates Responses/Audit/DLQ/HCWs and the **Apps & Settings** page aggregates Files/DataSettings/Versioning/Kill-switch/Quota. Today every sub-tab under a page shares that page's single perm (`dash_data` / `dash_apps`), so there is nothing finer to gate **without first introducing new perm columns** in `F2_Roles`. That is a larger schema + RBAC change; it is not required to ship FX-002. When it happens, the same `permissions` map extends to it and the gate attaches at each page's tab bar.

---

## 9. Test plan (summary)

| Layer | Assertion |
|---|---|
| Worker | login + change-password return `permissions` matching the role columns (built-in **and** custom role); `projectPermissions` ignores non-perm columns |
| Frontend | nav filtered by perm map; Help always shown; `permissions===null` shows all; false-perm item absent; empty group header hidden; mobile strip filtered identically |
| Manual | log in as a custom role granting only `dash_data` → sidebar shows only **Data** + **Help**; the rest are hidden; direct-navigating to a hidden route still 403s (server authority intact) |

---

## 10. Rollout

- **Backward-compatible**, **no migration**, **no JWT change**, **no AS change**.
- Ship Worker + frontend together or in either order — version skew degrades to "show all," which is exactly today's behavior.
- Single PR: `auth.ts` (PERM_KEYS + projection + 2 response fields) + `auth-context.tsx` (1 field) + `Layout.tsx` (requiredPerm tags + filter) + tests.
- Effort: ~½ day. The diff is small; the value is the closed cosmetic gap and a clean, server-authoritative perm surface that the sub-tab follow-up can reuse.

---

### Appendix — files touched

| File | Change |
|---|---|
| `worker/src/admin/handlers/auth.ts` | `PERM_KEYS`, `projectPermissions`, `LoginSuccess.permissions`, set in `handleLogin` + `handleChangeMyPassword` |
| `worker/test/admin/handlers/auth.test.ts` | login/change-pw return perms; projection unit |
| `app/src/admin/lib/auth-context.tsx` | `AdminLoginResponse.permissions?`, `AdminAuthState.permissions`, store in `setAuth` |
| `app/src/admin/Layout.tsx` | `NavItemSpec.requiredPerm`, route→perm tags, `canSee` filter + empty-group hide (desktop + mobile) |
| `app/src/admin/Layout.test.tsx` (new/extended) | nav-gating behavior |
</content>
