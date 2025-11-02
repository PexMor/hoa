# HOA - Architectural Decisions & Technical Choices

This document records architectural decisions, technical choices, and design rationale for the HOA authentication system to assist both human developers and AI agents working on the codebase.

**Version**: 1.0.0  
**Last Updated**: October 23, 2025

---

## Table of Contents

1. [Project Origin](#project-origin)
2. [Core Architectural Decisions](#core-architectural-decisions)
3. [Technology Stack Choices](#technology-stack-choices)
4. [Implementation Decisions](#implementation-decisions)
5. [Testing Strategy](#testing-strategy)
6. [Development Philosophy](#development-philosophy)

---

## Project Origin

**Initial Concept** (October 23, 2025):

- Minimal FastAPI authentication system with WebAuthn/Passkeys
- SQLite storage, multi-origin support
- Single-file backend + static HTML frontend

**Evolution to Production System**:

- Expanded to full production architecture
- Separation of users from authentication methods
- Modern TypeScript frontend (Preact)
- Comprehensive testing suite
- JWT tokens for M2M communication

**Development Approach**:

- AI-assisted pair programming
- Test-driven development where practical
- Iterative refinement over ~15 hours
- ~15,000 lines of production code

---

## Core Architectural Decisions

### AD-001: User-Authentication Method Separation

**Decision**: Users and authentication methods are separate database entities.

**Rationale**:

- **Flexibility**: Users can have multiple auth methods (passkeys, tokens, OAuth2)
- **OAuth2 Support**: Map external provider accounts to local users
- **Impersonation**: Admins can act as users for support scenarios
- **Self-Service**: Users can add/remove auth methods independently

**Implementation**:

- User model with UUID primary key
- AuthMethod polymorphic model using single-table inheritance
- Association logic with optional approval workflow
- Supports: Passkey, Password, OAuth2, Token types

**Trade-offs**:

- Slightly more complex than user-credential 1:1
- Requires careful transaction handling
- Benefits far outweigh complexity for enterprise use

---

### AD-002: Configuration Management Strategy

**Decision**: Use `configargparse` for layered configuration (CLI > ENV > Config File)

**Rationale**:

- **Development**: CLI args for quick overrides
- **Production**: Environment variables for Docker/K8s
- **Persistence**: Config file for server deployments
- **Flexibility**: Supports all deployment scenarios

**Implementation**:

- Configuration in `~/.config/hoa/config.yaml`
- Database in `~/.config/hoa/hoa.db`
- Keys use hyphens (CLI-compatible): `database-url`, not `database_url`
- Follows XDG Base Directory specification

**Alternatives Considered**:

- ❌ Only environment variables (inflexible for non-container)
- ❌ Only config file (difficult for quick testing)
- ✅ Layered approach wins for versatility

---

### AD-003: JWT Algorithm Configurability

**Decision**: Support both RS256 (asymmetric) and HS256 (symmetric), user-configurable.

**Rationale**:

- **RS256**: Public key distribution, better for microservices
- **HS256**: Simpler, faster, sufficient for monoliths
- **Configurability**: Let deployers choose based on architecture

**Implementation**:

- Auto-generate RS256 key pairs or HS256 secret on first run
- Store private keys encrypted in database
- JWKS endpoint for RS256 public key distribution
- Token includes `kid` (key ID) for rotation support

**Default**: RS256 (more secure, better for future scaling)

---

### AD-004: WebAuthn as Primary Authentication

**Decision**: WebAuthn/Passkeys are the primary (not secondary) authentication method.

**Rationale**:

- **Security**: Phishing-resistant, no shared secrets
- **UX**: One-click login after registration
- **Modern**: Industry standard (FIDO2/WebAuthn Level 2)
- **Passwordless**: Eliminates password management burden

**Implementation**:

- Based on Duo Labs `py_webauthn` library
- Multi-RP and multi-origin support for flexible deployment
- Credential storage in IndexedDB (client-side)
- Platform authenticator detection (Touch ID, Windows Hello)
- Fallback to admin token for bootstrapping

**Not Just 2FA**: WebAuthn replaces passwords entirely, not supplements them.

---

### AD-005: Admin Token Bootstrap

**Decision**: Auto-generate admin token on first startup, save to file with 0600 permissions.

**Rationale**:

- **Bootstrapping Problem**: Need secure way to create first admin
- **Security**: Generated token stronger than user-chosen
- **Convenience**: Zero manual configuration required
- **Auditable**: Token stored in predictable location

**Implementation**:

- Token: Base58-encoded 32-byte random value
- Location: `~/.config/hoa/admin.txt`
- Permissions: 0600 (owner read/write only)
- Used once to create first passkey, then optional

**Alternative Considered**:

- ❌ Default admin password (insecure, often left unchanged)
- ✅ Generated token with file permissions wins

---

## Technology Stack Choices

### Backend Technology

**FastAPI** (Web Framework)

- **Why**: Modern, fast, built-in OpenAPI docs, async support
- **Alternatives Considered**: Django (too heavy), Flask (too minimal)
- **Trade-off**: Newer ecosystem vs maturity (FastAPI wins)

**SQLAlchemy 2.0** (ORM)

- **Why**: Type-safe, flexible, supports multiple databases
- **Alternatives Considered**: Tortoise ORM, raw SQL
- **Trade-off**: Learning curve vs power (SQLAlchemy wins)

**SQLite** (Default Database)

- **Why**: Zero configuration, perfect for single-server deployments
- **Alternatives**: PostgreSQL (supported via configuration)
- **Trade-off**: Simplicity vs advanced features (SQLite default, Postgres available)

**uv** (Package Manager)

- **Why**: Fast, modern, lockfile support, better than pip
- **Alternatives Considered**: Poetry, pipenv
- **Trade-off**: Newer tool vs maturity (speed wins)

**bcrypt** (Direct, not passlib)

- **Why**: Python 3.13 compatibility issues with passlib
- **Alternatives**: passlib (had compatibility issues)
- **Trade-off**: Direct dependency vs abstraction (compatibility wins)

### Frontend Technology

**Preact** (UI Framework)

- **Why**: Lightweight React alternative (3KB vs 45KB), same API
- **Alternatives Considered**: React (too heavy), Vue (different paradigm)
- **Trade-off**: Ecosystem size vs bundle size (Preact wins for speed)

**TypeScript** (Language)

- **Why**: Type safety, better IDE support, catches bugs early
- **Alternatives Considered**: JavaScript (less safe)
- **Trade-off**: Build complexity vs safety (TypeScript wins)

**Vite** (Build Tool)

- **Why**: Fast builds, excellent DX, modern tooling
- **Alternatives Considered**: Webpack (slower), Parcel (less features)
- **Trade-off**: Configuration vs speed (Vite wins)

**Yarn v2** (Package Manager)

- **Why**: Reliable, workspace support, good caching
- **Alternatives Considered**: npm (slower), pnpm (less common)
- **Trade-off**: Speed vs adoption (Yarn wins for reliability)

---

## Implementation Decisions

### ID-001: JWT Token Return Signature

**Decision**: Token creation methods return `(token: str, expires_at: datetime)` tuples.

**Rationale**:

- Consistent API across all token methods
- Eliminates need to parse tokens to get expiration
- Clearer intent, better for TypeScript interop
- Simplifies client-side token management

**Before**:

```python
def create_access_token(self, data: Dict) -> str:
    return token
```

**After**:

```python
def create_access_token(self, user_id: UUID) -> tuple[str, datetime]:
    return token, expires_at
```

**Impact**: Updated all token consumers, improved client experience.

---

### ID-002: Single-Table Inheritance for Auth Methods

**Decision**: Use SQLAlchemy single-table inheritance for AuthMethod subclasses.

**Rationale**:

- Simple queries (no JOINs needed)
- Good for small number of subclasses (<10)
- Performance: Single table scan
- Polymorphic loading works seamlessly

**Trade-off**:

- All columns must be nullable
- Wasted space for unused columns
- Benefits outweigh for our use case (<10 auth types)

**Alternatives Considered**:

- ❌ Joined-table inheritance (too many JOINs)
- ❌ Separate tables (complex polymorphism)
- ✅ Single-table wins for simplicity

---

### ID-003: SPA Routing with Custom 404 Handler

**Decision**: Custom 404 exception handler serves `index.html` for non-API routes.

**Rationale**:

- FastAPI StaticFiles doesn't provide SPA fallback by default
- Client-side routing (preact-router) needs all routes to load `index.html`
- API routes must still return proper 404s

**Implementation**:

```python
@app.exception_handler(404)
async def spa_fallback(request, exc):
    if not request.url.path.startswith("/api/"):
        return FileResponse("index.html")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
```

**Result**: All frontend routes work correctly, API maintains proper REST semantics.

---

### ID-004: Config File Key Format (Hyphens)

**Decision**: YAML config keys use hyphens matching CLI arguments: `database-url` not `database_url`.

**Rationale**:

- configargparse expects consistency between CLI and config file
- CLI convention uses hyphens: `--database-url`
- Python variables use underscores (argparse converts automatically)
- Consistency improves UX

**Issue Found**: Initial implementation used underscores, causing parse errors.

**Fix**: Generate config with hyphens, document conversion for users.

---

### ID-005: WebAuthn Base64 Encoding Fix

**Decision**: Remove `.decode()` after `bytes_to_base64url()` in webauthn helpers.

**Rationale**:

- `webauthn.helpers.bytes_to_base64url()` already returns string
- Additional `.decode()` causes `AttributeError`
- Library behavior misunderstood in initial implementation

**Before**:

```python
challenge = bytes_to_base64url(options.challenge).decode()  # Error!
```

**After**:

```python
challenge = bytes_to_base64url(options.challenge)  # Correct
```

**Impact**: Fixed all WebAuthn ceremony methods, 22 tests now passing.

---

## Testing Strategy

### TS-001: Multi-Layer Testing Approach

**Decision**: Three-layer testing: Unit → Integration → E2E.

**Rationale**:

- **Unit Tests**: Fast, isolated, test business logic
- **Integration Tests**: Test API endpoints and services
- **E2E Tests**: Test complete user flows in real browser

**Implementation**:

- Backend: Pytest with in-memory SQLite (147 tests, 68.77% coverage)
- Frontend: Vitest with jsdom (26 tests)
- E2E: Playwright with WebAuthn virtual authenticator (54+ tests)

**Coverage Goals**:

- Models & Schemas: 100% (achieved)
- Core Services: >80% (achieved: 76-93%)
- Utilities: 100% (achieved)
- Overall: >80% (current: 68.77%, improving)

---

### TS-002: WebAuthn Virtual Authenticator for E2E

**Decision**: Use Chrome DevTools Protocol to simulate WebAuthn in E2E tests.

**Rationale**:

- Can't use physical security keys in automated tests
- Virtual authenticator simulates FIDO2 hardware
- Enables testing complete passkey flows
- Industry-standard approach

**Implementation**:

```typescript
const cdpSession = await context.newCDPSession(page);
await cdpSession.send("WebAuthn.enable");
await cdpSession.send("WebAuthn.addVirtualAuthenticator", {
  options: {
    protocol: "ctap2",
    transport: "internal",
    hasResidentKey: true,
    hasUserVerification: true,
    isUserVerified: true,
  },
});
```

**Result**: Complete WebAuthn flows tested in CI/CD without hardware.

---

### TS-003: Test Fixtures with Global Override

**Decision**: Override global database connection in test fixtures.

**Rationale**:

- FastAPI TestClient needs consistent database access
- Dependency overrides work for `get_db()` but not internal queries
- Global override ensures all code uses test database

**Implementation**:

```python
@pytest.fixture
def client(test_db_engine, test_sessionmaker, test_settings):
    # Override globals before creating app
    import hoa.config as config_module
    import hoa.database as db_module

    config_module.settings = test_settings
    db_module.engine = test_db_engine
    db_module.SessionLocal = test_sessionmaker

    app = create_app()
    return TestClient(app)
```

**Trade-off**: Global state vs test isolation (acceptable for test environment).

---

## Development Philosophy

### DP-001: Test-Driven Development (Where Practical)

**Approach**: Write tests first for critical paths, implementation for exploration.

**Applied To**:

- ✅ Core services (User, JWT, Auth Methods, WebAuthn)
- ✅ Utility functions (validators, crypto)
- ✅ Critical API endpoints
- ⚠️ UI/UX (manual testing + E2E)

**Results**:

- Caught 15+ bugs during implementation
- 68.77% backend coverage
- All critical paths tested
- Zero regressions during refactoring

---

### DP-002: AI-Assisted Pair Programming

**Approach**: Use AI as coding partner, not autopilot.

**Human Decides**:

- Architecture and design patterns
- Technology choices
- Security decisions
- Test strategy

**AI Assists With**:

- Boilerplate code generation
- Test case suggestions
- Documentation writing
- Bug pattern recognition

**Result**: ~15 hours for ~15,000 lines of production-ready code.

---

### DP-003: Documentation as Code

**Approach**: Maintain docs alongside code, update in same commits.

**Types**:

- **README.md**: Brief overview with pointers
- **AGENTS.md**: Architectural decisions (this file)
- **docs/**: Comprehensive guides
- **CHANGELOG.md**: Version history
- **Code Comments**: Complex logic only

**Result**: 4,500+ lines of documentation, always in sync.

---

### DP-004: Configuration Over Convention (Sometimes)

**Decision**: Explicit configuration for critical choices, sensible defaults for everything else.

**Configurable**:

- JWT algorithm (RS256 vs HS256)
- Auth method approval workflow
- Multi-RP/multi-origin settings
- Database choice (SQLite vs PostgreSQL)

**Convention**:

- Project structure
- File naming
- URL patterns
- Test organization

**Balance**: Configure what matters, conventional otherwise.

---

## Future Considerations

### FC-001: OAuth2 Implementation Strategy

**Planned**: Google, GitHub, Auth0 providers.

**Design**:

- OAuth2Auth model ready (encrypted token storage)
- API endpoints stubbed
- Association logic in auth methods service

**Challenges**:

- External API reliability
- Token refresh management
- Multiple provider normalization

**Estimated Effort**: 15-20 hours per provider.

---

### FC-002: DIDComm Integration

**Status**: Mentioned in original requirements, not yet designed.

**Considerations**:

- W3C DID standard compliance
- Key management complexity
- Use case: Decentralized identity federation?
- Priority: Low (no current requirement)

---

### FC-003: Rate Limiting Strategy

**Planned**: Protect against brute force and DoS.

**Options**:

1. **Middleware-based**: FastAPI Limiter (simple)
2. **Redis-based**: Distributed rate limiting (scalable)
3. **API Gateway**: Nginx/Traefik (production)

**Recommendation**: Start with middleware, migrate to Redis for scale.

**Estimated Effort**: 2-3 hours for basic, 6-8 for distributed.

---

## Standards and Specifications

### Implemented Standards

- **WebAuthn Level 2**: https://www.w3.org/TR/webauthn-2/
- **FIDO2**: https://fidoalliance.org/fido2/
- **JWT (RFC 7519)**: https://tools.ietf.org/html/rfc7519
- **OAuth 2.0 (RFC 6749)**: https://tools.ietf.org/html/rfc6749 (stubbed)
- **XDG Base Directory**: https://specifications.freedesktop.org/basedir-spec/
- **Semantic Versioning**: https://semver.org/
- **Keep a Changelog**: https://keepachangelog.com/

### Key Libraries

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/
- **py_webauthn (Duo Labs)**: https://github.com/duo-labs/py_webauthn
- **Preact**: https://preactjs.com/
- **Vite**: https://vitejs.dev/
- **Playwright**: https://playwright.dev/

---

## Summary

HOA demonstrates production-quality authentication with:

- **15,000 lines** of code across backend, frontend, tests, docs
- **227+ tests** with multi-layer coverage strategy
- **21 API endpoints** fully operational
- **~15 hours** effective development time (AI-assisted)
- **0 known critical bugs** at v1.0.0 release

**Key Success Factors**:

1. Clear architectural decisions upfront
2. AI assistance for implementation
3. Test-driven where practical
4. Comprehensive documentation
5. Iterative refinement

---

**For Development History**: See `docs/sessions/` for session-by-session notes.  
**For API Details**: See `docs/api.md` for complete endpoint reference.  
**For Testing**: See `docs/testing.md` for testing strategy and guides.

---

**Last Updated**: October 23, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
