/* CAPI Console — Active sessions (E9-ADMIN-023).               Carl, 2026-08-09
 *
 * "Who is signed in right now, and can I end it." The capability the old
 * stateless cookie could not provide at all: its sign-out was browser-side, so
 * a captured cookie stayed valid for the full eight hours.
 *
 * The handle shown in each row is the stored SHA-256 of the session token, not
 * the token. An admin list of live sessions must not double as an admin list
 * of usable credentials.
 */
'use strict';
(function (C) {
  var el = C.el, td = C.td, card = C.card;

  function render(host) {
    C.apiAdmin('GET', '/sessions').then(function (d) {
      host.textContent = '';
      host.appendChild(body(host, d));
    }).catch(function (e) {
      host.textContent = '';
      host.appendChild(C.errorState(e, function () { C.render(); }));
    });
  }

  function agent(ua) {
    if (!ua) return 'unknown client';
    if (/CSEntry|CSPro/i.test(ua)) return 'CSEntry';
    if (/curl|wget|python/i.test(ua)) return ua.split(' ')[0];
    var m = /(Edg|Chrome|Firefox|Safari)\/[\d.]+/.exec(ua);
    var os = /Windows/.test(ua) ? 'Windows' : /Android/.test(ua) ? 'Android'
           : /iPhone|iPad/.test(ua) ? 'iOS' : /Mac OS/.test(ua) ? 'macOS'
           : /Linux/.test(ua) ? 'Linux' : '';
    return (m ? m[0].replace('Edg', 'Edge') : 'browser') + (os ? ' · ' + os : '');
  }

  function body(host, d) {
    var rows = (d.sessions || []).map(function (s) {
      var kill = el('button', {
        class: 'btn sec', text: s.is_self ? 'This is you' : 'End session',
        disabled: !!s.is_self,
        title: s.is_self ? 'Use Sign out in the sidebar to end your own session.' : '',
        onclick: function () { confirmKill(host, s); }
      });

      return el('tr', {}, [
        el('td', {}, [
          el('a', { href: '#/users/' + s.user_id, class: 'mono', text: s.username }),
          s.full_name ? el('div', { class: 'muted', text: s.full_name }) : null,
          s.is_self ? el('div', {}, [C.badge('this session', 'live')]) : null
        ]),
        td(el('span', {}, [
          el('div', { text: agent(s.user_agent) }),
          el('div', { class: 'mono muted', text: s.ip })
        ])),
        el('td', { class: 'muted', title: C.fmt.stamp(s.issued_at), text: C.fmt.ago(s.issued_at) }),
        el('td', { class: 'muted', title: C.fmt.stamp(s.last_seen_at), text: C.fmt.ago(s.last_seen_at) }),
        el('td', { class: 'muted', title: C.fmt.stamp(s.expires_at), text: C.fmt.stamp(s.expires_at).slice(5, 16) }),
        td(el('div', { class: 'rowacts' }, [kill]))
      ]);
    });

    var idle = Math.round((d.idle_secs || 3600) / 60);

    return card('Active sessions',
      'A session counts as live when it is unrevoked, inside its 12-hour ceiling, and has been used in the '
      + 'last ' + idle + ' minutes — the same three tests the gate applies on every request, so what you see '
      + 'here is what the front door would accept.',
      [el('div', { class: 'adm-bar' }, [
         el('div', { class: 'right' }, [
           el('span', { class: 'adm-count', text: C.fmt.count(d.count || 0, 'live session') }),
           el('button', { class: 'btn sec', text: 'Refresh', onclick: function () { C.busy(host); render(host); } })
         ])
       ]),
       C.tbl(['Account', 'Client', 'Signed in', 'Last seen', 'Expires', ''], rows,
             { emptyText: 'Nobody is signed in right now.' }),
       el('p', { class: 'muted', style: 'margin-top:12px', text:
         'Ending a session takes effect on that account\'s very next request — there is no cache to wait for '
         + 'and no restart involved.' })]);
  }

  function confirmKill(host, s) {
    C.confirmDestructive({
      title: 'End this session for ' + s.username + '?',
      lead: 'Signs out this one client. Other sessions the account holds are untouched, and the password '
          + 'is unchanged, so they can sign back in.',
      confirmWord: s.username, verb: 'End session',
      preflight: function () {
        return Promise.resolve({ lines: [
          'Client: ' + agent(s.user_agent) + ' at ' + s.ip + '.',
          'Signed in ' + C.fmt.ago(s.issued_at) + ', last seen ' + C.fmt.ago(s.last_seen_at) + '.'
        ] });
      },
      run: function () { return C.apiAdmin('DELETE', '/sessions/' + encodeURIComponent(s.sid)); },
      done: function (r) {
        C.msg(r.revoked ? 'Session ended for ' + r.username + '.'
                        : 'That session had already ended.', 'ok');
        C.busy(host); render(host);
      }
    });
  }

  C.route('sessions', {
    title: 'Active sessions',
    lead: 'Everyone signed in to the console right now, and the button that ends it.',
    perm: 'admin.users',
    render: render
  });
})(window.CAPI);
