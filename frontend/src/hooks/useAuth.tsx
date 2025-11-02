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
import { getConfig } from '../config';

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
      // Get config for rp_id and origin
      const config = getConfig();
      const rp = config.allowed_rps[0]; // Use first RP
      const origin = window.location.origin;

      console.log('[AUTH] Starting registration for:', userData.email);
      
      // Step 1: Begin registration (get WebAuthn options)
      const { options, user_id } = await api.auth.registerBegin({
        rp_id: rp.rp_id,
        origin: origin,
        display_name: userData.first_name || userData.nick,
        username_hint: userData.email || userData.nick,
      });
      
      console.log('[AUTH] Got challenge, user_id:', user_id, 'challenge:', options.challenge.substring(0, 20) + '...');

      // Step 2: Create WebAuthn credential
      console.log('[AUTH] Creating WebAuthn credential...');
      const credential = await startRegistration(options);
      console.log('[AUTH] Credential created, id:', credential.id);

      // Step 3: Finish registration (send user data and credential)
      console.log('[AUTH] Finishing registration...');
      const response = await api.auth.registerFinish({
        rp_id: rp.rp_id,
        origin: origin,
        user_id,
        credential,
        name: userData.first_name,
        email: userData.email,
      });

      console.log('[AUTH] Registration complete!');
      setUser(response.user);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const login = async (identifier: string) => {
    try {
      // Get config for rp_id and origin
      const config = getConfig();
      const rp = config.allowed_rps[0]; // Use first RP
      const origin = window.location.origin;

      // Step 1: Begin authentication (get WebAuthn options)
      const { options } = await api.auth.loginBegin({
        rp_id: rp.rp_id,
        origin: origin,
        email: identifier,
      });

      // Step 2: Get WebAuthn credential
      const credential = await startAuthentication(options);

      // Step 3: Finish authentication
      const response = await api.auth.loginFinish({
        rp_id: rp.rp_id,
        origin: origin,
        credential,
      });

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

