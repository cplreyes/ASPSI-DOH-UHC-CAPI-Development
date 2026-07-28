/* CAPI Console — Admin SPA. Vanilla JS, no build step (the box has no toolchain).
   All DOM built with createElement/textContent: nothing from the API is ever
   interpolated as HTML. */
'use strict';
(function () {
  var API = '/docs/admin/api.php?r=';
  var csrf = (document.cookie.match(/(?:^|;\s*)adm_csrf=([^;]+)/) || [])[1] || '';
  var view = document.getElementById('admView');
  var msgBox = document.getElementById('admMsg');
  var TABS = [
    ['activities', 'Activities'], ['users', 'Users & access'], ['alerts', 'Alerting'],
    ['plan', 'Assignment plan'], ['audit', 'Audit trail']
  ];
  var LEAD = {
    activities: 'Named fieldwork periods with start and end dates. Cases classify to the activity that was running when they were collected.',
    users: 'Console accounts and their access tier. Field sees monitoring; staff adds the data room; admin adds this page.',
    alerts: 'Where alerts go and when they fire. Until a webhook is set, alerts only appear on the dashboard.',
    plan: 'The assignment plan behind coverage percentages. Clearing "provisional" is what makes a coverage figure quotable.',
    audit: 'Every administrative change, with who made it and when.'
  };
  var state = { tab: 'activities' };

  function el(t, attrs, kids) {
    var e = document.createElement(t);
    for (var k in (attrs || {})) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else if (k.slice(0, 2) === 'on') e[k] = attrs[k];
      else if (attrs[k] !== null && attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) e.appendChild(c); });
    return e;
  }
  function msg(text, kind) {
    msgBox.textContent = '';
    if (!text) return;
    msgBox.appendChild(el('div', { class: 'msg ' + (kind || 'ok'), text: text }));
    if (kind !== 'err') setTimeout(function () { msgBox.textContent = ''; }, 6000);
  }
  function api(res, body) {
    var opt = { headers: { 'Content-Type': 'application/json' }, cache: 'no-store' };
    if (body) { body._csrf = csrf; opt.method = 'POST'; opt.body = JSON.stringify(body); }
    return fetch(API + res, opt).then(function (r) { return r.json().catch(function () {
      throw new Error('server returned a non-JSON response (HTTP ' + r.status + ')'); }); })
      .then(function (j) { if (!j.ok) throw new Error(j.error || 'request failed'); return j; });
  }
  function busy() { view.textContent = ''; view.appendChild(el('div', { class: 'spin', text: 'Loading…' })); }
  function card(title, sub, kids) {
    return el('div', { class: 'adm-card' },
      [el('h3', { text: title }), sub ? el('div', { class: 'sub', text: sub }) : null].concat(kids || []));
  }
  function field(label, input) { return el('label', { text: label }, [input]); }
  function inp(attrs) { return el('input', attrs); }
  function sel(name, opts, val) {
    var s = el('select', { name: name });
    opts.forEach(function (o) {
      var op = el('option', { value: o[0], text: o[1] });
      if (o[0] === val) op.selected = true;
      s.appendChild(op);
    });
    return s;
  }
  function tbl(heads, rows) {
    var thead = el('thead', {}, [el('tr', {}, heads.map(function (h) { return el('th', { text: h }); }))]);
    return el('div', { class: 'tbl-wrap' }, [el('table', { class: 'tbl' }, [thead, el('tbody', {}, rows)])]);
  }
  function ago(iso) {
    if (!iso) return '—';
    var ms = Date.now() - Date.parse(iso);
    if (!isFinite(ms) || ms < 0) return iso;
    var h = Math.floor(ms / 36e5), d = Math.floor(h / 24);
    return d > 0 ? d + 'd ago' : h > 0 ? h + 'h ago' : Math.max(1, Math.floor(ms / 6e4)) + 'm ago';
  }

  /* ------------------------------------------------------------ activities */
  function renderActivities(acts) {
    var rows = acts.map(function (a) { return actRow(a); });
    var body = el('tbody', {});
    view.textContent = '';
    var t = tbl(['ID', 'Label', 'Phase', 'Kind', 'Start', 'End', 'Planned', 'Logins', 'Quotas', ''], rows);
    view.appendChild(card('Survey activities',
      'Roster wins over dates when they disagree; F2 always classifies by date. Remove never deletes cases — they reclassify.',
      [t,
       el('div', { class: 'adm-f', style: 'margin-top:14px' }, [
         el('button', { class: 'btn sec', text: '+ Add activity', onclick: function () {
           var tb = t.querySelector('tbody');
           tb.appendChild(actRow({ id: '', name: '', phase: 'training', kind: 'training', planned: true, logins: [], quotas: {} }));
         } }),
         el('button', { class: 'btn', text: 'Save activities', onclick: function () { saveActivities(t); } })
       ])]));
  }
  function actRow(a) {
    var q = Object.keys(a.quotas || {}).map(function (k) { return k + ':' + a.quotas[k]; }).join(' ');
    var tr = el('tr', {});
    function td(kid, cls) { return el('td', cls ? { class: cls } : {}, [kid]); }
    tr.appendChild(td(inp({ name: 'id', value: a.id || '', size: 5, placeholder: 'A4' })));
    tr.appendChild(td(inp({ name: 'name', value: a.name || '', placeholder: 'Training Batch 2' })));
    tr.appendChild(td(sel('phase', [['pretest', 'pretest'], ['training', 'training'], ['survey', 'survey']], a.phase)));
    tr.appendChild(td(sel('kind', [['pretest', 'pretest'], ['training', 'training'], ['collection', 'collection'],
      ['listing', 'listing'], ['mopup', 'mopup'], ['other', 'other']], a.kind)));
    tr.appendChild(td(inp({ name: 'start', type: 'date', value: a.start || '' })));
    tr.appendChild(td(inp({ name: 'end', type: 'date', value: a.end || '' })));
    var ck = inp({ name: 'planned', type: 'checkbox' }); ck.checked = !!a.planned;
    tr.appendChild(td(ck));
    tr.appendChild(td(inp({ name: 'logins', value: (a.logins || []).join(' '), size: 16, placeholder: 'tr-001 tr-002' })));
    tr.appendChild(td(inp({ name: 'quotas', value: q, size: 12, placeholder: 'f3:10 f4:20' })));
    tr.appendChild(td(el('button', { class: 'btn sec', text: 'Remove', onclick: function () { tr.remove(); } })));
    return tr;
  }
  function saveActivities(t) {
    var out = [], bad = null;
    Array.prototype.forEach.call(t.querySelectorAll('tbody tr'), function (tr) {
      function v(n) { var e = tr.querySelector('[name=' + n + ']'); return e ? e.value.trim() : ''; }
      if (!v('id') && !v('name')) return;
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
      .then(function (j) { msg('Saved ' + j.count + ' activities. Live surfaces update within ~2 minutes.'); load(); })
      .catch(function (e) { msg(e.message, 'err'); });
  }

  /* ----------------------------------------------------------------- users */
  function renderUsers(users) {
    var rows = users.map(function (u) {
      var acts = el('div', { class: 'rowacts' });
      if (!u.protected) {
        ['field', 'staff', 'admin'].filter(function (t) { return t !== u.tier; }).forEach(function (t) {
          acts.appendChild(el('button', { class: 'btn sec', text: '→ ' + t, onclick: function () {
            api('users', { action: 'tier', user: u.user, tier: t })
              .then(function () { msg('Moved ' + u.user + ' to ' + t + '.'); load(); })
              .catch(function (e) { msg(e.message, 'err'); });
          } }));
        });
        acts.appendChild(el('button', { class: 'btn sec', text: 'Password', onclick: function () {
          var pw = prompt('New password for ' + u.user + ' (min 10 chars):');
          if (!pw) return;
          api('users', { action: 'password', user: u.user, password: pw })
            .then(function () { msg('Password updated for ' + u.user + '.'); })
            .catch(function (e) { msg(e.message, 'err'); });
        } }));
        acts.appendChild(el('button', { class: 'btn danger', text: 'Remove', onclick: function () {
          if (!confirm('Remove ' + u.user + '? They lose access immediately.')) return;
          api('users', { action: 'delete', user: u.user })
            .then(function () { msg('Removed ' + u.user + '.'); load(); })
            .catch(function (e) { msg(e.message, 'err'); });
        } }));
      } else {
        acts.appendChild(el('span', { class: 'muted', text: 'protected' }));
      }
      return el('tr', {}, [
        el('td', {}, [el('span', { class: 'mono', text: u.user })]),
        el('td', {}, [el('span', { class: 'pillt ' + u.tier, text: u.tier })]),
        el('td', { class: 'muted', text: ago(u.last_seen) }),
        el('td', {}, [acts])
      ]);
    });
    var nu = inp({ placeholder: 'se-008', size: 12 }),
        np = inp({ placeholder: 'min 10 chars', type: 'password', size: 16 }),
        nt = sel('tier', [['field', 'field'], ['staff', 'staff'], ['admin', 'admin']], 'field');
    view.textContent = '';
    view.appendChild(card('Console accounts',
      'field = dashboard, map and sync feed · staff = adds the data room · admin = adds this page. "Last seen" comes from actual device syncs.',
      [tbl(['User', 'Tier', 'Last sync', 'Actions'], rows)]));
    view.appendChild(card('Add an account', 'The password is shown only here — copy it before saving.',
      [el('div', { class: 'adm-f' }, [
        field('Username', nu), field('Password', np), field('Tier', nt),
        el('button', { class: 'btn', text: 'Create account', onclick: function () {
          api('users', { action: 'create', user: nu.value.trim(), password: np.value, tier: nt.value })
            .then(function (j) { msg('Created ' + j.user + ' as ' + j.tier + '.'); load(); })
            .catch(function (e) { msg(e.message, 'err'); });
        } })])]));
  }

  /* ---------------------------------------------------------------- alerts */
  function renderAlerts(a) {
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
             .then(function () { msg('Webhook saved.'); load(); })
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
           .then(function () { msg('Thresholds saved.'); load(); })
           .catch(function (e) { msg(e.message, 'err'); });
       } })]));
  }

  /* ------------------------------------------------------------------ plan */
  function renderPlan(j) {
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
            if (isProv && !confirm('Mark ' + k.toUpperCase() + ' FINAL? Coverage percentages become quotable and the PROVISIONAL badges disappear from the console.')) return;
            api('plan', { action: 'provisional', inst: k, value: !isProv })
              .then(function () { msg(k.toUpperCase() + ' is now ' + (isProv ? 'final' : 'provisional') + '.'); load(); })
              .catch(function (e) { msg(e.message, 'err'); });
          } })])
      ]);
    });
    view.textContent = '';
    view.appendChild(card('Plan status per instrument',
      'This flag drives the PROVISIONAL badges on the Overview and the dashboard coverage banner. Uploading a replacement plan still runs through the vault pipeline.',
      [tbl(['Form', 'Status', 'Meaning', ''], rows)]));
  }

  /* ----------------------------------------------------------------- audit */
  function renderAudit(entries) {
    var box = el('div', { class: 'audit' });
    if (!entries.length) box.appendChild(el('div', { class: 'muted', text: 'No administrative changes recorded yet.' }));
    entries.forEach(function (e) {
      var line = el('div', {});
      line.appendChild(el('span', { class: 'muted', text: (e.ts || '').replace('T', ' ').replace('Z', '') + '  ' }));
      line.appendChild(el('b', { text: e.actor || '?' }));
      line.appendChild(document.createTextNode('  ' + (e.action || '') + '  '));
      line.appendChild(el('span', { class: 'mono', text: e.target || '' }));
      var d = e.detail && Object.keys(e.detail).length ? '  ' + JSON.stringify(e.detail) : '';
      if (d) line.appendChild(el('span', { class: 'muted', text: d }));
      box.appendChild(line);
    });
    view.textContent = '';
    view.appendChild(card('Audit trail', 'Most recent 200 administrative actions, newest first.', [box]));
  }

  /* ------------------------------------------------------------------ boot */
  function tabs() {
    var bar = document.getElementById('admTabs');
    bar.textContent = '';
    TABS.forEach(function (t) {
      bar.appendChild(el('button', { class: state.tab === t[0] ? 'on' : '', text: t[1],
        onclick: function () { state.tab = t[0]; location.hash = t[0]; tabs(); load(); } }));
    });
    document.getElementById('admTitle').textContent =
      (TABS.filter(function (t) { return t[0] === state.tab; })[0] || ['', 'Admin'])[1];
    document.getElementById('admLead').textContent = LEAD[state.tab] || '';
  }
  function load() {
    busy();
    var t = state.tab;
    api(t).then(function (j) {
      if (t !== state.tab) return;
      if (t === 'activities') renderActivities(j.activities || []);
      else if (t === 'users') renderUsers(j.users || []);
      else if (t === 'alerts') renderAlerts(j.alerts || {});
      else if (t === 'plan') renderPlan(j);
      else if (t === 'audit') renderAudit(j.entries || []);
    }).catch(function (e) {
      view.textContent = '';
      view.appendChild(el('div', { class: 'msg err', text: e.message }));
    });
  }
  document.querySelectorAll('.sb-nav a[data-tab]').forEach(function (a) {
    a.onclick = function (ev) { ev.preventDefault(); state.tab = a.getAttribute('data-tab');
      location.hash = state.tab; tabs(); load(); };
  });
  var h = (location.hash || '').replace('#', '');
  if (TABS.some(function (t) { return t[0] === h; })) state.tab = h;
  tabs(); load();
})();
