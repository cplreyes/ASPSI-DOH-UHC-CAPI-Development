/**
 * HMAC-SHA256 signing for Apps Script forward requests.
 * Canonicalisation matches `deliverables/F2/PWA/backend/src/Auth.js` byte-for-byte:
 *   `${METHOD}|${action}|${ts}|${body}`
 * Where `ts` is integer milliseconds (Date.now()) as a string, and the signature
 * is lowercase hex.
 */

const enc = new TextEncoder();

function bytesToHex(bytes: Uint8Array): string {
  let hex = '';
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i]!;
    hex += b.toString(16).padStart(2, '0');
  }
  return hex;
}

async function importHmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, [
    'sign',
  ]);
}

/**
 * Sign a request with the Apps Script HMAC.
 * @param secret  The HMAC secret (PROP_HMAC_SECRET on Apps Script side)
 * @param method  Uppercase HTTP method, e.g. "POST" or "GET"
 * @param action  Action name as it appears in the query param, e.g. "batch-submit", "config", "facilities"
 * @param tsMs    Timestamp as a string of milliseconds (must match the ?ts= query param exactly)
 * @param body    The request body string (empty string for GET)
 */
export async function signAppsScriptRequest(
  secret: string,
  method: string,
  action: string,
  tsMs: string,
  body: string,
): Promise<string> {
  const key = await importHmacKey(secret);
  const canonical = `${method}|${action}|${tsMs}|${body}`;
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(canonical));
  return bytesToHex(new Uint8Array(sig));
}
