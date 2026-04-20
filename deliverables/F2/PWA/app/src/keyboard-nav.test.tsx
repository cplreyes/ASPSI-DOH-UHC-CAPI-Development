import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nextProvider } from 'react-i18next';
import { i18n } from '@/i18n';
import { AuthProvider } from '@/lib/auth-context';
import { EnrollmentScreen } from '@/components/enrollment/EnrollmentScreen';

describe('keyboard nav', () => {
  it('Tab reaches HCW input first', async () => {
    const user = userEvent.setup();
    render(
      <I18nextProvider i18n={i18n}>
        <AuthProvider>
          <EnrollmentScreen onRefresh={async () => ({ ok: true, count: 0 })} />
        </AuthProvider>
      </I18nextProvider>,
    );
    await user.tab();
    expect(document.activeElement?.tagName).toBe('INPUT');
  });
});
