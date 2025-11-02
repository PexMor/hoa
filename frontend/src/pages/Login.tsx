/**
 * Login Page
 * 
 * Provides passkey login with admin token fallback
 */

import { useState } from 'preact/hooks';
import { route } from 'preact-router';
import { useAuth } from '../hooks/useAuth';
import { isWebAuthnSupported, isPlatformAuthenticatorAvailable } from '../services/webauthn';

interface RouteProps {
  path?: string;
}

export function Login(_props?: RouteProps) {
  const { login, bootstrapLogin } = useAuth();
  
  const [identifier, setIdentifier] = useState('');
  const [adminToken, setAdminToken] = useState('');
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [webAuthnSupported, setWebAuthnSupported] = useState(true);
  const [platformAuthAvailable, setPlatformAuthAvailable] = useState(false);

  // Check WebAuthn support on mount
  useState(() => {
    setWebAuthnSupported(isWebAuthnSupported());
    isPlatformAuthenticatorAvailable().then(setPlatformAuthAvailable);
  });

  const handlePasskeyLogin = async (e: Event) => {
    e.preventDefault();
    
    if (!identifier.trim()) {
      setError('Please enter your email or username');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await login(identifier);
      route('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdminLogin = async (e: Event) => {
    e.preventDefault();
    
    if (!adminToken.trim()) {
      setError('Please enter admin token');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      await bootstrapLogin(adminToken);
      route('/dashboard');
    } catch (err: any) {
      console.error('Admin login error:', err);
      setError(err.message || 'Invalid admin token');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Sign In to HOA</h1>
        
        {!webAuthnSupported && (
          <div className="warning">
            ⚠️ WebAuthn is not supported in this browser. Please use a modern browser.
          </div>
        )}

        {!showAdminLogin ? (
          // Passkey Login
          <form onSubmit={handlePasskeyLogin}>
            <div className="form-group">
              <label htmlFor="identifier">Email or Username</label>
              <input
                id="identifier"
                type="text"
                value={identifier}
                onInput={(e) => setIdentifier((e.target as HTMLInputElement).value)}
                placeholder="you@example.com"
                disabled={isLoading || !webAuthnSupported}
                autoFocus
              />
            </div>

            {error && <div className="error">{error}</div>}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || !webAuthnSupported}
            >
              {isLoading ? 'Signing in...' : '🔐 Sign in with Passkey'}
            </button>

            {platformAuthAvailable && (
              <div className="hint">
                ✨ Use your {navigator.platform.includes('Mac') ? 'Touch ID' : 'Windows Hello'} to sign in
              </div>
            )}

            <div className="divider">or</div>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowAdminLogin(true)}
              disabled={isLoading}
            >
              Use Admin Token
            </button>

            <div className="footer-links">
              Don't have an account? <a href="/register">Register</a>
            </div>
          </form>
        ) : (
          // Admin Token Login
          <form onSubmit={handleAdminLogin}>
            <div className="form-group">
              <label htmlFor="token">Admin Token</label>
              <input
                id="token"
                type="password"
                value={adminToken}
                onInput={(e) => setAdminToken((e.target as HTMLInputElement).value)}
                placeholder="Enter bootstrap token"
                disabled={isLoading}
                autoFocus
              />
              <small>
                This token is generated on first startup and stored in{' '}
                <code>~/.config/hoa/admin.txt</code>
              </small>
            </div>

            {error && <div className="error">{error}</div>}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign in with Token'}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setShowAdminLogin(false);
                setError(null);
              }}
              disabled={isLoading}
            >
              ← Back to Passkey Login
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default Login;
