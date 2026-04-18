import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('getSyncEnv', () => {
  const originalEnv = { ...import.meta.env };

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    Object.assign(import.meta.env, originalEnv);
  });

  it('returns the URL and secret when both env vars are set', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = 'https://example.com/exec';
    import.meta.env.VITE_F2_HMAC_SECRET = 'deadbeef';
    const { getSyncEnv } = await import('./env');
    expect(getSyncEnv()).toEqual({
      backendUrl: 'https://example.com/exec',
      hmacSecret: 'deadbeef',
    });
  });

  it('throws with a clear message when VITE_F2_BACKEND_URL is missing', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = '';
    import.meta.env.VITE_F2_HMAC_SECRET = 'x';
    const { getSyncEnv } = await import('./env');
    expect(() => getSyncEnv()).toThrow(/VITE_F2_BACKEND_URL/);
  });

  it('throws with a clear message when VITE_F2_HMAC_SECRET is missing', async () => {
    import.meta.env.VITE_F2_BACKEND_URL = 'https://x/exec';
    import.meta.env.VITE_F2_HMAC_SECRET = '';
    const { getSyncEnv } = await import('./env');
    expect(() => getSyncEnv()).toThrow(/VITE_F2_HMAC_SECRET/);
  });
});
