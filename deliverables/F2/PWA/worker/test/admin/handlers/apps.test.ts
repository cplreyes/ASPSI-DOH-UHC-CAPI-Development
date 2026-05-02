/**
 * F2 Admin Portal - Files dashboard handler tests.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 3.2)
 */
import { describe, expect, it } from 'vitest';
import {
  ALLOWED_MIME,
  MAX_FILE_BYTES,
  handleListFiles,
  handleUploadFile,
  handleDownloadFile,
  handleDeleteFile,
  type FileMetaRow,
  type FilesR2,
  type FilesListAsCallable,
  type FilesCreateAsCallable,
  type FilesGetAsCallable,
  type FilesDeleteAsCallable,
  type ListFilesData,
} from '../../../src/admin/handlers/apps';

const ACTOR = { username: 'admin-alice' };

function asListOk(data: ListFilesData): ReturnType<FilesListAsCallable> {
  return Promise.resolve({ ok: true, data });
}

function asListErr(code: string): ReturnType<FilesListAsCallable> {
  return Promise.resolve({ ok: false, error: { code, message: code } });
}

function asCreateOk(file: FileMetaRow): ReturnType<FilesCreateAsCallable> {
  return Promise.resolve({ ok: true, data: { file } });
}

function asCreateErr(code: string): ReturnType<FilesCreateAsCallable> {
  return Promise.resolve({ ok: false, error: { code, message: code } });
}

function asGetOk(file: FileMetaRow): ReturnType<FilesGetAsCallable> {
  return Promise.resolve({ ok: true, data: { file } });
}

function asGetErr(code: string): ReturnType<FilesGetAsCallable> {
  return Promise.resolve({ ok: false, error: { code, message: code } });
}

function asDeleteOk(file_id: string): ReturnType<FilesDeleteAsCallable> {
  return Promise.resolve({ ok: true, data: { file_id, deleted_at: '2026-05-02T00:00:00.000Z' } });
}

function asDeleteErr(code: string): ReturnType<FilesDeleteAsCallable> {
  return Promise.resolve({ ok: false, error: { code, message: code } });
}

interface FakeR2Calls {
  put: Array<{ key: string; httpMetadata?: { contentType?: string; contentDisposition?: string } }>;
  get: string[];
  delete: string[];
}

function makeR2(opts: {
  getResult?: Awaited<ReturnType<FilesR2['get']>>;
  putThrows?: boolean;
  deleteThrows?: boolean;
}): { r2: FilesR2; calls: FakeR2Calls } {
  const calls: FakeR2Calls = { put: [], get: [], delete: [] };
  const r2: FilesR2 = {
    async put(key, _value, options) {
      calls.put.push({ key, ...(options?.httpMetadata ? { httpMetadata: options.httpMetadata } : {}) });
      if (opts.putThrows) throw new Error('R2 put failed');
    },
    async get(key) {
      calls.get.push(key);
      return opts.getResult ?? null;
    },
    async delete(key) {
      calls.delete.push(key);
      if (opts.deleteThrows) throw new Error('R2 delete failed');
    },
  };
  return { r2, calls };
}

const SAMPLE_META: FileMetaRow = {
  file_id: 'f-001',
  filename: 'protocol-v1.pdf',
  content_type: 'application/pdf',
  size_bytes: 1024,
  uploaded_by: 'admin-alice',
  uploaded_at: '2026-05-01T12:00:00.000Z',
  description: '',
};

// Build a Request with a multipart body containing a single 'file' field.
function multipartReq(opts: {
  filename: string;
  type: string;
  bytes: Uint8Array;
  description?: string;
  contentTypeHeader?: string;
}): Request {
  const form = new FormData();
  const blob = new Blob([opts.bytes], { type: opts.type });
  // Attach a name property; in Workers FormData accepts (Blob, filename) too.
  form.append('file', blob, opts.filename);
  if (opts.description !== undefined) form.append('description', opts.description);
  return new Request('http://test/upload', {
    method: 'POST',
    body: form,
    ...(opts.contentTypeHeader ? { headers: { 'content-type': opts.contentTypeHeader } } : {}),
  });
}

// -------------------- handleListFiles --------------------

