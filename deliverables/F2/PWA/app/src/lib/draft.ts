import { db, type DraftRow, type SubmissionRow } from './db';

export const DRAFT_ID_KEY = 'f2_current_draft_id';
// R2-#120 S.A2: tester refreshed after submit, expected the thank-you
// screen to persist; got redirected to Section A (fresh survey). Tracking
// the most-recent client_submission_id in localStorage lets the App init
// short-circuit to status='submitted' on refresh, until the user
// explicitly starts a new survey.
export const COMPLETED_CSID_KEY = 'f2_completed_csid';
// R6 fix wave 2026-07-02 (#817 Q71a/Q71b split + Section F option additions):
// lexicographically later than '2026-04-17-m1' so post-split submissions are
// demarcated by spec_version. Do NOT raise the backend's
// min_accepted_spec_version until the offline queue drains.
export const LOCAL_SPEC_VERSION = '2026-07-14-r7';

export interface EnrollmentInfo {
  hcw_id: string;
  facility_id: string;
  /** 12-digit Questionnaire Number from the enrollment record; absent pre-qn. */
  qn?: string;
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

// R6 #820/#811: two Q5 role options and Q2 "Project" were RENAMED. Choice
// values derive from the English label, so in-flight drafts hold values that
// are no longer in the regenerated enums — the resumed respondent's answer
// would read as unanswered and role-gated sections would mis-route. Migrate
// on load; harmless once no pre-R6 drafts remain.
const RENAMED_VALUES: Record<string, Record<string, string>> = {
  Q2: { Project: 'Project-based' },
  Q5: {
    'Nutrition action officer/ coordinator':
      'Nutrition-Dietician or Nutrition Action Officer/Coordinator',
    'Pharmacist/Dispenser': 'Pharmacist/Dispenser or Assistant Pharmacist',
  },
};

export async function loadDraft(id: string): Promise<DraftRow | undefined> {
  const row = await db.drafts.get(id);
  if (!row) return row;
  for (const [field, map] of Object.entries(RENAMED_VALUES)) {
    const v = row.values[field];
    if (typeof v === 'string' && map[v] !== undefined) row.values[field] = map[v];
  }
  return row;
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

/** GPS capture outcome recorded alongside the coords (audit P1-4). 'not_requested'
 *  covers paths that never ask — consent refusals (#825). */
export type SubmitGpsStatus =
  | 'granted'
  | 'denied'
  | 'timeout'
  | 'unavailable'
  | 'unsupported'
  | 'not_requested';

export async function submitDraft(
  id: string,
  enrollment: EnrollmentInfo,
  coords: SubmitCoords | null = null,
  gpsStatus: SubmitGpsStatus = 'not_requested',
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
      gps_status: gpsStatus,
    };

    const submission: SubmissionRow = {
      // Anchor on the draft id, not a fresh UUID. R2-#122: the App.tsx
      // submit handler has no isSubmitting guard and getGeolocation
      // can take 5s, so a rapid double-tap can drive submitDraft twice
      // before the first transaction commits. Random UUIDs gave the two
      // resulting submissions different client_submission_ids — server's
      // findExisting couldn't dedup, two F2_Responses rows got recorded.
      // Anchoring on draft id makes IDB submissions.put() upsert on
      // primary key (one local row per draft) and keeps the server-side
      // findExisting useful as belt-and-suspenders.
      client_submission_id: id,
      hcw_id: enrollment.hcw_id,
      ...(enrollment.qn ? { qn: enrollment.qn } : {}),
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
