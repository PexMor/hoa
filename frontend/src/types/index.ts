/**
 * Shared TypeScript types for the HOA frontend
 */

// ===== User Types =====

export interface User {
  id: string;
  nick: string | null;
  first_name: string | null;
  second_name: string | null;
  email: string | null;
  phone_number: string | null;
  enabled: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  nick?: string;
  first_name?: string;
  second_name?: string;
  email?: string;
  phone_number?: string;
  enabled?: boolean;
}

export interface UserUpdate {
  nick?: string;
  first_name?: string;
  second_name?: string;
  email?: string;
  phone_number?: string;
}

// ===== Auth Method Types =====

export type AuthMethodType = 'passkey' | 'password' | 'oauth2' | 'token';

export interface AuthMethodBase {
  id: string;
  user_id: string;
  type: AuthMethodType;
  identifier: string | null;
  enabled: boolean;
  requires_approval: boolean;
  approved: boolean;
  approved_by: string | null;
  created_at: string;
}

export interface PasskeyAuthMethod extends AuthMethodBase {
  type: 'passkey';
  credential_id: string;
  rp_id: string;
  transports: string[] | null;
}

export interface PasswordAuthMethod extends AuthMethodBase {
  type: 'password';
}

export interface OAuth2AuthMethod extends AuthMethodBase {
  type: 'oauth2';
  provider: string;
  provider_user_id: string;
}

export interface TokenAuthMethod extends AuthMethodBase {
  type: 'token';
  description: string;
}

export type AuthMethod =
  | PasskeyAuthMethod
  | PasswordAuthMethod
  | OAuth2AuthMethod
  | TokenAuthMethod;

// ===== JWT Types =====

export interface JWTTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  expires_at: string;
}

// ===== Config Types =====

export interface RPConfig {
  rp_id: string;
  rp_name: string;
  origins: string[];
}

export interface AppConfig {
  api_base_url: string;
  allowed_rps: RPConfig[];
  require_auth_method_approval: boolean;
  allow_self_service_auth: boolean;
}

// ===== API Response Types =====

export interface APIErrorResponse {
  detail: string;
  status_code?: number;
}

export interface SuccessResponse {
  ok: boolean;
  message?: string;
}

// ===== Form Types =====

export interface LoginFormData {
  identifier: string;
}

export interface RegisterFormData {
  nick: string;
  email?: string;
  first_name?: string;
  second_name?: string;
  phone_number?: string;
}

export interface AdminTokenFormData {
  token: string;
}
