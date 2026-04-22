import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Navigator } from './Navigator';

describe('<Navigator>', () => {
  it('renders nothing when onSaveDraft is not provided', () => {
    const { container } = render(<Navigator />);
    expect(container.firstChild).toBeNull();
  });

  it('renders Save Draft button when onSaveDraft is provided', () => {
    render(<Navigator onSaveDraft={vi.fn()} />);
    expect(screen.getByRole('button', { name: /save draft/i })).toBeInTheDocument();
  });

  it('calls onSaveDraft when the button is clicked', async () => {
    const user = userEvent.setup();
    const onSaveDraft = vi.fn();
    render(<Navigator onSaveDraft={onSaveDraft} />);
    await user.click(screen.getByRole('button', { name: /save draft/i }));
    expect(onSaveDraft).toHaveBeenCalledTimes(1);
  });

  it('shows the saved confirmation when showSaved is true', () => {
    render(<Navigator onSaveDraft={vi.fn()} showSaved />);
    expect(screen.getByText(/draft saved/i)).toBeInTheDocument();
  });

  it('hides the saved confirmation when showSaved is false', () => {
    render(<Navigator onSaveDraft={vi.fn()} showSaved={false} />);
    expect(screen.queryByText(/draft saved/i)).toBeNull();
  });
});
