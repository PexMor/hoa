# HOA API Reference

Complete API documentation for HOA authentication system.

**Base URL**: `http://localhost:8000/api`

**Version**: 1.0.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Utility Endpoints](#utility-endpoints)
3. [Auth API](#auth-api)
4. [M2M API](#m2m-api)
5. [User API](#user-api)
6. [Admin API](#admin-api)
7. [Error Responses](#error-responses)
8. [WebAuthn Types](#webauthn-types)

---

## Authentication

HOA supports multiple authentication methods:

- **WebAuthn/Passkeys** (Primary): FIDO2-compliant biometric authentication
- **Admin Token**: Bootstrap authentication for initial setup
- **JWT Tokens**: Machine-to-machine authentication
- **Session Cookies**: Web session management (HTTP-only, secure)

### Session Authentication

Most endpoints require an authenticated session. After logging in via WebAuthn or admin token, the server sets a secure session cookie that is automatically included in subsequent requests.

### JWT Authentication

M2M endpoints support JWT bearer tokens:

```http
Authorization: Bearer <your-jwt-token>
```

---

## Utility Endpoints

### GET /api/health

Health check endpoint with version information.

**Response**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "git_commit": "799577c",
  "git_branch": "main",
  "build_date": "2025-10-23 19:08:59 UTC"
}
```

### GET /api/version

Get detailed version information.

**Response**:

```json
{
  "version": "1.0.0",
  "git_commit": "799577c",
  "git_branch": "main",
  "build_date": "2025-10-23 19:08:59 UTC"
}
```

### GET /api/config

Get frontend configuration including allowed RPs and feature flags.

**Response**:

```json
{
  "allowed_rps": [
    {
      "rp_id": "localhost",
      "rp_name": "Local Development",
      "allowed_origins": ["http://localhost:8000", "http://127.0.0.1:8000"]
    }
  ],
  "require_auth_method_approval": false,
  "environment": "development",
  "version": "1.0.0",
  "git_commit": "799577c",
  "git_branch": "main",
  "build_date": "2025-10-23 19:08:59 UTC"
}
```

---

## Auth API

### POST /api/auth/webauthn/register/begin

Begin WebAuthn registration ceremony.

**Request Body**:

```json
{
  "nick": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "second_name": "Doe",
  "phone_number": "+1234567890",
  "rp_id": "localhost"
}
```

**Response**:

```json
{
  "options": {
    "challenge": "base64url-encoded-challenge",
    "rp": {
      "id": "localhost",
      "name": "Local Development"
    },
    "user": {
      "id": "base64url-encoded-user-id",
      "name": "john@example.com",
      "displayName": "John Doe"
    },
    "pubKeyCredParams": [...],
    "timeout": 60000,
    "excludeCredentials": [...],
    "authenticatorSelection": {
      "residentKey": "preferred",
      "userVerification": "preferred"
    },
    "attestation": "none"
  },
  "user_id": "uuid-v4-string"
}
```

### POST /api/auth/webauthn/register/finish

Complete WebAuthn registration ceremony.

**Request Body**:

```json
{
  "user_id": "uuid-v4-string",
  "credential": {
    "id": "credential-id",
    "rawId": "base64url-encoded-raw-id",
    "response": {
      "clientDataJSON": "base64url-encoded-json",
      "attestationObject": "base64url-encoded-object"
    },
    "type": "public-key"
  },
  "rp_id": "localhost"
}
```

**Response**:

```json
{
  "user": {
    "id": "uuid-v4-string",
    "nick": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "second_name": "Doe",
    "phone_number": "+1234567890",
    "enabled": true,
    "is_admin": false,
    "created_at": "2025-10-23T19:00:00Z",
    "updated_at": "2025-10-23T19:00:00Z"
  }
}
```

**Note**: Sets session cookie on success.

### POST /api/auth/webauthn/login/begin

Begin WebAuthn authentication ceremony.

**Request Body**:

```json
{
  "rp_id": "localhost"
}
```

**Response**:

```json
{
  "options": {
    "challenge": "base64url-encoded-challenge",
    "timeout": 60000,
    "rpId": "localhost",
    "allowCredentials": [
      {
        "type": "public-key",
        "id": "base64url-encoded-credential-id",
        "transports": ["usb", "nfc", "ble", "internal"]
      }
    ],
    "userVerification": "preferred"
  }
}
```

### POST /api/auth/webauthn/login/finish

Complete WebAuthn authentication ceremony.

**Request Body**:

```json
{
  "credential": {
    "id": "credential-id",
    "rawId": "base64url-encoded-raw-id",
    "response": {
      "clientDataJSON": "base64url-encoded-json",
      "authenticatorData": "base64url-encoded-data",
      "signature": "base64url-encoded-signature",
      "userHandle": "base64url-encoded-user-id"
    },
    "type": "public-key"
  },
  "rp_id": "localhost"
}
```

**Response**:

```json
{
  "user": {
    "id": "uuid-v4-string",
    "nick": "john_doe",
    "email": "john@example.com",
    "enabled": true,
    "is_admin": false
  }
}
```

**Note**: Sets session cookie on success.

### POST /api/auth/token/bootstrap

Authenticate using admin bootstrap token.

**Request Body**:

```json
{
  "token": "admin-token-from-config",
  "nick": "admin",
  "email": "admin@example.com"
}
```

**Response**:

```json
{
  "user": {
    "id": "uuid-v4-string",
    "nick": "admin",
    "email": "admin@example.com",
    "enabled": true,
    "is_admin": true
  }
}
```

**Note**: Creates admin user if no users exist, otherwise validates against existing admin token auth method.

### POST /api/auth/logout

Logout and clear session.

**Response**:

```json
{
  "message": "Logged out successfully"
}
```

### GET /api/auth/me

Get current authenticated user.

**Response**:

```json
{
  "id": "uuid-v4-string",
  "nick": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "second_name": "Doe",
  "phone_number": "+1234567890",
  "enabled": true,
  "is_admin": false,
  "created_at": "2025-10-23T19:00:00Z",
  "updated_at": "2025-10-23T19:00:00Z"
}
```

---

## M2M API

Machine-to-machine JWT token management.

### POST /api/m2m/token/create

Create JWT access and refresh tokens for the authenticated user.

**Authentication**: Requires session cookie

**Request Body** (optional):

```json
{
  "expires_delta_minutes": 60
}
```

**Response**:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /api/m2m/token/refresh

Refresh an access token using a refresh token.

**Request Body**:

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

**Response**:

```json
{
  "access_token": "new-jwt-access-token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /api/m2m/token/validate

Validate a JWT token.

**Request Body**:

```json
{
  "token": "jwt-token-to-validate"
}
```

**Response**:

```json
{
  "valid": true,
  "user_id": "uuid-v4-string",
  "expires_at": "2025-10-23T20:00:00Z"
}
```

**Error Response** (invalid token):

```json
{
  "valid": false,
  "error": "Token expired"
}
```

---

## User API

User profile and authentication method management.

### GET /api/users/me

Get current user profile.

**Response**: Same as `GET /api/auth/me`

### PUT /api/users/me

Update current user profile.

**Request Body**:

```json
{
  "nick": "new_nickname",
  "email": "newemail@example.com",
  "first_name": "Jane",
  "second_name": "Smith",
  "phone_number": "+1987654321"
}
```

**Response**:

```json
{
  "id": "uuid-v4-string",
  "nick": "new_nickname",
  "email": "newemail@example.com",
  "first_name": "Jane",
  "second_name": "Smith",
  "phone_number": "+1987654321",
  "enabled": true,
  "is_admin": false,
  "created_at": "2025-10-23T19:00:00Z",
  "updated_at": "2025-10-23T19:30:00Z"
}
```

### GET /api/users/me/auth-methods

List all authentication methods for the current user.

**Response**:

```json
[
  {
    "id": "uuid-v4-string",
    "type": "passkey",
    "identifier": "Credential 1",
    "enabled": true,
    "requires_approval": false,
    "approved": true,
    "created_at": "2025-10-23T19:00:00Z"
  },
  {
    "id": "uuid-v4-string",
    "type": "password",
    "identifier": "john@example.com",
    "enabled": true,
    "requires_approval": false,
    "approved": true,
    "created_at": "2025-10-23T19:15:00Z"
  }
]
```

### DELETE /api/users/me/auth-methods/{auth_method_id}

Delete an authentication method.

**Path Parameters**:

- `auth_method_id`: UUID of the authentication method

**Response**:

```json
{
  "message": "Authentication method deleted successfully"
}
```

**Error** (last auth method):

```json
{
  "detail": "Cannot delete the last authentication method"
}
```

---

## Admin API

Administrative user and authentication method management. Requires admin privileges.

### GET /api/admin/users

List all users with optional filtering and pagination.

**Query Parameters**:

- `enabled`: boolean (optional) - Filter by enabled status
- `is_admin`: boolean (optional) - Filter by admin status
- `skip`: integer (optional, default=0) - Pagination offset
- `limit`: integer (optional, default=100) - Items per page

**Example**: `GET /api/admin/users?enabled=true&limit=50`

**Response**:

```json
[
  {
    "id": "uuid-v4-string",
    "nick": "john_doe",
    "email": "john@example.com",
    "enabled": true,
    "is_admin": false,
    "created_at": "2025-10-23T19:00:00Z"
  },
  ...
]
```

### GET /api/admin/users/{user_id}

Get details for a specific user.

**Path Parameters**:

- `user_id`: UUID of the user

**Response**: Same as user object

### POST /api/admin/users/{user_id}/toggle

Toggle user enabled/disabled status.

**Path Parameters**:

- `user_id`: UUID of the user

**Response**:

```json
{
  "id": "uuid-v4-string",
  "enabled": false,
  "message": "User disabled successfully"
}
```

### GET /api/admin/users/{user_id}/auth-methods

Get all authentication methods for a specific user.

**Path Parameters**:

- `user_id`: UUID of the user

**Response**: Same as `GET /api/users/me/auth-methods`

### POST /api/admin/auth-methods/{auth_method_id}/approve

Approve a pending authentication method.

**Path Parameters**:

- `auth_method_id`: UUID of the authentication method

**Response**:

```json
{
  "id": "uuid-v4-string",
  "approved": true,
  "approved_by": "admin-user-uuid",
  "message": "Authentication method approved"
}
```

### POST /api/admin/auth-methods/{auth_method_id}/toggle

Toggle authentication method enabled/disabled status.

**Path Parameters**:

- `auth_method_id`: UUID of the authentication method

**Response**:

```json
{
  "id": "uuid-v4-string",
  "enabled": false,
  "message": "Authentication method disabled"
}
```

### GET /api/admin/auth-methods/pending

Get all authentication methods pending approval.

**Response**:

```json
[
  {
    "id": "uuid-v4-string",
    "user_id": "user-uuid",
    "type": "passkey",
    "identifier": "New Credential",
    "enabled": true,
    "requires_approval": true,
    "approved": false,
    "created_at": "2025-10-23T19:00:00Z"
  },
  ...
]
```

---

## Error Responses

All endpoints return standard HTTP status codes and JSON error responses.

### Success Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully

### Client Error Codes

- `400 Bad Request`: Invalid request body or parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

### Server Error Codes

- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## WebAuthn Types

### Registration Options

Generated by `POST /api/auth/webauthn/register/begin`:

```typescript
{
  challenge: string;           // Base64url-encoded random challenge
  rp: {
    id: string;               // Relying Party ID (e.g., "localhost")
    name: string;             // Relying Party name
  };
  user: {
    id: string;               // Base64url-encoded user ID
    name: string;             // User identifier (email)
    displayName: string;      // User display name
  };
  pubKeyCredParams: Array<{
    type: "public-key";
    alg: number;              // Algorithm ID (e.g., -7 for ES256)
  }>;
  timeout: number;            // Timeout in milliseconds
  excludeCredentials?: Array<{
    type: "public-key";
    id: string;               // Base64url-encoded credential ID
    transports?: string[];    // ["usb", "nfc", "ble", "internal"]
  }>;
  authenticatorSelection?: {
    residentKey: "preferred" | "required" | "discouraged";
    userVerification: "preferred" | "required" | "discouraged";
  };
  attestation: "none" | "indirect" | "direct";
}
```

### Authentication Options

Generated by `POST /api/auth/webauthn/login/begin`:

```typescript
{
  challenge: string; // Base64url-encoded random challenge
  timeout: number; // Timeout in milliseconds
  rpId: string; // Relying Party ID
  allowCredentials: Array<{
    type: "public-key";
    id: string; // Base64url-encoded credential ID
    transports?: string[]; // ["usb", "nfc", "ble", "internal"]
  }>;
  userVerification: "preferred" | "required" | "discouraged";
}
```

### Registration Credential

Sent to `POST /api/auth/webauthn/register/finish`:

```typescript
{
  id: string; // Credential ID
  rawId: string; // Base64url-encoded raw credential ID
  response: {
    clientDataJSON: string; // Base64url-encoded client data
    attestationObject: string; // Base64url-encoded attestation object
  }
  type: "public-key";
}
```

### Authentication Credential

Sent to `POST /api/auth/webauthn/login/finish`:

```typescript
{
  id: string;                 // Credential ID
  rawId: string;              // Base64url-encoded raw credential ID
  response: {
    clientDataJSON: string;   // Base64url-encoded client data
    authenticatorData: string;// Base64url-encoded authenticator data
    signature: string;        // Base64url-encoded signature
    userHandle?: string;      // Base64url-encoded user handle
  };
  type: "public-key";
}
```

---

## Rate Limiting

**Status**: Not implemented (planned for future release)

Rate limiting will be added to prevent abuse:

- Auth endpoints: 10 requests/minute per IP
- M2M endpoints: 100 requests/minute per user
- Admin endpoints: 50 requests/minute per admin

---

## CORS Configuration

CORS is configurable via environment variables:

```bash
HOA_CORS_ENABLED=true
HOA_CORS_ORIGINS='["http://localhost:8000", "https://yourdomain.com"]'
```

Defaults allow localhost origins in development.

---

## Examples

### Complete Registration Flow

```javascript
// 1. Begin registration
const beginResponse = await fetch("/api/auth/webauthn/register/begin", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    nick: "john_doe",
    email: "john@example.com",
    rp_id: "localhost",
  }),
});

const { options, user_id } = await beginResponse.json();

// 2. Create credential with WebAuthn API
const credential = await navigator.credentials.create({
  publicKey: options,
});

// 3. Finish registration
const finishResponse = await fetch("/api/auth/webauthn/register/finish", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id,
    credential: credentialToJSON(credential),
    rp_id: "localhost",
  }),
});

const { user } = await finishResponse.json();
console.log("Registered:", user);
```

### Complete Login Flow

```javascript
// 1. Begin authentication
const beginResponse = await fetch("/api/auth/webauthn/login/begin", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ rp_id: "localhost" }),
});

const { options } = await beginResponse.json();

// 2. Get credential with WebAuthn API
const credential = await navigator.credentials.get({
  publicKey: options,
});

// 3. Finish authentication
const finishResponse = await fetch("/api/auth/webauthn/login/finish", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    credential: credentialToJSON(credential),
    rp_id: "localhost",
  }),
});

const { user } = await finishResponse.json();
console.log("Logged in:", user);
```

### M2M Token Usage

```javascript
// 1. Create token (after web login)
const tokenResponse = await fetch("/api/m2m/token/create", {
  method: "POST",
  credentials: "include", // Include session cookie
});

const { access_token } = await tokenResponse.json();

// 2. Use token for API requests
const apiResponse = await fetch("https://api.example.com/data", {
  headers: {
    Authorization: `Bearer ${access_token}`,
  },
});
```

---

## See Also

- [Development Guide](development.md)
- [Deployment Guide](deployment.md)
- [Architecture Documentation](../AGENTS.md)
- [WebAuthn Specification](https://www.w3.org/TR/webauthn-2/)
