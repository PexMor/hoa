/**
 * WebAuthn Client Helpers
 * 
 * Handles client-side WebAuthn/Passkey operations including:
 * - ArrayBuffer <-> Base64URL conversion
 * - Registration ceremony
 * - Authentication ceremony
 * - IndexedDB credential storage
 */

// ===== Base64URL Conversion =====

/**
 * Convert ArrayBuffer to Base64URL string
 */
function arrayBufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  // Convert base64 to base64url
  return base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

/**
 * Convert Base64URL string to ArrayBuffer
 */
function base64urlToArrayBuffer(base64url: string): ArrayBuffer {
  // Convert base64url to base64
  let base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  // Pad with =
  while (base64.length % 4) {
    base64 += '=';
  }
  
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

// ===== WebAuthn Types =====

export interface RegistrationOptions {
  challenge: string;
  rp: {
    id: string;
    name: string;
  };
  user: {
    id: string;
    name: string;
    displayName: string;
  };
  pubKeyCredParams: Array<{
    type: 'public-key';
    alg: number;
  }>;
  timeout?: number;
  attestation?: AttestationConveyancePreference;
  authenticatorSelection?: AuthenticatorSelectionCriteria;
  excludeCredentials?: Array<{
    id: string;
    type: 'public-key';
    transports?: AuthenticatorTransport[];
  }>;
}

export interface AuthenticationOptions {
  challenge: string;
  rpId: string;
  timeout?: number;
  userVerification?: UserVerificationRequirement;
  allowCredentials?: Array<{
    id: string;
    type: 'public-key';
    transports?: AuthenticatorTransport[];
  }>;
}

export interface RegistrationCredential {
  id: string;
  rawId: string;
  response: {
    clientDataJSON: string;
    attestationObject: string;
    transports?: AuthenticatorTransport[];
  };
  type: 'public-key';
}

export interface AuthenticationCredential {
  id: string;
  rawId: string;
  response: {
    clientDataJSON: string;
    authenticatorData: string;
    signature: string;
    userHandle: string | null;
  };
  type: 'public-key';
}

// ===== Registration =====

/**
 * Start WebAuthn registration ceremony
 * Converts backend options to WebAuthn API format and creates credential
 */
export async function startRegistration(
  options: RegistrationOptions
): Promise<RegistrationCredential> {
  // Convert options to WebAuthn API format
  const publicKeyOptions: PublicKeyCredentialCreationOptions = {
    challenge: base64urlToArrayBuffer(options.challenge),
    rp: {
      id: options.rp.id,
      name: options.rp.name,
    },
    user: {
      id: base64urlToArrayBuffer(options.user.id),
      name: options.user.name,
      displayName: options.user.displayName,
    },
    pubKeyCredParams: options.pubKeyCredParams,
    timeout: options.timeout || 60000,
    attestation: options.attestation || 'none',
    authenticatorSelection: options.authenticatorSelection || {
      authenticatorAttachment: 'platform',
      residentKey: 'preferred',
      userVerification: 'preferred',
    },
    excludeCredentials: options.excludeCredentials?.map((cred) => ({
      id: base64urlToArrayBuffer(cred.id),
      type: 'public-key',
      transports: cred.transports,
    })),
  };

  // Create credential
  const credential = await navigator.credentials.create({
    publicKey: publicKeyOptions,
  }) as PublicKeyCredential;

  if (!credential) {
    throw new Error('Failed to create credential');
  }

  // Convert credential to format expected by backend
  const response = credential.response as AuthenticatorAttestationResponse;
  
  return {
    id: credential.id,
    rawId: arrayBufferToBase64url(credential.rawId),
    response: {
      clientDataJSON: arrayBufferToBase64url(response.clientDataJSON),
      attestationObject: arrayBufferToBase64url(response.attestationObject),
      transports: response.getTransports ? (response.getTransports() as AuthenticatorTransport[]) : undefined,
    },
    type: 'public-key',
  };
}

/**
 * Format registration credential for backend
 */
export function finishRegistration(
  credential: RegistrationCredential
): RegistrationCredential {
  // Already in correct format from startRegistration
  return credential;
}

// ===== Authentication =====

/**
 * Start WebAuthn authentication ceremony
 * Converts backend options to WebAuthn API format and gets credential
 */
export async function startAuthentication(
  options: AuthenticationOptions
): Promise<AuthenticationCredential> {
  // Convert options to WebAuthn API format
  const publicKeyOptions: PublicKeyCredentialRequestOptions = {
    challenge: base64urlToArrayBuffer(options.challenge),
    rpId: options.rpId,
    timeout: options.timeout || 60000,
    userVerification: options.userVerification || 'preferred',
    allowCredentials: options.allowCredentials?.map((cred) => ({
      id: base64urlToArrayBuffer(cred.id),
      type: 'public-key',
      transports: cred.transports,
    })),
  };

  // Get credential
  const credential = await navigator.credentials.get({
    publicKey: publicKeyOptions,
  }) as PublicKeyCredential;

  if (!credential) {
    throw new Error('Failed to get credential');
  }

  // Convert credential to format expected by backend
  const response = credential.response as AuthenticatorAssertionResponse;
  
  return {
    id: credential.id,
    rawId: arrayBufferToBase64url(credential.rawId),
    response: {
      clientDataJSON: arrayBufferToBase64url(response.clientDataJSON),
      authenticatorData: arrayBufferToBase64url(response.authenticatorData),
      signature: arrayBufferToBase64url(response.signature),
      userHandle: response.userHandle ? arrayBufferToBase64url(response.userHandle) : null,
    },
    type: 'public-key',
  };
}

/**
 * Format authentication credential for backend
 */
export function finishAuthentication(
  credential: AuthenticationCredential
): AuthenticationCredential {
  // Already in correct format from startAuthentication
  return credential;
}

// ===== IndexedDB Storage =====

const DB_NAME = 'HOA_WebAuthn';
const DB_VERSION = 1;
const STORE_NAME = 'credentials';

/**
 * Initialize IndexedDB for credential storage
 */
function initDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'credentialId' });
        store.createIndex('userId', 'userId', { unique: false });
      }
    };
  });
}