describe('handleListFiles', () => {
  it('returns files JSON on AS success', async () => {
    const url = new URL('http://x/admin/api/dashboards/apps/files');
    const r = await handleListFiles(url, () => asListOk({ files: [SAMPLE_META], total: 1 }));
    expect(r.status).toBe(200);
    const body = (await r.json()) as ListFilesData;
    expect(body.total).toBe(1);
    expect(body.files[0]?.file_id).toBe('f-001');
  });

  it('forwards q filter to AS', async () => {
    let captured: { q?: string } | undefined;
    const url = new URL('http://x/admin/api/dashboards/apps/files?q=protocol');
    await handleListFiles(url, (filters) => {
      captured = filters;
      return asListOk({ files: [], total: 0 });
    });
    expect(captured?.q).toBe('protocol');
  });

  it('returns 502 E_BACKEND on AS failure', async () => {
    const url = new URL('http://x/admin/api/dashboards/apps/files');
    const r = await handleListFiles(url, () => asListErr('E_BACKEND'));
    expect(r.status).toBe(502);
  });
});

// -------------------- handleUploadFile --------------------

describe('handleUploadFile', () => {
  it('rejects non-multipart with 400 E_VALIDATION', async () => {
    const req = new Request('http://test/upload', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: '{}',
    });
    const { r2 } = makeR2({});
    const r = await handleUploadFile(req, ACTOR, r2, () => asCreateOk(SAMPLE_META));
    expect(r.status).toBe(400);
    const body = (await r.json()) as { error: { code: string } };
    expect(body.error.code).toBe('E_VALIDATION');
  });

  it('rejects empty actor username with 500 E_INTERNAL', async () => {
    const req = multipartReq({ filename: 'a.pdf', type: 'application/pdf', bytes: new Uint8Array([1]) });
    const { r2 } = makeR2({});
    const r = await handleUploadFile(req, { username: '' }, r2, () => asCreateOk(SAMPLE_META));
    expect(r.status).toBe(500);
  });

  it('rejects oversize file with 413', async () => {
    // Allocate a real >cap-sized buffer so it survives multipart round-trip.
    // 100MB+1 — slow but reliable; Object.defineProperty on Blob.size doesn't
    // propagate through Request.formData() which reconstructs from raw bytes.
    const bytes = new Uint8Array(MAX_FILE_BYTES + 1);
    const req = multipartReq({ filename: 'big.pdf', type: 'application/pdf', bytes });
    const { r2 } = makeR2({});
    const r = await handleUploadFile(req, ACTOR, r2, () => asCreateOk(SAMPLE_META));
    expect(r.status).toBe(413);
  });

  it.each([
    ['image/svg+xml'],
    ['text/html'],
    ['application/javascript'],
  ])('rejects disallowed MIME %s with 400', async (mime) => {
    const req = multipartReq({ filename: 'evil.svg', type: mime, bytes: new Uint8Array([1, 2, 3]) });
    const { r2 } = makeR2({});
    const r = await handleUploadFile(req, ACTOR, r2, () => asCreateOk(SAMPLE_META));
    expect(r.status).toBe(400);
    const body = (await r.json()) as { error: { code: string; message: string } };
    expect(body.error.code).toBe('E_VALIDATION');
    expect(body.error.message).toContain(mime);
  });

  it.each(Array.from(ALLOWED_MIME).map((m) => [m] as const))(
    'accepts allowed MIME %s and writes to R2 + AS',
    async (mime) => {
      const req = multipartReq({ filename: 'doc.bin', type: mime, bytes: new Uint8Array([1, 2, 3, 4]) });
      const { r2, calls } = makeR2({});
      let asPayload: Record<string, unknown> | undefined;
      const r = await handleUploadFile(req, ACTOR, r2, (payload) => {
        asPayload = payload;
        return asCreateOk({
          ...SAMPLE_META,
          file_id: String(payload.file_id),
          content_type: mime,
          size_bytes: 4,
          filename: String(payload.filename),
        });
      });
      expect(r.status).toBe(201);
      // R2 received exactly one put with the correct key prefix.
      expect(calls.put).toHaveLength(1);
      expect(calls.put[0]?.key).toMatch(/^files\/[0-9a-f-]+$/);
      // AS received the matching metadata.
      expect(asPayload?.uploaded_by).toBe('admin-alice');
      expect(asPayload?.content_type).toBe(mime);
      expect(asPayload?.size_bytes).toBe(4);
    },
  );

  it('purges R2 if AS create fails (orphan cleanup)', async () => {
    const req = multipartReq({ filename: 'doc.pdf', type: 'application/pdf', bytes: new Uint8Array([1]) });
    const { r2, calls } = makeR2({});
    const r = await handleUploadFile(req, ACTOR, r2, () => asCreateErr('E_LOCK_TIMEOUT'));
    expect(r.status).toBe(503);
    // One put followed by one delete on the same key.
    expect(calls.put).toHaveLength(1);
    expect(calls.delete).toHaveLength(1);
    expect(calls.delete[0]).toBe(calls.put[0]?.key);
  });

  it('still returns the AS error if R2 cleanup throws', async () => {
    const req = multipartReq({ filename: 'doc.pdf', type: 'application/pdf', bytes: new Uint8Array([1]) });
    const { r2 } = makeR2({ deleteThrows: true });
    const r = await handleUploadFile(req, ACTOR, r2, () => asCreateErr('E_BACKEND'));
    expect(r.status).toBe(502);
  });

  it('sanitizes filenames before storing them', async () => {
    const req = multipartReq({
      filename: 'naughty"name.pdf',
      type: 'application/pdf',
      bytes: new Uint8Array([1]),
    });
    const { r2, calls } = makeR2({});
    let asPayload: Record<string, unknown> | undefined;
    await handleUploadFile(req, ACTOR, r2, (payload) => {
      asPayload = payload;
      return asCreateOk({ ...SAMPLE_META, filename: String(payload.filename) });
    });
    // No double quote in the stored filename or in the Content-Disposition.
    expect(String(asPayload?.filename)).not.toContain('"');
    expect(calls.put[0]?.httpMetadata?.contentDisposition).not.toMatch(/[^a-z]"[^a-z]/);
  });
});

