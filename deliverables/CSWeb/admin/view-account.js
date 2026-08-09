/* CAPI Console — My account (E9-ADMIN-025).                    Carl, 2026-08-09
 *
 * Self-service. Small on purpose: the password change itself lives at
 * /docs/idp/change-password, which is the flow that is already deployed,
 * tested end-to-end, and — critically — the only route that stays reachable
 * while an account still owes a password change. Re-implementing it here would
 * create a second codepath through the one screen a locked-out person needs.
 */
'use strict';
(function (C) {
  var el = C.el, card = C.card;

  var PERM_LABEL = {
    'monitoring.view': 'See the sync dashboard, map and feed',
    'case.view': 'Open an individual respondent case',
    'data.export': 'Download microdata and exports',
    'tabulations.view': 'View the tabulation tables',
    'admin.users': 'Administer console accounts',
    'admin.system': 'Change alerting, activities and the plan',
    'audit.view': 'Read the audit trail'
  };

  function render(host) {
    C.me(true).then(function (m) {
      host.textContent = '';
      if (!m || !m.signed_in) {
        host.appendChild(C.errorState(new Error('You are not signed in.')));
        return;
      }
      host.appendChild(identityCard(m));
      host.appendChild(sessionsCard(host, m));
      host.appendChild(mfaCard());
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  function identityCard(m) {
    var kv = el('dl', { class: 'adm-kv' });
    function row(k, v) {
      kv.appendChild(el('dt', { text: k }));
      kv.appendChild(el('dd', {}, [typeof v === 'string' ? document.createTextNode(v) : v]));
    }
    row('Signed in as', el('span', { class: 'mono', text: m.user }));
    row('Roles', el('span', {}, (m.roles || []).map(function (r, i) {
      return el('span', {}, [i ? ' ' : '', C.pill(r.replace(/_/g, ' '), r)]);
    })));

    var perms = el('div', {}, (m.perms || []).slice().sort().map(function (p) {
      return el('div', { style: 'margin:3px 0' }, [
        el('span', { class: 'mono', text: p }),
        el('span', { class: 'muted', text: '  ' + (PERM_LABEL[p] || '') })
      ]);
    }));
    row('You may', (m.perms && m.perms.length) ? perms : el('span', { class: 'muted', text: 'nothing yet' }));

    var actions = el('div', { class: 'adm-f', style: 'margin-top:16px' }, [
      el('a', { class: 'btn', href: '/docs/idp/change-password?next='
                + encodeURIComponent('/docs/admin/#/account'), text: 'Change my password' }),
      el('a', { class: 'btn sec', href: '/docs/idp/logout', text: 'Sign out' })
    ]);

    var warn = m.must_change
      ? el('div', { class: 'msg warn', text: 'This account is still on its setup password. Change it now — '
          + 'until you do, the admin tools refuse every request from it.' })
      : null;

    return card('My account', 'What the identity provider knows about you, and what that entitles you to reach.',
      [warn, kv, actions]);
  }

  /**
   * Your own live sessions. Uses the admin endpoint filtered to yourself,
   * which is honest about the permission it needs rather than pretending a
   * self-service route exists that does not.
   */
  function sessionsCard(host, m) {
    if (!C.can('admin.users')) {
      return card('My sessions',
        'Listing sessions needs the admin.users permission, which this account does not hold. '
        + 'Signing out ends the session you are using right now.', []);
    }

    var holder = el('div', {}, [el('div', { class: 'spin', text: 'Loading your sessions…' })]);

    C.apiAdmin('GET', '/users?q=' + encodeURIComponent(m.user)).then(function (d) {
      var me = (d.users || []).filter(function (u) { return u.username === m.user; })[0];
      if (!me) { holder.textContent = ''; holder.appendChild(el('p', { class: 'muted', text: 'No record found.' })); return; }
      return C.apiAdmin('GET', '/sessions?user_id=' + me.id).then(function (s) {
        holder.textContent = '';
        var rows = (s.sessions || []).map(function (x) {
          return el('tr', {}, [
            C.td(el('span', { class: 'mono', text: x.ip })),
            el('td', { class: 'muted', text: x.user_agent || 'unknown client' }),
            el('td', { class: 'muted', title: C.fmt.stamp(x.issued_at), text: C.fmt.ago(x.issued_at) }),
            C.td(x.is_self ? C.badge('this one', 'live') : el('span', { class: 'muted', text: '—' }))
          ]);
        });
        holder.appendChild(C.tbl(['IP', 'Client', 'Signed in', ''], rows,
                                 { emptyText: 'No live session — which is odd, since you are reading this.' }));
        if ((s.sessions || []).length > 1) {
          holder.appendChild(el('p', { class: 'muted', style: 'margin-top:10px', text:
            'More than one session is open. If you do not recognise one, end it from Active sessions '
            + 'and change your password.' }));
        }
      });
    }).catch(function (e) {
      holder.textContent = '';
      holder.appendChild(el('div', { class: 'msg err', text: e.message }));
    });

    return card('My sessions', 'Every client currently signed in as you.', [holder]);
  }

  /** Placeholder, deliberately inert until E9-ADMIN-042 ships. */
  function mfaCard() {
    return card('Two-factor authentication',
      'Not enabled yet. When it ships it will be required for owners, programme admins, and anyone who can '
      + 'export microdata.',
      [el('div', { class: 'adm-f' }, [
         el('button', { class: 'btn sec', text: 'Set up authenticator app', disabled: true,
                        title: 'Not built yet — tracked as E9-ADMIN-042.' }),
         el('span', { class: 'muted', text:
           'A second owner with their own device has to exist before this can be enforced, or a lost phone '
           + 'means an SSH session as root is the only way back in.' })
       ])]);
  }

  C.route('account', {
    title: 'My account',
    lead: 'Your identity, your permissions, and the sessions open in your name.',
    render: render
  });
})(window.CAPI);
