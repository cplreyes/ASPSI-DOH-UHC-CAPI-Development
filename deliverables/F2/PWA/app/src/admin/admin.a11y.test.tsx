import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { axe, AXE_COMPONENT_CONFIG } from '@/test/axe-helpers';
import { AdminAuthProvider } from './lib/auth-context';
import { RouterProvider } from './lib/pages-router';
import { Login } from './Login';
import { HelpPage } from './help/HelpPage';
import { Layout } from './Layout';

function wrap(ui: React.ReactNode) {
  return (
    <AdminAuthProvider>
      <RouterProvider>{ui}</RouterProvider>
    </AdminAuthProvider>
  );
}

describe('admin a11y', () => {
  it('Login screen has no axe violations', async () => {
    const noopFetch = (() => Promise.reject(new Error('not used'))) as unknown as typeof fetch;
    const { container } = render(wrap(<Login apiBaseUrl="https://example" fetchImpl={noopFetch} />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('HelpPage has no axe violations', async () => {
    const { container } = render(wrap(<HelpPage />));
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });

  it('Layout shell (with placeholder children) has no axe violations', async () => {
    const { container } = render(
      wrap(
        <Layout>
          <section>
            <h2>Placeholder content</h2>
            <p>Sample dashboard content for layout a11y verification.</p>
          </section>
        </Layout>,
      ),
    );
    expect(await axe(container, AXE_COMPONENT_CONFIG)).toHaveNoViolations();
  });
});
