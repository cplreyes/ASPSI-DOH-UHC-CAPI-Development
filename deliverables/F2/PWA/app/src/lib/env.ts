export interface SyncEnv {
  backendUrl: string;
  hmacSecret: string;
}

export function getSyncEnv(): SyncEnv {
  const backendUrl = import.meta.env.VITE_F2_BACKEND_URL;
  const hmacSecret = import.meta.env.VITE_F2_HMAC_SECRET;

  if (!backendUrl) {
    throw new Error(
      'VITE_F2_BACKEND_URL is not set. Copy .env.example to .env.local and fill in the Apps Script /exec URL.',
    );
  }
  if (!hmacSecret) {
    throw new Error(
      'VITE_F2_HMAC_SECRET is not set. Copy .env.example to .env.local and paste the HMAC secret from the backend ScriptProperties.',
    );
  }
  return { backendUrl, hmacSecret };
}
