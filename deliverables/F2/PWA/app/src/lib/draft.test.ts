import { describe, it, expect, beforeEach } from 'vitest';
import {
  getOrCreateDraftId,
  loadDraft,
  saveDraft,
  submitDraft,
  type EnrollmentInfo,
} from './draft';
import { db } from './db';

const ENROLLMENT: EnrollmentInfo = {
  hcw_id: 'HCW-1',
  facility_id: 'F-001',
  facility_type: 'Hospital',
};

describe('getOrCreateDraftId', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('generates and persists a new UUID when localStorage is empty', () => {
    const id = getOrCreateDraftId();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i);
    expect(localStorage.getItem('f2_current_draft_id')).toBe(id);
  });

  it('returns the existing id when localStorage already has one', () => {
    localStorage.setItem('f2_current_draft_id', 'existing-id');
    expect(getOrCreateDraftId()).toBe('existing-id');
  });
});

describe('saveDraft + loadDraft', () => {
  beforeEach(async () => {
    localStorage.clear();
    if (!db.isOpen()) await db.open();
  });

  it('returns undefined for an unknown id', async () => {
    expect(await loadDraft('nope')).toBeUndefined();
  });

  it('round-trips values', async () => {
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 }, ENROLLMENT);
    const row = await loadDraft('draft-1');
    expect(row?.values).toEqual({ Q3: 'Female', Q4: 25 });
    expect(row?.hcw_id).toBe('HCW-1');
    expect(typeof row?.updated_at).toBe('number');
  });

  it('overwrites on repeated saves and updates updated_at', async () => {
    await saveDraft('draft-1', { Q3: 'Male' }, ENROLLMENT);
    const first = await loadDraft('draft-1');
    await new Promise((r) => setTimeout(r, 5));
    await saveDraft('draft-1', { Q3: 'Male', Q4: 30 }, ENROLLMENT);
    const second = await loadDraft('draft-1');
    expect(second?.values).toEqual({ Q3: 'Male', Q4: 30 });
    expect(second!.updated_at).toBeGreaterThanOrEqual(first!.updated_at);
  });
});

describe('submitDraft', () => {
  beforeEach(async () => {
    localStorage.clear();
    if (!db.isOpen()) await db.open();
  });

  it('creates a submission row and deletes the draft', async () => {
    localStorage.setItem('f2_current_draft_id', 'draft-1');
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 }, ENROLLMENT);

    const submission = await submitDraft('draft-1', ENROLLMENT);

    expect(submission.status).toBe('pending_sync');
    expect(submission.synced_at).toBeNull();
    expect(submission.hcw_id).toBe('HCW-1');
    expect(submission.values).toMatchObject({
      Q3: 'Female',
      Q4: 25,
      facility_id: 'F-001',
      facility_type: 'Hospital',
    });
    expect(submission.client_submission_id).toBe('draft-1');
    expect(submission.spec_version).toBe('2026-04-17-m1');

    expect(await loadDraft('draft-1')).toBeUndefined();
    expect(localStorage.getItem('f2_current_draft_id')).toBeNull();

    const stored = await db.submissions.get(submission.client_submission_id);
    expect(stored).toEqual(submission);
  });

  it('throws if the draft does not exist', async () => {
    await expect(submitDraft('nope', ENROLLMENT)).rejects.toThrow(/not found/i);
  });

  it('records null submission_lat/submission_lng when no coords are provided', async () => {
    await saveDraft('draft-2', { Q3: 'Female' }, ENROLLMENT);
    const submission = await submitDraft('draft-2', ENROLLMENT);
    expect(submission.values.submission_lat).toBeNull();
    expect(submission.values.submission_lng).toBeNull();
  });

  it('records submission_lat/submission_lng when coords are provided', async () => {
    await saveDraft('draft-3', { Q3: 'Female' }, ENROLLMENT);
    const submission = await submitDraft('draft-3', ENROLLMENT, { lat: 14.5995, lng: 120.9842 });
    expect(submission.values.submission_lat).toBe(14.5995);
    expect(submission.values.submission_lng).toBe(120.9842);
  });

  it('records null when coords are explicitly null (geolocation declined)', async () => {
    await saveDraft('draft-4', { Q3: 'Male' }, ENROLLMENT);
    const submission = await submitDraft('draft-4', ENROLLMENT, null);
    expect(submission.values.submission_lat).toBeNull();
    expect(submission.values.submission_lng).toBeNull();
  });

  // R2-#122: client_submission_id must derive from the draft id, not a fresh
  // random UUID per call. Otherwise rapid double-tap on Submit (within the
  // 5s getGeolocation window in App.tsx handleSubmit) generates two
  // submissions with different client_submission_ids — server-side
  // findExisting can't dedup, two F2_Responses rows recorded.
  // Anchoring to draft id makes IDB submissions.put() upsert on primary
  // key (only one local row per draft) and keeps server-side findExisting
  // useful as a second line of defense.
  it('uses the draft id as the client_submission_id (idempotency anchor)', async () => {
    await saveDraft('draft-idem', { Q3: 'Female' }, ENROLLMENT);
    const submission = await submitDraft('draft-idem', ENROLLMENT);
    expect(submission.client_submission_id).toBe('draft-idem');
  });
});
