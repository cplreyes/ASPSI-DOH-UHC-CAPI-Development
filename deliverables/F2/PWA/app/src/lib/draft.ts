import { db, type DraftRow, type SubmissionRow } from './db';

export const DRAFT_ID_KEY = 'f2_current_draft_id';
export const LOCAL_SPEC_VERSION = '2026-04-17-m1';

export interface EnrollmentInfo {
  hcw_id: string;
  facility_id: string;
  /**
   * Optional — see EnrollmentRow comment in db.ts. Submissions made before
   * the facilities cache populates carry an empty `facility_type`; backend
   * tolerates this and the value can be backfilled from facility_id at
   * analysis time.
   */
  facility_type?: string;
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

/**
 * GPS coordinates captured at submit time. `null` (or omitted) means the
 * device couldn't acquire a fix — the submission still rides through with
 * `submission_lat`/`submission_lng` set to null. Admin Map Report tolerates
 * null rows; spec §9 — graceful degradation over forced location capture.
 */
export interface SubmitCoords {
  lat: number;
  lng: number;
}

export async function submitDraft(
  id: string,
  enrollment: EnrollmentInfo,
  coords: SubmitCoords | null = null,
): Promise<SubmissionRow> {
  return db.transaction('rw', db.drafts, db.submissions, async () => {
    const draft = await db.drafts.get(id);
    if (!draft) throw new Error(`Draft ${id} not found`);

    const valuesWithFacility = {
      ...draft.values,
      facility_id: enrollment.facility_id,
      facility_type: enrollment.facility_type ?? '',
      submission_lat: coords ? coords.lat : null,
      submission_lng: coords ? coords.lng : null,
    };

    const submission: SubmissionRow = {
      client_submission_id: crypto.randomUUID(),
      hcw_id: enrollment.hcw_id,
      status: 'pending_sync',
      synced_at: null,
      submitted_at: Date.now(),
      spec_version: LOCAL_SPEC_VERSION,
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
