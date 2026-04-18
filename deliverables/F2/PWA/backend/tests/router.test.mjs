import { describe, it, expect, vi } from 'vitest';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { dispatch } = require('../src/Router.js');

function makeCtx(configOverrides) {
  return {
    config: {
      get: (k) => (configOverrides && configOverrides[k] != null ? configOverrides[k] : ''),
      readAll: () => [],
    },
    responses: {},
    dlq: {},
    audit: {},
    facilities: { readAll: () => [] },
    nowMs: () => 1,
    generateUuid: () => 'fixed',
  };
}

describe('dispatch', () => {
  it('returns E_ACTION_UNKNOWN for unknown actions', () => {
    const r = dispatch({ action: 'wtf', method: 'GET', body: '' }, makeCtx(), {});
    expect(r.error.code).toBe('E_ACTION_UNKNOWN');
  });

  it('returns E_METHOD_UNKNOWN when POST-only action is called with GET', () => {
    const r = dispatch({ action: 'submit', method: 'GET', body: '' }, makeCtx(), {});
    expect(r.error.code).toBe('E_METHOD_UNKNOWN');
  });

  it('returns E_METHOD_UNKNOWN when GET-only action is called with POST', () => {
    const r = dispatch({ action: 'facilities', method: 'POST', body: '{}' }, makeCtx(), {});
    expect(r.error.code).toBe('E_METHOD_UNKNOWN');
  });

  it('returns E_KILL_SWITCH when config.kill_switch is true', () => {
    const r = dispatch(
      { action: 'facilities', method: 'GET', body: '' },
      makeCtx({ kill_switch: 'true' }),
      {},
    );
    expect(r.error.code).toBe('E_KILL_SWITCH');
  });

  it('calls the correct handler for each known action', () => {
    const handlers = {
      handleSubmit: vi.fn(() => ({ ok: true, data: 'submit-ok' })),
      handleBatchSubmit: vi.fn(() => ({ ok: true, data: 'batch-ok' })),
      handleAudit: vi.fn(() => ({ ok: true, data: 'audit-ok' })),
      handleFacilities: vi.fn(() => ({ ok: true, data: 'fac-ok' })),
      handleConfig: vi.fn(() => ({ ok: true, data: 'cfg-ok' })),
      handleSpecHash: vi.fn(() => ({ ok: true, data: 'hash-ok' })),
    };
    expect(dispatch({ action: 'submit', method: 'POST', body: '{"a":1}' }, makeCtx(), handlers).data).toBe('submit-ok');
    expect(handlers.handleSubmit).toHaveBeenCalledWith({ a: 1 }, expect.any(Object));
    expect(dispatch({ action: 'batch-submit', method: 'POST', body: '{"responses":[]}' }, makeCtx(), handlers).data).toBe('batch-ok');
    expect(dispatch({ action: 'audit', method: 'POST', body: '{"event_type":"x"}' }, makeCtx(), handlers).data).toBe('audit-ok');
    expect(dispatch({ action: 'facilities', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('fac-ok');
    expect(dispatch({ action: 'config', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('cfg-ok');
    expect(dispatch({ action: 'spec-hash', method: 'GET', body: '' }, makeCtx(), handlers).data).toBe('hash-ok');
  });

  it('returns E_PAYLOAD_INVALID when POST body is not valid JSON', () => {
    const handlers = { handleSubmit: vi.fn() };
    const r = dispatch({ action: 'submit', method: 'POST', body: 'not-json' }, makeCtx(), handlers);
    expect(r.error.code).toBe('E_PAYLOAD_INVALID');
    expect(handlers.handleSubmit).not.toHaveBeenCalled();
  });
});
