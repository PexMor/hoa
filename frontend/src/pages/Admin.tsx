/**
 * Admin Panel Page
 * 
 * Complete admin interface for user and authentication method management
 */

import { useState, useEffect } from 'preact/hooks';
import { route } from 'preact-router';
import { useAuth } from '../hooks/useAuth';
import { api } from '../services/api';
import type { User, AuthMethod } from '../types';
import VersionInfo from '../components/VersionInfo';

interface RouteProps {
  path?: string;
}

interface UserWithAuthMethods extends User {
  authMethodCount?: number;
}

type TabType = 'users' | 'approvals';

export function Admin(_props?: RouteProps) {
  const { user, isAuthenticated, isAdmin } = useAuth();
  
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [users, setUsers] = useState<UserWithAuthMethods[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<AuthMethod[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userAuthMethods, setUserAuthMethods] = useState<AuthMethod[]>([]);
  
  // Filters
  const [filterEnabled, setFilterEnabled] = useState<boolean | null>(null);
  const [filterAdmin, setFilterAdmin] = useState<boolean | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Pagination (not yet implemented)
  // const [currentPage, setCurrentPage] = useState(0);
  // const [pageSize] = useState(20);
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Redirect if not authenticated or not admin
  useEffect(() => {
    if (!isAuthenticated) {
      route('/login');
    } else if (!isAdmin) {
      route('/dashboard');
    }
  }, [isAuthenticated, isAdmin]);

  // Load data based on active tab
  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      if (activeTab === 'users') {
        loadUsers();
      } else {
        loadPendingApprovals();
      }
    }
  }, [isAuthenticated, isAdmin, activeTab, filterEnabled, filterAdmin]);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // const params = new URLSearchParams();
      // if (filterEnabled !== null) params.append('enabled', String(filterEnabled));
      // if (filterAdmin !== null) params.append('is_admin', String(filterAdmin));
      // params.append('skip', String(currentPage * pageSize));
      // params.append('limit', String(pageSize));
      
      const allUsers = await api.admin.listUsers();
      
      // Apply filters client-side for now
      let filtered = allUsers;
      if (filterEnabled !== null) {
        filtered = filtered.filter(u => u.enabled === filterEnabled);
      }
      if (filterAdmin !== null) {
        filtered = filtered.filter(u => u.is_admin === filterAdmin);
      }
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(u => 
          u.nick?.toLowerCase().includes(query) ||
          u.email?.toLowerCase().includes(query) ||
          u.first_name?.toLowerCase().includes(query) ||
          u.second_name?.toLowerCase().includes(query)
        );
      }
      
      setUsers(filtered);
    } catch (err: any) {
      console.error('Failed to load users:', err);
      setError(err.message || 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const loadPendingApprovals = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const approvals = await api.admin.getPendingApprovals();
      setPendingApprovals(approvals);
    } catch (err: any) {
      console.error('Failed to load pending approvals:', err);
      setError(err.message || 'Failed to load pending approvals');
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserDetails = async (userId: string) => {
    try {
      setActionLoading('user-details');
      const userDetails = await api.admin.getUser(userId);
      const authMethods = await api.admin.getUserAuthMethods(userId);
      setSelectedUser(userDetails);
      setUserAuthMethods(authMethods);
    } catch (err: any) {
      console.error('Failed to load user details:', err);
      alert(`Failed to load user details: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleUser = async (userId: string, currentEnabled: boolean) => {
    if (!confirm('Are you sure you want to toggle this user\'s enabled status?')) {
      return;
    }
    
    try {
      setActionLoading(`toggle-user-${userId}`);
      await api.admin.toggleUser(userId, !currentEnabled);
      await loadUsers();
      if (selectedUser?.id === userId) {
        await loadUserDetails(userId);
      }
    } catch (err: any) {
      console.error('Failed to toggle user:', err);
      alert(`Failed to toggle user: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleApproveAuthMethod = async (authMethodId: string) => {
    try {
      setActionLoading(`approve-${authMethodId}`);
      await api.admin.approveAuthMethod(authMethodId, true);
      await loadPendingApprovals();
      if (selectedUser) {
        await loadUserDetails(selectedUser.id);
      }
    } catch (err: any) {
      console.error('Failed to approve auth method:', err);
      alert(`Failed to approve: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleToggleAuthMethod = async (authMethodId: string, currentEnabled: boolean) => {
    if (!confirm('Are you sure you want to toggle this authentication method?')) {
      return;
    }
    
    try {
      setActionLoading(`toggle-auth-${authMethodId}`);
      await api.admin.toggleAuthMethod(authMethodId, !currentEnabled);
      if (selectedUser) {
        await loadUserDetails(selectedUser.id);
      }
    } catch (err: any) {
      console.error('Failed to toggle auth method:', err);
      alert(`Failed to toggle auth method: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getAuthMethodIcon = (type: string) => {
    switch (type) {
      case 'passkey': return '🔐';
      case 'password': return '🔑';
      case 'oauth2': return '🌐';
      case 'token': return '🎟️';
      default: return '❓';
    }
  };

  if (!isAuthenticated || !isAdmin) {
    return null;
  }

  return (
    <div className="container">
      <div className="admin-header">
        <div>
          <h1>Admin Panel</h1>
          <p>Manage users and authentication methods</p>
        </div>
        <button className="btn btn-secondary" onClick={() => route('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users ({users.length})
        </button>
        <button
          className={`tab ${activeTab === 'approvals' ? 'active' : ''}`}
          onClick={() => setActiveTab('approvals')}
        >
          Pending Approvals ({pendingApprovals.length})
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="admin-content">
          {/* Filters */}
          <div className="card">
            <h3>Filters</h3>
            <div className="filters">
              <div className="filter-group">
                <label>Search</label>
                <input
                  type="text"
                  placeholder="Search by name, email, nick..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery((e.target as HTMLInputElement).value)}
                  className="input"
                />
              </div>
              
              <div className="filter-group">
                <label>Status</label>
                <select
                  value={filterEnabled === null ? 'all' : String(filterEnabled)}
                  onChange={(e) => {
                    const value = (e.target as HTMLSelectElement).value;
                    setFilterEnabled(value === 'all' ? null : value === 'true');
                  }}
                  className="input"
                >
                  <option value="all">All Users</option>
                  <option value="true">Enabled Only</option>
                  <option value="false">Disabled Only</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Role</label>
                <select
                  value={filterAdmin === null ? 'all' : String(filterAdmin)}
                  onChange={(e) => {
                    const value = (e.target as HTMLSelectElement).value;
                    setFilterAdmin(value === 'all' ? null : value === 'true');
                  }}
                  className="input"
                >
                  <option value="all">All Roles</option>
                  <option value="true">Admins Only</option>
                  <option value="false">Users Only</option>
                </select>
              </div>
              
              <button
                onClick={() => {
                  setSearchQuery('');
                  setFilterEnabled(null);
                  setFilterAdmin(null);
                }}
                className="btn btn-secondary"
              >
                Clear Filters
              </button>
            </div>
          </div>

          {/* User List */}
          <div className="card">
            <h3>Users</h3>
            {isLoading ? (
              <p>Loading users...</p>
            ) : users.length === 0 ? (
              <p>No users found matching the filters.</p>
            ) : (
              <div className="user-table">
                <table>
                  <thead>
                    <tr>
                      <th>Nick</th>
                      <th>Email</th>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className={!u.enabled ? 'user-disabled' : ''}>
                        <td>
                          <strong>{u.nick || '—'}</strong>
                          {u.id === user?.id && <span className="badge badge-info">You</span>}
                        </td>
                        <td>{u.email || '—'}</td>
                        <td>{u.first_name && u.second_name ? `${u.first_name} ${u.second_name}` : '—'}</td>
                        <td>
                          {u.is_admin ? (
                            <span className="badge badge-warning">Admin</span>
                          ) : (
                            <span className="badge badge-secondary">User</span>
                          )}
                        </td>
                        <td>
                          {u.enabled ? (
                            <span className="badge badge-success">Enabled</span>
                          ) : (
                            <span className="badge badge-error">Disabled</span>
                          )}
                        </td>
                        <td>{formatDate(u.created_at)}</td>
                        <td>
                          <div className="action-buttons">
                            <button
                              onClick={() => loadUserDetails(u.id)}
                              className="btn btn-sm btn-primary"
                              disabled={actionLoading === 'user-details'}
                            >
                              Details
                            </button>
                            <button
                              onClick={() => handleToggleUser(u.id, u.enabled)}
                              className={`btn btn-sm ${u.enabled ? 'btn-warning' : 'btn-success'}`}
                              disabled={actionLoading === `toggle-user-${u.id}` || u.id === user?.id}
                              title={u.id === user?.id ? 'Cannot toggle your own account' : ''}
                            >
                              {u.enabled ? 'Disable' : 'Enable'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* User Details Modal */}
          {selectedUser && (
            <div className="modal-overlay" onClick={() => setSelectedUser(null)}>
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                  <h2>User Details</h2>
                  <button className="modal-close" onClick={() => setSelectedUser(null)}>✕</button>
                </div>
                
                <div className="modal-body">
                  <div className="user-details-grid">
                    <div className="detail-item">
                      <strong>ID:</strong>
                      <span className="monospace">{selectedUser.id}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Nick:</strong>
                      <span>{selectedUser.nick || '—'}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Email:</strong>
                      <span>{selectedUser.email || '—'}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Name:</strong>
                      <span>
                        {selectedUser.first_name && selectedUser.second_name
                          ? `${selectedUser.first_name} ${selectedUser.second_name}`
                          : '—'}
                      </span>
                    </div>
                    <div className="detail-item">
                      <strong>Phone:</strong>
                      <span>{selectedUser.phone_number || '—'}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Role:</strong>
                      <span>{selectedUser.is_admin ? 'Admin' : 'User'}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Status:</strong>
                      <span>{selectedUser.enabled ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Created:</strong>
                      <span>{formatDate(selectedUser.created_at)}</span>
                    </div>
                    <div className="detail-item">
                      <strong>Updated:</strong>
                      <span>{formatDate(selectedUser.updated_at)}</span>
                    </div>
                  </div>

                  <h3 style={{ marginTop: '2rem' }}>Authentication Methods</h3>
                  {userAuthMethods.length === 0 ? (
                    <p>No authentication methods found.</p>
                  ) : (
                    <div className="auth-methods-list">
                      {userAuthMethods.map((method) => (
                        <div key={method.id} className="auth-method-item">
                          <div className="auth-method-header">
                            <span className="auth-method-icon">{getAuthMethodIcon(method.type)}</span>
                            <strong>{method.identifier || method.type}</strong>
                            {method.enabled ? (
                              <span className="badge badge-success">Enabled</span>
                            ) : (
                              <span className="badge badge-error">Disabled</span>
                            )}
                            {method.requires_approval && !method.approved && (
                              <span className="badge badge-warning">Pending</span>
                            )}
                          </div>
                          <div className="auth-method-details">
                            <small>Type: {method.type}</small>
                            <small>Created: {formatDate(method.created_at)}</small>
                          </div>
                          <div className="auth-method-actions">
                            {method.requires_approval && !method.approved && (
                              <button
                                onClick={() => handleApproveAuthMethod(method.id)}
                                className="btn btn-sm btn-success"
                                disabled={actionLoading === `approve-${method.id}`}
                              >
                                Approve
                              </button>
                            )}
                            <button
                              onClick={() => handleToggleAuthMethod(method.id, method.enabled)}
                              className={`btn btn-sm ${method.enabled ? 'btn-warning' : 'btn-success'}`}
                              disabled={actionLoading === `toggle-auth-${method.id}`}
                            >
                              {method.enabled ? 'Disable' : 'Enable'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pending Approvals Tab */}
      {activeTab === 'approvals' && (
        <div className="admin-content">
          <div className="card">
            <h3>Pending Authentication Method Approvals</h3>
            {isLoading ? (
              <p>Loading pending approvals...</p>
            ) : pendingApprovals.length === 0 ? (
              <p>No pending approvals.</p>
            ) : (
              <div className="approvals-list">
                {pendingApprovals.map((method) => (
                  <div key={method.id} className="approval-item card">
                    <div className="approval-header">
                      <span className="auth-method-icon">{getAuthMethodIcon(method.type)}</span>
                      <div>
                        <strong>{method.identifier || method.type}</strong>
                        <br />
                        <small className="text-muted">Type: {method.type}</small>
                      </div>
                      <span className="badge badge-warning">Pending Approval</span>
                    </div>
                    <div className="approval-details">
                      <p><strong>User ID:</strong> <span className="monospace">{method.user_id}</span></p>
                      <p><strong>Created:</strong> {formatDate(method.created_at)}</p>
                      <p><strong>Enabled:</strong> {method.enabled ? 'Yes' : 'No'}</p>
                    </div>
                    <div className="approval-actions">
                      <button
                        onClick={() => handleApproveAuthMethod(method.id)}
                        className="btn btn-success"
                        disabled={actionLoading === `approve-${method.id}`}
                      >
                        {actionLoading === `approve-${method.id}` ? 'Approving...' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleToggleAuthMethod(method.id, method.enabled)}
                        className="btn btn-error"
                        disabled={actionLoading === `toggle-auth-${method.id}`}
                      >
                        Disable
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Version Info */}
      <div style={{ marginTop: '3rem' }}>
        <VersionInfo />
      </div>
    </div>
  );
}

export default Admin;

