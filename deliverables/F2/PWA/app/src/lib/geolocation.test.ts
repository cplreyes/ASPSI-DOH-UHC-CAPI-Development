/**
 * F2 PWA — geolocation helper tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 2.5)
 * P1-4 instrumentation (2026-07-17): every outcome is NAMED — the result is
 * { coords, status } so the admin Map Report can explain missing GPS.
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

  it('reports unsupported when navigator.geolocation is undefined', async () => {
    setGeolocation(undefined);
    expect(await getGeolocation()).toEqual({ coords: null, status: 'unsupported' });
  });

  it('returns coords + granted on a successful position fix', async () => {
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
    expect(await getGeolocation()).toEqual({
      coords: { lat: 14.5995, lng: 120.9842 },
      status: 'granted',
    });
  });

  it('names a permission denial (PERMISSION_DENIED → denied)', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 1, message: 'User denied geolocation', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toEqual({ coords: null, status: 'denied' });
  });

  it('names a timeout (TIMEOUT → timeout)', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 3, message: 'Timeout', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toEqual({ coords: null, status: 'timeout' });
  });

  it('names POSITION_UNAVAILABLE → unavailable', async () => {
    setGeolocation({
      getCurrentPosition: (_success: PositionCallback, error: PositionErrorCallback) => {
        error({ code: 2, message: 'Unavailable', PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError);
      },
    });
    expect(await getGeolocation()).toEqual({ coords: null, status: 'unavailable' });
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
    expect(result).toEqual({ coords: { lat: 1, lng: 2 }, status: 'granted' });
    expect(secondInvocation).toBe(true); // confirms test setup actually fired both callbacks
  });
});
