/**
 * F2 Admin Portal — paper-encoder page.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.3)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.13)
 *
 * Wraps the existing MultiSectionForm in mode='encoded' so the GPS
 * disclosure is suppressed and the consent text isn't shown. onSubmit
 * POSTs the same form payload to /admin/api/encode/:hcw_id with the
 * admin JWT in Authorization. The Worker stamps source_path and
 * encoded_by; the AS write path is shared with the PWA submit (Task
 * 2.7), so encoded rows land in the same F2_Responses sheet with
 * provenance markers distinguishing them from self-admin.
 *
 * Autosave + draft restore deferred — paper-encoder sessions are
 * usually short-lived in one sitting; if Operators ask for resume,
 * a Sprint 4 follow-up wires Dexie keyed by hcw_id+admin_username.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LocaleProvider } from '@/i18n/locale-context';
import { MultiSectionForm } from '@/components/survey/MultiSectionForm';
import type { FormValues } from '@/lib/skip-logic';
import { LOCAL_SPEC_VERSION } from '@/lib/draft';
import { adminFetch, type ApiError } from '../lib/api-client';
import { useAdminAuth } from '../lib/auth-context';
import { Link, useRouter } from '../lib/pages-router';

export interface EncodePageProps {
  apiBaseUrl: string;
  hcwId: string;
  fetchImpl?: typeof fetch;
}

interface EncodeResponse {
  submission_id: string;
  status: 'accepted' | 'duplicate' | 'rejected';
  server_timestamp: string;
}

export function EncodePage({ apiBaseUrl, hcwId, fetchImpl }: EncodePageProps): JSX.Element {
  const { token, clearAuth } = useAdminAuth();
  const { navigate } = useRouter();
  const [submitState, setSubmitState] = useState<
    | { kind: 'idle' }
    | { kind: 'submitting' }
    | { kind: 'submitted'; submission_id: string }
    | { kind: 'failed'; error: ApiError }
  >({ kind: 'idle' });

  const onSubmit = async (values: FormValues): Promise<void> => {
    setSubmitState({ kind: 'submitting' });
    const payload = {
      client_submission_id: crypto.randomUUID(),
      spec_version: LOCAL_SPEC_VERSION,
      app_version: 'admin-encode',
      submitted_at_client: Date.now(),
      device_fingerprint: 'admin-encoder',
      values,
    };
    const r = await adminFetch<EncodeResponse>(
      `${apiBaseUrl}/admin/api/encode/${encodeURIComponent(hcwId)}`,
      { method: 'POST', body: JSON.stringify(payload) },
      {
        ...(token ? { token } : {}),
        onUnauthorized: () => {
          clearAuth();
          navigate('/admin/login');
        },
        ...(fetchImpl ? { fetchImpl } : {}),
      },
    );
    if (!r.ok) {
      setSubmitState({ kind: 'failed', error: r.error });
      return;
    }
    setSubmitState({ kind: 'submitted', submission_id: r.data.submission_id });
  };

  if (submitState.kind === 'submitted') {
    return <EncodedSuccess submissionId={submitState.submission_id} />;
  }

  return (
    <section className="flex flex-col gap-4">
      <header className="border-b border-hairline pb-4">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Paper Encoder
        </p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">
          Encoding for HCW <span className="font-mono text-base">{hcwId}</span>
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Transcribe the paper survey below. The submission is recorded with your admin username as{' '}
          <code className="font-mono">encoded_by</code> and marked{' '}
          <code className="font-mono">source_path=paper_encoded</code>.
        </p>
      </header>

      {submitState.kind === 'failed' ? (
        <EncodeError error={submitState.error} onDismiss={() => setSubmitState({ kind: 'idle' })} />
      ) : null}

      <LocaleProvider>
        <MultiSectionForm
          initialValues={{}}
          mode="encoded"
          onAutosave={() => undefined}
          onSubmit={onSubmit}
        />
      </LocaleProvider>
    </section>
  );
}

function EncodedSuccess({ submissionId }: { submissionId: string }): JSX.Element {
  return (
    <section className="flex flex-col gap-4 py-8">
      <header className="border-b border-hairline pb-4">
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Recorded</p>
        <h2 className="mt-1 font-serif text-2xl font-medium tracking-tight">
          Encoded successfully
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Submission ID <code className="font-mono">{submissionId}</code>
        </p>
      </header>
      <div className="flex flex-wrap gap-3 pt-2">
        <Link
          to="/admin/encode"
          className="inline-flex h-11 items-center justify-center rounded-md border border-hairline px-4 text-sm hover:bg-secondary"
        >
          Back to encode queue
        </Link>
      </div>
    </section>
  );
}

function EncodeError({
  error,
  onDismiss,
}: {
  error: ApiError;
  onDismiss: () => void;
}): JSX.Element {
  const { t } = useTranslation();
  return (
    <div role="alert" className="border-l-2 border-error bg-secondary/30 px-3 py-2">
      <p className="text-sm text-error">
        {error.code === 'E_PERM_DENIED'
          ? 'Your role lacks dict_paper_encoded_up. Contact an Administrator.'
          : error.code === 'E_BACKEND'
            ? 'The Apps Script backend rejected the submission. Check that the staging deployment is live.'
            : error.code === 'E_NETWORK'
              ? 'Network unavailable. Submission was not recorded; retry when reconnected.'
              : (error.message ?? t('chrome.submitFailedBody'))}
      </p>
      {error.requestId ? (
        <p className="mt-1 font-mono text-xs text-muted-foreground">ref {error.requestId}</p>
      ) : null}
      <button
        type="button"
        onClick={onDismiss}
        className="mt-2 font-mono text-xs uppercase tracking-wider text-muted-foreground hover:text-ink"
      >
        Dismiss
      </button>
    </div>
  );
}
