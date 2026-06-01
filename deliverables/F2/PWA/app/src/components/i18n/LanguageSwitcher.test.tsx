import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

// The switcher renders one button per READY locale (LOCALE_META.ready in
// src/i18n/index.ts). All 8 locales (English + the 7 PSA-target PH languages) are
// wired from ASPSI's questionnaire docs, so all 8 appear. A locale set to ready:false
// would be omitted — covered by the LOCALE_META unit guarantees rather than a button.
describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders a button per ready locale (EN + the 7 PH languages)', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    for (const name of [/english/i, /filipino/i, /cebuano/i, /bisaya/i, /ilocano/i, /hiligaynon/i, /waray/i, /bikol/i]) {
      expect(screen.getByRole('button', { name })).toBeInTheDocument();
    }
  });

  it('only renders locales flagged ready in LOCALE_META', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    // Switcher is driven by READY_LOCALES; with all 8 ready it shows 8 buttons
    // (each LOCALE_META entry is ready:true today). The group exposes exactly those.
    const group = screen.getByRole('group');
    const buttons = within(group).getAllByRole('button');
    expect(buttons).toHaveLength(8);
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
