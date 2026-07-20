import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, getTokens, setTokens, type User } from "./api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string) => Promise<void>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  resendVerification: (email: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getTokens()) {
      setLoading(false);
      return;
    }
    api.me()
      .then(setUser)
      .catch(() => setTokens(null))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login: async (email, password) => {
      const tokens = await api.login(email, password);
      setTokens(tokens);
      setUser(await api.me());
    },
    register: async (email, password, firstName) => {
      await api.register(email, password, firstName);
    },
    verifyEmail: async (email, code) => {
      await api.verifyEmail(email, code);
    },
    resendVerification: async (email) => {
      await api.resendVerification(email);
    },
    forgotPassword: async (email) => {
      await api.forgotPassword(email);
    },
    resetPassword: async (email, code, newPassword) => {
      await api.resetPassword(email, code, newPassword);
    },
    logout: () => {
      setTokens(null);
      setUser(null);
    },
  }), [loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
