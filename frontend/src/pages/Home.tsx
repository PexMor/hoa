/**
 * Home Page
 * 
 * Landing page with links to login/register
 */

import { route } from 'preact-router';
import { useAuth } from '../hooks/useAuth';
import { useEffect } from 'preact/hooks';
import VersionInfo from '../components/VersionInfo';

interface RouteProps {
  path?: string;
}

export function Home(_props?: RouteProps) {
  const { isAuthenticated } = useAuth();

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      route('/dashboard');
    }
  }, [isAuthenticated]);

  return (
    <div className="home-container">
      <div className="hero">
        <h1>🔐 HOA</h1>
        <p className="tagline">Heavily Over-engineered Authentication</p>
        <p className="subtitle">
          Passwordless authentication with WebAuthn/Passkeys
        </p>

        <div className="cta-buttons">
          <button className="btn btn-primary btn-large" onClick={() => route('/login')}>
            Sign In
          </button>
          <button className="btn btn-secondary btn-large" onClick={() => route('/register')}>
            Create Account
          </button>
        </div>
      </div>

      <div className="features">
        <div className="feature">
          <h3>🔒 Secure</h3>
          <p>Phishing-resistant authentication using FIDO2/WebAuthn standards</p>
        </div>
        <div className="feature">
          <h3>🚀 Fast</h3>
          <p>One-click login with Touch ID, Windows Hello, or security keys</p>
        </div>
        <div className="feature">
          <h3>🎯 Simple</h3>
          <p>No passwords to remember, no SMS codes, no email verification</p>
        </div>
      </div>

      <div style={{ marginTop: '3rem' }}>
        <VersionInfo />
      </div>
    </div>
  );
}

export default Home;
