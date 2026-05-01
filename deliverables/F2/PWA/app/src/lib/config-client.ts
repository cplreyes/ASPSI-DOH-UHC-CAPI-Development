export interface ConfigValue {
  current_spec_version: string;
  min_accepted_spec_version: string;
  kill_switch: boolean;
  broadcast_message: string;
  spec_hash: string;
}

export interface GetConfigDeps {
  /** Cloudflare Worker origin (e.g. https://f2-pwa-worker.example.workers.dev). */
  proxyUrl: string;
  /** Per-tablet device JWT, sent as Authorization: Bearer <token>. */
  deviceToken: string;
  fetchImpl: typeof fetch;
}

export type GetConfigResponse =
  | { ok: true; config: ConfigValue }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function getConfig(deps: GetConfigDeps): Promise<GetConfigResponse> {
  const url = `${deps.proxyUrl}/exec?action=config`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'GET',
      headers: { Authorization: `Bearer ${deps.deviceToken}` },
    });
  } catch (err) {
    return {
      ok: false,
      transport: true,
      error: { code: 'E_NETWORK', message: (err as Error).message || 'Network error' },
    };
  }

  if (!response.ok) {
    // Auth-class errors come from the Worker as JSON; surface their code so the PWA
    // can route to re-enrolment (E_TOKEN_*) or backoff (E_BACKEND_BUSY).
    let workerErr: { code?: string; message?: string } | undefined;
    try {
      const body = (await response.json()) as { error?: { code?: string; message?: string } };
      workerErr = body.error;
    } catch {
      /* fall through to generic */
    }
    return {
      ok: false,
      transport: true,
      error: {
        code: workerErr?.code ?? 'E_HTTP_' + response.status,
        message: workerErr?.message ?? `HTTP ${response.status}`,
      },
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
