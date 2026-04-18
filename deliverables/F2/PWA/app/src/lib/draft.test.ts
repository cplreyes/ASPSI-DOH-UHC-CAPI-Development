import { describe, it, expect, beforeEach } from 'vitest';
import {
  getOrCreateDraftId,
  loadDraft,
  saveDraft,
  submitDraft,
} from './draft';
import { db } from './db';

describe('getOrCreateDraftId', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('generates and persists a new UUID when localStorage is empty', () => {
    const id = getOrCreateDraftId();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
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
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 });
    const row = await loadDraft('draft-1');
    expect(row?.values).toEqual({ Q3: 'Female', Q4: 25 });
    expect(row?.hcw_id).toBe('anonymous');
    expect(typeof row?.updated_at).toBe('number');
  });

  it('overwrites on repeated saves and updates updated_at', async () => {
    await saveDraft('draft-1', { Q3: 'Male' });
    const first = await loadDraft('draft-1');
    await new Promise((r) => setTimeout(r, 5));
    await saveDraft('draft-1', { Q3: 'Male', Q4: 30 });
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
    await saveDraft('draft-1', { Q3: 'Female', Q4: 25 });

    const submission = await submitDraft('draft-1');

    expect(submission.status).toBe('pending_sync');
    expect(submission.synced_at).toBeNull();
    expect(submission.values).toEqual({ Q3: 'Female', Q4: 25 });
    expect(submission.client_submission_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
    expect(submission.spec_version).toBe('2026-04-17-m1');

    expect(await loadDraft('draft-1')).toBeUndefined();
    expect(localStorage.getItem('f2_current_draft_id')).toBeNull();

    const stored = await db.submissions.get(submission.client_submission_id);
    expect(stored).toEqual(submission);
  });

  it('throws if the draft does not exist', async () => {
    await expect(submitDraft('nope')).rejects.toThrow(/not found/i);
  });
});
