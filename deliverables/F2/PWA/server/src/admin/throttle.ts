/**
 * F2 Admin Portal — two-axis login throttle (port of worker/src/admin/throttle.ts).
 * Where the Worker used CF KV, the box uses the AdminStore's auth_kv seam
 * (MySQL table with expiry; in-memory map in tests). Key names and limits
 * are identical to the Worker.
 */

const WINDOW_SECONDS = 15 * 60;
const PER_USER_LIMIT = 10;
const PER_IP_LIMIT = 50;

/** KV subset the throttle needs — satisfied by AdminStore's kv methods. */
export interface ThrottleKv {
  kvGet(key: string): Promise<string | null>;
  kvPut(key: string, value: string, ttlSeconds?: number): Promise<void>;
  kvDelete(key: string): Promise<void>;
}

function windowStart(): number {
  return Math.floor(Date.now() / 1000 / WINDOW_SECONDS) * WINDOW_SECONDS;
}

export interface ThrottleResult {
  allowed: boolean;
  reason?: 'username' | 'ip';
}

export async function checkLoginThrottle(
  kv: ThrottleKv,
  username: string,
  ipHash: string,
): Promise<ThrottleResult> {
  const w = windowStart();
  const userKey = `throttle:login:user:${username}:${w}`;
  const ipKey = `throttle:login:ip:${ipHash}:${w}`;
  const [u, i] = await Promise.all([kv.kvGet(userKey), kv.kvGet(ipKey)]);
  if (u && Number(u) >= PER_USER_LIMIT) return { allowed: false, reason: 'username' };
  if (i && Number(i) >= PER_IP_LIMIT) return { allowed: false, reason: 'ip' };
  return { allowed: true };
}

export async function recordFailedLogin(
  kv: ThrottleKv,
  username: string,
  ipHash: string,
): Promise<void> {
  const w = windowStart();
  const userKey = `throttle:login:user:${username}:${w}`;
  const ipKey = `throttle:login:ip:${ipHash}:${w}`;
  const [u, i] = await Promise.all([kv.kvGet(userKey), kv.kvGet(ipKey)]);
  await Promise.all([
    kv.kvPut(userKey, String(Number(u || '0') + 1), WINDOW_SECONDS),
    kv.kvPut(ipKey, String(Number(i || '0') + 1), WINDOW_SECONDS),
  ]);
}

/** Clear the per-username counter after a successful login (per-IP preserved). */
export async function resetLoginThrottle(kv: ThrottleKv, username: string): Promise<void> {
  const w = windowStart();
  await kv.kvDelete(`throttle:login:user:${username}:${w}`);
}

/** Seconds until the current 15-minute window rolls over (Retry-After). */
export function retryAfterSeconds(): number {
  const now = Math.floor(Date.now() / 1000);
  const winStart = Math.floor(now / WINDOW_SECONDS) * WINDOW_SECONDS;
  return Math.max(1, winStart + WINDOW_SECONDS - now);
}
