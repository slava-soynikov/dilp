import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { authApi } from "../api/auth";
import { usersApi, type Me } from "../api/users";
import {
  clearTokens,
  getTokens,
  setTokens,
  type Tokens,
} from "./tokenStore";

type AuthState = {
  tokens: Tokens | null;
  me: Me | null;
  loadingMe: boolean;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setSession: (tokens: Tokens) => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokensState] = useState<Tokens | null>(() => getTokens());
  const [me, setMe] = useState<Me | null>(null);
  const [loadingMe, setLoadingMe] = useState<boolean>(false);

  const refreshMe = useCallback(async () => {
    if (!getTokens()?.access_token) {
      setMe(null);
      return;
    }
    setLoadingMe(true);
    try {
      const m = await usersApi.me();
      setMe(m);
    } catch {
      // Token exists but is rejected (server restart, revoked, expired refresh).
      // Clear it so RequireAuth redirects to /login instead of hanging in
      // "Wird geladen…" forever.
      clearTokens();
      setTokensState(null);
      setMe(null);
    } finally {
      setLoadingMe(false);
    }
  }, []);

  useEffect(() => {
    if (tokens?.access_token) {
      refreshMe();
    } else {
      setMe(null);
    }
  }, [tokens, refreshMe]);

  const setSession = useCallback((next: Tokens) => {
    setTokens(next);
    setTokensState(next);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authApi.login(email, password);
      setSession(res);
    },
    [setSession]
  );

  const logout = useCallback(async () => {
    const current = getTokens();
    if (current?.refresh_token) {
      try {
        await authApi.logout(current.refresh_token);
      } catch {
        // ignore
      }
    }
    clearTokens();
    setTokensState(null);
    setMe(null);
  }, []);

  const hasRole = useCallback(
    (role: string) => me?.roles?.includes(role) ?? false,
    [me]
  );

  const value = useMemo<AuthState>(
    () => ({
      tokens,
      me,
      loadingMe,
      isAuthenticated: !!tokens?.access_token,
      hasRole,
      login,
      logout,
      setSession,
      refreshMe,
    }),
    [tokens, me, loadingMe, hasRole, login, logout, setSession, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}