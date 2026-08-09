/* CAPI Console — admin portal UI kit (E9-ADMIN-020).          Carl, 2026-08-09
 *
 * Shared primitives for every admin screen: DOM building, the two API clients,
 * the hash router, and the destructive-action dialog. Vanilla JS, classic
 * script, no build step — the box has no toolchain, and DESIGN.md §6 settled
 * that rather than committing dist/ assets to a copy-to-box deploy.
 *
 * TWO RULES THIS FILE EXISTS TO ENFORCE
 *
 * 1. Nothing from an API is ever interpolated as HTML. el() writes through
 *    textContent; there is no innerHTML anywhere in the admin app. A username
 *    is operator-supplied data displayed to other operators, which is exactly
 *    the shape of a stored-XSS bug.
 *
 * 2. No optimistic UI on a security write. A row does not change appearance
 *    because a request was sent — it changes because the server was re-read.
 *    An admin who sees "disabled" must be looking at the store's answer, not
 *    at the client's hope. That is the same defect class the whole identity
 *    migration exists to remove.
 */
'use strict';
window.CAPI = (function () {
  var CAPI = {};

  /* ------------------------------------------------------------------ DOM */

  /** el('div', {class,text,onclick,...}, [children]) — `text` is textContent. */
  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in (attrs || {})) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') e.className = v;
      else if (k === 'text') e.textContent = v;
      else if (k === 'html') throw new Error('el(): html is not supported, by design');
      else if (k.slice(0, 2) === 'on') e[k] = v;
      else if (v === true) e.setAttribute(k, '');
      else e.setAttribute(k, v);
    }
    (kids || []).forEach(function (c) {
      if (c === null || c === undefined || c === false) return;
      e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return e;
  }

  function frag(kids) { var f = document.createDocumentFragment(); (kids || []).forEach(function (c) { if (c) f.appendChild(c); }); return f; }

  /* ---------------------------------------------------------- formatting */

  var fmt = {
    /** Relative age. Returns an em dash for null so a column never reads "Invalid Date". */
    ago: function (iso) {
      if (!iso) return '—';
      var ms = Date.now() - Date.parse(String(iso).replace(' ', 'T') + (/[Z+]/.test(iso) ? '' : 'Z'));
      if (!isFinite(ms)) return String(iso);
      if (ms < 0) return 'just now';
      var m = Math.floor(ms / 6e4), h = Math.floor(m / 60), d = Math.floor(h / 24);
      if (d > 0) return d + (d === 1 ? ' day ago' : ' days ago');
      if (h > 0) return h + (h === 1 ? ' hour ago' : ' hours ago');
      if (m > 0) return m + (m === 1 ? ' min ago' : ' mins ago');
      return 'just now';
    },
    /** Absolute, for tooltips and the audit trail — ambiguity is worse than length. */
    stamp: function (iso) {
      if (!iso) return '';
      var d = new Date(String(iso).replace(' ', 'T') + (/[Z+]/.test(iso) ? '' : 'Z'));
      return isNaN(d) ? String(iso) : d.toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    },
    /** A count that must never render a bare 0 as if it were "not loaded yet". */
    count: function (n, one, many) {
      n = Number(n) || 0;
      return n + ' ' + (n === 1 ? one : (many || one + 's'));
    }
  };

  /* ------------------------------------------------------------- messages */

  function msg(text, kind) {
    var box = document.getElementById('admMsg');
    if (!box) return;
    box.textContent = '';
    if (!text) return;
    var m = el('div', { class: 'msg ' + (kind || 'ok'), role: kind === 'err' ? 'alert' : 'status', text: text });
    box.appendChild(m);
    if (kind !== 'err') setTimeout(function () { if (box.contains(m)) box.textContent = ''; }, 7000);
    box.scrollIntoView({ block: 'nearest' });
  }

  /* ------------------------------------------------------------ surfaces */

  function card(title, sub, kids) {
    return el('div', { class: 'adm-card' }, [
      title ? el('h3', { text: title }) : null,
      sub ? el('div', { class: 'sub', text: sub }) : null
    ].concat(kids || []));
  }

  function busy(where, label) {
    var host = where || document.getElementById('admView');
    host.textContent = '';
    host.appendChild(el('div', { class: 'spin', role: 'status', text: (label || 'Loading') + '…' }));
  }

  /** Empty state. Always says what would put something here. */
  function empty(line, hint) {
    return el('div', { class: 'adm-empty' }, [
      el('p', { text: line }),
      hint ? el('p', { class: 'muted', text: hint }) : null
    ]);
  }

  /**
   * The 403 screen. Rendered as a real explanation rather than a blank pane:
   * hiding a nav link is cosmetic (the edge enforces), so anyone can arrive
   * here by typing a URL and deserves to be told why they were refused.
   */
  function notPermitted(need) {
    return el('div', { class: 'adm-card adm-deny' }, [
      el('h3', { text: 'Not permitted' }),
      el('p', { text: 'Your account does not hold the permission this screen needs' +
                      (need ? ' (' + need + ').' : '.') }),
      el('p', { class: 'muted', text: 'Ask an owner to grant it. Hiding the link would not have '
              + 'changed the answer — the gate refuses the request itself.' })
    ]);
  }

  function errorState(e, retry) {
    var kids = [el('h3', { text: 'That did not load' }), el('p', { text: e && e.message ? e.message : String(e) })];
    if (e && e.requestId) {
      kids.push(el('p', { class: 'muted' }, [
        'Quote this if you report it: ', el('span', { class: 'mono', text: e.requestId })
      ]));
    }
    if (retry) kids.push(el('div', { class: 'adm-f', style: 'margin-top:12px' },
      [el('button', { class: 'btn sec', text: 'Try again', onclick: retry })]));
    return el('div', { class: 'adm-card adm-deny' }, kids);
  }

  /* ---------------------------------------------------------------- forms */

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
  /** A labelled control. The <label> wraps the input, so no id/for to keep in sync. */
  function field(label, input, hint) {
    return el('label', {}, [
      el('span', { text: label }),
      input,
      hint ? el('em', { class: 'fhint', text: hint }) : null
    ]);
  }

  /* --------------------------------------------------------------- tables */

  /**
   * tbl(cols, rows) — cols are strings (or {label, cls}); rows are <tr>.
   *
   * Every <td> gets data-label from its column heading, which is what makes
   * the sub-640px card layout work (.tbl.stack td::before renders the label).
   * Backfilled here rather than at each call site precisely because a call
   * site will forget, and the failure is invisible on a desktop screen.
   */
  function tbl(cols, rows, opts) {
    opts = opts || {};
    var labels = cols.map(function (c) { return typeof c === 'string' ? c : c.label; });
    var head = el('tr', {}, cols.map(function (c) {
      return el('th', typeof c === 'string' ? { text: c } : { text: c.label, class: c.cls || '' });
    }));

    (rows || []).forEach(function (tr) {
      Array.prototype.forEach.call(tr.children, function (td, i) {
        if (!td.hasAttribute('data-label') && labels[i]) td.setAttribute('data-label', labels[i]);
      });
    });

    var body = rows && rows.length ? rows
      : [el('tr', {}, [el('td', { colspan: cols.length, class: 'adm-none',
            text: opts.emptyText || 'Nothing to show.' })])];

    return el('div', { class: 'tbl-wrap' }, [
      el('table', { class: 'tbl stack' }, [el('thead', {}, [head]), el('tbody', {}, body)])
    ]);
  }

  function td(kid, cls) {
    return el('td', cls ? { class: cls } : {}, [typeof kid === 'string' ? document.createTextNode(kid) : kid]);
  }

  function pill(text, kind) { return el('span', { class: 'pillt ' + (kind || 'none'), text: text }); }
  function badge(text, kind) { return el('span', { class: 'badge ' + (kind || ''), text: text }); }

  /* ------------------------------------------------------------ API layer */

  function cookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  function ApiError(message, opts) {
    var e = new Error(message);
    e.name = 'ApiError';
    e.code = (opts && opts.code) || 'error';
    e.field = (opts && opts.field) || '';
    e.status = (opts && opts.status) || 0;
    e.requestId = (opts && opts.requestId) || '';
    return e;
  }

  /**
   * The legacy console API (/docs/admin/api.php). Flat envelope, string errors.
   * Still the right client for Activities / Alerting / Assignment plan, which
   * are configuration files and have nothing to do with identity.
   */
  function apiConsole(res, body) {
    var opt = { headers: { 'Content-Type': 'application/json' }, cache: 'no-store', credentials: 'same-origin' };
    if (body) { body._csrf = cookie('adm_csrf'); opt.method = 'POST'; opt.body = JSON.stringify(body); }
    return fetch('/docs/admin/api.php?r=' + res, opt).then(function (r) {
      return r.json().catch(function () {
        throw ApiError('The server returned a non-JSON response (HTTP ' + r.status + ').', { status: r.status });
      }).then(function (j) {
        if (!j.ok) throw ApiError(j.error || 'The request failed.', { status: r.status, code: j.code || 'error' });
        return j;
      });
    });
  }

  /**
   * The identity API (/docs/idp/admin/...). Envelope {ok,data,request_id}.
   *
   * CSRF is the `__Host-capi_csrf` cookie double-submitted as a header; the shell
   * guarantees the cookie exists so this never depends on the user having
   * arrived via the sign-in page.
   *
   * `idem` sends an Idempotency-Key. Use it on anything that mints a
   * credential or is otherwise not naturally repeatable — without it a
   * double-clicked reset issues a second temporary password and silently
   * invalidates the one already copied into a chat message.
   */
  function apiAdmin(method, path, opts) {
    opts = opts || {};
    var headers = { 'Accept': 'application/json' };
    var init = { method: method, cache: 'no-store', credentials: 'same-origin', headers: headers };

    if (method !== 'GET' && method !== 'HEAD') {
      headers['X-CSRF-Token'] = cookie('__Host-capi_csrf');
      if (opts.body !== undefined) {
        headers['Content-Type'] = 'application/json';
        init.body = JSON.stringify(opts.body);
      }
      if (opts.idem) headers['Idempotency-Key'] = opts.idem === true ? newIdemKey() : opts.idem;
    }

    return fetch('/docs/idp/admin' + path, init).then(function (r) {
      if (r.status === 401) {
        // The session is gone — expired, revoked, or the account disabled.
        // Bounce to sign-in rather than showing six broken panes.
        location.href = '/docs/idp/login?next=' + encodeURIComponent(location.pathname + location.hash);
        throw ApiError('Your session has ended. Signing you in again…', { status: 401, code: 'unauthenticated' });
      }
      return r.json().catch(function () {
        throw ApiError('The server returned a non-JSON response (HTTP ' + r.status + ').', { status: r.status });
      }).then(function (j) {
        if (!j.ok) {
          var er = j.error || {};
          throw ApiError(er.message || 'The request failed.', {
            code: er.code, field: er.field, status: r.status, requestId: j.request_id
          });
        }
        j.data = j.data || {};
        j.data._requestId = j.request_id;
        return j.data;
      });
    });
  }

  function newIdemKey() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'k-' + Date.now() + '-' + Math.random().toString(16).slice(2);
  }

  /** /docs/idp/me — cached for the page's lifetime; the nav and guards read it. */
  var _me = null;
  function me(force) {
    if (_me && !force) return Promise.resolve(_me);
    return fetch('/docs/idp/me', { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { return r.json().catch(function () { return { signed_in: false }; }); })
      .then(function (j) { _me = j; return j; });
  }
  function can(perm) { return !!(_me && _me.perms && _me.perms.indexOf(perm) >= 0); }
  function isOwner() { return !!(_me && _me.roles && _me.roles.indexOf('owner') >= 0); }
  function whoami() { return _me; }

  /* --------------------------------------------------------------- modals */

  /**
   * Native <dialog> + showModal(): the browser gives focus trapping, Esc, and
   * inertness of the page behind for free. A hand-rolled overlay gets the
   * focus trap wrong roughly always.
   */
  function modal(opts) {
    var dlg = el('dialog', { class: 'adm-dlg' });
    var body = el('div', { class: 'dlg-body' }, opts.body || []);
    var foot = el('div', { class: 'dlg-foot' }, opts.actions || []);
    dlg.appendChild(el('form', { method: 'dialog', class: 'dlg-x' },
      [el('button', { class: 'x', 'aria-label': 'Close', text: '×' })]));
    dlg.appendChild(el('h3', { text: opts.title || '' }));
    if (opts.lead) dlg.appendChild(el('p', { class: 'dlg-lead', text: opts.lead }));
    dlg.appendChild(body);
    dlg.appendChild(foot);
    document.body.appendChild(dlg);
    dlg.addEventListener('close', function () { dlg.remove(); });
    dlg.showModal();
    return { dlg: dlg, body: body, foot: foot, close: function () { dlg.close(); } };
  }

  /**
   * The destructive-action pattern (E9-ADMIN-027).
   *
   *   - The blast radius is FETCHED, never guessed. The dialog opens in a
   *     checking state and the confirm button stays disabled until the server
   *     answers. It never renders "0 sessions" as a placeholder, because a
   *     confident wrong zero is what makes an admin click without reading.
   *   - The operator types the exact name. window.confirm() is muscle memory;
   *     typing is not.
   *   - No optimistic UI: on success the caller re-reads from the server.
   *
   * opts = {title, lead, confirmWord, verb, preflight():Promise<{lines[],blocked?}>,
   *         run():Promise, done(result)}
   */
  function confirmDestructive(opts) {
    var status = el('div', { class: 'dlg-check', text: 'Checking what this affects…' });
    var typed = inp({ type: 'text', autocomplete: 'off', autocapitalize: 'none',
                      spellcheck: 'false', 'aria-label': 'Type ' + opts.confirmWord + ' to confirm' });
    var typeRow = el('div', { class: 'dlg-type', hidden: true }, [
      field('Type ' + opts.confirmWord + ' to confirm', typed)
    ]);
    var go = el('button', { class: 'btn danger', text: opts.verb || 'Confirm', disabled: true });
    var cancel = el('button', { class: 'btn sec', text: 'Cancel' });

    var m = modal({ title: opts.title, lead: opts.lead, body: [status, typeRow], actions: [cancel, go] });
    cancel.onclick = function () { m.close(); };

    var ready = false;
    typed.oninput = function () { go.disabled = !ready || typed.value.trim() !== opts.confirmWord; };

    opts.preflight().then(function (info) {
      status.textContent = '';
      status.className = 'dlg-radius';
      (info.lines || []).forEach(function (l) { status.appendChild(el('div', { text: l })); });

      if (info.blocked) {
        status.appendChild(el('div', { class: 'msg err', text: info.blocked }));
        return;                                   // go stays disabled, permanently
      }
      ready = true;
      typeRow.hidden = false;
      typed.focus();
    }).catch(function (e) {
      status.className = 'dlg-radius';
      status.textContent = '';
      status.appendChild(el('div', { class: 'msg err',
        text: 'Could not check what this affects, so the action is blocked: ' + e.message }));
    });

    go.onclick = function () {
      go.disabled = true; cancel.disabled = true;
      go.textContent = 'Working…';
      opts.run().then(function (res) {
        m.close();
        if (opts.done) opts.done(res);
      }).catch(function (e) {
        go.disabled = false; cancel.disabled = false;
        go.textContent = opts.verb || 'Confirm';
        status.textContent = '';
        status.appendChild(el('div', { class: 'msg err', text: e.message }));
      });
    };
  }

  /* --------------------------------------------------------------- router */

  var routes = {};
  var current = null;
  var firstPaint = true;

  /**
   * def = {title, lead, nav:'group', perm:'x.y', render(host, params)}
   * `perm` hides the nav entry and short-circuits to notPermitted(); the API
   * enforces independently, so this is purely so the UI reads honestly.
   */
  function route(name, def) { routes[name] = def; def.name = name; return def; }

  function parseHash() {
    var h = (location.hash || '').replace(/^#\/?/, '');
    var parts = h.split('/').filter(Boolean).map(decodeURIComponent);
    return { name: parts[0] || '', params: parts.slice(1) };
  }

  function go(hash) { location.hash = '#/' + String(hash).replace(/^#?\/?/, ''); }

  function render() {
    var at = parseHash();
    var def = routes[at.name] || routes[CAPI.defaultRoute];
    if (!def) return;
    current = def;

    document.getElementById('admTitle').textContent = def.title || 'Admin';
    document.getElementById('admLead').textContent = def.lead || '';
    document.title = (def.title || 'Admin') + ' — ASPSI CAPI';
    paintNav(def.name);
    msg('');

    var host = document.getElementById('admView');
    host.textContent = '';

    // Move focus into the content on a route change so the next Tab starts
    // here rather than back at the top of a fifteen-link sidebar. Skipped on
    // the first paint, where nothing has moved and stealing focus would only
    // scroll the page out from under someone.
    if (!firstPaint) { host.focus({ preventScroll: true }); }
    firstPaint = false;

    if (def.perm && !can(def.perm)) { host.appendChild(notPermitted(def.perm)); return; }

    busy(host);
    try {
      def.render(host, at.params);
    } catch (e) {
      host.textContent = '';
      host.appendChild(errorState(e));
    }
  }

  function paintNav(activeName) {
    document.querySelectorAll('.sb-nav a[data-route]').forEach(function (a) {
      var on = a.getAttribute('data-route') === activeName;
      a.classList.toggle('on', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
  }

  /**
   * Hide nav entries the account cannot use, and drop a whole group when it
   * empties. Cosmetic only — stated here as loudly as in me.php because the
   * temptation to treat a hidden link as a control is perennial.
   */
  function applyNavPermissions() {
    document.querySelectorAll('.sb-nav a[data-perm]').forEach(function (a) {
      if (!can(a.getAttribute('data-perm'))) a.hidden = true;
    });
    document.querySelectorAll('.sb-nav .sb-sec').forEach(function (sec) {
      var any = false, n = sec.nextElementSibling;
      while (n && !n.classList.contains('sb-sec')) {
        if (n.tagName === 'A' && !n.hidden) any = true;
        n = n.nextElementSibling;
      }
      if (!any) sec.hidden = true;
    });
  }

  function start(defaultRoute) {
    CAPI.defaultRoute = defaultRoute;
    window.addEventListener('hashchange', render);
    me().then(function (m) {
      var who = document.getElementById('admWho');
      if (who && m.user) who.textContent = m.user;
      applyNavPermissions();
      if (!location.hash) go(defaultRoute);
      else render();
    });
  }

  CAPI.el = el; CAPI.frag = frag; CAPI.fmt = fmt; CAPI.msg = msg;
  CAPI.card = card; CAPI.busy = busy; CAPI.empty = empty;
  CAPI.notPermitted = notPermitted; CAPI.errorState = errorState;
  CAPI.inp = inp; CAPI.sel = sel; CAPI.field = field;
  CAPI.tbl = tbl; CAPI.td = td; CAPI.pill = pill; CAPI.badge = badge;
  CAPI.apiConsole = apiConsole; CAPI.apiAdmin = apiAdmin; CAPI.ApiError = ApiError;
  CAPI.newIdemKey = newIdemKey;
  CAPI.me = me; CAPI.can = can; CAPI.isOwner = isOwner; CAPI.whoami = whoami;
  CAPI.modal = modal; CAPI.confirmDestructive = confirmDestructive;
  CAPI.route = route; CAPI.go = go; CAPI.render = render; CAPI.start = start;
  CAPI.routes = routes;
  return CAPI;
})();
