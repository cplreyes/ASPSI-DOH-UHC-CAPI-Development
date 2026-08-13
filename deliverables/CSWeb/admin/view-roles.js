/* CAPI Console — Roles & permissions (E9-ADMIN-022).           Carl, 2026-08-09
 *
 * The 5 x 7 matrix. Read by anyone who administers users — you cannot sensibly
 * assign a role you are not allowed to look at — and written only by an owner,
 * because editing a role changes what every holder of it can reach. That is a
 * different act from moving one person between roles, and the UI says so.
 */
'use strict';
(function (C) {
  var el = C.el, card = C.card;

  var PERM_NOTE = {
    'case.view': 'Respondent-level detail.',
    'data.export': 'Bulk microdata. The widest grant on this page.',
    'admin.users': 'Can create, disable and re-role accounts.',
    'admin.system': 'Can change alerting, activities and the assignment plan.',
    'audit.view': 'Can read who did what, including data reads.'
  };

  function render(host) {
    C.apiAdmin('GET', '/roles').then(function (d) {
      host.textContent = '';
      host.appendChild(matrixCard(host, d));
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  function matrixCard(host, d) {
    var roles = d.roles || [];
    var keys = Object.keys(d.keys || {});
    var editable = !!d.editable;
    var floor = (d.floor && d.floor.owner) || [];

    var boxes = {};                            // role -> perm -> checkbox
    var table = el('table', { class: 'matrix' });

    // Subject on top, verb underneath: "MONITORING / view", not "VIEW /
    // monitoring". Reading a matrix means scanning the header row once, and
    // the thing being protected is what you are scanning for — leading with
    // the verb also puts two unrelated columns under an identical "ADMIN".
    var head = el('tr', {}, [el('th', { text: 'Role', style: 'text-align:left' })].concat(
      keys.map(function (k) {
        var part = k.split('.');
        return el('th', { title: k }, [
          el('div', { text: part[0] }),
          el('div', { class: 'mono hdr-verb', text: part[1] })
        ]);
      })));
    table.appendChild(el('thead', {}, [head]));

    var body = el('tbody', {});
    roles.forEach(function (r) {
      boxes[r.name] = {};
      var th = el('th', {}, [
        el('span', { text: r.label }),
        el('span', { class: 'k', text: r.name }),
        el('span', { class: 'k', text: C.fmt.count(r.user_count, 'account') + ' · v' + r.version })
      ]);
      var tr = el('tr', {}, [th].concat(keys.map(function (k) {
        var locked = (r.name === 'owner' && floor.indexOf(k) >= 0);
        var cb = C.inp({ type: 'checkbox', 'aria-label': r.label + ' — ' + k });
        cb.checked = (r.perms || []).indexOf(k) >= 0;
        cb.disabled = !editable || locked;
        if (locked) cb.title = 'The owner role must keep this, or nobody can administer the console.';
        boxes[r.name][k] = cb;
        cb.onchange = function () { refreshDirty(); };
        return el('td', locked ? { class: 'locked' } : {}, [cb]);
      })));
      body.appendChild(tr);

      if (r.other_perms && r.other_perms.length) {
        body.appendChild(el('tr', {}, [el('td', { colspan: keys.length + 1, class: 'muted',
          text: r.label + ' also holds keys this screen does not manage (' + r.other_perms.join(', ')
              + '). They are left untouched when you save.' })]));
      }
    });
    table.appendChild(body);

    function currentSet(name) {
      return Object.keys(boxes[name]).filter(function (k) { return boxes[name][k].checked; });
    }
    function dirtyRoles() {
      return roles.filter(function (r) {
        var now = currentSet(r.name).slice().sort();
        var was = (r.perms || []).slice().sort();
        return now.join('|') !== was.join('|');
      });
    }

    var save = el('button', { class: 'btn', text: 'Save changes', disabled: true });
    var reset = el('button', { class: 'btn sec', text: 'Discard', disabled: true,
      onclick: function () { C.busy(host); render(host); } });
    var count = el('span', { class: 'adm-count', text: '' });

    function refreshDirty() {
      var n = dirtyRoles().length;
      save.disabled = !n; reset.disabled = !n;
      count.textContent = n ? n + (n === 1 ? ' role changed' : ' roles changed') : '';
    }

    save.onclick = function () {
      var changed = dirtyRoles();
      C.confirmDestructive({
        title: 'Apply permission changes?',
        lead: 'Editing a role changes what every holder of it can reach.',
        confirmWord: 'apply', verb: 'Apply changes',
        preflight: function () {
          return Promise.resolve({ lines: changed.map(function (r) {
            var now = currentSet(r.name), was = r.perms || [];
            var added = now.filter(function (k) { return was.indexOf(k) < 0; });
            var removed = was.filter(function (k) { return now.indexOf(k) < 0; });
            return r.label + ': ' + (added.length ? '+' + added.join(', ') : '')
                 + (added.length && removed.length ? '  ' : '')
                 + (removed.length ? '−' + removed.join(', ') : '')
                 + '  — signs out ' + C.fmt.count(r.user_count, 'account') + ' holding it.';
          }) });
        },
        run: function () {
          // Sequential rather than parallel: each PUT bumps a role version and
          // the audit trail reads better in the order the operator saw them.
          return changed.reduce(function (p, r) {
            return p.then(function () {
              return C.apiAdmin('PUT', '/roles/' + encodeURIComponent(r.name) + '/perms',
                                { body: { perms: currentSet(r.name) } });
            });
          }, Promise.resolve());
        },
        done: function () {
          C.msg('Permissions updated for ' + C.fmt.count(changed.length, 'role') + '.', 'ok');
          C.busy(host); render(host);
        }
      });
    };

    var legend = el('div', { class: 'matrix-legend' }, [
      el('span', {}, [el('span', { class: 'sw', style: 'background:repeating-linear-gradient(45deg,#fdf7e8,#fdf7e8 4px,#fbf1d8 4px,#fbf1d8 8px)' }),
                      'Locked — the owner role cannot lose this']),
      el('span', {}, ['v = role version; every change bumps it and ends the sessions holding it'])
    ]);

    var notes = keys.filter(function (k) { return PERM_NOTE[k]; }).map(function (k) {
      return el('div', {}, [el('span', { class: 'mono', text: k }), ' — ', PERM_NOTE[k]]);
    });

    return card('Roles and permissions',
      editable
        ? 'Tick to grant. Saving a row bumps that role\'s version, which ends every live session holding it — '
          + 'so a permission you remove stops applying at once rather than at next sign-in.'
        : 'Read-only: only an owner can change what a role is allowed to do. You can still assign these roles '
          + 'to people from the Users screen.',
      [el('div', { class: 'adm-bar' }, [
         el('div', { class: 'right' }, [count, reset, editable ? save : null])
       ]),
       el('div', { class: 'matrix-wrap' }, [table]),
       legend,
       el('div', { class: 'muted', style: 'margin-top:14px;line-height:1.9' }, notes)]);
  }

  C.route('roles', {
    title: 'Roles & permissions',
    lead: 'What each role is allowed to reach. Permissions are granted to roles; roles are granted to people.',
    perm: 'admin.users',
    render: render
  });
})(window.CAPI);
