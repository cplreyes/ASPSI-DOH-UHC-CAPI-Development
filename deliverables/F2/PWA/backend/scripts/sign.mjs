#!/usr/bin/env node
// Usage: node scripts/sign.mjs <method> <action> <body-or-empty>
// Reads BACKEND_URL and HMAC_SECRET from env.
// Prints a curl-ready command to stdout.

import crypto from 'node:crypto';

const [method, action, body = ''] = process.argv.slice(2);
if (!method || !action) {
  console.error('Usage: node scripts/sign.mjs <METHOD> <ACTION> [BODY]');
  process.exit(2);
}

const url = process.env.BACKEND_URL;
const secret = process.env.HMAC_SECRET;
if (!url || !secret) {
  console.error('Set BACKEND_URL and HMAC_SECRET env vars.');
  process.exit(2);
}

const ts = Date.now();
const canonical = `${method.toUpperCase()}|${action}|${ts}|${body}`;
const sig = crypto.createHmac('sha256', secret).update(canonical).digest('hex');
const q = new URLSearchParams({ action, ts: String(ts), sig }).toString();
const fullUrl = `${url}?${q}`;

if (method.toUpperCase() === 'GET') {
  console.log(`curl -sSL "${fullUrl}"`);
} else {
  console.log(`curl -sSL -X POST -H "Content-Type: application/json" --data '${body.replace(/'/g, "'\\''")}' "${fullUrl}"`);
}
