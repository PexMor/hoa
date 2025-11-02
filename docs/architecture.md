# HOA Architecture

## Overview

HOA (Heavily Over-engineered Authentication) is a production-ready authentication system built with modern web technologies. It features WebAuthn/Passkeys as the primary authentication method, JWT tokens for machine-to-machine communication, and a flexible architecture that separates users from authentication methods.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │  Preact + TypeScript (SPA)
│  (Vite Build)   │  - Dynamic config loading
└────────┬────────┘  - IndexedDB for credentials
         │
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│   FastAPI       │  Python Backend
│   Backend       │  - REST API
│                 │  - Session management
│                 │  - JWT issuing
└────────┬────────┘
         │
         │ SQLAlchemy ORM
         ▼
┌─────────────────┐
│    Database     │  SQLite / PostgreSQL
│   (SQLAlchemy)  │  - Users
│                 │  - AuthMethods
│                 │  - Sessions
│                 │  - JWT Keys
└─────────────────┘
```

### Backend Architecture

#### Layered Architecture

1. **API Layer** (`hoa/api/`)

   - REST endpoints
   - Request validation (Pydantic)
   - Response serialization
   - Routes: auth, users, admin, m2m

2. **Service Layer** (`hoa/services/`)

   - Business logic
   - WebAuthn ceremonies
   - JWT token management
   - User management
   - Auth method management

3. **Data Layer** (`hoa/models/`)

   - SQLAlchemy ORM models
   - Database schema
   - Relationships

4. **Utilities** (`hoa/utils/`)
   - Cryptography
   - Validation
   - Helper functions

#### Key Components

##### Configuration Management

- **configargparse**: CLI > ENV > Config File precedence
- Configuration stored in `~/.config/hoa/config.yaml`
- Auto-generated admin token in `~/.config/hoa/admin.txt`

##### Authentication Flow

**WebAuthn Registration:**

```
1. Client → POST /api/auth/webauthn/register/begin
   ↓ Server generates challenge, stores in session
2. Client → Browser WebAuthn API (navigator.credentials.create())
   ↓ User authenticates with biometrics/security key
3. Client → POST /api/auth/webauthn/register/finish
   ↓ Server verifies attestation, stores credential
4. Server → Creates user, creates session
```

**WebAuthn Login:**

```
1. Client → POST /api/auth/webauthn/login/begin
   ↓ Server generates challenge, stores in session
2. Client → Browser WebAuthn API (navigator.credentials.get())
   ↓ User authenticates with biometrics/security key
3. Client → POST /api/auth/webauthn/login/finish
   ↓ Server verifies assertion, validates credential
4. Server → Creates session, returns user info
```

**Bootstrap Authentication:**

```
1. Admin → POST /api/auth/token/bootstrap
   ↓ Provides admin token from admin.txt
