import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubEnv('VITE_FIL_READY', 'true');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('renders nothing when VITE_FIL_READY is unset (Filipino translations not ready)', () => {
    vi.stubEnv('VITE_FIL_READY', '');
    const { container } = render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(container.firstChild).toBeNull();
    expect(screen.queryByRole('button', { name: /filipino/i })).not.toBeInTheDocument();
  });

  it('renders both EN and FIL buttons', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: /english/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /filipino/i })).toBeInTheDocument();
  });

  it('clicking FIL persists fil to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole('button', { name: /filipino/i }));
    expect(localStorage.getItem('f2_locale')).toBe('fil');
  });

  it('marks the current locale button as pressed', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
    await user.click(screen.getByRole('button', { name: /filipino/i }));
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute(
      'aria-pressed',
      'false',
    );
  });
});
