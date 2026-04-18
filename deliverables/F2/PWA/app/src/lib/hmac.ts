export function canonicalString(
  method: string,
  action: string,
  ts: number | string,
  body: string,
): string {
  return `${method.toUpperCase()}|${action}|${ts}|${body}`;
}

export async function hmacSha256Hex(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder();
  const keyBytes = enc.encode(secret);
  const msgBytes = enc.encode(message);
  const key = await crypto.subtle.importKey(
    'raw',
    keyBytes,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const sigBuffer = await crypto.subtle.sign('HMAC', key, msgBytes);
  return bytesToHex(new Uint8Array(sigBuffer));
}

function bytesToHex(bytes: Uint8Array): string {
  let out = '';
  for (let i = 0; i < bytes.length; i++) {
    const v = bytes[i]!;
    out += v < 16 ? '0' + v.toString(16) : v.toString(16);
  }
  return out;
}
