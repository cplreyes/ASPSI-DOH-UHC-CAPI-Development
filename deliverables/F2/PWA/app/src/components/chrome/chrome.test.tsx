import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
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
    expect(screen.getByRole('alert')).toBeInTheDocument();
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
});
