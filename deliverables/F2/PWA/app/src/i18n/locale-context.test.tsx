import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocaleProvider, useLocale } from './locale-context';

function Probe() {
  const { locale, setLocale } = useLocale();
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <button onClick={() => setLocale('fil')}>fil</button>
      <button onClick={() => setLocale('en')}>en</button>
    </div>
  );
}

describe('<LocaleProvider>', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('defaults to en when nothing is persisted', async () => {
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
  });

  it('hydrates from localStorage', async () => {
    localStorage.setItem('f2_locale', 'fil');
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('fil'));
  });

  it('setLocale persists to localStorage and updates state', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
    await user.click(screen.getByRole('button', { name: 'fil' }));
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('fil'));
    expect(localStorage.getItem('f2_locale')).toBe('fil');
  });

  it('ignores garbage in localStorage and falls back to en', async () => {
    localStorage.setItem('f2_locale', 'klingon');
    render(
      <LocaleProvider>
        <Probe />
      </LocaleProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('locale').textContent).toBe('en'));
  });
});
