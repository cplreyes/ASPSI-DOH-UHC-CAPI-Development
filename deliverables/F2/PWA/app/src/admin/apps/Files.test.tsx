/**
 * Regression tests for the Files panel download path.
 *
 * #315 (UAT R3, 5A.7): the filename was a plain `<a href download>`. A bare
 * anchor navigation cannot carry the Authorization header, and the admin JWT
 * lives in memory only — so every download hit the worker unauthenticated,
 * got a 401, and the error JSON ("access denied") was saved as the "file".
 *
 * These tests assert the download now goes through an authenticated fetch
 * (Authorization header present) and resolves the bytes into a blob.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { useEffect } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Files } from './Files';
import { AdminAuthProvider, useAdminAuth } from '../lib/auth-context';
import { RouterProvider } from '../lib/pages-router';

const TOKEN = 'test-token';
const SAMPLE_FILE = {
  file_id: 'f-1',
  filename: 'protocol.pdf',
  content_type: 'application/pdf',
  size_bytes: 2048,
  uploaded_by: 'shan_admin',
  uploaded_at: '2026-05-20T10:00:00Z',
};

/** Mock fetch: records calls, serves the file list, and the download bytes. */
function makeFetch(downloadStatus = 200): {
  fetch: typeof fetch;
  calls: { url: string; init: RequestInit | undefined }[];
} {
  const calls: { url: string; init: RequestInit | undefined }[] = [];
  const impl = (async (url: string | URL, init?: RequestInit) => {
    const u = String(url);
    calls.push({ url: u, init });
    if (/\/apps\/files\/[^/]+$/.test(u)) {
      // Download path (has a file-id segment).
      if (downloadStatus !== 200) {
        return new Response(
          JSON.stringify({ ok: false, error: { code: 'E_AUTH_INVALID', message: 'access denied' } }),
          { status: downloadStatus, headers: { 'Content-Type': 'application/json' } },
        );
      }
      // String body — Response.blob() still resolves to a Blob, and a string
      // body avoids the cross-realm Blob mismatch undici throws on.
      return new Response('%PDF-1.7 bytes', {
        status: 200,
        headers: { 'Content-Type': 'application/pdf' },
      });
    }
    // List path.
    return new Response(JSON.stringify({ files: [SAMPLE_FILE], total: 1 }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }) as unknown as typeof fetch;
  return { fetch: impl, calls };
}

function AuthPrime({ children }: { children: React.ReactNode }): JSX.Element | null {
  const { setAuth, isAuthenticated } = useAdminAuth();
  useEffect(() => {
    setAuth('shan_admin', {
      token: TOKEN,
      role: 'Administrator',
      role_version: 0,
      expires_at: Math.floor(Date.now() / 1000) + 3600,
      password_must_change: false,
    });
  }, [setAuth]);
  return isAuthenticated ? <>{children}</> : null;
}

function renderFiles(fetchImpl: typeof fetch) {
  return render(
    <AdminAuthProvider>
      <RouterProvider>
        <AuthPrime>
          <Files apiBaseUrl="https://worker.example" fetchImpl={fetchImpl} />
        </AuthPrime>
      </RouterProvider>
    </AdminAuthProvider>,
  );
}

let createObjURL: ReturnType<typeof vi.fn>;
let revokeObjURL: ReturnType<typeof vi.fn>;
let origCreate: typeof URL.createObjectURL;
let origRevoke: typeof URL.revokeObjectURL;

beforeEach(() => {
  origCreate = URL.createObjectURL;
  origRevoke = URL.revokeObjectURL;
  createObjURL = vi.fn(() => 'blob:fake-object-url');
  revokeObjURL = vi.fn();
  URL.createObjectURL = createObjURL as unknown as typeof URL.createObjectURL;
  URL.revokeObjectURL = revokeObjURL as unknown as typeof URL.revokeObjectURL;
});

afterEach(() => {
  URL.createObjectURL = origCreate;
  URL.revokeObjectURL = origRevoke;
});

describe('<Files /> — #315 authenticated download', () => {
  it('downloads via an authenticated fetch carrying the Bearer token', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeFetch();
    renderFiles(mockFetch);

    // The filename is a button (an action), not a bare <a href> link.
    const btn = await screen.findByRole('button', { name: 'protocol.pdf' });
    expect(screen.queryByRole('link', { name: 'protocol.pdf' })).toBeNull();

    await user.click(btn);

    // Wait for the full async chain — fetch → resp.blob() → createObjectURL.
    await waitFor(() => expect(createObjURL).toHaveBeenCalledTimes(1));

    const dl = calls.find((c) => /\/apps\/files\/f-1$/.test(c.url));
    expect(dl).toBeTruthy();
    const headers = (dl!.init?.headers ?? {}) as Record<string, string>;
    expect(headers.Authorization).toBe(`Bearer ${TOKEN}`);

    // The bytes were resolved into a blob and handed to the browser to save.
    // (Identity check via toBeInstanceOf is unreliable here — undici's Blob
    // and jsdom's global Blob are different realms — so assert on shape.)
    const savedBlob = createObjURL.mock.calls[0][0] as Blob;
    expect(savedBlob.size).toBe('%PDF-1.7 bytes'.length);
    expect(savedBlob.type).toBe('application/pdf');
  });

  it('does not start a browser save when the download is rejected', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch } = makeFetch(401);
    vi.spyOn(window, 'alert').mockImplementation(() => {});
    renderFiles(mockFetch);

    const btn = await screen.findByRole('button', { name: 'protocol.pdf' });
    await user.click(btn);

    // A 401 must not produce a blob save — the old bug saved the error body.
    await waitFor(() => expect(createObjURL).not.toHaveBeenCalled());
  });
});