2. Server → Creates/retrieves admin user
3. Server → Creates session
```

### Database Schema

#### Users Table

```sql
users (
  id: UUID (PK)
  nick: VARCHAR(100)
  first_name: VARCHAR(100)
  second_name: VARCHAR(100)
  email: VARCHAR(320) UNIQUE
  phone_number: VARCHAR(20)
  enabled: BOOLEAN
  is_admin: BOOLEAN
  created_at: DATETIME
  updated_at: DATETIME
)
```

#### Auth Methods Table (Polymorphic)

```sql
auth_methods (
  id: UUID (PK)
  user_id: UUID (FK → users.id)
  type: VARCHAR(50)  -- discriminator
  identifier: VARCHAR(320)
  enabled: BOOLEAN
  requires_approval: BOOLEAN
  approved: BOOLEAN
  approved_by: UUID (FK → users.id)
  approved_at: DATETIME
  created_at: DATETIME
  updated_at: DATETIME

  -- Passkey-specific
  credential_id: VARCHAR(1024) UNIQUE
  public_key: TEXT
  sign_count: INTEGER
  transports: VARCHAR(200)
  rp_id: VARCHAR(255)

  -- Password-specific
  password_hash: VARCHAR(255)
  password_changed_at: DATETIME

  -- OAuth2-specific
  provider: VARCHAR(50)
  provider_user_id: VARCHAR(255)
  access_token_encrypted: TEXT
  refresh_token_encrypted: TEXT
  token_expires_at: DATETIME

  -- Token-specific
  token_hash: VARCHAR(255) UNIQUE
  description: VARCHAR(500)
  expires_at: DATETIME
  last_used_at: DATETIME
)
```

#### Sessions Table

```sql
sessions (
  id: UUID (PK)
  user_id: UUID (FK → users.id)
  session_token: VARCHAR(255) UNIQUE
  expires_at: DATETIME
  ip_address: VARCHAR(45)
  user_agent: VARCHAR(500)
  created_at: DATETIME
  last_activity_at: DATETIME
)
```

#### JWT Keys Table

```sql
jwt_keys (
  id: UUID (PK)
  algorithm: VARCHAR(10)  -- RS256 or HS256
  public_key: TEXT
  private_key_encrypted: TEXT
  key_id: VARCHAR(50) UNIQUE
  is_active: BOOLEAN
  created_at: DATETIME
  expires_at: DATETIME
  rotated_at: DATETIME
)
```

### Frontend Architecture

#### Technology Stack

- **Preact**: Lightweight React alternative (3KB)
- **TypeScript**: Type safety and better DX
- **Vite**: Fast build tool and dev server

#### Key Features

- **Dynamic Configuration**: Loads config from `/config.json` at runtime
- **WebAuthn Integration**: Browser native passkey support
- **IndexedDB**: Credential storage for quick login
- **Session Management**: HTTP-only cookies

#### Component Structure

```
src/
├── main.tsx           # Entry point
├── app.tsx            # Main app component
├── config.ts          # Dynamic config loader
├── types/             # TypeScript types
├── services/
│   ├── api.ts         # API client
│   ├── webauthn.ts    # WebAuthn helpers
│   └── storage.ts     # IndexedDB wrapper
├── hooks/
│   ├── useAuth.ts     # Auth state hook
│   └── useConfig.ts   # Config hook
├── components/        # Reusable components
└── pages/             # Page components
```

## Security Considerations

### Authentication

- **WebAuthn**: FIDO2 compliant, phishing-resistant
- **Multi-RP Support**: Different domains can use same HOA instance
- **Sign Counter**: Replay attack protection
- **User Verification**: Optional biometric verification

### Session Management

- **HTTP-only Cookies**: XSS protection
- **SameSite**: CSRF protection
- **Secure Flag**: HTTPS-only (production)
- **Expiration**: Configurable max age

### JWT Tokens

- **RS256**: Asymmetric signing, public key verification
- **HS256**: Symmetric signing (faster, simpler)
- **Key Rotation**: Automatic key rotation support
- **Short-lived Access Tokens**: 1-hour default
- **Long-lived Refresh Tokens**: 30-day default

### Password Storage

- **Bcrypt**: Industry-standard password hashing
- **Optional**: Passwords are opt-in, not primary auth

### Admin Token

- **Auto-generated**: Secure random generation
- **File Permissions**: 0600 (owner read/write only)
- **One-time Bootstrap**: Used to create first admin

## Scalability

### Horizontal Scaling

- **Stateless API**: Session data in database or Redis
- **JWT Validation**: Can be done without database lookup (with public key)
- **Read Replicas**: Database can have read replicas

### Performance

- **Connection Pooling**: SQLAlchemy connection pool
- **Indexed Queries**: All foreign keys and lookups indexed
- **Caching**: Can add Redis for session caching

## Deployment

### Configuration

1. Copy `config.example.yaml` to `~/.config/hoa/config.yaml`
2. Set environment variables or CLI arguments
3. Admin token auto-generated on first run

### Database

- **Development**: SQLite (default)
- **Production**: PostgreSQL (recommended)
- **Migrations**: Manual via SQLAlchemy (future: Alembic)

### Frontend Build

```bash
cd frontend
yarn install
yarn build
# Outputs to frontend/dist/
# FastAPI serves from hoa/static/
```

### Process Management

- **systemd**: Recommended for Linux
- **Docker**: Container support (future)
- **Kubernetes**: Helm chart (future)

## Monitoring

### Health Check

- `GET /api/health`: Returns service health status

### Metrics (Future)

- Request count by endpoint
- Authentication success/failure rates
- Active sessions count
- JWT token issuance rate

### Logging

- Structured logging with configurable level
- Authentication events
- Error tracking
- Audit trail

## Future Enhancements

### Planned Features

1. **OAuth2 Implementation**: Google, GitHub, Auth0
2. **DIDComm Integration**: Decentralized identity
3. **Rate Limiting**: Brute force protection
4. **Audit Logging**: Comprehensive event tracking
5. **Email Verification**: Email-based auth methods
6. **2FA/MFA**: Additional authentication factors
7. **Session Management UI**: View/revoke sessions
8. **LDAP/SAML**: Enterprise SSO

### Technical Improvements

1. **Alembic Migrations**: Database schema versioning
2. **Redis Integration**: Session caching
3. **Docker Compose**: Local development setup
4. **Kubernetes Deployment**: Production deployment
5. **Monitoring Stack**: Prometheus + Grafana
6. **E2E Tests**: Playwright/Cypress tests
7. **Performance Testing**: Load testing suite
8. **Documentation**: API docs, tutorials, examples
