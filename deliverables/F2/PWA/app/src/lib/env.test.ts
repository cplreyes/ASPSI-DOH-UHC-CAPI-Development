import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('getSyncEnv', () => {
  const originalEnv = { ...import.meta.env };

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    Object.assign(import.meta.env, originalEnv);
  });

  it('returns the proxyUrl when VITE_F2_PROXY_URL is set', async () => {
    import.meta.env.VITE_F2_PROXY_URL = 'https://worker.example.workers.dev';
    const { getSyncEnv } = await import('./env');
    expect(getSyncEnv()).toEqual({ proxyUrl: 'https://worker.example.workers.dev' });
  });

  it('throws with a clear message when VITE_F2_PROXY_URL is missing', async () => {
    import.meta.env.VITE_F2_PROXY_URL = '';
    const { getSyncEnv } = await import('./env');
    expect(() => getSyncEnv()).toThrow(/VITE_F2_PROXY_URL/);
  });
});
