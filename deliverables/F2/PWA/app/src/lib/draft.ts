import { db, type DraftRow, type SubmissionRow } from './db';

const DRAFT_ID_KEY = 'f2_current_draft_id';
const SPEC_VERSION_PLACEHOLDER = '2026-04-17-m1';

export interface EnrollmentInfo {
  hcw_id: string;
  facility_id: string;
  facility_type: string;
}

export function getOrCreateDraftId(): string {
  const existing = localStorage.getItem(DRAFT_ID_KEY);
  if (existing) return existing;
  const fresh = crypto.randomUUID();
  localStorage.setItem(DRAFT_ID_KEY, fresh);
  return fresh;
}

export async function loadDraft(id: string): Promise<DraftRow | undefined> {
  return db.drafts.get(id);
}

export async function saveDraft(
  id: string,
  values: Record<string, unknown>,
  enrollment: EnrollmentInfo,
): Promise<void> {
  const row: DraftRow = {
    id,
    hcw_id: enrollment.hcw_id,
    updated_at: Date.now(),
    values,
  };
  await db.drafts.put(row);
}

export async function submitDraft(
  id: string,
  enrollment: EnrollmentInfo,
): Promise<SubmissionRow> {
  return db.transaction('rw', db.drafts, db.submissions, async () => {
    const draft = await db.drafts.get(id);
    if (!draft) throw new Error(`Draft ${id} not found`);

    const valuesWithFacility = {
      ...draft.values,
      facility_id: enrollment.facility_id,
      facility_type: enrollment.facility_type,
    };

    const submission: SubmissionRow = {
      client_submission_id: crypto.randomUUID(),
      hcw_id: enrollment.hcw_id,
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: SPEC_VERSION_PLACEHOLDER,
      values: valuesWithFacility,
      retry_count: 0,
      next_retry_at: null,
      last_error: null,
    };

    await db.submissions.put(submission);
    await db.drafts.delete(id);
    if (localStorage.getItem(DRAFT_ID_KEY) === id) {
      localStorage.removeItem(DRAFT_ID_KEY);
    }

    return submission;
  });
}
