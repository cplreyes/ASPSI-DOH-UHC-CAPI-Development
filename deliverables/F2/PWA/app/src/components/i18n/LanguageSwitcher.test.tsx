import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

// The switcher renders one button per READY locale (LOCALE_META.ready in
// src/i18n/index.ts). Today the ready set is en + fil (Tagalog); dialects whose
// translations aren't wired yet (ceb/bis/ilo/hil/war/bcl) never appear, so a
// respondent is never shown a language that would render as English.
describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders a button per ready locale (EN + FIL today)', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.getByRole('button', { name: /english/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /filipino/i })).toBeInTheDocument();
  });

  it('does not render a not-ready locale (e.g. Cebuano, Waray)', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    expect(screen.queryByRole('button', { name: /cebuano/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /waray/i })).not.toBeInTheDocument();
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
