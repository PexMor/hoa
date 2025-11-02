# HOA Documentation Index

Welcome to the HOA (Heavily Over-engineered Authentication) documentation!

---

## 📚 Essential Guides

### Getting Started

- **[../README.md](../README.md)** - Quick start and project overview
- **[development.md](development.md)** - Setup, development workflows, and testing
- **[api.md](api.md)** - Complete API reference with examples

### Production Deployment

- **[deployment.md](deployment.md)** - Production deployment, configuration, and operations
- **[../CHANGELOG.md](../CHANGELOG.md)** - Version history and changes

---

## 🏗️ Architecture & Design

### System Design

- **[architecture.md](architecture.md)** - System architecture and data models
- **[../AGENTS.md](../AGENTS.md)** - Architectural decisions and technical choices
- **[testing.md](testing.md)** - Testing strategy, tools, and best practices

---

## 📖 Additional Resources

### Development History

- **[sessions/](sessions/)** - Development session notes and summaries
  - Session summaries with detailed implementation notes
  - Testing progress tracking
  - E2E testing implementation details
  - Documentation audit results

### Project Management

- **[sessions/TODO.md](sessions/TODO.md)** - Implementation checklist and status
- **[sessions/IMPLEMENTATION_STATUS.md](sessions/IMPLEMENTATION_STATUS.md)** - Detailed status tracking

---

## 🎯 Quick Reference

### By Role

**For Developers**:

1. Start with [development.md](development.md)
2. Review [api.md](api.md) for endpoints
3. Check [testing.md](testing.md) for test guidelines
4. Refer to [../AGENTS.md](../AGENTS.md) for design decisions

**For Operators**:

1. Start with [deployment.md](deployment.md)
2. Review [architecture.md](architecture.md) for system overview
3. Check [../CHANGELOG.md](../CHANGELOG.md) for version changes

**For Contributors**:

1. Read [development.md](development.md) for setup
2. Review [../AGENTS.md](../AGENTS.md) for architectural context
3. Check [testing.md](testing.md) for test requirements
4. Follow [../CHANGELOG.md](../CHANGELOG.md) format for changes

---

## 📊 Documentation Statistics

| Document            | Lines      | Purpose                 |
| ------------------- | ---------- | ----------------------- |
| **api.md**          | ~600       | API endpoint reference  |
| **development.md**  | ~500       | Development guide       |
| **deployment.md**   | ~700       | Production deployment   |
| **architecture.md** | ~600       | System design           |
| **testing.md**      | ~800       | Testing guide           |
| **AGENTS.md**       | ~400       | Architectural decisions |
| **README.md**       | ~150       | Project overview        |
| **CHANGELOG.md**    | ~150       | Version history         |
| **Total**           | **~3,900** | **Complete docs**       |

---

## 🔍 Finding Information

### By Topic

**Authentication**:

- WebAuthn/Passkeys: [api.md](api.md#authentication-api), [architecture.md](architecture.md#webauthn-service)
- JWT Tokens: [api.md](api.md#m2m-api), [../AGENTS.md](../AGENTS.md#ad-003-jwt-algorithm-configurability)
- Admin Token: [deployment.md](deployment.md#initial-setup), [../AGENTS.md](../AGENTS.md#ad-005-admin-token-bootstrap)

**Configuration**:

- Setup: [deployment.md](deployment.md#configuration)
- Options: [../README.md](../README.md#quick-configuration)
- Decisions: [../AGENTS.md](../AGENTS.md#ad-002-configuration-management-strategy)

**Database**:

- Models: [architecture.md](architecture.md#database-models)
- Migrations: [development.md](development.md#database-management)
- Design: [../AGENTS.md](../AGENTS.md#ad-001-user-authentication-method-separation)

**Testing**:

- Strategy: [testing.md](testing.md#test-architecture)
- Running Tests: [development.md](development.md#testing)
- Results: [sessions/TESTING_PROGRESS.md](sessions/TESTING_PROGRESS.md)

**API**:

- Endpoints: [api.md](api.md)
- Examples: [api.md](api.md#examples)
- Authentication: [api.md](api.md#authentication)

---

## 🚀 Common Tasks

### Development

```bash
# Setup → development.md#setup
uv sync && cd frontend && yarn install

# Run Server → development.md#running-the-server
uv run python run_dev.py

# Run Tests → testing.md#backend-testing
uv run pytest --cov=hoa

# E2E Tests → testing.md#e2e-testing
cd frontend && yarn test:e2e
```

### Deployment

```bash
# Production Deploy → deployment.md#production-deployment
uv run python -m hoa --host 0.0.0.0 --port 8000

# Configuration → deployment.md#configuration
vi ~/.config/hoa/config.yaml

# Database → deployment.md#database
# See deployment.md for PostgreSQL setup
```

---

## 📝 Document Conventions

### File Organization

- **Root** (`../`): Overview and essential references
- **docs/** (this directory): Comprehensive guides
- **docs/sessions/**: Development history and notes

### Formatting

- All documents use Markdown
- Code blocks specify language for syntax highlighting
- Internal links use relative paths
- External links use full URLs

### Updates

- Update `CHANGELOG.md` for version changes
- Update relevant docs in same commit as code
- Keep README.md brief, details in docs/

---

## 🤝 Contributing to Documentation

### When to Update

**Always Update**:

- Adding/removing API endpoints → `api.md`
- Changing configuration options → `deployment.md`
- Adding dependencies → `development.md`
- Fixing bugs → `CHANGELOG.md`
- Making architectural decisions → `AGENTS.md`

**Consider Updating**:

- Improving test coverage → `testing.md`
- Adding examples → relevant guide
- Clarifying setup → `development.md` or `deployment.md`

### Documentation Style

- **Be Concise**: Get to the point
- **Be Complete**: Include all necessary details
- **Be Clear**: Use simple language
- **Be Current**: Keep docs in sync with code
- **Be Helpful**: Think like a new contributor

---

## 📧 Questions?

- **Issues**: GitHub issue tracker
- **Development**: See [development.md](development.md)
- **Architecture**: See [../AGENTS.md](../AGENTS.md)
- **API**: See [api.md](api.md)

---

**HOA Documentation v1.0.0**  
**Last Updated**: October 23, 2025  
**Status**: ✅ Complete and Production-Ready
