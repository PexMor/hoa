/**
 * Registration Page
 * 
 * New user registration with passkey creation
 */

import { useState, useRef } from 'preact/hooks';
import { route } from 'preact-router';
import { useAuth } from '../hooks/useAuth';
import { isWebAuthnSupported } from '../services/webauthn';
import type { RegisterFormData } from '../types';

interface RouteProps {
  path?: string;
}

export function Register(_props?: RouteProps) {
  const { register } = useAuth();
  
  const [formData, setFormData] = useState<RegisterFormData>({
    nick: '',
    email: '',
    first_name: '',
    second_name: '',
    phone_number: '',
  });
  
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [webAuthnSupported] = useState(isWebAuthnSupported());
  const submittingRef = useRef(false);

  const handleInputChange = (field: keyof RegisterFormData, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    
    // Prevent duplicate submissions
    if (submittingRef.current) {
      console.log('[DEBUG] Preventing duplicate submission');
      return;
    }
    
    // Validation
    if (!formData.nick.trim()) {
      setError('Username is required');
      return;
    }

    if (!formData.email?.trim()) {
      setError('Email is required');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setError(null);
    setIsLoading(true);
    submittingRef.current = true;

    try {
      // Register user and create passkey
      await register({
        nick: formData.nick,
        email: formData.email,
        first_name: formData.first_name || undefined,
        second_name: formData.second_name || undefined,
        phone_number: formData.phone_number || undefined,
      });
      
      // Auto-redirect to dashboard on success
      route('/dashboard');
    } catch (err: any) {
      console.error('Registration error:', err);
      
      // Handle specific error cases
      if (err.message?.includes('already exists')) {
        setError('A user with this email already exists');
      } else if (err.message?.includes('canceled')) {
        setError('Passkey creation was canceled. Please try again.');
      } else if (err.message?.includes('NotAllowedError')) {
        setError('Unable to create passkey. Please check your authenticator.');
      } else {
        setError(err.message || 'Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
      submittingRef.current = false;
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h1>Create Account</h1>
        <p className="subtitle">Join HOA with passwordless authentication</p>
        
        {!webAuthnSupported && (
          <div className="warning">
            ⚠️ WebAuthn is not supported in this browser. Please use a modern browser.
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="nick">Username *</label>
            <input
              id="nick"
              type="text"
              value={formData.nick}
              onInput={(e) => handleInputChange('nick', (e.target as HTMLInputElement).value)}
              placeholder="johndoe"
              disabled={isLoading || !webAuthnSupported}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onInput={(e) => handleInputChange('email', (e.target as HTMLInputElement).value)}
              placeholder="john@example.com"
              disabled={isLoading || !webAuthnSupported}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                id="first_name"
                type="text"
                value={formData.first_name}
                onInput={(e) => handleInputChange('first_name', (e.target as HTMLInputElement).value)}
                placeholder="John"
                disabled={isLoading || !webAuthnSupported}
              />
            </div>

            <div className="form-group">
              <label htmlFor="second_name">Last Name</label>
              <input
                id="second_name"
                type="text"
                value={formData.second_name}
                onInput={(e) => handleInputChange('second_name', (e.target as HTMLInputElement).value)}
                placeholder="Doe"
                disabled={isLoading || !webAuthnSupported}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="phone_number">Phone Number</label>
            <input
              id="phone_number"
              type="tel"
              value={formData.phone_number}
              onInput={(e) => handleInputChange('phone_number', (e.target as HTMLInputElement).value)}
              placeholder="+1 (555) 123-4567"
              disabled={isLoading || !webAuthnSupported}
            />
          </div>

          {error && <div className="error">{error}</div>}

          <div className="info">
            ℹ️ After submitting, you'll be prompted to create a passkey using your device's authenticator
            (Touch ID, Windows Hello, or security key).
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !webAuthnSupported}
          >
            {isLoading ? 'Creating account...' : '🔐 Create Account & Passkey'}
          </button>

          <div className="footer-links">
            Already have an account? <a href="/login">Sign in</a>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Register;
