import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { BroadcastSection } from './DataSettings';

function jsonResponse(obj: unknown, status = 200): Response {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

describe('BroadcastSection (M12d broadcast editor)', () => {
  it('self-hides when the admin broadcast route is unavailable (Worker not deployed)', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ ok: false, error: { code: 'E_NOT_FOUND', message: 'not found' } }, 404),
    );
    const authOpts = () => ({ fetchImpl });
    const { container } = render(<BroadcastSection apiBaseUrl="https://api" authOpts={authOpts} />);
    await waitFor(() => expect(fetchImpl).toHaveBeenCalled());
    // 404 (route not deployed) → the whole section renders null, no stray editor.
    expect(container.querySelector('textarea')).toBeNull();
  });

  it('shows an error (does not self-hide) when the route exists but the GET errors', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse(
        { ok: false, error: { code: 'E_BACKEND', message: 'Apps Script unavailable' } },
        502,
      ),
    );
    const authOpts = () => ({ fetchImpl });
    const { container } = render(<BroadcastSection apiBaseUrl="https://api" authOpts={authOpts} />);
    // A 502 means the route IS deployed (the request reached the handler), so
    // surface the failure instead of vanishing the way a 404 does.
    expect(await screen.findByRole('alert')).toHaveTextContent('Apps Script unavailable');
    expect(container.querySelector('textarea')).toBeNull();
  });

  it('loads the current message and PATCHes a trimmed edit', async () => {
    const calls: Array<{ method: string; body: string | null }> = [];
    const fetchImpl = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      const method = init?.method ?? 'GET';
      calls.push({ method, body: (init?.body as string) ?? null });
      if (method === 'GET') {
        return jsonResponse({ broadcast_message: 'old notice' });
      }
      return jsonResponse({ broadcast_message: 'new notice' });
    });
    const authOpts = () => ({ fetchImpl });
    render(<BroadcastSection apiBaseUrl="https://api" authOpts={authOpts} />);

    const ta = (await screen.findByLabelText('Broadcast message')) as HTMLTextAreaElement;
    expect(ta.value).toBe('old notice');

    fireEvent.change(ta, { target: { value: '  new notice  ' } });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => expect(calls.some((c) => c.method === 'PATCH')).toBe(true));
    const patch = calls.find((c) => c.method === 'PATCH')!;
    expect(JSON.parse(patch.body!)).toEqual({ broadcast_message: 'new notice' });
    await waitFor(() => expect(screen.getByText('Saved')).toBeInTheDocument());
  });

  it('disables Save until the message is changed', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ broadcast_message: 'unchanged' }));
    const authOpts = () => ({ fetchImpl });
    render(<BroadcastSection apiBaseUrl="https://api" authOpts={authOpts} />);
    await screen.findByLabelText('Broadcast message');
    expect(screen.getByRole('button', { name: /save/i })).toBeDisabled();
  });
});
