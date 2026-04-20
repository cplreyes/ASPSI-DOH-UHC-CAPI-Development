export interface ConfigValue {
  current_spec_version: string;
  min_accepted_spec_version: string;
  kill_switch: boolean;
  broadcast_message: string;
  spec_hash: string;
}

export interface GetConfigDeps {
  backendUrl: string;
  hmacSecret: string;
  hmacSign: (secret: string, message: string) => Promise<string>;
  nowMs: () => number;
  fetchImpl: typeof fetch;
}

export type GetConfigResponse =
  | { ok: true; config: ConfigValue }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function getConfig(deps: GetConfigDeps): Promise<GetConfigResponse> {
  const ts = deps.nowMs();
  const canonical = `GET|config|${ts}|`;
  const sig = await deps.hmacSign(deps.hmacSecret, canonical);
  const params = new URLSearchParams({ action: 'config', ts: String(ts), sig });
  const url = `${deps.backendUrl}?${params.toString()}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, { method: 'GET' });
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' },
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_HTTP_' + response.status, message: `HTTP ${response.status}` },
    };
  }

  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_PARSE', message: 'Invalid JSON from backend' },
    };
  }

  const env = parsed as
    | { ok: true; data: ConfigValue }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, config: env.data };
  }
  return {
    ok: false,
    transport: false,
    error:
      env && 'error' in env
        ? env.error
        : { code: 'E_UNKNOWN', message: 'Malformed backend envelope' },
  };
}
