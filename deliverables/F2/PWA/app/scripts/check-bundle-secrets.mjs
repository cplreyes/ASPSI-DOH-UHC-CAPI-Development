#!/usr/bin/env node
/**
 * Build guard for the auth re-arch (spec §7.2 / §8.5).
 *
 * Scans `dist/assets/*.js` for patterns that look like leaked secrets and fails
 * the build if any are found. Runs as the last step of `npm run build` so
 * Cloudflare Pages will refuse to deploy a bundle that smuggles a secret.
 *
 * Patterns:
 *   - long hex blobs (HMAC, hash digests, hex-encoded keys)
 *   - long base64 / base64url blobs (signing keys, tokens)
 *   - literal env names that should never appear in client output
 */
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const bundleDir = resolve(here, '..', 'dist', 'assets');

if (!existsSync(bundleDir)) {
  console.error(`check-bundle-secrets: ${bundleDir} not found. Did vite build run?`);
  process.exit(2);
}

const HEX_RE = /[a-f0-9]{40,}/i;
const B64_RE = /[A-Za-z0-9+/_-]{40,}={0,2}/;
const SECRET_NAMES = ['JWT_SIGNING_KEY', 'APPS_SCRIPT_HMAC', 'ADMIN_PASSWORD'];

let failures = [];

const files = readdirSync(bundleDir).filter((f) => f.endsWith('.js'));
for (const f of files) {
  const path = join(bundleDir, f);
  const contents = readFileSync(path, 'utf8');

  // 1. Long hex blobs.
  const hexMatch = contents.match(HEX_RE);
  if (hexMatch) {
    failures.push(
      `${f}: long hex literal found (${hexMatch[0].slice(0, 12)}…). Possible HMAC or hex-encoded key leak.`,
    );
  }

  // 2. Long base64 blobs. Skip well-known harmless patterns (source map URLs,
  // sourceMappingURL data URIs, Workbox precache hashes which are intentional).
  // We do a coarse exclusion: skip lines that contain 'sourceMappingURL' or
  // start with the workbox precache shape.
  const lines = contents.split('\n');
  for (const line of lines) {
    if (line.includes('sourceMappingURL') || line.includes('precacheManifest')) continue;
    const b64Match = line.match(B64_RE);
    if (b64Match && b64Match[0].length >= 60) {
      // Only flag if it's NOT a JWT-like 3-part dotted string (those are public
      // device tokens parsed from the URL or storage at runtime, not bundled keys).
      const isJwtLike = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(b64Match[0]);
      if (isJwtLike) continue;
      failures.push(
        `${f}: long base64 literal found (${b64Match[0].slice(0, 12)}…). Possible signing-key leak.`,
      );
      break; // one finding per file is enough
    }
  }

  // 3. Literal secret env names.
  for (const name of SECRET_NAMES) {
    if (contents.includes(name)) {
      failures.push(`${f}: secret env name '${name}' referenced in client bundle.`);
    }
  }
}

if (failures.length > 0) {
  console.error('check-bundle-secrets: FAIL');
  for (const f of failures) console.error('  - ' + f);
  console.error(
    '\nIf any of these are false positives, refine the patterns in scripts/check-bundle-secrets.mjs.',
  );
  process.exit(1);
}

console.log(`check-bundle-secrets: OK (${files.length} bundle file(s) scanned)`);
