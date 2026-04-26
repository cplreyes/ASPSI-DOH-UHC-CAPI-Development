import { db, type EnrollmentRow } from './db';

export interface SetEnrollmentInput {
  hcw_id: string;
  facility_id: string;
  /** Per-tablet JWT (spec §5). Required after the auth re-arch. */
  device_token: string;
}

export async function getEnrollment(): Promise<EnrollmentRow | null> {
  const row = await db.enrollment.get('singleton');
  return row ?? null;
}

export async function setEnrollment(input: SetEnrollmentInput): Promise<EnrollmentRow> {
  const trimmedHcw = input.hcw_id.trim();
  if (trimmedHcw.length === 0) {
    throw new Error('hcw_id is required');
  }
  const trimmedToken = input.device_token.trim();
  if (trimmedToken.length === 0) {
    throw new Error('device_token is required');
  }
  const facility = await db.facilities.get(input.facility_id);
  if (!facility) {
    throw new Error(`Unknown facility ${input.facility_id}`);
  }
  const row: EnrollmentRow = {
    id: 'singleton',
    hcw_id: trimmedHcw,
    facility_id: facility.facility_id,
    facility_type: facility.facility_type,
    enrolled_at: Date.now(),
    device_token: trimmedToken,
  };
  await db.enrollment.put(row);
  return row;
}

export async function clearEnrollment(): Promise<void> {
  await db.enrollment.delete('singleton');
}

/**
 * Read the device JWT from the enrollment row, returning null if absent or expired.
 * Claims are parsed from the JWT on demand (spec §7.2 — no cached `device_token_exp`).
 */
export async function getDeviceToken(): Promise<{ token: string; expEpochS: number } | null> {
  const row = await getEnrollment();
  if (!row || !row.device_token) return null;
  const claims = parseJwtClaimsUnsafe(row.device_token);
  if (!claims || typeof claims.exp !== 'number') return null;
  const nowS = Math.floor(Date.now() / 1000);
  if (claims.exp < nowS) return null;
  return { token: row.device_token, expEpochS: claims.exp };
}

/**
 * Parse JWT claims WITHOUT verifying signature. UI-side only; the server is the
 * authority. Used for: client-side expiry check before request fires (avoids a
 * round-trip), enrollment-screen facility scoping.
 */
export function parseJwtClaimsUnsafe(token: string): Record<string, unknown> | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const payload = parts[1]!.replace(/-/g, '+').replace(/_/g, '/');
    const padded = payload + '==='.slice((payload.length + 3) % 4);
    return JSON.parse(atob(padded)) as Record<string, unknown>;
  } catch {
    return null;
  }
}