// ---- #175 rename + #174 folders ----

const ROOT_FOLDER = {
  file_id: 'd-1',
  filename: 'protocols',
  content_type: 'application/x-directory',
  size_bytes: 0,
  uploaded_by: 'shan_admin',
  uploaded_at: '2026-05-19T10:00:00Z',
  is_folder: true,
  folder_path: '/',
};
const INNER_FILE = {
  file_id: 'f-2',
  filename: 'inner.pdf',
  content_type: 'application/pdf',
  size_bytes: 512,
  uploaded_by: 'shan_admin',
  uploaded_at: '2026-05-21T10:00:00Z',
  is_folder: false,
  folder_path: '/protocols',
};

/**
 * Richer mock that serves root + folder listings and handles rename (PATCH)
 * and create-folder (POST /folders). Records every call for assertions.
 */
function makeRichFetch(): {
  fetch: typeof fetch;
  calls: { url: string; method: string; init: RequestInit | undefined }[];
} {
  const calls: { url: string; method: string; init: RequestInit | undefined }[] = [];
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
  const impl = (async (url: string | URL, init?: RequestInit) => {
    const u = String(url);
    const method = (init?.method ?? 'GET').toUpperCase();
    calls.push({ url: u, method, init });
    // Create folder — checked before the by-id branch so "/folders" isn't an id.
    if (/\/apps\/files\/folders$/.test(u) && method === 'POST') {
      const name = (JSON.parse(init!.body as string) as { name: string }).name;
      return json({ folder: { ...ROOT_FOLDER, file_id: 'd-new', filename: name } }, 201);
    }
    const idMatch = u.match(/\/apps\/files\/([^/?]+)$/);
    if (idMatch && method === 'PATCH') {
      const filename = (JSON.parse(init!.body as string) as { filename: string }).filename;
      return json({ file: { ...SAMPLE_FILE, filename } }, 200);
    }
    if (idMatch && method === 'GET') {
      // download path — not exercised here
      return new Response('%PDF-1.7', { status: 200, headers: { 'Content-Type': 'application/pdf' } });
    }
    // List — branch on ?path=.
    const path = new URL(u).searchParams.get('path');
    if (path === '/protocols') return json({ files: [INNER_FILE], total: 1 });
    return json({ files: [ROOT_FOLDER, SAMPLE_FILE], total: 2 });
  }) as unknown as typeof fetch;
  return { fetch: impl, calls };
}

