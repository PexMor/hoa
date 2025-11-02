/**
 * Dashboard Page
 * 
 * User profile and auth methods management
 */

import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';
import type { AuthMethod } from '../types';
import VersionInfo from '../components/VersionInfo';

interface RouteProps {
  path?: string;
}

export function Dashboard(_props?: RouteProps) {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  
  const [authMethods, setAuthMethods] = useState<AuthMethod[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      route('/login');
    }
  }, [isAuthenticated]);

  // Load auth methods on mount
  useEffect(() => {
    if (isAuthenticated) {
      loadAuthMethods();
    }
  }, [isAuthenticated]);

  const loadAuthMethods = async () => {
    try {
      setIsLoading(true);
      const methods = await api.user.getAuthMethods();
      setAuthMethods(methods);
    } catch (err: any) {
      console.error('Failed to load auth methods:', err);
      setError('Failed to load authentication methods');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAuthMethod = async (methodId: string) => {
    if (!confirm('Are you sure you want to delete this authentication method?')) {
      return;
    }

    try {
      await api.user.deleteAuthMethod(methodId);
      await loadAuthMethods(); // Reload list
    } catch (err: any) {
      console.error('Failed to delete auth method:', err);
      alert(err.message || 'Failed to delete authentication method');
    }
  };

  const handleLogout = async () => {
    await logout();
    route('/login');
  };

  if (!user) {
    return null;
  }

  const getAuthMethodIcon = (type: string) => {
    switch (type) {
      case 'passkey':
        return '🔐';
      case 'password':
        return '🔑';
      case 'oauth2':
        return '🌐';
      case 'token':
        return '🎫';
      default:
        return '❓';
    }
  };

  const getAuthMethodLabel = (method: AuthMethod) => {
    switch (method.type) {
      case 'passkey':
        return `Passkey (${method.identifier || method.id.substring(0, 8)})`;
      case 'password':
        return `Password (${method.identifier || 'primary'})`;
      case 'oauth2':
        return `OAuth2 - ${(method as any).provider}`;
      case 'token':
        return `Token - ${(method as any).description}`;
      default:
        return 'Unknown method';
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button className="btn btn-secondary" onClick={handleLogout}>
          Logout
        </button>
      </div>

      {/* User Info Card */}
      <div className="card">
        <h2>Profile</h2>
        <div className="profile-info">
          <div className="info-row">
            <span className="label">Username:</span>
            <span className="value">{user.nick || '(not set)'}</span>
          </div>
          {user.email && (
            <div className="info-row">
              <span className="label">Email:</span>
              <span className="value">{user.email}</span>
            </div>
          )}
          {user.first_name && (
            <div className="info-row">
              <span className="label">First Name:</span>
              <span className="value">{user.first_name}</span>
            </div>
          )}
          {user.second_name && (
            <div className="info-row">
              <span className="label">Last Name:</span>
              <span className="value">{user.second_name}</span>
            </div>
          )}
          {user.phone_number && (
            <div className="info-row">
              <span className="label">Phone:</span>
              <span className="value">{user.phone_number}</span>
            </div>
          )}
          <div className="info-row">
            <span className="label">Status:</span>
            <span className={`badge ${user.enabled ? 'badge-success' : 'badge-danger'}`}>
              {user.enabled ? 'Active' : 'Disabled'}
            </span>
          </div>
          {isAdmin && (
            <div className="info-row">
              <span className="label">Role:</span>
              <span className="badge badge-primary">Administrator</span>
            </div>
          )}
          <div className="info-row">
            <span className="label">Member since:</span>
            <span className="value">
              {new Date(user.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={() => alert('Edit profile coming soon!')}>
          Edit Profile
        </button>
      </div>

      {/* Auth Methods Card */}
      <div className="card">
        <h2>Authentication Methods</h2>
        
        {isLoading ? (
          <div className="loading">Loading authentication methods...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <>
            <div className="auth-methods-list">
              {authMethods.map((method) => (
                <div key={method.id} className="auth-method-item">
                  <div className="method-info">
                    <span className="method-icon">{getAuthMethodIcon(method.type)}</span>
                    <div className="method-details">
                      <div className="method-label">{getAuthMethodLabel(method)}</div>
                      <div className="method-meta">
                        {!method.enabled && <span className="badge badge-danger">Disabled</span>}
                        {method.requires_approval && !method.approved && (
                          <span className="badge badge-warning">Pending Approval</span>
                        )}
                        <span className="method-created">
                          Added {new Date(method.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="method-actions">
                    {authMethods.length > 1 && (
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDeleteAuthMethod(method.id)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {authMethods.length === 0 && (
              <div className="empty-state">
                No authentication methods configured
              </div>
            )}
          </>
        )}
        
        <button
          className="btn btn-primary"
          onClick={() => alert('Add authentication method coming soon!')}
        >
          + Add Authentication Method
        </button>
      </div>

      {/* Admin Panel Link */}
      {isAdmin && (
        <div className="card">
          <h2>Administration</h2>
          <p>You have administrative privileges.</p>
          <button
            className="btn btn-primary"
            onClick={() => route('/admin')}
          >
            Go to Admin Panel
          </button>
        </div>
      )}

      {/* Version Info */}
      <div style={{ marginTop: '2rem' }}>
        <VersionInfo />
      </div>
    </div>
  );
}

export default Dashboard;
