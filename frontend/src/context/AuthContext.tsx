import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { User } from '../types/api';
import { loginApi, registerApi, setAuthToken, setStoredUser, getStoredUser, getAuthToken } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, role: string, full_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(getStoredUser);
  const [token, setToken] = useState<string | null>(getAuthToken);

  const login = useCallback(async (username: string, password: string) => {
    const data = await loginApi(username, password);
    setUser(data.user); setToken(data.access_token);
  }, []);

  const register = useCallback(async (username: string, email: string, password: string, role: string, full_name: string) => {
    const data = await registerApi(username, email, password, role, full_name);
    setUser(data.user); setToken(data.access_token);
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null); setStoredUser(null); setUser(null); setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token && !!user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
