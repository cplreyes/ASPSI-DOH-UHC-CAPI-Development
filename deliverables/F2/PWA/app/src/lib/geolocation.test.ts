/**
 * F2 PWA — geolocation helper tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.5)
 *
 * Cases per the plan: missing browser API → null; success → {lat,lng};
 * user deny → null; timeout → null. Plus a sanity check that a 5s timeout
 * passes through to the browser API (we don't burn 5 real seconds in the
 * test — we just confirm the option is wired correctly).
 */
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { getGeolocation } from './geolocation';

describe('getGeolocation', () => {
  const originalDescriptor = Object.getOwnPropertyDescriptor(globalThis.navigator, 'geolocation');

  function setGeolocation(value: unknown): void {
    Object.defineProperty(globalThis.navigator, 'geolocation', {
      value,
      configurable: true,
    });
  }

  beforeEach(() => {
    vi.useRealTimers();
  });

  afterEach(() => {
    if (originalDescriptor) {
      Object.defineProperty(globalThis.navigator, 'geolocation', originalDescriptor);
    } else {
      // jsdom lacks geolocation natively — leave it unset.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (globalThis.navigator as any).geolocation;
    }
  });

  it('returns null when navigator.geolocation is undefined', async () => {
    setGeolocation(undefined);
    expect(await getGeolocation()).toBeNull();
  });

  it('returns {lat, lng} on a successful position fix', async () => {
    setGeolocation({
      getCurrentPosition: (success: PositionCallback) => {
        success({
          coords: {
            latitude: 14.5995,
            longitude: 120.9842,
            accuracy: 25,
            altitude: null,
            altitudeAccuracy: null,
            heading: null,
            speed: null,
          },
          timestamp: Date.now(),
        } as GeolocationPosition);
      },
    });
    const result = await getGeolocation();
    expect(result).toEqual({ lat: 14.5995, lng: 120.9842 });
  });

  it('returns null when the user denies permission (PERMISSION_DENIED)', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 1, message: 'User denied geolocation', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toBeNull();
  });

  it('returns null on timeout (TIMEOUT)', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 3, message: 'Timeout', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toBeNull();
  });

  it('returns null on POSITION_UNAVAILABLE', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 2, message: 'Unavailable', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toBeNull();
  });

  it('passes a 5000ms timeout to the browser API', async () => {
    let capturedOptions: PositionOptions | undefined;
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, _error: PositionErrorCallback, options?: PositionOptions) => {
        capturedOptions = options;
        _error({ code: 3, message: 'Timeout', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    await getGeolocation();
    expect(capturedOptions?.timeout).toBe(5000);
  });

  it('resolves only once even if the browser fires success and error sequentially', async () => {
    let secondInvocation = false;
    setGeolocation({
      getCurrentPosition: (success: PositionCallback, error: PositionErrorCallback) => {
        success({
          coords: { latitude: 1, longitude: 2, accuracy: 10, altitude: null, altitudeAccuracy: null, heading: null, speed: null },
          timestamp: Date.now(),
        } as GeolocationPosition);
        // Buggy browsers might also fire error; the helper must ignore it.
        try {
          error({ code: 3, message: 'Timeout', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
          secondInvocation = true;
        } catch { /* ignore */ }
      },
    });
    const result = await getGeolocation();
    expect(result).toEqual({ lat: 1, lng: 2 });
    expect(secondInvocation).toBe(true); // confirms test setup actually fired both callbacks
  });
});
