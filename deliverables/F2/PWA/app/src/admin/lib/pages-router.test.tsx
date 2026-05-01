import { describe, expect, it } from 'vitest';
import { matchRoute } from './pages-router';

describe('matchRoute', () => {
  const routes = [
    { path: '/admin/data' },
    { path: '/admin/data/responses' },
    { path: '/admin/report' },
    { path: '/admin/users' },
  ];

  it('returns null when nothing matches', () => {
    expect(matchRoute(routes, '/somewhere/else')).toBeNull();
  });

  it('returns exact match', () => {
    expect(matchRoute(routes, '/admin/data')?.path).toBe('/admin/data');
  });

  it('returns the longest prefix match for nested paths', () => {
    expect(matchRoute(routes, '/admin/data/responses/abc-123')?.path).toBe('/admin/data/responses');
  });

  it('falls back to a shorter prefix when the deeper one does not match', () => {
    expect(matchRoute(routes, '/admin/data/something-not-listed')?.path).toBe('/admin/data');
  });

  it('does not match a path that only shares a prefix with no boundary', () => {
    // /admin/dataXXX should not match /admin/data
    expect(matchRoute(routes, '/admin/dataXXX')).toBeNull();
  });
});