describe('<Files /> — #175 rename', () => {
  it('commits a rename via an authenticated PATCH carrying the new filename', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeRichFetch();
    renderFiles(mockFetch);

    const renameBtn = await screen.findByRole('button', { name: 'Rename' });
    await user.click(renameBtn);

    const input = await screen.findByRole('textbox', { name: /rename protocol\.pdf/i });
    await user.clear(input);
    await user.type(input, 'renamed.pdf');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      const patch = calls.find(
        (c) => c.method === 'PATCH' && /\/apps\/files\/f-1$/.test(c.url),
      );
      expect(patch).toBeTruthy();
      expect(JSON.parse(patch!.init!.body as string)).toEqual({ filename: 'renamed.pdf' });
      // adminFetch attaches the token as a Headers instance, not a plain object.
      const headers = new Headers(patch!.init?.headers);
      expect(headers.get('Authorization')).toBe(`Bearer ${TOKEN}`);
    });
  });

  it('Escape cancels the rename without issuing a PATCH', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeRichFetch();
    renderFiles(mockFetch);

    const renameBtn = await screen.findByRole('button', { name: 'Rename' });
    await user.click(renameBtn);

    const input = await screen.findByRole('textbox', { name: /rename protocol\.pdf/i });
    await user.type(input, 'zzz');
    await user.keyboard('{Escape}');

    // Back to the filename button; no PATCH was sent.
    await screen.findByRole('button', { name: 'protocol.pdf' });
    expect(calls.some((c) => c.method === 'PATCH')).toBe(false);
  });
});

describe('<Files /> — #174 folders', () => {
  it('navigating into a folder refetches the list with ?path=', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeRichFetch();
    renderFiles(mockFetch);

    // The folder row renders as a button named by its filename (the [dir]
    // marker is aria-hidden, so it's excluded from the accessible name).
    const folderBtn = await screen.findByRole('button', { name: 'protocols' });
    await user.click(folderBtn);

    await waitFor(() => {
      const listWithPath = calls.find(
        (c) => c.method === 'GET' && /\/apps\/files\?path=/.test(c.url),
      );
      expect(listWithPath).toBeTruthy();
      expect(decodeURIComponent(listWithPath!.url)).toContain('path=/protocols');
    });
    // The folder's child file appears.
    await screen.findByRole('button', { name: 'inner.pdf' });
  });

  it('breadcrumb "Files" navigates back to root (list without ?path=)', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeRichFetch();
    renderFiles(mockFetch);

    await user.click(await screen.findByRole('button', { name: 'protocols' }));
    await screen.findByRole('button', { name: 'inner.pdf' });

    const before = calls.length;
    await user.click(await screen.findByRole('button', { name: 'Files' }));

    await waitFor(() => {
      const rootList = calls
        .slice(before)
        .find((c) => c.method === 'GET' && /\/apps\/files$/.test(c.url));
      expect(rootList).toBeTruthy();
    });
  });

  it('creates a folder via POST /folders and reloads', async () => {
    const user = userEvent.setup();
    const { fetch: mockFetch, calls } = makeRichFetch();
    renderFiles(mockFetch);

    await user.click(await screen.findByRole('button', { name: '+ New folder' }));
    const input = await screen.findByRole('textbox', { name: 'New folder name' });
    await user.type(input, 'training');
    await user.click(screen.getByRole('button', { name: 'Create' }));

    await waitFor(() => {
      const post = calls.find(
        (c) => c.method === 'POST' && /\/apps\/files\/folders$/.test(c.url),
      );
      expect(post).toBeTruthy();
      expect(JSON.parse(post!.init!.body as string)).toEqual({ name: 'training' });
    });
  });
});
