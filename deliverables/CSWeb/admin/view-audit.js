/* CAPI Console — Audit trail (E9-ADMIN-024).                   Carl, 2026-08-09
 *
 * Answers "who looked at what". Append-only by construction: there is no write
 * path on this screen or behind it.
 *
 * Paging is by cursor, not page number. The table gains a row per protected
 * request after cutover, and offset paging over something that grows while you
 * read it either skips rows or repeats them — in an audit trail, both are
 * worse than being slow.
 */
'use strict';
(function (C) {
  var el = C.el, td = C.td, card = C.card, inp = C.inp, sel = C.sel, field = C.field;

  var f = { actor: '', verb: '', target: '', from: '', to: '' };
  var cursor = null, rowsSoFar = [];

  /* Verbs grouped so a reader can tell a data read from a config change
     without memorising the vocabulary. */
  var VERB_KIND = {
    'login': 'live', 'logout': 'off', 'login.fail': 'bad', 'perm.deny': 'bad',
    'password.change': 'soon', 'password.change.fail': 'bad',
    'user.create': 'live', 'user.update': 'soon', 'user.disable': 'bad',
    'user.roles': 'soon', 'user.password.reset': 'soon', 'user.forcelogout': 'bad',
    'role.perms': 'bad', 'session.kill': 'bad', 'audit.export': 'soon',
    'user.import': 'off', 'error': 'bad', 'rehash.fail': 'bad'
  };

  function qs() {
    var p = [];
    Object.keys(f).forEach(function (k) { if (f[k]) p.push(k + '=' + encodeURIComponent(f[k])); });
    return p;
  }

  function render(host) {
    cursor = null; rowsSoFar = [];
    load(host, true);
  }

  function load(host, fresh) {
    var p = qs();
    p.push('limit=50');
    if (cursor) p.push('before_id=' + cursor);

    C.apiAdmin('GET', '/audit?' + p.join('&')).then(function (d) {
      rowsSoFar = fresh ? (d.entries || []) : rowsSoFar.concat(d.entries || []);
      cursor = d.next_before;
      host.textContent = '';
      host.appendChild(body(host, d));
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  function body(host, d) {
    var a = inp({ value: f.actor, placeholder: 'username', size: 14 });
    var v = inp({ value: f.verb, placeholder: 'login, or user. for the family', size: 18 });
    var t = inp({ value: f.target, placeholder: 'account or path', size: 16 });
    var d1 = inp({ type: 'date', value: f.from });
    var d2 = inp({ type: 'date', value: f.to });

    function apply() {
      f.actor = a.value.trim(); f.verb = v.value.trim(); f.target = t.value.trim();
      f.from = d1.value; f.to = d2.value;
      C.busy(host); render(host);
    }
    [a, v, t].forEach(function (i) { i.onkeydown = function (ev) { if (ev.key === 'Enter') apply(); }; });
    d1.onchange = apply; d2.onchange = apply;

    function clear() {
      Object.keys(f).forEach(function (k) { f[k] = ''; });
      C.busy(host); render(host);
    }

    // Same filters, same rows: the export must be what the operator is looking
    // at. Two filter implementations is how an export quietly widens scope.
    var csv = el('a', { class: 'btn sec', href: '/docs/idp/admin/audit.csv' + (qs().length ? '?' + qs().join('&') : ''),
                        text: 'Export CSV' });

    var bar = el('div', { class: 'adm-bar' }, [
      field('Actor', a), field('Verb', v), field('Target', t),
      field('From', d1), field('To', d2),
      el('button', { class: 'btn sec', text: 'Apply', onclick: apply }),
      el('button', { class: 'btn link', text: 'Clear', onclick: clear }),
      el('div', { class: 'right' }, [
        el('span', { class: 'adm-count', text: rowsSoFar.length + (d.has_more ? '+' : '') + ' entries' }),
        csv
      ])
    ]);

    var rows = rowsSoFar.map(function (e) {
      var detail = e.detail && Object.keys(e.detail).length
        ? el('details', {}, [el('summary', { class: 'muted', text: 'detail' }),
             el('pre', { class: 'mono', style: 'white-space:pre-wrap;margin-top:4px',
                         text: JSON.stringify(e.detail, null, 1) })])
        : null;

      return el('tr', {}, [
        el('td', { class: 'mono', title: C.fmt.stamp(e.ts), text: C.fmt.stamp(e.ts).slice(0, 19) }),
        td(el('a', { href: '#/audit', class: 'mono', text: e.actor || '—',
                     onclick: function (ev) { ev.preventDefault(); f.actor = e.actor; C.busy(host); render(host); } })),
        td(C.badge(e.verb, VERB_KIND[e.verb] || '')),
        td(el('span', { class: 'mono', text: e.target || '—' })),
        el('td', { class: 'mono muted', text: e.ip || '—' }),
        td(detail || el('span', { class: 'muted', text: '—' }))
      ]);
    });

    var more = d.has_more
      ? el('div', { class: 'adm-f', style: 'margin-top:14px;justify-content:center' }, [
          el('button', { class: 'btn sec', text: 'Load 50 more', onclick: function () { load(host, false); } })])
      : el('p', { class: 'muted', style: 'margin-top:12px;text-align:center',
                  text: rowsSoFar.length ? 'That is the whole trail for these filters.' : '' });

    return card('Audit trail',
      'Sign-ins, permission denials, every account change, and — after cutover — every read of respondent '
      + 'data. Append-only: nothing on this screen or behind it can edit a row.',
      [bar,
       C.tbl(['When (UTC)', 'Actor', 'Action', 'Target', 'IP', ''], rows,
             { emptyText: 'No entry matches those filters.' }),
       more]);
  }

  C.route('audit', {
    title: 'Audit trail',
    lead: 'Who did what, when, and from where. Filter it, then export exactly what you filtered.',
    perm: 'audit.view',
    render: render
  });
})(window.CAPI);
