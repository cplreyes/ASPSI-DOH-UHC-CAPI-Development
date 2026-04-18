import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { EnrollmentRow } from './db';
import {
  clearEnrollment,
  getEnrollment,
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
    void getEnrollment().then((row) => {
      if (cancelled) return;
      setEnrollmentState(row);
      setStatus(row ? 'enrolled' : 'unenrolled');
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
