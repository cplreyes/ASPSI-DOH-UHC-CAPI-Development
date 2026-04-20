import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import {
  RuntimeConfigProvider,
  useRuntimeConfig,
  RUNTIME_CONFIG_CACHE_KEY,
} from './runtime-config';

function Probe() {
  const cfg = useRuntimeConfig();
  return <pre data-testid="cfg">{JSON.stringify(cfg)}</pre>;
}

describe('RuntimeConfigProvider', () => {
  it('uses defaults when no cache and fetcher fails', async () => {
    localStorage.removeItem(RUNTIME_CONFIG_CACHE_KEY);
    const fetcher = vi.fn().mockResolvedValue({
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: '' },
    });
    render(
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={60_000}>
        <Probe />
      </RuntimeConfigProvider>,
    );
    await waitFor(() => expect(fetcher).toHaveBeenCalled());
    const cfg = JSON.parse(screen.getByTestId('cfg').textContent || '{}');
    expect(cfg.kill_switch).toBe(false);
    expect(cfg.broadcast_message).toBe('');
  });

  it('hydrates from cache on mount then refreshes', async () => {
    const cached = {
      current_spec_version: '2026-04-17-m1',
      min_accepted_spec_version: '2026-04-17-m1',
      kill_switch: false,
      broadcast_message: 'hi',
      spec_hash: 'x',
    };
    localStorage.setItem(RUNTIME_CONFIG_CACHE_KEY, JSON.stringify(cached));
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      config: { ...cached, broadcast_message: 'fresh' },
    });
    render(
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={60_000}>
        <Probe />
      </RuntimeConfigProvider>,
    );
    await waitFor(() => {
      const cfg = JSON.parse(screen.getByTestId('cfg').textContent || '{}');
      expect(cfg.broadcast_message).toBe('fresh');
    });
  });

  it('writes successful fetch result to cache', async () => {
    localStorage.removeItem(RUNTIME_CONFIG_CACHE_KEY);
    const cfg = {
      current_spec_version: 'v',
      min_accepted_spec_version: 'v',
      kill_switch: true,
      broadcast_message: 'test',
      spec_hash: 'h',
    };
    const fetcher = vi.fn().mockResolvedValue({ ok: true, config: cfg });
    render(
      <RuntimeConfigProvider fetcher={fetcher} refreshIntervalMs={60_000}>
        <Probe />
      </RuntimeConfigProvider>,
    );
    await waitFor(() => {
      const stored = JSON.parse(localStorage.getItem(RUNTIME_CONFIG_CACHE_KEY) || '{}');
      expect(stored.broadcast_message).toBe('test');
    });
  });
});
