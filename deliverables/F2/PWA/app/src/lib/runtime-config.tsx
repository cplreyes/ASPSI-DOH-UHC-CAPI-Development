import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import type { ConfigValue, GetConfigResponse } from './config-client';

export const RUNTIME_CONFIG_CACHE_KEY = 'f2_runtime_config_v1';

export const DEFAULT_CONFIG: ConfigValue = {
  current_spec_version: '',
  min_accepted_spec_version: '',
  kill_switch: false,
  broadcast_message: '',
  spec_hash: '',
};

const RuntimeConfigContext = createContext<ConfigValue>(DEFAULT_CONFIG);

function coerceConfig(input: unknown): ConfigValue {
  if (!input || typeof input !== 'object') return DEFAULT_CONFIG;
  const o = input as Record<string, unknown>;
  return {
    current_spec_version:
      typeof o.current_spec_version === 'string'
        ? o.current_spec_version
        : DEFAULT_CONFIG.current_spec_version,
    min_accepted_spec_version:
      typeof o.min_accepted_spec_version === 'string'
        ? o.min_accepted_spec_version
        : DEFAULT_CONFIG.min_accepted_spec_version,
    kill_switch: typeof o.kill_switch === 'boolean' ? o.kill_switch : DEFAULT_CONFIG.kill_switch,
    broadcast_message:
      typeof o.broadcast_message === 'string'
        ? o.broadcast_message
        : DEFAULT_CONFIG.broadcast_message,
    spec_hash: typeof o.spec_hash === 'string' ? o.spec_hash : DEFAULT_CONFIG.spec_hash,
  };
}

function readCache(): ConfigValue | null {
  try {
    const raw = localStorage.getItem(RUNTIME_CONFIG_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') return coerceConfig(parsed);
    return null;
  } catch {
    return null;
  }
}

function writeCache(cfg: ConfigValue) {
  try {
    localStorage.setItem(RUNTIME_CONFIG_CACHE_KEY, JSON.stringify(cfg));
  } catch {
    /* quota exceeded — non-fatal */
  }
}

interface Props {
  fetcher: () => Promise<GetConfigResponse>;
  refreshIntervalMs: number;
  children: ReactNode;
}

export function RuntimeConfigProvider({ fetcher, refreshIntervalMs, children }: Props) {
  const [config, setConfig] = useState<ConfigValue>(() => readCache() ?? DEFAULT_CONFIG);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    let cancelled = false;
    const refresh = async () => {
      let r: GetConfigResponse;
      try {
        r = await fetcherRef.current();
      } catch (err) {
        console.warn('[F2] runtime-config fetch threw:', (err as Error).message);
        return;
      }
      if (cancelled) return;
      if (r.ok) {
        setConfig(r.config);
        writeCache(r.config);
      }
    };
    void refresh();
    const id = window.setInterval(refresh, refreshIntervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [refreshIntervalMs]);

  return <RuntimeConfigContext.Provider value={config}>{children}</RuntimeConfigContext.Provider>;
}

export function useRuntimeConfig(): ConfigValue {
  return useContext(RuntimeConfigContext);
}
