import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the Hello F2 heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /hello f2/i })).toBeInTheDocument();
  });

  it('renders the iOS fallback copy when beforeinstallprompt has not fired', () => {
    render(<App />);
    expect(screen.getByText(/add to home screen/i)).toBeInTheDocument();
  });
});
