/* CAPI Console — Users & access (E9-ADMIN-021).                Carl, 2026-08-09
 *
 * The screen the module exists for. Everything here reads and writes
 * console_users through /docs/idp/admin — the store the gate consults — so
 * that "disabled" on this page and "refused" at the front door are the same
 * fact rather than two hopes.
 *
 * No optimistic UI anywhere below. Every mutation is followed by a re-read.
 */
'use strict';
(function (C) {
  var el = C.el, td = C.td, card = C.card, inp = C.inp, sel = C.sel, field = C.field;

  var ROLE_HELP = {
    owner: 'Everything, including roles and permissions.',
    programme_admin: 'Onboard and offboard staff; all console surfaces.',
    analyst: 'Monitoring, cases, tabulations and the data room.',
    field_supervisor: 'Monitoring, cases and tabulations. No bulk export.',
    client_viewer: 'Monitoring and tabulations only. No respondent detail.'
  };

  function rolePills(roles) {
    if (!roles || !roles.length) return el('span', { class: 'pillt none', text: 'no role' });
    return el('span', {}, roles.map(function (r, i) {
      return el('span', {}, [i ? ' ' : '', C.pill(r.replace(/_/g, ' '), r)]);
    }));
  }

  function statusBadge(u) {
    if (u.status !== 'active') return C.badge('disabled', 'off');
    if (u.locked_until || u.locked) return C.badge('locked out', 'bad');
    if (u.must_change) return C.badge('setup password', 'soon');
    return C.badge('active', 'live');
  }

  /* ------------------------------------------------------------ list view */

  var filters = { q: '', status: '', role: '' };

  function renderList(host) {
    var qs = [];
    if (filters.q) qs.push('q=' + encodeURIComponent(filters.q));
    if (filters.status) qs.push('status=' + encodeURIComponent(filters.status));
    if (filters.role) qs.push('role=' + encodeURIComponent(filters.role));

    Promise.all([
      C.apiAdmin('GET', '/users' + (qs.length ? '?' + qs.join('&') : '')),
      // Drift is only knowable by comparing the two stores, and only the
      // legacy endpoint can see .htpasswd. Failure here is not fatal — the
      // account list is authoritative on its own.
      C.apiConsole('users').catch(function () { return null; })
    ]).then(function (r) {
      var d = r[0], legacy = r[1];
      host.textContent = '';
      host.appendChild(driftCard(legacy));
      host.appendChild(listCard(host, d));
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  /**
   * Drift between console_users and .htpasswd while both still exist.
   * `blocking` names the side that costs somebody access right now, which
   * flips at cutover — so the card says which direction is dangerous today
   * instead of leaving the reader to work it out.
   */
  function driftCard(legacy) {
    if (!legacy || !legacy.drift) return document.createDocumentFragment();
    var d = legacy.drift;
    var ht = d.htpasswd_only || [], cn = d.console_only || [];

    if (!ht.length && !cn.length) {
      return card('Store drift', 'The gate currently reads: ' + (d.gate || 'unknown') + '.',
        [el('div', { class: 'msg ok', text:
          'Both stores list exactly the same accounts. Nothing loses access when the gate is cut over.' })]);
    }
    var kids = [];
    if (ht.length) kids.push(el('div', { class: 'msg ' + (d.blocking === 'htpasswd_only' ? 'err' : 'warn'),
      text: 'In .htpasswd only — ' + (d.gate === 'idp'
        ? 'these have already lost console access: ' : 'these lose console access at cutover: ') + ht.join(', ') }));
    if (cn.length) kids.push(el('div', { class: 'msg ' + (d.blocking === 'console_only' ? 'err' : 'warn'),
      text: 'In console_users only — these exist but cannot sign in until cutover: ' + cn.join(', ') }));
    return card('Store drift', 'The gate currently reads: ' + (d.gate || 'unknown') + '.', kids);
  }

  function listCard(host, d) {
    var users = d.users || [];
    var roles = d.roles || [];

    var q = inp({ type: 'search', value: filters.q, placeholder: 'name, username or email', size: 22 });
    var st = sel('status', [['', 'any status'], ['active', 'active'], ['disabled', 'disabled']], filters.status);
    var rl = sel('role', [['', 'any role']].concat(roles.map(function (r) { return [r.name, r.label]; })), filters.role);

    function apply() {
      filters.q = q.value.trim(); filters.status = st.value; filters.role = rl.value;
      C.busy(host); renderList(host);
    }
    q.onkeydown = function (ev) { if (ev.key === 'Enter') apply(); };
    st.onchange = apply; rl.onchange = apply;

    var bar = el('div', { class: 'adm-bar' }, [
      field('Search', q), field('Status', st), field('Role', rl),
      el('button', { class: 'btn sec', text: 'Apply', onclick: apply }),
      el('div', { class: 'right' }, [
        el('span', { class: 'adm-count', text: C.fmt.count(users.length, 'account') }),
        el('button', { class: 'btn', text: '+ Add account', onclick: function () { openCreate(host, roles); } })
      ])
    ]);

    // The username is the link — there is no separate "Open" column. A row in
    // a dense operational table should not need a button to say the obvious,
    // and the extra column pushed the control away from the name it acted on.
    var rows = users.map(function (u) {
      var marks = [];
      if (u.protected) marks.push(C.badge('break-glass', 'soon'));
      if (u.duplicate) marks.push(C.badge('duplicate', 'soon'));

      var name = el('td', {}, [
        el('div', { class: 'u-line' }, [
          el('a', { href: '#/users/' + u.id, class: 'mono', text: u.username })
        ].concat(marks)),
        u.full_name ? el('div', { class: 'muted', text: u.full_name }) : null
      ]);

      return el('tr', {}, [
        name,
        td(rolePills(u.roles)),
        td(statusBadge(u)),
        el('td', { class: 'num', text: u.live_sessions ? String(u.live_sessions) : '·' }),
        td(el('span', { class: 'mono', text: u.pw_algo })),
        el('td', { class: 'muted', title: C.fmt.stamp(u.last_login_at), text: C.fmt.ago(u.last_login_at) })
      ]);
    });

    var dupNote = users.some(function (u) { return u.duplicate; })
      ? el('p', { class: 'muted', text: 'Accounts marked "duplicate" differ from another only by _ versus -. '
          + 'Compare their sign-in history before disabling either — the two spellings may be two different '
          + 'people, and guessing hands one of them the other\'s access.' })
      : null;

    return card('Console accounts',
      'Read from the identity provider. "Sessions" counts sign-ins live right now; "Hash" shows apr1 '
      + 'for accounts still on their imported password, which upgrades to argon2id the next time they sign in.',
      [bar, dupNote,
       C.tbl(['User', 'Roles', 'Status', 'Sessions', 'Hash', 'Last sign-in'], rows,
             { emptyText: 'No account matches those filters.' })]);
  }

  /* ---------------------------------------------------------- create flow */

  function roleChecklist(roles, selected, disableOwner) {
    var boxes = {};
    var wrap = el('div', { class: 'adm-kv', role: 'group', 'aria-label': 'Roles' });
    roles.forEach(function (r) {
      var cb = inp({ type: 'checkbox' });
      cb.checked = (selected || []).indexOf(r.name) >= 0;
      if (r.name === 'owner' && disableOwner) { cb.disabled = true; cb.title = 'Only an owner can grant the owner role.'; }
      boxes[r.name] = cb;
      wrap.appendChild(el('dt', {}, [el('label', { style: 'flex-direction:row;gap:8px;align-items:center;text-transform:none;letter-spacing:0;font-size:13px' },
        [cb, el('span', { text: r.label })])]));
      wrap.appendChild(el('dd', { class: 'muted', text: ROLE_HELP[r.name] || '' }));
    });
    return { node: wrap, value: function () {
      return Object.keys(boxes).filter(function (k) { return boxes[k].checked; });
    } };
  }

  function openCreate(host, roles) {
    var u = inp({ placeholder: 'se-008', autocapitalize: 'none', spellcheck: 'false', size: 18 });
    var n = inp({ placeholder: 'Juana dela Cruz', size: 24 });
    var m = inp({ type: 'email', placeholder: 'optional', size: 24 });
    var rc = roleChecklist(roles, ['field_supervisor'], !C.isOwner());
    var err = el('div', {});

    var save = el('button', { class: 'btn', text: 'Create account' });
    var cancel = el('button', { class: 'btn sec', text: 'Cancel' });
    var dlg = C.modal({
      title: 'Add a console account',
      lead: 'A temporary password is generated and shown once. The account must change it at first sign-in.',
      body: [err, el('div', { class: 'adm-f' }, [
               field('Username', u, 'lowercase; letters, digits, . _ -'),
               field('Full name', n), field('Email', m)]),
             el('h4', { style: 'margin:14px 0 6px;font-size:13px', text: 'Roles' }), rc.node],
      actions: [cancel, save]
    });
    cancel.onclick = function () { dlg.close(); };
    setTimeout(function () { u.focus(); }, 30);

    // One key per dialog, not per click: a double-click must not mint two
    // accounts, and must not mint a second temporary password for the first.
    var idem = C.newIdemKey();

    save.onclick = function () {
      err.textContent = '';
      save.disabled = true; save.textContent = 'Creating…';
      C.apiAdmin('POST', '/users', {
        idem: idem,
        body: { username: u.value.trim().toLowerCase(), full_name: n.value.trim(),
                email: m.value.trim(), roles: rc.value() }
      }).then(function (d) {
        dlg.close();
        showCredential('Account created', d.username, d.temp_password, d.gate_notice);
        C.busy(host); renderList(host);
      }).catch(function (e) {
        save.disabled = false; save.textContent = 'Create account';
        err.appendChild(el('div', { class: 'msg err', text: e.message }));
        if (e.field === 'username') { u.setAttribute('aria-invalid', 'true'); u.focus(); }
      });
    };
  }

  /**
   * A credential is shown exactly once — only its argon2id hash was stored, so
   * there is no "show it again". Says so plainly rather than letting the admin
   * find out by closing the dialog.
   */
  function showCredential(title, username, password, gateNotice) {
    var done = el('button', { class: 'btn', text: 'I have copied it' });
    var copy = el('button', { class: 'btn sec', text: 'Copy' });
    var body = [
      el('p', {}, ['Temporary password for ', el('b', { text: username }), ':']),
      el('div', { class: 'cred', text: password }),
      el('p', { class: 'muted', style: 'margin-top:10px', text:
        'This is the only time it is shown — the server kept only its hash. If it is lost, '
        + 'reset the password again rather than looking it up.' })
    ];
    if (gateNotice) body.push(el('div', { class: 'msg warn', style: 'margin-top:12px', text: gateNotice }));

    var m = C.modal({ title: title, body: body, actions: [copy, done] });
    done.onclick = function () { m.close(); };
    copy.onclick = function () {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(password).then(function () { copy.textContent = 'Copied'; },
                                                     function () { copy.textContent = 'Select it manually'; });
      } else { copy.textContent = 'Select it manually'; }
    };
  }

  /* ---------------------------------------------------------- detail view */

  function renderDetail(host, id) {
    C.apiAdmin('GET', '/users/' + id).then(function (d) {
      host.textContent = '';
      host.appendChild(detail(host, d.user, d.roles || []));
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  function reload(host, id) { C.busy(host); renderDetail(host, id); }

  function detail(host, u, roles) {
    var me = C.whoami() || {};
    var isSelf = (u.username === me.user);
    var owner = C.isOwner();
    var wrap = el('div', { class: 'adm-split two' });

    /* ---- left: the record ---- */
    var kv = el('dl', { class: 'adm-kv' });
    function row(k, v) {
      kv.appendChild(el('dt', { text: k }));
      kv.appendChild(el('dd', {}, [typeof v === 'string' ? document.createTextNode(v) : v]));
    }
    row('Username', el('span', { class: 'mono', text: u.username }));
    row('Full name', u.full_name || '—');
    row('Email', u.email || '—');
    row('Roles', rolePills(u.roles));
    row('Status', statusBadge(u));
    row('Live sessions', el('span', {}, [
      el('b', { text: String(u.live_sessions) }),
      u.live_sessions ? el('span', {}, [' · ', el('a', { href: '#/sessions', text: 'view sessions' })]) : null
    ]));
    row('Password', el('span', {}, [
      el('span', { class: 'mono', text: u.pw_algo }),
      u.pw_algo === 'apr1' ? el('span', { class: 'muted', text: '  (imported; upgrades on next sign-in)' }) : null,
      u.must_change ? el('div', {}, [C.badge('must change at next sign-in', 'soon')]) : null
    ]));
    row('Last sign-in', u.last_login_at ? C.fmt.stamp(u.last_login_at) : 'never');
    row('Password set', u.pw_changed_at ? C.fmt.stamp(u.pw_changed_at) : '—');
    if (u.locked_until) row('Locked until', C.fmt.stamp(u.locked_until));
    row('Created', C.fmt.stamp(u.created_at) + (u.created_by ? ' by ' + u.created_by : ''));
    if (u.updated_at) row('Last change', C.fmt.stamp(u.updated_at) + (u.updated_by ? ' by ' + u.updated_by : ''));
    row('Record version', el('span', { class: 'mono', text: String(u.row_version) }));

    var back = el('div', { class: 'adm-f' }, [
      el('button', { class: 'btn sec', text: '← All accounts', onclick: function () { C.go('users'); } })
    ]);

    var left = card(u.username, u.protected
      ? 'Break-glass account. It cannot be disabled here — that is deliberate, so a mistake on this screen '
        + 'cannot lock everyone out.'
      : 'Everything the identity provider knows about this account.', [back, kv]);

    /* ---- right: what you can do ---- */
    var acts = [];

    acts.push(el('button', { class: 'btn sec', text: 'Edit name and email',
      onclick: function () { openEdit(host, u); } }));

    acts.push(el('button', {
      class: 'btn sec', text: 'Change roles',
      disabled: isSelf || (!owner && (u.roles || []).indexOf('owner') >= 0),
      title: isSelf ? 'You cannot change your own roles. Ask another owner.'
           : (!owner && (u.roles || []).indexOf('owner') >= 0) ? 'Only an owner can change an owner.' : '',
      onclick: function () { openRoles(host, u, roles); }
    }));

    acts.push(el('button', { class: 'btn sec', text: 'Reset password',
      onclick: function () { confirmReset(host, u); } }));

    acts.push(el('button', {
      class: 'btn sec', text: 'Sign out everywhere',
      disabled: !u.live_sessions,
      title: u.live_sessions ? '' : 'This account has no live session.',
      onclick: function () { confirmForceLogout(host, u); }
    }));

    if (u.locked_until) {
      acts.push(el('button', { class: 'btn sec', text: 'Clear lockout',
        onclick: function () { patch(host, u, { locked: false }, 'Lockout cleared.'); } }));
    }

    // Visual break before the destructive action. Without it "Sign out
    // everywhere" and "Disable account" sit flush, and the two differ by one
    // mis-aimed click and an account that can no longer work.
    if (u.status === 'active') {
      acts.push(el('hr', { class: 'act-sep' }));
      acts.push(el('button', {
        class: 'btn danger', text: 'Disable account',
        disabled: isSelf || u.protected,
        title: isSelf ? 'You cannot disable your own account. Ask another owner.'
             : u.protected ? 'Break-glass accounts cannot be disabled here.' : '',
        onclick: function () { confirmDisable(host, u); }
      }));
    } else {
      acts.push(el('button', { class: 'btn', text: 'Re-enable account',
        onclick: function () { patch(host, u, { status: 'active' }, 'Account re-enabled.'); } }));
    }

    var notes = [];
    if (isSelf) notes.push('This is your own account, so the actions that could lock you out are disabled. '
      + 'Another owner can perform them.');
    if (u.impact && u.impact.is_last_owner) notes.push('This is the last active owner. Disabling it or removing '
      + 'the owner role is refused by the server, not just hidden here.');
    if (u.dup_group) {
      notes.push('If another account differs from this one only by _ versus -, compare their sign-in history '
        + 'before disabling either.');
    }

    var right = card('Actions', null, [
      el('div', { class: 'rowacts', style: 'flex-direction:column;align-items:stretch;gap:8px' }, acts)
    ].concat(notes.map(function (t) { return el('p', { class: 'muted', style: 'margin-top:10px', text: t }); })));

    wrap.appendChild(left);
    wrap.appendChild(right);
    return wrap;
  }

  /* --------------------------------------------------------- mutations */

  function patch(host, u, body, okMsg) {
    body.row_version = u.row_version;
    C.apiAdmin('PATCH', '/users/' + u.id, { body: body }).then(function () {
      C.msg(okMsg, 'ok');
      reload(host, u.id);                       // re-read; never repaint from hope
    }).catch(function (e) {
      C.msg(e.message, 'err');
      if (e.code === 'conflict') reload(host, u.id);
    });
  }

  function openEdit(host, u) {
    var n = inp({ value: u.full_name || '', size: 24 });
    var m = inp({ type: 'email', value: u.email || '', size: 24 });
    var err = el('div', {});
    var save = el('button', { class: 'btn', text: 'Save' });
    var cancel = el('button', { class: 'btn sec', text: 'Cancel' });
    var dlg = C.modal({
      title: 'Edit ' + u.username, body: [err, el('div', { class: 'adm-f' }, [field('Full name', n), field('Email', m)])],
      actions: [cancel, save]
    });
    cancel.onclick = function () { dlg.close(); };
    save.onclick = function () {
      save.disabled = true; save.textContent = 'Saving…';
      C.apiAdmin('PATCH', '/users/' + u.id, {
        body: { full_name: n.value.trim(), email: m.value.trim(), row_version: u.row_version }
      }).then(function () { dlg.close(); C.msg('Saved.', 'ok'); reload(host, u.id); })
        .catch(function (e) {
          save.disabled = false; save.textContent = 'Save';
          err.textContent = ''; err.appendChild(el('div', { class: 'msg err', text: e.message }));
        });
    };
  }

  function openRoles(host, u, roles) {
    var rc = roleChecklist(roles, u.roles, !C.isOwner());
    var err = el('div', {});
    var save = el('button', { class: 'btn', text: 'Save roles' });
    var cancel = el('button', { class: 'btn sec', text: 'Cancel' });
    var dlg = C.modal({
      title: 'Roles for ' + u.username,
      lead: 'Saving replaces the full set. Any live session this account holds is signed out, because a role '
          + 'change that leaves the old session running is not a role change.',
      body: [err, rc.node], actions: [cancel, save]
    });
    cancel.onclick = function () { dlg.close(); };
    save.onclick = function () {
      save.disabled = true; save.textContent = 'Saving…';
      C.apiAdmin('PUT', '/users/' + u.id + '/roles', {
        body: { roles: rc.value(), row_version: u.row_version }
      }).then(function (d) {
        dlg.close();
        C.msg(d.changed
          ? 'Roles updated. ' + C.fmt.count(d.revoked_sessions, 'session') + ' signed out.'
          : 'No change — that is already the role set.', 'ok');
        reload(host, u.id);
      }).catch(function (e) {
        save.disabled = false; save.textContent = 'Save roles';
        err.textContent = ''; err.appendChild(el('div', { class: 'msg err', text: e.message }));
      });
    };
  }

  function confirmReset(host, u) {
    var idem = C.newIdemKey();
    C.confirmDestructive({
      title: 'Reset the password for ' + u.username + '?',
      lead: 'A new temporary password is generated and shown once. The account must change it at next sign-in.',
      confirmWord: u.username, verb: 'Reset password',
      preflight: function () {
        return C.apiAdmin('GET', '/users/' + u.id).then(function (d) {
          return { lines: [
            'Signs out ' + C.fmt.count(d.user.impact.live_sessions, 'live session') + '.',
            'The current password stops working immediately.'
          ] };
        });
      },
      run: function () { return C.apiAdmin('POST', '/users/' + u.id + '/password', { idem: idem }); },
      done: function (d) {
        showCredential('Password reset', d.username, d.temp_password, d.gate_notice);
        reload(host, u.id);
      }
    });
  }

  function confirmForceLogout(host, u) {
    var idem = C.newIdemKey();
    C.confirmDestructive({
      title: 'Sign ' + u.username + ' out everywhere?',
      lead: 'Ends every session this account holds. The password is unchanged, so they can sign back in.',
      confirmWord: u.username, verb: 'Sign out everywhere',
      preflight: function () {
        return C.apiAdmin('GET', '/users/' + u.id).then(function (d) {
          return { lines: ['Ends ' + C.fmt.count(d.user.impact.live_sessions, 'live session') + '.'] };
        });
      },
      run: function () { return C.apiAdmin('POST', '/users/' + u.id + '/logout', { idem: idem }); },
      done: function (d) {
        C.msg(C.fmt.count(d.revoked_sessions, 'session') + ' ended.', 'ok');
        reload(host, u.id);
      }
    });
  }

  function confirmDisable(host, u) {
    C.confirmDestructive({
      title: 'Disable ' + u.username + '?',
      lead: 'The account keeps its history and audit trail — disabling is how an account is removed here, '
          + 'because a hard delete would orphan the rows that record what it did.',
      confirmWord: u.username, verb: 'Disable account',
      preflight: function () {
        return C.apiAdmin('GET', '/users/' + u.id).then(function (d) {
          var im = d.user.impact;
          var lines = [
            'Signs out ' + C.fmt.count(im.live_sessions, 'live session') + ' immediately.',
            'Blocks sign-in until the account is re-enabled.'
          ];
          var blocked = null;
          if (im.is_self) blocked = 'This is your own account. Ask another owner.';
          else if (im.is_protected) blocked = 'This is a break-glass account and cannot be disabled here.';
          else if (im.is_last_owner) blocked = 'This is the last active owner — the server will refuse.';
          return { lines: lines, blocked: blocked };
        });
      },
      run: function () { return C.apiAdmin('DELETE', '/users/' + u.id); },
      done: function (d) {
        C.msg('Disabled ' + d.username + '. ' + C.fmt.count(d.revoked_sessions, 'session') + ' signed out.', 'ok');
        reload(host, u.id);
      }
    });
  }

  /* ---------------------------------------------------------------- route */

  C.route('users', {
    title: 'Users & access',
    lead: 'Console accounts, their roles, and the sessions they hold. Changes take effect at the gate '
        + 'immediately — disabling an account ends its sessions in the same transaction.',
    perm: 'admin.users',
    render: function (host, params) {
      if (params && params[0]) renderDetail(host, params[0]);
      else renderList(host);
    }
  });
})(window.CAPI);
