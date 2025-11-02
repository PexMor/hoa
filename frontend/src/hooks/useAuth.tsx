/**
 * Auth Context and Hook
 * 
 * Manages authentication state and provides auth methods
 */

import { createContext } from 'preact';
import { useContext, useState, useEffect } from 'preact/hooks';
import type { User, UserCreate } from '../types';
import { api } from '../services/api';
import { startRegistration, startAuthentication } from '../services/webauthn';

// ===== Types =====

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
  login: (identifier: string) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  bootstrapLogin: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// ===== Context =====

const AuthContext = createContext<AuthContextValue | null>(null);

// ===== Provider =====

export function AuthProvider({ children }: { children: any }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    refreshUser();
  }, []);

  const refreshUser = async () => {
    try {
      const response = await api.auth.me();
      setUser(response.user);
    } catch (error) {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: UserCreate) => {
    try {
      // Step 1: Begin registration (get WebAuthn options)
      const { options, user_id } = await api.auth.registerBegin(userData);

      // Step 2: Create WebAuthn credential
      const credential = await startRegistration(options);

      // Step 3: Finish registration
      const response = await api.auth.registerFinish({
        user_id,
        credential,
      });

      setUser(response.user);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const login = async (identifier: string) => {
    try {
      // Step 1: Begin authentication (get WebAuthn options)
      const { options } = await api.auth.loginBegin(identifier);

      // Step 2: Get WebAuthn credential
      const credential = await startAuthentication(options);

      // Step 3: Finish authentication
      const response = await api.auth.loginFinish(credential);

      setUser(response.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const bootstrapLogin = async (token: string) => {
    try {
      const response = await api.auth.bootstrapLogin(token);
      setUser(response.user);
    } catch (error) {
      console.error('Bootstrap login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
    }
  };

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin ?? false,
    isLoading,
    login,
    register,
    bootstrapLogin,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ===== Hook =====

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

