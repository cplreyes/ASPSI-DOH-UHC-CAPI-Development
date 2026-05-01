/**
 * F2 PWA — geolocation helper.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§9)
 *
 * Wraps navigator.geolocation.getCurrentPosition with a 5s timeout and
 * collapses every failure mode (browser unsupported, permission denied,
 * position unavailable, timeout) into a clean `null` so the submit flow
 * can degrade gracefully — submission still goes through, just without
 * lat/lng. The admin Map Report tolerates missing GPS rows.
 *
 * Returning a permissive null (instead of throwing) is deliberate: a
 * healthcare worker who declines GPS once should still be able to submit.
 */

const TIMEOUT_MS = 5_000;

export interface GeoCoords {
  lat: number;
  lng: number;
}

export async function getGeolocation(): Promise<GeoCoords | null> {
  const geo = typeof navigator !== 'undefined' ? navigator.geolocation : undefined;
  if (!geo) return null;

  return new Promise<GeoCoords | null>((resolve) => {
    let settled = false;
    const settle = (value: GeoCoords | null) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };

    geo.getCurrentPosition(
      (pos) => settle({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => settle(null),
      { enableHighAccuracy: false, timeout: TIMEOUT_MS, maximumAge: 0 },
    );
  });
}
