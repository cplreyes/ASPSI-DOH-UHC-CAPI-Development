/* CAPI Console — admin portal boot.                            Carl, 2026-08-09
 *
 * Loaded last, after ui.js has defined window.CAPI and every view-*.js has
 * registered its route. Its whole job is to pick the landing screen and start
 * the router.
 *
 * The landing screen is chosen from what the account can actually do, not
 * hard-coded: a programme admin arrives at Users, and an account that somehow
 * reaches this page with neither admin permission lands on My account rather
 * than on a "Not permitted" pane it can do nothing about.
 */
'use strict';
(function (C) {
  C.me().then(function () {
    var first = C.can('admin.users') ? 'users'
              : C.can('admin.system') ? 'activities'
              : C.can('audit.view') ? 'audit'
              : 'account';
    C.start(first);
  });
})(window.CAPI);
