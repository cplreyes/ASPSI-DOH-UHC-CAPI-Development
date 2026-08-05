import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider } from '@/i18n/locale-context';
import { LanguageSwitcher } from './LanguageSwitcher';

// The switcher is a single native <select> with one <option> per READY locale
// (LOCALE_META.ready in src/i18n/index.ts). All 8 locales (English + the 7
// PSA-target PH languages) are wired from ASPSI's questionnaire docs, so all 8
// options appear. A locale set to ready:false would be omitted — covered by the
// LOCALE_META unit guarantees rather than an option.
describe('<LanguageSwitcher>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders an option per ready locale (EN + the 7 PH languages)', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    for (const name of ['English', 'Filipino', 'Cebuano', 'Bisaya', 'Ilocano', 'Hiligaynon', 'Waray', 'Bikol']) {
      expect(screen.getByRole('option', { name })).toBeInTheDocument();
    }
  });

  it('exposes exactly the READY locales as options', () => {
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    // Driven by READY_LOCALES; with all 8 ready it shows 8 options. The select is
    // the only combobox on screen, so getAllByRole('option') scopes to it.
    expect(screen.getByRole('combobox', { name: /language/i })).toBeInTheDocument();
    expect(screen.getAllByRole('option')).toHaveLength(8);
  });

  it('selecting Filipino persists fil to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    await user.selectOptions(screen.getByRole('combobox', { name: /language/i }), 'fil');
    expect(localStorage.getItem('f2_locale')).toBe('fil');
  });

  it('reflects the active locale as the selected option', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );
    const select = screen.getByRole('combobox', { name: /language/i });
    expect(select).toHaveValue('en');
    await user.selectOptions(select, 'fil');
    expect(select).toHaveValue('fil');
  });
});
