import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { EnrollmentRow } from './db';
import {
  clearEnrollment,
  getEnrollment,
  parseJwtClaimsUnsafe,
  setEnrollment,
  type SetEnrollmentInput,
} from './enrollment';

export type AuthStatus = 'loading' | 'unenrolled' | 'enrolled';

export interface AuthContextValue {
  status: AuthStatus;
  enrollment: EnrollmentRow | null;
  enroll: (input: SetEnrollmentInput) => Promise<EnrollmentRow>;
  unenroll: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [enrollment, setEnrollmentState] = useState<EnrollmentRow | null>(null);

  useEffect(() => {
    let cancelled = false;
    getEnrollment()
      .then(async (row) => {
        if (cancelled) return;
        // Spec §4.2 step 6: treat a row with missing/expired device_token as unenrolled.
        // Clearing the row forces the user back through the enrollment flow.
        if (row && !isDeviceTokenStillValid(row.device_token)) {
          await clearEnrollment();
          if (cancelled) return;
          setEnrollmentState(null);
          setStatus('unenrolled');
          return;
        }
        setEnrollmentState(row);
        setStatus(row ? 'enrolled' : 'unenrolled');
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('[F2] failed to read enrollment:', err);
        setEnrollmentState(null);
        setStatus('unenrolled');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const enroll = async (input: SetEnrollmentInput) => {
    const row = await setEnrollment(input);
    setEnrollmentState(row);
    setStatus('enrolled');
    return row;
  };

  const unenroll = async () => {
    await clearEnrollment();
    setEnrollmentState(null);
    setStatus('unenrolled');
  };

  return (
    <AuthContext.Provider value={{ status, enrollment, enroll, unenroll }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an <AuthProvider>');
  }
  return ctx;
}

function isDeviceTokenStillValid(token: string | undefined): boolean {
  if (!token) return false;
  const claims = parseJwtClaimsUnsafe(token);
  if (!claims || typeof claims.exp !== 'number') return false;
  const nowS = Math.floor(Date.now() / 1000);
  return claims.exp > nowS;
}
