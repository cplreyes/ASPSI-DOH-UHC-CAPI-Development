const SPEC_VERSION_RE = /^(\d{4}-\d{2}-\d{2})-m(\d+)$/;

export function isServerNewer(local: string, serverMin: string): boolean {
  if (!serverMin) return false;
  const a = local.match(SPEC_VERSION_RE);
  const b = serverMin.match(SPEC_VERSION_RE);
  if (!a || !b) return serverMin > local;
  if (a[1] !== b[1]) return b[1] > a[1];
  return Number(b[2]) > Number(a[2]);
}
