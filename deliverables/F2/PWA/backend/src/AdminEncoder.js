/**
 * F2 Admin Portal — paper-encoder submit handler.
 *
 * Plan: docs/superpowers/plans/2026-05-01-f2-admin-portal-impl.md (Task 4.2)
 * Spec: docs/superpowers/specs/2026-05-01-f2-admin-portal-design.md (§7.13)
 *
 * Pure logic: takes a payload + ctx, dispatches to handleSubmit with three
 * fields force-injected: source_path='paper_encoded', encoded_by from the
 * admin actor context, encoded_at from server time. The Operator role
 * transcribes paper-collected surveys into the same F2_Responses sheet
 * the PWA writes to; only the provenance differs.
 *
 * handleSubmit is resolved through `ctx.submit` if present (Node tests
 * inject it explicitly), otherwise falls back to the global `handleSubmit`
 * (Apps Script — every top-level function is global). The encoder client
 * may omit submitted_at_client (paper has no client clock); fallback is
 * server-now so sheet ordering stays sensible.
 */
function adminEncodeSubmit(payload, ctx) {
  if (!payload || typeof payload !== 'object') {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'payload required' } };
  }
  if (!payload.hcw_id) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'hcw_id required' } };
  }
  if (!ctx || !ctx.actor_username) {
    return { ok: false, error: { code: 'E_VALIDATION', message: 'admin actor context required' } };
  }

  var submitFn = ctx.submit || (typeof handleSubmit !== 'undefined' ? handleSubmit : null);
  if (!submitFn) {
    return { ok: false, error: { code: 'E_INTERNAL', message: 'submit fn unavailable' } };
  }

  var nowMs = ctx.nowMs ? ctx.nowMs() : Date.now();
  var enriched = {};
  for (var k in payload) {
    if (Object.prototype.hasOwnProperty.call(payload, k)) {
      enriched[k] = payload[k];
    }
  }
  enriched.source_path = 'paper_encoded';
  enriched.encoded_by = ctx.actor_username;
  enriched.encoded_at = new Date(nowMs).toISOString();
  if (enriched.submitted_at_client == null) {
    enriched.submitted_at_client = nowMs;
  }

  return submitFn(enriched, ctx);
}

if (typeof module !== 'undefined') {
  module.exports = {
    adminEncodeSubmit: adminEncodeSubmit,
  };
}
