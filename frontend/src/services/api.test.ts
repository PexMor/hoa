/**
 * API Client Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api, APIError, setApiBaseUrl } from './api';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    setApiBaseUrl('/api');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('setApiBaseUrl', () => {
    it('sets the API base URL', () => {
      setApiBaseUrl('https://example.com/api');
      // Verify by making a request and checking the URL
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy' }),
      } as Response);
      
      api.auth.health();
      
      expect(mockFetch).toHaveBeenCalledWith(
        'https://example.com/api/health',
        expect.any(Object)
      );
    });
  });

  describe('APIError', () => {
    it('creates error with message and status', () => {
      const error = new APIError('Test error', 400, { detail: 'Bad request' });
      
      expect(error.message).toBe('Test error');
      expect(error.status).toBe(400);
      expect(error.detail).toEqual({ detail: 'Bad request' });
      expect(error.name).toBe('APIError');
    });
  });

  describe('auth API', () => {
    it('fetches health status', async () => {
      const mockResponse = {
        status: 'healthy',
        version: '1.0.0',
        git_commit: 'abc123',
        git_branch: 'main',
        build_date: '2025-10-23',
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);
      
      const result = await api.auth.health();
      
      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/health',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
    });

    it('fetches current user', async () => {
      const mockUser = {
        id: '123',
        nick: 'testuser',
        email: 'test@example.com',
        enabled: true,
        is_admin: false,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      } as Response);
      
      const result = await api.auth.me();
      
      expect(result).toEqual(mockUser);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/auth/me',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
    });

    it('handles logout', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logged out' }),
      } as Response);
      
      const result = await api.auth.logout();
      
      expect(result).toEqual({ message: 'Logged out' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/auth/logout',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      );
    });
  });

  describe('error handling', () => {
    it('throws APIError on 400 error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad request' }),
      } as Response);
      
      try {
        await api.auth.health();
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Bad request');
        expect((error as APIError).status).toBe(400);
      }
    });

    it('throws APIError on 401 error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      } as Response);
      
      try {
        await api.auth.me();
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Unauthorized');
        expect((error as APIError).status).toBe(401);
      }
    });

    it('throws APIError on 404 error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      } as Response);
      
      try {
        await api.auth.me();
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Not found');
        expect((error as APIError).status).toBe(404);
      }
    });

    it('throws APIError on 500 error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal error' }),
      } as Response);
      
      try {
        await api.auth.health();
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Internal error');
        expect((error as APIError).status).toBe(500);
      }
    });

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      
      try {
        await api.auth.health();
        expect.fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe('Network error');
      }
    });
  });

  describe('user API', () => {
    it('gets user auth methods', async () => {
      const mockMethods = [
        {
          id: '1',
          type: 'passkey',
          identifier: 'Credential 1',
          enabled: true,
          created_at: '2025-10-23',
        },
      ];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMethods,
      } as Response);
      
      const result = await api.user.getAuthMethods();
      
      expect(result).toEqual(mockMethods);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/users/me/auth-methods',
        expect.any(Object)
      );
    });

    it('updates user profile', async () => {
      const updateData = {
        nick: 'newnick',
        email: 'newemail@example.com',
      };
      
      const mockResponse = {
        ...updateData,
        id: '123',
        enabled: true,
        is_admin: false,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);
      
      const result = await api.user.updateProfile(updateData);
      
      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/users/me',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
    });

    it('deletes auth method', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Deleted' }),
      } as Response);
      
      const result = await api.user.deleteAuthMethod('method-id-123');
      
      expect(result).toEqual({ message: 'Deleted' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/users/me/auth-methods/method-id-123',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('m2m API', () => {
    it('creates JWT token', async () => {
      const mockToken = {
        access_token: 'token123',
        refresh_token: 'refresh123',
        token_type: 'bearer',
        expires_in: 3600,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      } as Response);
      
      const result = await api.m2m.createToken();
      
      expect(result).toEqual(mockToken);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/m2m/token/create',
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('refreshes JWT token', async () => {
      const mockToken = {
        access_token: 'newtoken123',
        token_type: 'bearer',
        expires_in: 3600,
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      } as Response);
      
      const result = await api.m2m.refreshToken('refresh123');
      
      expect(result).toEqual(mockToken);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/m2m/token/refresh',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ refresh_token: 'refresh123' }),
        })
      );
    });

    it('validates JWT token', async () => {
      const mockValidation = {
        valid: true,
        user_id: '123',
        expires_at: '2025-10-24',
      };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidation,
      } as Response);
      
      const result = await api.m2m.validateToken('token123');
      
      expect(result).toEqual(mockValidation);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/m2m/token/validate',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ token: 'token123' }),
        })
      );
    });
  });

  describe('admin API', () => {
    it('lists all users', async () => {
      const mockUsers = [
        { id: '1', nick: 'user1', enabled: true },
        { id: '2', nick: 'user2', enabled: false },
      ];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers,
      } as Response);
      
      const result = await api.admin.listUsers();
      
      expect(result).toEqual(mockUsers);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/users',
        expect.any(Object)
      );
    });

    it('gets specific user', async () => {
      const mockUser = { id: '123', nick: 'testuser', enabled: true };
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      } as Response);
      
      const result = await api.admin.getUser('123');
      
      expect(result).toEqual(mockUser);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/users/123',
        expect.any(Object)
      );
    });

    it('toggles user status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true, message: 'User toggled' }),
      } as Response);
      
      const result = await api.admin.toggleUser('123', false);
      
      expect(result).toEqual({ ok: true, message: 'User toggled' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/users/123/toggle',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ enabled: false }),
        })
      );
    });

    it('approves auth method', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true, message: 'Approved' }),
      } as Response);
      
      const result = await api.admin.approveAuthMethod('method-123', true);
      
      expect(result).toEqual({ ok: true, message: 'Approved' });
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/auth-methods/method-123/approve',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ approved: true }),
        })
      );
    });

    it('gets pending approvals', async () => {
      const mockApprovals = [
        { id: '1', type: 'passkey', approved: false },
      ];
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockApprovals,
      } as Response);
      
      const result = await api.admin.getPendingApprovals();
      
      expect(result).toEqual(mockApprovals);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/admin/auth-methods/pending',
        expect.any(Object)
      );
    });
  });
});

