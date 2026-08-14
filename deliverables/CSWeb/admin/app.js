/* CAPI Console — console configuration screens.   Carl, 2026-07-27; split 2026-08-09
 *
 * Activities · Alerting · Assignment plan. These edit JSON files on disk and
 * have nothing to do with identity, which is why they kept the flat
 * /docs/admin/api.php envelope while the access screens moved to the identity
 * API. Splitting them out of one 400-line file was E9-ADMIN-020.
 *
 * The view logic below is unchanged from the version that has been running
 * since July; only the plumbing moved — helpers now come from ui.js, and each
 * screen registers a route instead of being dispatched by a hand-rolled tab
 * switch. Deliberately a small diff: these three screens are live and in use
 * during pretest, and a rewrite would be risk with no return.
 *
 * Users, roles, sessions and audit used to live here too. They are now
 * view-*.js against /docs/idp/admin, because the store they must read is the
 * one the gate consults.
 */
'use strict';
(function (C) {
  var el = C.el, card = C.card, tbl = C.tbl, inp = C.inp, sel = C.sel,
      field = C.field, msg = C.msg, api = C.apiConsole;

  function reload() { C.busy(); C.render(); }

  /* ------------------------------------------------------------ activities */
  function renderActivities(view, acts) {
    var rows = acts.map(function (a) { return actRow(a); });
    view.textContent = '';
    var t = tbl(['ID', 'Label', 'Phase', 'Kind', 'Start', 'End', 'Planned', 'Logins', 'Quotas', ''], rows);
    view.appendChild(card('Survey activities',
      'Roster wins over dates when they disagree; F2 always classifies by date. Remove never deletes cases — they reclassify.',
      [t,
       el('div', { class: 'adm-f', style: 'margin-top:14px' }, [
         el('button', { class: 'btn sec', text: '+ Add activity', onclick: function () {
           var tb = t.querySelector('tbody');
           var blank = tb.querySelector('td.adm-none');
           if (blank) tb.textContent = '';
           tb.appendChild(actRow({ id: '', name: '', phase: 'training', kind: 'training',
                                   planned: true, logins: [], quotas: {} }));
         } }),
         el('button', { class: 'btn', text: 'Save activities', onclick: function () { saveActivities(t); } })
       ])]));
  }

  function actRow(a) {
    var q = Object.keys(a.quotas || {}).map(function (k) { return k + ':' + a.quotas[k]; }).join(' ');
    var tr = el('tr', {});
    function cell(kid, cls) { return el('td', cls ? { class: cls } : {}, [kid]); }
    tr.appendChild(cell(inp({ name: 'id', value: a.id || '', size: 5, placeholder: 'A4' })));
    tr.appendChild(cell(inp({ name: 'name', value: a.name || '', placeholder: 'Training Batch 2' })));
    tr.appendChild(cell(sel('phase', [['pretest', 'pretest'], ['training', 'training'], ['survey', 'survey']], a.phase)));
    tr.appendChild(cell(sel('kind', [['pretest', 'pretest'], ['training', 'training'], ['collection', 'collection'],
      ['listing', 'listing'], ['mopup', 'mopup'], ['other', 'other']], a.kind)));
    tr.appendChild(cell(inp({ name: 'start', type: 'date', value: a.start || '' })));
    tr.appendChild(cell(inp({ name: 'end', type: 'date', value: a.end || '' })));
    var ck = inp({ name: 'planned', type: 'checkbox' }); ck.checked = !!a.planned;
    tr.appendChild(cell(ck));
    tr.appendChild(cell(inp({ name: 'logins', value: (a.logins || []).join(' '), size: 16, placeholder: 'tr-001 tr-002' })));
    tr.appendChild(cell(inp({ name: 'quotas', value: q, size: 12, placeholder: 'f3:10 f4:20' })));
    tr.appendChild(cell(el('button', { class: 'btn sec', text: 'Remove', onclick: function () { tr.remove(); } })));
    return tr;
  }

  function saveActivities(t) {
    var out = [], bad = null;
    Array.prototype.forEach.call(t.querySelectorAll('tbody tr'), function (tr) {
      function v(n) { var e = tr.querySelector('[name=' + n + ']'); return e ? e.value.trim() : ''; }
      if (!tr.querySelector('[name=id]')) return;              // the empty-state row
      var quotas = {};
      v('quotas').split(/[\s,]+/).filter(Boolean).forEach(function (p) {
        var m = /^(f1|f3|f4|f2):(\d+)$/.exec(p);
        if (!m) { bad = 'Quota "' + p + '" must look like f3:10'; return; }
        quotas[m[1]] = parseInt(m[2], 10);
      });
      out.push({ id: v('id'), name: v('name'), phase: v('phase'), kind: v('kind'),
        start: v('start'), end: v('end'),
        planned: tr.querySelector('[name=planned]').checked,
        logins: v('logins').split(/[\s,]+/).filter(Boolean), quotas: quotas });
    });
    if (bad) return msg(bad, 'err');
    api('activities', { activities: out })
      .then(function (j) { msg('Saved ' + j.count + ' activities. Live surfaces update within ~2 minutes.'); reload(); })
      .catch(function (e) { msg(e.message, 'err'); });
  }

  /* ---------------------------------------------------------------- alerts */
  function renderAlerts(view, a) {
    var w = inp({ placeholder: a.webhook_set ? a.webhook : 'https://hooks.slack.com/services/…', size: 44 });
    var sh = inp({ type: 'number', value: a.silence_hours, min: 1, max: 240, size: 4 });
    var hh = inp({ type: 'number', value: a.high_hours, min: 1, max: 480, size: 4 });
    var eh = inp({ type: 'number', value: a.expire_hours, min: 2, max: 720, size: 4 });
    var qs = inp({ type: 'time', value: a.quiet_start || '' });
    var qe = inp({ type: 'time', value: a.quiet_end || '' });
    var cks = {};
    var typeRow = el('div', { class: 'adm-f' });
    ['silence', 'offplan', 'dup'].forEach(function (t) {
      var c = inp({ type: 'checkbox' }); c.checked = !!(a.types || {})[t];
      cks[t] = c;
      typeRow.appendChild(el('label', { text: t }, [c]));
    });
    view.textContent = '';
    view.appendChild(card('Off-page delivery',
      a.webhook_set ? 'A webhook is configured. Send a test to confirm it still works.'
                    : 'No webhook set — alerts currently reach nobody unless the dashboard is open.',
      [el('div', { class: 'adm-f' }, [
         field('Slack incoming webhook', w),
         el('button', { class: 'btn', text: 'Save webhook', onclick: function () {
           api('alerts', { webhook: w.value.trim() })
             .then(function () { msg('Webhook saved.'); reload(); })
             .catch(function (e) { msg(e.message, 'err'); });
         } }),
         el('button', { class: 'btn sec', text: 'Send test alert', onclick: function () {
           api('alerts', { action: 'test' })
             .then(function (j) { msg('Test alert delivered (HTTP ' + j.http + ').'); })
             .catch(function (e) { msg(e.message, 'err'); });
         } })])]));
    view.appendChild(card('Thresholds',
      'Silence: hours without a sync before an enumerator is flagged. High: when it escalates. Expire: when it stops nagging (a finished activity should not alert forever).',
      [el('div', { class: 'adm-f' }, [
        field('Silence (h)', sh), field('Escalate (h)', hh), field('Expire (h)', eh),
        field('Quiet from', qs), field('Quiet until', qe)]),
       el('div', { class: 'sub', text: 'Alert types to deliver off-page:' }), typeRow,
       el('button', { class: 'btn', text: 'Save thresholds', onclick: function () {
         api('alerts', { silence_hours: +sh.value, high_hours: +hh.value, expire_hours: +eh.value,
           quiet_start: qs.value, quiet_end: qe.value,
           types: { silence: cks.silence.checked, offplan: cks.offplan.checked, dup: cks.dup.checked } })
           .then(function () { msg('Thresholds saved.'); reload(); })
           .catch(function (e) { msg(e.message, 'err'); });
       } })]));
  }

  /* ------------------------------------------------------------------ plan */
  function renderPlan(view, j) {
    var prov = j.provisional || {};
    var rows = ['f1', 'f3', 'f4', 'f2'].map(function (k) {
      var isProv = !!prov[k];
      return el('tr', {}, [
        el('td', {}, [el('span', { class: 'mono', text: k.toUpperCase() })]),
        el('td', {}, [el('span', { class: 'pillt ' + (isProv ? 'admin' : 'field'),
          text: isProv ? 'provisional' : 'final' })]),
        el('td', { class: 'muted', text: isProv
          ? 'Coverage % is measured against a placeholder plan — not quotable.'
          : 'Coverage % is measured against the committed plan.' }),
        el('td', {}, [el('button', { class: 'btn sec', text: isProv ? 'Mark final' : 'Mark provisional',
          onclick: function () {
            if (isProv) {
              // Marking FINAL is the one irreversible-in-spirit action here:
              // it makes coverage percentages quotable to DOH.
              C.confirmDestructive({
                title: 'Mark ' + k.toUpperCase() + ' final?',
                lead: 'Coverage percentages for this instrument become quotable and the PROVISIONAL badges '
                    + 'disappear from the console and the Overview.',
                confirmWord: k.toUpperCase(), verb: 'Mark final',
                preflight: function () {
                  return Promise.resolve({ lines: [
                    'Affects the dashboard coverage banner and the Overview badges.',
                    'Reversible from this screen, but anything already quoted is not.'
                  ] });
                },
                run: function () { return api('plan', { action: 'provisional', inst: k, value: false }); },
                done: function () { msg(k.toUpperCase() + ' is now final.'); reload(); }
              });
              return;
            }
            api('plan', { action: 'provisional', inst: k, value: true })
              .then(function () { msg(k.toUpperCase() + ' is now provisional.'); reload(); })
              .catch(function (e) { msg(e.message, 'err'); });
          } })])
      ]);
    });
    view.textContent = '';
    view.appendChild(card('Plan status per instrument',
      'This flag drives the PROVISIONAL badges on the Overview and the dashboard coverage banner. Uploading a replacement plan still runs through the vault pipeline.',
      [tbl(['Form', 'Status', 'Meaning', ''], rows)]));
  }

  /* ---------------------------------------------------------------- routes */

  function loader(resource, paint) {
    return function (view) {
      api(resource).then(function (j) { paint(view, j); }).catch(function (e) {
        view.textContent = '';
        view.appendChild(C.errorState(e, function () { C.render(); }));
      });
    };
  }

  C.route('activities', {
    title: 'Activities',
    lead: 'Named fieldwork periods with start and end dates. Cases classify to the activity that was running '
        + 'when they were collected.',
    perm: 'admin.system',
    render: loader('activities', function (v, j) { renderActivities(v, j.activities || []); })
  });

  C.route('alerts', {
    title: 'Alerting',
    lead: 'Where alerts go and when they fire. Until a webhook is set, alerts only appear on the dashboard.',
    perm: 'admin.system',
    render: loader('alerts', function (v, j) { renderAlerts(v, j.alerts || {}); })
  });

  C.route('plan', {
    title: 'Assignment plan',
    lead: 'The assignment plan behind coverage percentages. Clearing "provisional" is what makes a coverage '
        + 'figure quotable.',
    perm: 'admin.system',
    render: loader('plan', function (v, j) { renderPlan(v, j); })
  });
})(window.CAPI);
