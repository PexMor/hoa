/**
 * Add Authentication Method Modal
 * 
 * Modal for adding new authentication methods (passkeys, password)
 */

import { useState } from 'preact/hooks';
import { api } from '../services/api';
import { startRegistration } from '../services/webauthn';
import { getConfig } from '../config';

interface AddAuthMethodModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

type AuthMethodType = 'passkey' | 'password' | 'token';

export function AddAuthMethodModal({ onClose, onSuccess }: AddAuthMethodModalProps) {
  const [selectedType, setSelectedType] = useState<AuthMethodType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Password form state
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Token form state
  const [tokenDescription, setTokenDescription] = useState('');
  const [tokenExpireDays, setTokenExpireDays] = useState('30');
  const [createdToken, setCreatedToken] = useState<{
    access_token: string;
    refresh_token: string;
    expires_at: string;
  } | null>(null);

  const handleAddPassword = async () => {
    setError(null);

    // Validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await api.user.addPasswordAuth(password);
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Failed to add password:', err);
      setError(err.message || 'Failed to add password authentication');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateToken = async () => {
    setError(null);

    // Validation
    if (tokenDescription.trim().length < 3) {
      setError('Description must be at least 3 characters long');
      return;
    }

    const days = parseInt(tokenExpireDays);
    if (isNaN(days) || days < 1 || days > 365) {
      setError('Expiration must be between 1 and 365 days');
      return;
    }

    setIsLoading(true);

    try {
      const result = await api.user.createApiToken(tokenDescription, days);
      setCreatedToken({
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        expires_at: result.expires_at,
      });
      onSuccess();
      // Don't close yet - show the tokens first
    } catch (err: any) {
      console.error('Failed to create token:', err);
      setError(err.message || 'Failed to create API token');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPasskey = async () => {
    setError(null);
    setIsLoading(true);

    try {
      const config = getConfig();
      const rp = config.allowed_rps[0];
      const origin = window.location.origin;

      // Step 1: Begin passkey registration
      const { options } = await api.user.beginAddPasskey({
        rp_id: rp.rp_id,
        origin: origin,
        display_name: 'Additional Passkey',
      });

      // Step 2: Create WebAuthn credential
      const credential = await startRegistration(options);

      // Step 3: Finish passkey registration
      await api.user.finishAddPasskey({
        rp_id: rp.rp_id,
        origin: origin,
        credential,
      });

      onSuccess();
      onClose();
    } catch (err: any) {
      console.error('Failed to add passkey:', err);
      if (err.name === 'NotAllowedError') {
        setError('Passkey creation was cancelled');
      } else {
        setError(err.message || 'Failed to add passkey');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Authentication Method</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {!selectedType ? (
            // Selection screen
            <div className="auth-method-selection">
              <p>Choose an authentication method to add:</p>
              
              <button
                className="auth-method-option"
                onClick={() => setSelectedType('passkey')}
              >
                <span className="option-icon">🔐</span>
                <div className="option-details">
                  <strong>Passkey</strong>
                  <p>Use Touch ID, Windows Hello, or a security key</p>
                </div>
              </button>

              <button
                className="auth-method-option"
                onClick={() => setSelectedType('password')}
              >
                <span className="option-icon">🔑</span>
                <div className="option-details">
                  <strong>Password</strong>
                  <p>Traditional password authentication</p>
                </div>
              </button>

              <button
                className="auth-method-option"
                onClick={() => setSelectedType('token')}
              >
                <span className="option-icon">🎫</span>
                <div className="option-details">
                  <strong>API Token</strong>
                  <p>JWT token for API access and automation</p>
                </div>
              </button>
            </div>
          ) : selectedType === 'password' ? (
            // Password form
            <div className="auth-method-form">
              <button
                className="btn btn-link"
                onClick={() => setSelectedType(null)}
              >
                ← Back
              </button>

              <h3>Add Password</h3>

              <div className="form-group">
                <label htmlFor="password">Password *</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onInput={(e) => setPassword((e.target as HTMLInputElement).value)}
                  placeholder="Enter password (min 8 characters)"
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password *</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onInput={(e) => setConfirmPassword((e.target as HTMLInputElement).value)}
                  placeholder="Confirm password"
                  disabled={isLoading}
                  required
                />
              </div>

              {error && <div className="error">{error}</div>}

              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleAddPassword}
                  disabled={isLoading || !password || !confirmPassword}
                >
                  {isLoading ? 'Adding...' : 'Add Password'}
                </button>
              </div>
            </div>
          ) : selectedType === 'token' ? (
            // Token creation form
            <div className="auth-method-form">
              <button
                className="btn btn-link"
                onClick={() => {
                  setSelectedType(null);
                  setCreatedToken(null);
                }}
              >
                ← Back
              </button>

              {!createdToken ? (
                <>
                  <h3>Create API Token</h3>

                  <p>
                    Create a JWT token for API access. This token can be used for
                    automation and programmatic access to your account.
                  </p>

                  <div className="form-group">
                    <label htmlFor="tokenDescription">Description *</label>
                    <input
                      id="tokenDescription"
                      type="text"
                      value={tokenDescription}
                      onInput={(e) => setTokenDescription((e.target as HTMLInputElement).value)}
                      placeholder="e.g., CI/CD Pipeline, Mobile App, etc."
                      disabled={isLoading}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="tokenExpireDays">Expires in (days) *</label>
                    <input
                      id="tokenExpireDays"
                      type="number"
                      min="1"
                      max="365"
                      value={tokenExpireDays}
                      onInput={(e) => setTokenExpireDays((e.target as HTMLInputElement).value)}
                      disabled={isLoading}
                      required
                    />
                    <small className="form-hint">
                      Token will expire in {tokenExpireDays} days (max 365)
                    </small>
                  </div>

                  {error && <div className="error">{error}</div>}

                  <div className="modal-footer">
                    <button
                      className="btn btn-secondary"
                      onClick={onClose}
                      disabled={isLoading}
                    >
                      Cancel
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleCreateToken}
                      disabled={isLoading || !tokenDescription.trim()}
                    >
                      {isLoading ? 'Creating...' : '🎫 Create Token'}
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <h3>✅ Token Created Successfully!</h3>

                  <div className="warning">
                    <strong>⚠️ Important:</strong> Copy these tokens now. You won't be able
                    to see them again!
                  </div>

                  <div className="form-group">
                    <label htmlFor="accessToken">Access Token</label>
                    <textarea
                      id="accessToken"
                      value={createdToken.access_token}
                      readOnly
                      rows={4}
                      onClick={(e) => (e.target as HTMLTextAreaElement).select()}
                    />
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        navigator.clipboard.writeText(createdToken.access_token);
                        alert('Access token copied to clipboard!');
                      }}
                    >
                      📋 Copy Access Token
                    </button>
                  </div>

                  <div className="form-group">
                    <label htmlFor="refreshToken">Refresh Token</label>
                    <textarea
                      id="refreshToken"
                      value={createdToken.refresh_token}
                      readOnly
                      rows={4}
                      onClick={(e) => (e.target as HTMLTextAreaElement).select()}
                    />
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => {
                        navigator.clipboard.writeText(createdToken.refresh_token);
                        alert('Refresh token copied to clipboard!');
                      }}
                    >
                      📋 Copy Refresh Token
                    </button>
                  </div>

                  <div className="info">
                    <p><strong>Expires:</strong> {new Date(createdToken.expires_at).toLocaleString()}</p>
                    <p><strong>Usage:</strong> Include the access token in your API requests:</p>
                    <code>Authorization: Bearer YOUR_ACCESS_TOKEN</code>
                  </div>

                  <div className="modal-footer">
                    <button
                      className="btn btn-primary"
                      onClick={onClose}
                    >
                      Done
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            // Passkey prompt
            <div className="auth-method-form">
              <button
                className="btn btn-link"
                onClick={() => setSelectedType(null)}
              >
                ← Back
              </button>

              <h3>Add Passkey</h3>

              <p>
                Click the button below to create a new passkey using your device's
                authenticator (Touch ID, Windows Hello, or security key).
              </p>

              {error && <div className="error">{error}</div>}

              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={handleAddPasskey}
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating passkey...' : '🔐 Create Passkey'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AddAuthMethodModal;

