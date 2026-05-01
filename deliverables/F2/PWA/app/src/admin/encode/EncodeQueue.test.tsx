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

  it('URL-encodes special characters in hcw_id', async () => {
    const user = userEvent.setup();
    renderWithRouter();
    const input = screen.getByRole('textbox', { name: /hcw id/i });
    await user.type(input, 'hcw with space');
    await user.click(screen.getByRole('button', { name: /open encoder/i }));
    expect(screen.getByTestId('pathname')).toHaveTextContent('/admin/encode/hcw%20with%20space');
  });
});
