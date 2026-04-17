import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('<App>', () => {
  it('renders Section A heading', () => {
    render(<App />);
    expect(
      screen.getByRole('heading', { name: /Section A — Healthcare Worker Profile/ }),
    ).toBeInTheDocument();
  });

  it('renders at least one Section A question', () => {
    render(<App />);
    expect(screen.getByLabelText(/What is your sex at birth/)).toBeInTheDocument();
  });
});