// -------------------- handleDownloadFile --------------------

describe('handleDownloadFile', () => {
  it('rejects empty file_id with 400', async () => {
    const { r2 } = makeR2({});
    const r = await handleDownloadFile('', r2, () => asGetOk(SAMPLE_META));
    expect(r.status).toBe(400);
  });

  it('returns 404 when AS reports the file is soft-deleted', async () => {
    const { r2 } = makeR2({ getResult: { body: new Blob(['x']).stream(), httpMetadata: {} } });
    const deletedMeta = { ...SAMPLE_META, deleted_at: '2026-05-01T00:00:00.000Z' };
    const r = await handleDownloadFile('f-001', r2, () => asGetOk(deletedMeta));
    expect(r.status).toBe(404);
  });

  it('returns 404 when bytes missing in R2 even though metadata exists', async () => {
    const { r2 } = makeR2({ getResult: null });
    const r = await handleDownloadFile('f-001', r2, () => asGetOk(SAMPLE_META));
    expect(r.status).toBe(404);
  });

  it('forwards AS error code (404 E_NOT_FOUND when AS lacks the row)', async () => {
    const { r2 } = makeR2({});
    const r = await handleDownloadFile('f-001', r2, () => asGetErr('E_NOT_FOUND'));
    expect(r.status).toBe(404);
  });

  it('streams bytes with Content-Disposition: attachment', async () => {
    const { r2 } = makeR2({
      getResult: { body: new Blob(['hello']).stream(), httpMetadata: { contentType: 'application/pdf' } },
    });
    const r = await handleDownloadFile('f-001', r2, () => asGetOk(SAMPLE_META));
    expect(r.status).toBe(200);
    expect(r.headers.get('content-type')).toBe('application/pdf');
    expect(r.headers.get('content-disposition')).toContain('attachment');
    expect(r.headers.get('content-disposition')).toContain('protocol-v1.pdf');
  });
});

// -------------------- handleDeleteFile --------------------

describe('handleDeleteFile', () => {
  it('returns 204 on AS soft-delete success and purges R2', async () => {
    const { r2, calls } = makeR2({});
    const r = await handleDeleteFile('f-001', r2, () => asDeleteOk('f-001'));
    expect(r.status).toBe(204);
    expect(calls.delete).toEqual(['files/f-001']);
  });

  it('still returns 204 if R2 purge throws (AS soft-delete is the source of truth)', async () => {
    const { r2 } = makeR2({ deleteThrows: true });
    const r = await handleDeleteFile('f-001', r2, () => asDeleteOk('f-001'));
    expect(r.status).toBe(204);
  });

  it('forwards AS error: 404 E_NOT_FOUND when row missing', async () => {
    const { r2, calls } = makeR2({});
    const r = await handleDeleteFile('f-001', r2, () => asDeleteErr('E_NOT_FOUND'));
    expect(r.status).toBe(404);
    // R2 must NOT be touched when AS rejects the delete.
    expect(calls.delete).toHaveLength(0);
  });

  it('forwards AS error: 503 E_LOCK_TIMEOUT', async () => {
    const { r2 } = makeR2({});
    const r = await handleDeleteFile('f-001', r2, () => asDeleteErr('E_LOCK_TIMEOUT'));
    expect(r.status).toBe(503);
  });
});