export interface StoredCredential {
  credentialId: string;
  userId: string;
  userName: string;
  displayName: string;
  rpId: string;
  createdAt: string;
}

/**
 * Store credential info in IndexedDB
 */
export async function storeCredential(credential: StoredCredential): Promise<void> {
  const db = await initDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  const store = tx.objectStore(STORE_NAME);
  
  await new Promise<void>((resolve, reject) => {
    const request = store.put(credential);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
  
  db.close();
}

/**
 * Get all stored credentials for a user
 */
export async function getStoredCredentials(userId?: string): Promise<StoredCredential[]> {
  const db = await initDB();
  const tx = db.transaction(STORE_NAME, 'readonly');
  const store = tx.objectStore(STORE_NAME);
  
  const credentials: StoredCredential[] = await new Promise((resolve, reject) => {
    if (userId) {
      const index = store.index('userId');
      const request = index.getAll(userId);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    } else {
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    }
  });
  
  db.close();
  return credentials;
}

/**
 * Delete a stored credential
 */
export async function deleteStoredCredential(credentialId: string): Promise<void> {
  const db = await initDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  const store = tx.objectStore(STORE_NAME);
  
  await new Promise<void>((resolve, reject) => {
    const request = store.delete(credentialId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
  
  db.close();
}

/**
 * Clear all stored credentials
 */
export async function clearStoredCredentials(): Promise<void> {
  const db = await initDB();
  const tx = db.transaction(STORE_NAME, 'readwrite');
  const store = tx.objectStore(STORE_NAME);
  
  await new Promise<void>((resolve, reject) => {
    const request = store.clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
  
  db.close();
}

// ===== WebAuthn Support Detection =====

/**
 * Check if WebAuthn is supported in this browser
 */
export function isWebAuthnSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    typeof window.PublicKeyCredential !== 'undefined' &&
    navigator.credentials &&
    typeof navigator.credentials.create !== 'undefined' &&
    typeof navigator.credentials.get !== 'undefined'
  );
}

/**
 * Check if platform authenticator is available (TouchID, Windows Hello, etc.)
 */
export async function isPlatformAuthenticatorAvailable(): Promise<boolean> {
  if (!isWebAuthnSupported()) {
    return false;
  }
  
  try {
    if (typeof PublicKeyCredential !== 'undefined' && 
        typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function') {
      return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    }
    return false;
  } catch {
    return false;
  }
}

