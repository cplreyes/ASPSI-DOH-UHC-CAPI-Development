import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { i18n } from '@/i18n';
import { BroadcastBanner } from './BroadcastBanner';
import { KillSwitchOverlay } from './KillSwitchOverlay';
import { SpecDriftOverlay } from './SpecDriftOverlay';

function wrap(ui: React.ReactNode) {
  return <I18nextProvider i18n={i18n}>{ui}</I18nextProvider>;
}

describe('chrome', () => {
  it('BroadcastBanner renders nothing when empty', () => {
    const { container } = render(wrap(<BroadcastBanner message="" />));
    expect(container.textContent).toBe('');
  });

  it('BroadcastBanner renders message when non-empty', () => {
    render(wrap(<BroadcastBanner message="Maintenance tonight 8pm." />));
    expect(screen.getByRole('status')).toHaveTextContent('Maintenance');
  });

  it('KillSwitchOverlay renders when active', () => {
    render(wrap(<KillSwitchOverlay active={true} />));
    // #284: now a modal alertdialog (was a passive role="alert").
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('KillSwitchOverlay renders nothing when inactive', () => {
    const { container } = render(wrap(<KillSwitchOverlay active={false} />));
    expect(container.textContent).toBe('');
  });

  it('SpecDriftOverlay shows reload button when drift=true', () => {
    render(wrap(<SpecDriftOverlay drift={true} localVersion="a" serverMin="b" />));
    expect(screen.getByRole('button', { name: /reload/i })).toBeInTheDocument();
  });

  it('SpecDriftOverlay renders nothing when drift=false', () => {
    const { container } = render(
      wrap(<SpecDriftOverlay drift={false} localVersion="a" serverMin="a" />),
    );
    expect(container.textContent).toBe('');
  });

  // #284: blocking overlays must trap focus — the form behind was only
  // blocked at submit; keyboard/AT could still edit it.
  it('KillSwitchOverlay is a modal dialog that pulls focus off the form (#284)', () => {
    render(
      wrap(
        <>
          <input data-testid="form-field" />
          <KillSwitchOverlay active={true} />
        </>,
      ),
    );
    const dialog = screen.getByRole('alertdialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    // Focus left the form and is pinned on the (control-less) dialog.
    expect(screen.getByTestId('form-field')).not.toHaveFocus();
    expect(dialog).toHaveFocus();
  });

  it('KillSwitchOverlay traps Tab inside the dialog (#284)', async () => {
    const user = userEvent.setup();
    render(
      wrap(
        <>
          <input data-testid="form-field" />
          <KillSwitchOverlay active={true} />
        </>,
      ),
    );
    const dialog = screen.getByRole('alertdialog');
    await user.tab();
    // Tab does not escape into the form behind the overlay.
    expect(screen.getByTestId('form-field')).not.toHaveFocus();
    expect(dialog).toHaveFocus();
  });

  it('SpecDriftOverlay moves focus to Reload and keeps Tab trapped (#284)', async () => {
    const user = userEvent.setup();
    render(
      wrap(
        <>
          <input data-testid="form-field" />
          <SpecDriftOverlay drift={true} localVersion="a" serverMin="b" />
        </>,
      ),
    );
    const reload = screen.getByRole('button', { name: /reload/i });
    expect(reload).toHaveFocus();
    await user.tab();
    expect(screen.getByTestId('form-field')).not.toHaveFocus();
    expect(reload).toHaveFocus(); // only focusable in the dialog → stays
  });
});
