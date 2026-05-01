import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { i18n } from '@/i18n';
import { AuthProvider } from '@/lib/auth-context';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';

describe('keyboard nav', () => {
  it('Tab reaches the tablet-token textarea first (Step 1 of enrollment)', async () => {
    const user = userEvent.setup();
    render(
      <I18nextProvider i18n={i18n}>
        <AuthProvider>
          <EnrollmentScreen />
        </AuthProvider>
      </I18nextProvider>,
    );
    await user.tab();
    // Token paste is the first focusable control after the auth re-arch.
    expect(document.activeElement?.tagName).toBe('TEXTAREA');
    expect((document.activeElement as HTMLElement).getAttribute('data-testid')).toBe(
      'enrollment-token-input',
    );
  });
});
