/**
 * F2 PWA — geolocation helper.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.5)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§9)
 *
 * Wraps navigator.geolocation.getCurrentPosition with a 5s timeout. The
 * submit flow degrades gracefully — submission still goes through without
 * lat/lng — but since 2026-07-17 (Reports-tab audit P1-4) every failure mode
 * is NAMED instead of collapsing into an indistinguishable null, so the admin
 * Map Report can show WHY coordinates are missing (denied vs timeout vs
 * unsupported) and the fix-capture-vs-pivot-map decision can be made on data.
 *
 * A permissive result (instead of throwing) is deliberate: a healthcare
 * worker who declines GPS once should still be able to submit.
 */

const TIMEOUT_MS = 5_000;

export interface GeoCoords {
  lat: number;
  lng: number;
}

/** Capture outcome — mirrors the server's whitelist (handlers.ts). */
export type GpsStatus = 'granted' | 'denied' | 'timeout' | 'unavailable' | 'unsupported';

export interface GeoResult {
  coords: GeoCoords | null;
  status: GpsStatus;
}

export async function getGeolocation(): Promise<GeoResult> {
  const geo = typeof navigator !== 'undefined' ? navigator.geolocation : undefined;
  if (!geo) return { coords: null, status: 'unsupported' };

  return new Promise<GeoResult>((resolve) => {
    let settled = false;
    const settle = (value: GeoResult) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };

    geo.getCurrentPosition(
      (pos) =>
        settle({
          coords: { lat: pos.coords.latitude, lng: pos.coords.longitude },
          status: 'granted',
        }),
      (err) =>
        settle({
          coords: null,
          status: err.code === 1 ? 'denied' : err.code === 3 ? 'timeout' : 'unavailable',
        }),
      { enableHighAccuracy: false, timeout: TIMEOUT_MS, maximumAge: 0 },
    );
  });
}
