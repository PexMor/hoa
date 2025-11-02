# Changelog

All notable changes to HOA (Heavily Over-engineered Authentication) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-10-23

### Added

**Core Authentication**

- WebAuthn/Passkey authentication with FIDO2 support
- Multi-RP and multi-origin WebAuthn support
- JWT token system (RS256 and HS256)
- Admin token bootstrap authentication
- Session management with HTTP-only cookies

**Backend (21 API Endpoints)**

- Auth API: WebAuthn registration/login, bootstrap token, session management (7 endpoints)
- M2M API: JWT token creation, refresh, validation (3 endpoints)
- User API: Profile management, auth methods CRUD (4 endpoints)
- Admin API: User management, approval workflows (7 endpoints)

**Services & Infrastructure**

- User service with CRUD operations (19 tests, 83.53% coverage)
- JWT service with RS256/HS256 support (14 tests, 72.45% coverage)
- WebAuthn service with ceremony handling (22 tests, 76.92% coverage)
- Auth methods service with approval workflow (21 tests, 93.10% coverage)

**Database Models**

- User model with UUID primary keys
- AuthMethod polymorphic model (Passkey, Password, OAuth2, Token)
- Session and JWTKey models
- SQLAlchemy 2.0 with SQLite (PostgreSQL-ready)

**Frontend (6 Pages)**

- Home page with feature showcase and version display
- Login page with WebAuthn and admin token fallback
- Registration page with passkey creation
- Dashboard with user profile and auth methods management
- Admin panel with user management and approval queue (550 lines)
- 404 Not Found handler

**Frontend Infrastructure**

- Complete WebAuthn client implementation (380 lines)
- API client for all 21 endpoints (240 lines)
- Auth context with hooks (135 lines)
- IndexedDB credential storage
- Platform authenticator detection (Touch ID, Windows Hello)
- Dynamic configuration loading from /config.json

**Configuration System**

- configargparse for layered configuration (CLI > ENV > config file)
- Auto-generation of config file in ~/.config/hoa/
- Auto-generation of admin token on first startup
- SQLite database in ~/.config/hoa/hoa.db

**Version Tracking**

- Git-integrated version information
- Dynamic version display in UI (frontend + backend)
- Build date and commit tracking
- /api/version endpoint

**Testing (227+ Tests)**

- 147 backend tests (68.77% coverage, ~9.5s runtime)
- 26 frontend unit tests (Vitest, ~1s runtime)
- 54+ E2E tests (Playwright with WebAuthn virtual authenticator, ~2.5s runtime)
- Test fixtures for database, users, and WebAuthn credentials

**Documentation (~4,500 lines)**

- Comprehensive API reference with examples (600 lines)
- Development guide with setup and workflows (500 lines)
- Deployment guide with production configs (700 lines)
- Architecture overview
- Testing strategy and guide
- Session development notes

**Development Tools**

- Development server script (run_dev.py)
- Pytest configuration with in-memory SQLite
- Vitest configuration with jsdom
- Playwright configuration with auto server start
- TypeScript strict mode
- Ruff linting for Python

### Changed

- Migrated from passlib to direct bcrypt for Python 3.13 compatibility
- JWT service returns (token, expires_at) tuples for consistency
- Config file uses hyphenated keys matching CLI arguments
- SPA routing with custom 404 exception handler

### Fixed

- SQLAlchemy single-table inheritance column nullability
- WebAuthn base64 encoding (removed erroneous .decode())
- Config file CLI argument mapping (hyphens vs underscores)
- UTC datetime deprecation warnings
- Frontend API endpoint paths
- TypeScript router props interface

### Security

- Secure admin token generation with 0600 file permissions
- bcrypt password hashing with salt
- JWT signing with configurable algorithms
- WebAuthn user verification
- HTTP-only session cookies
- CORS configuration

---

## [0.1.0-dev] - 2025-10-23

### Added

- Initial project structure
- Basic FastAPI application
- Minimal WebAuthn prototype
- Project planning and architecture

### Notes

- Prototype version, replaced by 1.0.0 implementation

---

## [Unreleased]

### Planned

- OAuth2 provider integration (Google, GitHub, Auth0)
- Rate limiting middleware
- Audit logging system
- Email verification
- Session management UI
- LDAP/SAML integration
- Docker and docker-compose configuration
- CI/CD pipeline (GitHub Actions)

### To Fix

- Session middleware in backend tests (25 tests skipped)
- Increase backend test coverage to >80%

---

[1.0.0]: https://github.com/yourusername/hoa/releases/tag/v1.0.0
[0.1.0-dev]: https://github.com/yourusername/hoa/releases/tag/v0.1.0-dev
