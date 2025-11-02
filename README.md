# HOA - Heavily Over-engineered Authentication

> A production-ready authentication system featuring WebAuthn/Passkeys, JWT tokens, and multi-authentication method support.

**Version**: 1.0.0  
**Status**: ✅ Production Ready

---

## Quick Start

```bash
# Install dependencies
uv sync
cd frontend && yarn install && cd ..

# Build frontend
cd frontend && yarn build && cd ..

# Run server (generates config & admin token on first run)
uv run python run_dev.py
```

Open `http://localhost:8000` in your browser.

The admin token will be saved to `~/.config/hoa/admin.txt` on first startup.

---

## Features

- **WebAuthn/Passkeys**: FIDO2-based passwordless authentication
- **JWT Tokens**: RS256/HS256 for machine-to-machine auth
- **Multi-Auth Support**: Multiple authentication methods per user
- **Admin Panel**: User management and approval workflows
- **Flexible Configuration**: CLI, environment variables, or config file
- **Modern Stack**: FastAPI + SQLAlchemy + Preact + TypeScript

---

## Documentation

### Essential Guides

- **[API Reference](docs/api.md)** - Complete API documentation with examples
- **[Development Guide](docs/development.md)** - Setup, testing, and development workflows
- **[Deployment Guide](docs/deployment.md)** - Production deployment and operations

### Architecture & Design

- **[AGENTS.md](AGENTS.md)** - Architectural decisions and technical choices
- **[Architecture Overview](docs/architecture.md)** - System design and data models
- **[Testing Strategy](docs/testing.md)** - Comprehensive testing documentation

### Project History

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[Session Notes](docs/sessions/)** - Development session summaries

---

## Architecture Overview

HOA separates **users** from **authentication methods**, allowing:

- Multiple auth methods per user (passkeys, tokens, OAuth2)
- Self-service auth method addition with optional approval
- Admin impersonation for support scenarios
- Flexible identity management

See [Architecture Documentation](docs/architecture.md) for detailed design.

---

## Project Statistics

| Component             | Lines       | Status        |
| --------------------- | ----------- | ------------- |
| Backend (Python)      | ~3,500      | ✅ Complete   |
| Frontend (TypeScript) | ~3,200      | ✅ Complete   |
| Tests                 | ~4,000      | ✅ 259+ tests |
| Documentation         | ~4,500      | ✅ Complete   |
| **Total**             | **~15,000** | ✅ **v1.0.0** |

**Test Coverage**:

- 179 backend tests (72.52% coverage)
- 26 frontend unit tests
- 54+ E2E tests (Playwright)
- Total: 259+ tests, ~14.3s runtime

---

## Technology Stack

**Backend**:

- FastAPI (web framework)
- SQLAlchemy (ORM)
- py_webauthn (WebAuthn/FIDO2)
- Python 3.13 (uv package manager)

**Frontend**:

- Preact (lightweight React)
- TypeScript (type safety)
- Vite (build tool)
- Playwright (E2E testing)

**Database**:

- SQLite (default, supports PostgreSQL)

---

## Quick Configuration

Edit `~/.config/hoa/config.yaml`:

```yaml
host: 0.0.0.0
port: 8000
database-url: sqlite:////path/to/hoa.db
jwt-algorithm: RS256
allowed-rps: localhost|Local Dev|http://localhost:8000
cors-origins:
  - http://localhost:8000
  - http://localhost:5173
```

See [docs/deployment.md](docs/deployment.md) for production configuration.

---

## Development

```bash
# Backend tests
uv run pytest
uv run pytest --cov=hoa --cov-report=html

# Frontend tests
cd frontend
yarn test                    # Unit tests
yarn test:e2e               # E2E tests
yarn test:e2e:ui            # Interactive E2E

# Type checking
cd frontend && yarn type-check

# Linting
uv run ruff check hoa/
```

See [docs/development.md](docs/development.md) for detailed workflows.

---

## API Endpoints

| Category  | Endpoints      | Purpose                       |
| --------- | -------------- | ----------------------------- |
| **Auth**  | `/api/auth/*`  | Login, registration, sessions |
| **Users** | `/api/users/*` | Profile and auth methods      |
| **Admin** | `/api/admin/*` | User management, approvals    |
| **M2M**   | `/api/m2m/*`   | JWT token operations          |

**Total**: 21 operational endpoints

See [docs/api.md](docs/api.md) for complete API reference.

---

## Deployment

**Quick Deploy**:

```bash
# Build frontend
cd frontend && yarn build && cd ..

# Run production server
uv run python -m hoa --host 0.0.0.0 --port 8000
```

**Docker** (recommended):

```bash
# Coming soon - see docs/deployment.md for current options
```

See [docs/deployment.md](docs/deployment.md) for:

- SystemD service configuration
- PostgreSQL setup
- Nginx reverse proxy
- SSL/TLS with Let's Encrypt
- Monitoring and logging

---

## Security Features

- ✅ WebAuthn with user verification
- ✅ JWT signing (RS256/HS256)
- ✅ HTTP-only cookies
- ✅ Configurable CORS
- ✅ Admin approval workflow
- ✅ Secure token generation
- ✅ Password hashing with bcrypt

---

## License

See [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please read [docs/development.md](docs/development.md) for guidelines.

---

## Support

- **Issues**: GitHub issue tracker
- **Documentation**: See `docs/` directory
- **Architecture**: See `AGENTS.md` for design decisions

---

**Built with ❤️ using AI-assisted development**  
See [AGENTS.md](AGENTS.md) for architectural decisions and development notes.
