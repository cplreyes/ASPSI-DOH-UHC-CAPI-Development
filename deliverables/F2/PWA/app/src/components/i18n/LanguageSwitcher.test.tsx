import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
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
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute('aria-pressed', 'false');
    await user.click(screen.getByRole('button', { name: /filipino/i }));
    expect(screen.getByRole('button', { name: /filipino/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /english/i })).toHaveAttribute('aria-pressed', 'false');
  });
});
