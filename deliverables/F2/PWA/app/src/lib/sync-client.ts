export interface BatchSubmitItem {
  client_submission_id: string;
  hcw_id: string;
  facility_id: string;
  spec_version: string;
  app_version: string;
  submitted_at_client: number;
  device_fingerprint: string;
  values: Record<string, unknown>;
}

export interface BatchSubmitResultItem {
  client_submission_id: string | null;
  submission_id?: string;
  status: 'accepted' | 'duplicate' | 'rejected';
  error?: { code: string; message: string };
}

export interface SyncClientDeps {
  backendUrl: string;
  hmacSecret: string;
  hmacSign: (secret: string, message: string) => Promise<string>;
  nowMs: () => number;
  fetchImpl: typeof fetch;
}

export type BatchSubmitResponse =
  | { ok: true; results: BatchSubmitResultItem[] }
  | { ok: false; transport: boolean; error: { code: string; message: string } };

export async function postBatchSubmit(
  items: BatchSubmitItem[],
  deps: SyncClientDeps,
): Promise<BatchSubmitResponse> {
  const body = JSON.stringify({ responses: items });
  const ts = deps.nowMs();
  const canonical = `POST|batch-submit|${ts}|${body}`;
  const sig = await deps.hmacSign(deps.hmacSecret, canonical);
  const params = new URLSearchParams({ action: 'batch-submit', ts: String(ts), sig });
  const url = `${deps.backendUrl}?${params.toString()}`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });
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
    | { ok: true; data: { results: BatchSubmitResultItem[] } }
    | { ok: false; error: { code: string; message: string } };

  if (env && env.ok === true) {
    return { ok: true, results: env.data.results };
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
