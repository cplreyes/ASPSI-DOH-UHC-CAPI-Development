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
  proxyUrl: string;
  deviceToken: string;
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
  const url = `${deps.proxyUrl}/exec?action=batch-submit`;

  let response: Response;
  try {
    response = await deps.fetchImpl(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
        Authorization: `Bearer ${deps.deviceToken}`,
      },
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
    let workerErr: { code?: string; message?: string } | undefined;
    try {
      const errBody = (await response.json()) as { error?: { code?: string; message?: string } };
      workerErr = errBody.error;
    } catch {
      /* fall through */
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
