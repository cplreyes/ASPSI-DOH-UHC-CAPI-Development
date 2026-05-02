/**
 * F2 Admin Portal — Apps Script HMAC client.
 *
 * Worker calls Apps Script `?action=admin_*` RPCs by POSTing
 * `{ action, ts, request_id, payload, hmac }` envelopes signed over the
 * canonical string `${action}.${ts}.${request_id}.${stable_json_payload}`.
 *
 * Distinct from the existing PWA submit HMAC in src/hmac.ts (`METHOD|action|ts|body`).
 *
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§6.2)
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.4)
 */

const enc = new TextEncoder();

function bytesToHex(bytes: Uint8Array): string {
  let hex = '';
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i]!;
    hex += b.toString(16).padStart(2, '0');
  }
  return hex;
}

/**
 * Stable JSON serialization with deterministic key ordering, so equivalent
 * payloads with different key orders produce identical signatures.
 *
 * Note: this is a one-level sort. Nested objects are not deeply sorted;
 * for simple admin payloads (flat key/value plus arrays) this is sufficient.
 * If deeper structures are needed in the future, switch to a canonical-JSON
 * library on both sides (Worker + Apps Script).
 */
function stableJson(payload: unknown): string {
  if (payload === null || payload === undefined) return 'null';
  if (typeof payload !== 'object' || Array.isArray(payload)) {
    return JSON.stringify(payload);
  }
  const keys = Object.keys(payload as Record<string, unknown>).sort();
  return JSON.stringify(payload, keys);
}

async function importHmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
}

/**
 * Sign an admin RPC envelope. Returned signature is lowercase hex SHA-256.
 *
 * @param secret      The HMAC secret (APPS_SCRIPT_HMAC; mirrors the AS-side ScriptProperty)
 * @param action      Admin action name, e.g. "admin_users_list"
 * @param ts          Unix seconds (must match the ts in the envelope body)
 * @param requestId   UUID propagated from Worker edge through Apps Script to F2_Audit
 * @param payload     Action-specific payload (will be stable-JSON-serialized)
 */
export async function signRequest(
  secret: string,
  action: string,
  ts: number,
  requestId: string,
  payload: unknown,
): Promise<string> {
  const canonical = `${action}.${ts}.${requestId}.${stableJson(payload)}`;
  const key = await importHmacKey(secret);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(canonical));
  return bytesToHex(new Uint8Array(sig));
}

export interface AppsScriptResponse<T = unknown> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string };
}

/**
 * Minimal KV surface for the per-day quota counter. Accepting an interface
 * (not the full KVNamespace) keeps tests trivial - production wiring still
 * passes env.F2_AUTH which structurally satisfies this.
 */
export interface QuotaKv {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
}

/**
 * Per-UTC-day Apps Script quota counter. Reads `as_quota:<YYYY-MM-DD>`,
 * increments by 1, writes back with a 7-day TTL so old keys self-evict.
 *
 * Errors are swallowed - a counter blip must never fail the underlying
 * AS request. The QuotaWidget tolerates an occasional miss.
 */
export async function bumpAdminQuota(kv: QuotaKv, now: Date = new Date()): Promise<void> {
  try {
    const pad = (n: number) => String(n).padStart(2, '0');
    const ymd = `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())}`;
    const key = `as_quota:${ymd}`;
    const raw = await kv.get(key);
    const next = (raw ? Number(raw) || 0 : 0) + 1;
    await kv.put(key, String(next), { expirationTtl: 7 * 86400 });
  } catch {
    // never propagate - counter is observability, not load-bearing
  }
}

/**
 * Call an Apps Script admin RPC. Returns the parsed envelope.
 * On HTTP failure, returns `{ ok: false, error: { code: 'E_BACKEND', ... }}`.
 *
 * Pass `kv` to bump the per-day quota counter on each invocation (read by
 * the QuotaWidget endpoint). Bump runs after the fetch but before the
 * envelope is returned, so it counts every AS round-trip whether the
 * envelope is ok or not (failures still consume Google's daily quota).
 */
export async function callAppsScript<T = unknown>(
  url: string,
  secret: string,
  action: string,
  payload: unknown,
  requestId: string,
  kv?: QuotaKv,
): Promise<AppsScriptResponse<T>> {
  const ts = Math.floor(Date.now() / 1000);
  const hmac = await signRequest(secret, action, ts, requestId, payload);
  const body = JSON.stringify({ action, ts, request_id: requestId, payload, hmac });
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  });
  if (kv) await bumpAdminQuota(kv);
  if (!r.ok) {
    return { ok: false, error: { code: 'E_BACKEND', message: `Apps Script ${r.status}` } };
  }
  return r.json() as Promise<AppsScriptResponse<T>>;
}
