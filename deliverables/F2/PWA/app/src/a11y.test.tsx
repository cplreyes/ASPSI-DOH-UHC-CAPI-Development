import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import { i18n } from '@/i18n';
import { axe, AXE_COMPONENT_CONFIG } from './test/axe-helpers';
import { BroadcastBanner } from '@/components/chrome/BroadcastBanner';
import { KillSwitchOverlay } from '@/components/chrome/KillSwitchOverlay';
import { SpecDriftOverlay } from '@/components/chrome/SpecDriftOverlay';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';
import { SyncPage } from '@/components/sync/SyncPage';
import { AuthProvider } from '@/lib/auth-context';
import { db } from '@/lib/db';

function wrap(ui: React.ReactNode) {
  return (
    <I18nextProvider i18n={i18n}>
      <AuthProvider>{ui}</AuthProvider>
    </I18nextProvider>
  );
}

describe('a11y chrome', () => {
  it('broadcast banner has no violations', async () => {
    const { container } = render(wrap(<BroadcastBanner message="hi" />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('kill-switch overlay has no violations', async () => {
    const { container } = render(wrap(<KillSwitchOverlay active={true} />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('spec-drift overlay has no violations', async () => {
    const { container } = render(
      wrap(<SpecDriftOverlay drift={true} localVersion="a" serverMin="b" />),
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});

describe('a11y pages', () => {
  beforeEach(async () => {
    if (!db.isOpen()) await db.open();
    await db.submissions.clear();
    await db.facilities.clear();
    await db.enrollment.clear();
  });

  it('enrollment screen has no violations', async () => {
    const { container } = render(wrap(<EnrollmentScreen />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('sync page empty state has no violations', async () => {
    const { container } = render(
      wrap(
        <SyncPage
          runSync={async () => ({
            attempted: 0,
            synced: 0,
            failed: 0,
            retryScheduled: 0,
            alreadyRunning: false,
          })}
        />,
      ),
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});
