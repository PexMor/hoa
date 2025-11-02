/**
 * API Client
 * 
 * Provides typed API methods for all backend endpoints
 */

import type {
  User,
  UserUpdate,
  AuthMethod,
  JWTTokenResponse,
} from '../types';

import type {
  RegistrationOptions,
  RegistrationCredential,
  AuthenticationOptions,
  AuthenticationCredential,
} from './webauthn';

// ===== Configuration =====

let apiBaseUrl = '/api';

/**
 * Set the API base URL (call this on app init with config)
 */
export function setApiBaseUrl(url: string) {
  apiBaseUrl = url;
}

// ===== HTTP Client =====

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${apiBaseUrl}${path}`;
  
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Include cookies for session
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(
      errorData.detail || `HTTP ${response.status}`,
      response.status,
      errorData
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' });
}

function post<T>(path: string, data?: any): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

function put<T>(path: string, data?: any): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

// ===== Auth API =====

export const authAPI = {
  /**
   * Get server health status
   */
  health: () => get<{ status: string; version: string; git_commit: string; git_branch: string; build_date: string }>('/health'),

  /**
   * Get server configuration (allowed RPs, features, etc.)
   */
  config: () => get<{
    allowed_rps: Array<{
      rp_id: string;
      rp_name: string;
      origins: string[];
    }>;
    require_auth_method_approval: boolean;
    allow_self_service_auth: boolean;
  }>('/auth/config'),

  /**
   * Get current user info
   */
  me: () => get<{ user: User | null }>('/auth/me'),

  /**
   * Begin WebAuthn registration
   */
  registerBegin: (data: {
    rp_id: string;
    origin: string;
    display_name?: string;
    username_hint?: string;
  }) =>
    post<{ options: RegistrationOptions; user_id: string }>(
      '/auth/webauthn/register/begin',
      data
    ),

  /**
   * Complete WebAuthn registration
   */
  registerFinish: (data: {
    rp_id: string;
    origin: string;
    user_id: string;
    credential: RegistrationCredential;
    name?: string;
    email?: string;
  }) => post<{ user: User; session_id: string }>('/auth/webauthn/register/finish', data),

  /**
   * Begin WebAuthn authentication
   */
  loginBegin: (data: {
    rp_id: string;
    origin: string;
    email?: string;
  }) =>
    post<{ options: AuthenticationOptions }>(
      '/auth/webauthn/login/begin',
      data
    ),

  /**
   * Complete WebAuthn authentication
   */
  loginFinish: (data: {
    rp_id: string;
    origin: string;
    credential: AuthenticationCredential;
  }) =>
    post<{ user: User; session_id: string }>(
      '/auth/webauthn/login/finish',
      data
    ),

  /**
   * Bootstrap login with admin token
   */
  bootstrapLogin: (token: string) =>
    post<{ user: User; session_id: string }>(
      '/auth/token/bootstrap',
      { token }
    ),

  /**
   * Logout current user
   */
  logout: () => post<{ ok: boolean }>('/auth/logout'),
};

// ===== User API =====

export const userAPI = {
  /**
   * Get current user profile
   */
  getProfile: () => get<User>('/users/me'),

  /**
   * Update current user profile
   */
  updateProfile: (data: UserUpdate) => put<User>('/users/me', data),

  /**
   * Get current user's auth methods
   */
  getAuthMethods: () => get<AuthMethod[]>('/users/me/auth-methods'),

  /**
   * Delete an auth method
   */
  deleteAuthMethod: (authMethodId: string) =>
    del<{ ok: boolean; message: string }>(`/users/me/auth-methods/${authMethodId}`),

  /**
   * Add password authentication method
   */
  addPasswordAuth: (password: string, identifier?: string) =>
    post<AuthMethod>('/users/me/auth-methods/password', { password, identifier }),

  /**
   * Begin adding a new passkey
   */
  beginAddPasskey: (data: { rp_id: string; origin: string; display_name?: string }) =>
    post<{ options: RegistrationOptions }>('/users/me/auth-methods/passkey/begin', data),

  /**
   * Finish adding a new passkey
   */
  finishAddPasskey: (data: { rp_id: string; origin: string; credential: RegistrationCredential }) =>
    post<AuthMethod>('/users/me/auth-methods/passkey/finish', data),

  /**
   * Create an API token
   */
  createApiToken: (description: string, expiresInDays?: number) =>
    post<{
      auth_method: AuthMethod;
      access_token: string;
      refresh_token: string;
      expires_at: string;
    }>('/users/me/auth-methods/token/create', {
      description,
      expires_in_days: expiresInDays,
    }),
};

// ===== M2M API =====

export const m2mAPI = {
  /**
   * Create JWT access and refresh tokens
   */
  createToken: (options?: { expires_in_minutes?: number }) =>
    post<JWTTokenResponse>('/m2m/token/create', options || {}),

  /**
   * Refresh JWT access token
   */
  refreshToken: (refreshToken: string) =>
    post<JWTTokenResponse>('/m2m/token/refresh', { refresh_token: refreshToken }),

  /**
   * Validate JWT token
   */
  validateToken: (token: string) =>
    post<{
      valid: boolean;
      payload?: any;
      error?: string;
    }>('/m2m/token/validate', { token }),
};

// ===== Admin API =====

export const adminAPI = {
  /**
   * List all users
   */
  listUsers: (params?: {
    enabled_only?: boolean;
    offset?: number;
    limit?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.enabled_only) query.append('enabled_only', 'true');
    if (params?.offset !== undefined) query.append('offset', params.offset.toString());
    if (params?.limit !== undefined) query.append('limit', params.limit.toString());
    
    const queryString = query.toString();
    return get<User[]>(`/admin/users${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get specific user by ID
   */
  getUser: (userId: string) => get<User>(`/admin/users/${userId}`),

  /**
   * Toggle user enabled status
   */
  toggleUser: (userId: string, enabled: boolean) =>
    post<{ ok: boolean; message: string }>(
      `/admin/users/${userId}/toggle`,
      { enabled }
    ),

  /**
   * Get user's auth methods
   */
  getUserAuthMethods: (userId: string) =>
    get<AuthMethod[]>(`/admin/users/${userId}/auth-methods`),

  /**
   * Approve/reject auth method
   */
  approveAuthMethod: (authMethodId: string, approved: boolean) =>
    post<{ ok: boolean; message: string }>(
      `/admin/auth-methods/${authMethodId}/approve`,
      { approved }
    ),

  /**
   * Toggle auth method enabled status
   */
  toggleAuthMethod: (authMethodId: string, enabled: boolean) =>
    post<{ ok: boolean; message: string }>(
      `/admin/auth-methods/${authMethodId}/toggle`,
      { enabled }
    ),

  /**
   * Get pending approval queue
   */
  getPendingApprovals: () => get<AuthMethod[]>('/admin/auth-methods/pending'),
};

// ===== Export all APIs =====

export const api = {
  auth: authAPI,
  user: userAPI,
  m2m: m2mAPI,
  admin: adminAPI,
};

export default api;

// ===== Export error type =====

export { APIError };
