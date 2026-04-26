import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressBar } from './ProgressBar';

describe('<ProgressBar>', () => {
  it('renders the current / total label', () => {
    render(<ProgressBar current={2} total={3} />);
    expect(screen.getByText(/Section 2 of 3/)).toBeInTheDocument();
  });

  it('exposes aria-valuenow as a percent', () => {
    render(<ProgressBar current={2} total={3} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '67');
    expect(bar).toHaveAttribute('aria-valuemin', '0');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('caps at 100% when current === total', () => {
    render(<ProgressBar current={3} total={3} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
  });

  it('renders the typographic ledger with zero-padded counters', () => {
    render(<ProgressBar current={4} total={35} />);
    const bar = screen.getByRole('progressbar');
    // Zero-padded to total's width: 35 → 2 chars, so 4 → '04'
    expect(bar.textContent).toContain('04');
    expect(bar.textContent).toContain('35');
  });
});
