/**
 * F2 Admin Portal — two-axis login throttle.
 *
 * Per-username throttle (10 attempts / 15 min) is the correctness control:
 * stops a brute-force attack on a known username regardless of IP rotation.
 * Per-IP throttle (50 attempts / 15 min) is the spam shield: stops a single
 * attacker hammering the login endpoint across many usernames. Both are
 * required — keying only by IP traps shared NATs (whole ASPSI office gets
 * locked out by one fat-fingered colleague); keying only by username lets
 * an attacker rotate residential proxies past the per-user counter.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 1.9)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§5.10, §10.1)
 */

const WINDOW_SECONDS = 15 * 60;
const PER_USER_LIMIT = 10;
const PER_IP_LIMIT = 50;

/**
 * Minimal KV interface satisfied by Cloudflare's KVNamespace as well as
 * the in-memory test fakes. We bind a read-write subset because the
 * throttle increments + expires keys but never iterates them.
 */
export interface ThrottleKv {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
  delete(key: string): Promise<void>;
}

function windowStart(): number {
  return Math.floor(Date.now() / 1000 / WINDOW_SECONDS) * WINDOW_SECONDS;
}

export interface ThrottleResult {
  allowed: boolean;
  reason?: 'username' | 'ip';
}

/**
 * Returns `{ allowed: true }` if both per-username AND per-IP counters are
 * under threshold for the current 15-minute window.
 *
 * If either is over, returns `{ allowed: false, reason }`. The per-username
 * check is evaluated first so the more specific reason wins.
 */
export async function checkLoginThrottle(
  kv: ThrottleKv,
  username: string,
  ipHash: string,
): Promise<ThrottleResult> {
  const w = windowStart();
  const userKey = `throttle:login:user:${username}:${w}`;
  const ipKey = `throttle:login:ip:${ipHash}:${w}`;
  const [u, i] = await Promise.all([kv.get(userKey), kv.get(ipKey)]);
  if (u && Number(u) >= PER_USER_LIMIT) return { allowed: false, reason: 'username' };
  if (i && Number(i) >= PER_IP_LIMIT) return { allowed: false, reason: 'ip' };
  return { allowed: true };
}

/**
 * Increment both counters. Both are TTL'd to the window length so they
 * roll off automatically without explicit cleanup.
 */
export async function recordFailedLogin(
  kv: ThrottleKv,
  username: string,
  ipHash: string,
): Promise<void> {
  const w = windowStart();
  const userKey = `throttle:login:user:${username}:${w}`;
  const ipKey = `throttle:login:ip:${ipHash}:${w}`;
  const [u, i] = await Promise.all([kv.get(userKey), kv.get(ipKey)]);
  await Promise.all([
    kv.put(userKey, String(Number(u || '0') + 1), { expirationTtl: WINDOW_SECONDS }),
    kv.put(ipKey, String(Number(i || '0') + 1), { expirationTtl: WINDOW_SECONDS }),
  ]);
}

/**
 * Clear the per-username counter for the current window. Called after a
 * successful login so the user isn't locked out by a fat-fingered prior
 * attempt. The per-IP counter is intentionally NOT reset — it tracks
 * cross-user attack volume from a single source and resets naturally with
 * the window.
 */
export async function resetLoginThrottle(kv: ThrottleKv, username: string): Promise<void> {
  const w = windowStart();
  await kv.delete(`throttle:login:user:${username}:${w}`);
}
