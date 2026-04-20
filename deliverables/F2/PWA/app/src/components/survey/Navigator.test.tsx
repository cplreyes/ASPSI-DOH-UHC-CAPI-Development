import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Navigator } from './Navigator';

describe('<Navigator>', () => {
  it('disables Previous on the first section', () => {
    render(
      <Navigator isFirst isLast={false} onPrev={vi.fn()} onNext={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('renders Next (not Submit) on a middle section', () => {
    render(
      <Navigator
        isFirst={false}
        isLast={false}
        onPrev={vi.fn()}
        onNext={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /submit/i })).toBeNull();
  });

  it('renders Submit (not Next) on the last section', () => {
    render(
      <Navigator isFirst={false} isLast onPrev={vi.fn()} onNext={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /next/i })).toBeNull();
  });

  it('calls onPrev / onNext / onSubmit when the respective buttons are clicked', async () => {
    const user = userEvent.setup();
    const onPrev = vi.fn();
    const onNext = vi.fn();
    const onSubmit = vi.fn();

    const { rerender } = render(
      <Navigator
        isFirst={false}
        isLast={false}
        onPrev={onPrev}
        onNext={onNext}
        onSubmit={onSubmit}
      />,
    );
    await user.click(screen.getByRole('button', { name: /previous/i }));
    await user.click(screen.getByRole('button', { name: /next/i }));

    rerender(
      <Navigator isFirst={false} isLast onPrev={onPrev} onNext={onNext} onSubmit={onSubmit} />,
    );
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onPrev).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
