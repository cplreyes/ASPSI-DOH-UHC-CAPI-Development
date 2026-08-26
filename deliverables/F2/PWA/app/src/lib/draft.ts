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
// r7 (2026-07-14): enrollment `qn` + submit-time `gps_status` join the payload.
// r8 (2026-08-05, #1003/#1004): Section K questionnaire-feedback items
// FB1–FB5 + optional consent-page raffle_phone (#1002) join the values
// payload — post-r8 submissions carry them, earlier ones don't.
// m1 (2026-08-19, aug17 migration Task 3.1): F2 spec rewritten to the Aug-17
// instrument — full Q1–Q124 renumber (Q108 gap retired), Section-B
// attribution battery split into new Q13.1–Q24.2 sub-items, Section J ids
// from the old Q109 onward shift down by one. Pre-m1 drafts/submissions use
// the old ids; do not silently merge them against post-m1 data.
// m2 (2026-08-20, UAT R7 fix batch): the Section-B attribution sub-items are
// re-keyed from the paper's dotted numbers to underscores (Q13.1 -> Q13_1 …
// Q24.2 -> Q24_2) — see #1291. Under m1 those probes never stored a usable
// value at all: react-hook-form read the dot as a nested path, so answering one
// overwrote its PARENT stem instead (Q13 became an array). So there is no m1
// sub-item data to preserve, and any m1 draft holding a corrupted parent should
// be treated as suspect rather than merged. Also in m2: #1292 option ORDER now
// follows the paper's column-major reading on 15 questions (values unchanged —
// F2 stores option label text, not positional codes, so this is display-only),
// and #1293 narrows Q89's gate to Q88=Yes.
// Backend `min_accepted_spec_version` is deliberately NOT raised here — see the
// note above; that only moves once the offline queue has drained.
// m3 (2026-08-25, UAT R7 #1312 + #1313): Q24.2's 3-entry placeholder option
// list replaced with DOH's printed 10 options (schema enum widened; the one
// surviving label is renamed and migrated by RENAMED_VALUES below, 'Dashboards'
// has no successor and is flagged by the schema for re-pick). Consent Part I
// text synced to the Aug-17 paper (#1313) — text only, no payload change.
// No m2 submission carries Q24_2 in the field, so nothing to migrate server-side.
// m4 (2026-08-26, ASPSI revised Deliverable 2 Aug-21): the seven dialect maps under
// spec/translations re-imported from the Aug-21 translated questionnaires (Aug-21 wins
// over the June-5/Aug-17 values except the tracked aug21-overrides.json entries) via
// scripts/apply-paper-translations.py — text only, no payload/schema change; option
// values stay English. English source unchanged (Aug-24 English == build), so items.ts
// differs in dialect strings ONLY: no ids, no enums, no schema change. Nothing to
// migrate; the stamp moves so a submission records which translation set the HCW saw.
export const LOCAL_SPEC_VERSION = '2026-08-26-m4';

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
// aug17 migration (R12, Task 3.2, 2026-08-19): the same two Q5 roles were
// reworded again, to the Aug-17 paper's verbatim wording (skip-logic.ts's
// SECTION_CDE_ROLES/SECTION_E_ROLES/ROLES_WITH_SPECIALTY). Chained onto the
// R6 targets below so a draft saved any time since R6 still resolves to the
// current canonical value in one pass.
const RENAMED_VALUES: Record<string, Record<string, string>> = {
  Q2: { Project: 'Project-based' },
  Q5: {
    'Nutrition action officer/ coordinator':
      'Nutrition action officer/coordinator/Nutritionist-Dietician',
    'Pharmacist/Dispenser': 'Pharmacist/Dispenser/Assistant Pharmacist',
    // R6 → aug17 chain targets (R12 reworded these again; see comment above).
    'Nutrition-Dietician or Nutrition Action Officer/Coordinator':
      'Nutrition action officer/coordinator/Nutritionist-Dietician',
    'Pharmacist/Dispenser or Assistant Pharmacist': 'Pharmacist/Dispenser/Assistant Pharmacist',
  },
  // #1312 (2026-08-25): Q24.2's 3-entry placeholder list replaced with DOH's
  // 10 options. The one survivor is renamed; 'Dashboards' has no successor and
  // is left for the schema to flag (the respondent re-picks). Multi values are
  // arrays — mapped element-wise below.
  Q24_2: { 'Client satisfaction survey': 'Patient or Client satisfaction survey' },
};

export async function loadDraft(id: string): Promise<DraftRow | undefined> {
  const row = await db.drafts.get(id);
  if (!row) return row;
  for (const [field, map] of Object.entries(RENAMED_VALUES)) {
    const v = row.values[field];
    if (typeof v === 'string' && map[v] !== undefined) row.values[field] = map[v];
    else if (Array.isArray(v)) row.values[field] = v.map((x) => (typeof x === 'string' && map[x] !== undefined ? map[x] : x));
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
