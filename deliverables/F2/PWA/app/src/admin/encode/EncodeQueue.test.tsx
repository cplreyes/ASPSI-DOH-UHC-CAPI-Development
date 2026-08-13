import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EncodeQueue } from './EncodeQueue';
import { RouterProvider, useRouter } from '../lib/pages-router';

function PathnameProbe() {
  const { pathname } = useRouter();
  return <div data-testid="pathname">{pathname}</div>;
}

function renderWithRouter() {
  return render(
    <RouterProvider>
      <EncodeQueue />
      <PathnameProbe />
    </RouterProvider>,
  );
}

describe('<EncodeQueue />', () => {
  it('renders the placeholder copy and disabled CTA', () => {
    renderWithRouter();
    expect(screen.getByRole('heading', { name: /encode queue/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /open encoder/i })).toBeDisabled();
    expect(screen.getAllByText(/sprint 2\.9/i).length).toBeGreaterThan(0);
  });

  it('navigates to /admin/encode/:hcw_id on submit with a non-empty id', async () => {
    const user = userEvent.setup();
    renderWithRouter();
    const input = screen.getByRole('textbox', { name: /hcw id/i });
    await user.type(input, 'hcw-001');
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('pathname')).toHaveTextContent('/admin/encode/hcw-001');
  });

  // #847: pre-fix, any string navigated through (a pasted enrollment token
  // reached the backend and stored). Malformed IDs now stay on the queue
  // page with an inline error.
  it('#847: rejects an ID with spaces (format error, no navigation)', async () => {
    const user = userEvent.setup();
    renderWithRouter();
    const input = screen.getByRole('textbox', { name: /hcw id/i });
    await user.type(input, 'hcw with space');
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('hcw-id-error')).toHaveTextContent(/not a valid hcw id/i);
    expect(screen.getByTestId('pathname')).toHaveTextContent('/');
  });

  it('#847: rejects a pasted enrollment token (JWT shape) with the token message', async () => {
    const user = userEvent.setup();
    renderWithRouter();
    const input = screen.getByRole('textbox', { name: /hcw id/i });
    await user.click(input);
    await user.paste('eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoY3ctMDAxIn0.c2lnbmF0dXJl');
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('hcw-id-error')).toHaveTextContent(/enrollment token or link key/i);
    expect(screen.getByTestId('pathname')).toHaveTextContent('/');
  });

  it('#847: rejects a pasted enrollment link (URL with k=) and recovers on retype', async () => {
    const user = userEvent.setup();
    renderWithRouter();
    const input = screen.getByRole('textbox', { name: /hcw id/i });
    await user.click(input);
    await user.paste('https://uhc-hcw.asiansocial.org/e/LBRHU1-HCW-03?k=abc123');
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('hcw-id-error')).toHaveTextContent(/enrollment token or link key/i);
    // Typing clears the error; a real ID then navigates.
    await user.clear(input);
    await user.type(input, 'LBRHU1-HCW-03');
    expect(screen.queryByTestId('hcw-id-error')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('pathname')).toHaveTextContent('/admin/encode/LBRHU1-HCW-03');
  });
});
