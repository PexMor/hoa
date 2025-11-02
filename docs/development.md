# HOA Development Guide

Complete guide for developers working on the HOA authentication system.

**Version**: 1.0.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Database Management](#database-management)
8. [Frontend Development](#frontend-development)
9. [Backend Development](#backend-development)
10. [Debugging](#debugging)
11. [Contributing](#contributing)

---

## Prerequisites

### Required

- **Python**: 3.11 or higher (tested on 3.13)
- **Node.js**: 18+ (for frontend)
- **uv**: Modern Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **yarn v2**: Frontend package manager
  ```bash
  npm install -g yarn
  ```

### Recommended

- **Git**: For version control
- **VS Code** or **PyCharm**: IDE with Python support
- **Chrome/Edge**: For WebAuthn testing (best platform authenticator support)

---

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/hoa.git
cd hoa

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend
yarn install
cd ..
```

### 2. Run Development Server

```bash
# Option 1: Using run_dev.py (recommended)
uv run python run_dev.py

# Option 2: Manual uvicorn
uv run uvicorn hoa.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

### 3. Build Frontend

```bash
cd frontend
yarn build  # Builds to ../hoa/static/
```

### 4. Access Application

- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## Project Structure

```
hoa/
├── hoa/                    # Python backend package
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── app.py              # FastAPI application factory
│   ├── config.py           # Configuration management
│   ├── database.py         # SQLAlchemy setup
│   ├── version.py          # Version information
│   ├── models/             # Database models
│   │   ├── user.py         # User model
│   │   ├── auth_method.py  # Auth method polymorphic models
│   │   └── session.py      # Session and JWTKey models
│   ├── schemas/            # Pydantic schemas
│   │   ├── user.py         # User schemas
│   │   ├── auth.py         # Auth request/response schemas
│   │   └── token.py        # JWT schemas
│   ├── api/                # API endpoints
│   │   ├── deps.py         # FastAPI dependencies
│   │   ├── auth.py         # Auth endpoints
│   │   ├── users.py        # User endpoints
│   │   ├── admin.py        # Admin endpoints
│   │   └── m2m.py          # M2M JWT endpoints
│   ├── services/           # Business logic
│   │   ├── jwt_service.py  # JWT management
│   │   ├── webauthn.py     # WebAuthn ceremonies
│   │   ├── auth_methods.py # Auth method management
│   │   └── user_service.py # User management
│   ├── utils/              # Utilities
│   │   ├── crypto.py       # Cryptography helpers
│   │   └── validators.py   # Custom validators
│   └── static/             # Built frontend files
├── frontend/               # Preact TypeScript frontend
│   ├── src/
│   │   ├── main.tsx        # Entry point
│   │   ├── app.tsx         # Main app component
│   │   ├── config.ts       # Config loader
│   │   ├── types/          # TypeScript types
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API and WebAuthn clients
│   │   ├── hooks/          # React hooks
│   │   └── styles/         # CSS
│   ├── public/             # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── tests/                  # Pytest test suite
│   ├── conftest.py         # Test fixtures
│   ├── test_user_service.py
│   ├── test_jwt_service.py
│   ├── test_auth_methods_service.py
│   ├── test_webauthn_service.py
│   ├── test_api_auth.py
│   ├── test_api_m2m.py
│   ├── test_api_users.py
│   └── test_api_admin.py
├── docs/                   # Documentation
│   ├── api.md              # API reference
│   ├── development.md      # This file
│   └── deployment.md       # Deployment guide
├── pyproject.toml          # Python project config
├── run_dev.py              # Development server script
├── README.md
├── AGENTS.md               # Architecture decisions
├── CHANGELOG.md            # Version history
└── TODO.md                 # Implementation tracking
```

---

## Development Workflow

### Daily Development

1. **Start dev server** (auto-reload enabled):

   ```bash
   uv run python run_dev.py
   ```

2. **Make changes** to backend or frontend code

3. **Frontend rebuild** (if needed):

   ```bash
   cd frontend && yarn build
   ```

4. **Run tests**:

   ```bash
   uv run pytest
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

### Feature Development

1. **Create feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first** (TDD approach):

   ```python
   # tests/test_your_feature.py
   def test_your_feature():
       # Arrange
       ...
       # Act
       ...
       # Assert
       ...
   ```

3. **Implement feature**:

   - Add models if needed
   - Create/update service methods
   - Add/update API endpoints
   - Update frontend if needed

4. **Verify tests pass**:

   ```bash
   uv run pytest tests/test_your_feature.py -v
   ```

5. **Check coverage**:

   ```bash
   uv run pytest --cov=hoa --cov-report=html
   open htmlcov/index.html
   ```

6. **Create pull request**

---

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_user_service.py

# Specific test
uv run pytest tests/test_user_service.py::test_create_user

# With verbose output
uv run pytest -v

# With coverage
uv run pytest --cov=hoa --cov-report=term-missing

# Skip slow tests
uv run pytest -m "not slow"

# Run only integration tests
uv run pytest -m "integration"
```

### Test Structure

```python
# tests/test_example.py
import pytest
from hoa.services.user_service import UserService

def test_example(test_db, test_settings):
    """Test example with fixtures."""
    # Arrange
    service = UserService(test_db, test_settings)

    # Act
    result = service.some_method()

    # Assert
    assert result is not None
```

### Available Fixtures

```python
# From tests/conftest.py
test_db                # SQLAlchemy session (in-memory SQLite)
test_db_engine         # SQLAlchemy engine
test_settings          # Settings instance for testing
client                 # FastAPI TestClient
test_user              # Pre-created test user
test_admin             # Pre-created admin user
```

### Writing Tests

1. **Use descriptive names**:

   ```python
   def test_user_creation_with_valid_email_succeeds():
       ...

   def test_user_creation_with_duplicate_email_fails():
       ...
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert):

   ```python
   def test_create_user():
       # Arrange
       service = UserService(test_db, test_settings)
       user_data = UserCreate(email="test@example.com", nick="test")

       # Act
       user = service.create(user_data)

       # Assert
       assert user.email == "test@example.com"
       assert user.id is not None
   ```

3. **Test edge cases**:

   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error scenarios

4. **Use parametrize for multiple cases**:
   ```python
   @pytest.mark.parametrize("email,expected_valid", [
       ("valid@example.com", True),
       ("invalid", False),
       ("", False),
   ])
   def test_email_validation(email, expected_valid):
       ...
   ```

---

## Code Style

### Python

HOA uses **ruff** for linting and formatting:

```bash
# Check code
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

**Configuration** in `pyproject.toml`:

- Line length: 100 characters
- Python version: 3.11+
- Follows PEP 8 with some exceptions

### TypeScript

Frontend uses TypeScript strict mode:

```bash
# Type check
cd frontend && yarn tsc --noEmit

# Build (includes type checking)
cd frontend && yarn build
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add password reset functionality
fix: correct JWT expiration calculation
docs: update API documentation
test: add tests for WebAuthn service
refactor: simplify user service
chore: update dependencies
```

---

## Database Management

### Configuration

Database URL is configured via environment or config file:

```bash
# SQLite (default for development)
HOA_DATABASE_URL="sqlite:////Users/you/.config/hoa/hoa.db"

# PostgreSQL (production)
HOA_DATABASE_URL="postgresql://user:pass@localhost/hoa"
```

### Reset Database

```bash
# Delete database file (SQLite)
rm ~/.config/hoa/hoa.db

# Restart server (will recreate tables)
uv run python run_dev.py
```

### Inspect Database

```bash
# SQLite
sqlite3 ~/.config/hoa/hoa.db

# View tables
.tables

# View schema
.schema users

# Query
SELECT * FROM users;
```

### Migrations

**Status**: Alembic not yet integrated (planned)

Currently, schema changes require:

1. Update models in `hoa/models/`
2. Delete database
3. Restart server (recreates tables)

For production, use Alembic:

```bash
# TODO: Add migration commands
```

---

## Frontend Development

### Development Server

```bash
cd frontend
yarn dev  # Starts on http://localhost:5173
```

Frontend dev server proxies API requests to `http://localhost:8000`.

### Build for Production

```bash
cd frontend
yarn build  # Output: ../hoa/static/
```

### Project Structure

```
frontend/src/
├── main.tsx              # Entry point
├── app.tsx               # Router and layout
├── config.ts             # Dynamic config loader
├── types/
│   └── index.ts          # TypeScript type definitions
├── components/
│   └── VersionInfo.tsx   # Reusable components
├── pages/
│   ├── Home.tsx          # Landing page
│   ├── Login.tsx         # Login with WebAuthn
│   ├── Register.tsx      # Registration
│   ├── Dashboard.tsx     # User dashboard
│   └── NotFound.tsx      # 404 page
├── services/
│   ├── api.ts            # API client (240 lines)
│   └── webauthn.ts       # WebAuthn helpers (380 lines)
├── hooks/
│   └── useAuth.tsx       # Auth context hook
└── styles/
    └── main.css          # Global styles
```

### Adding a New Page

1. **Create page component**:

   ```typescript
   // frontend/src/pages/NewPage.tsx
   export function NewPage() {
     return (
       <div className="container">
         <h1>New Page</h1>
       </div>
     );
   }
   ```

2. **Add route** in `app.tsx`:

   ```typescript
   import NewPage from "./pages/NewPage";

   <Router>
     <Home path="/" />
     <Login path="/login" />
     <NewPage path="/new" />
     ...
   </Router>;
   ```

3. **Rebuild**:
   ```bash
   cd frontend && yarn build
   ```

### WebAuthn Integration

Use the WebAuthn service from `services/webauthn.ts`:

```typescript
import { startRegistration, finishRegistration } from "../services/webauthn";

// Registration
const credential = await startRegistration(options);
await finishRegistration(userId, credential, rpId);

// Authentication
const credential = await startAuthentication(options);
await finishAuthentication(credential, rpId);
```

---

## Backend Development

### Adding a New API Endpoint

1. **Define schema** in `hoa/schemas/`:

   ```python
   # hoa/schemas/example.py
   from pydantic import BaseModel

   class ExampleRequest(BaseModel):
       name: str
       value: int

   class ExampleResponse(BaseModel):
       id: str
       result: str
   ```

2. **Add service method** in `hoa/services/`:

   ```python
   # hoa/services/example_service.py
   from uuid import uuid4

   class ExampleService:
       def __init__(self, db: Session):
           self.db = db

       def process(self, data: ExampleRequest) -> ExampleResponse:
           # Business logic here
           return ExampleResponse(
               id=str(uuid4()),
               result=f"Processed {data.name}"
           )
   ```

3. **Create endpoint** in `hoa/api/`:

   ```python
   # hoa/api/example.py
   from fastapi import APIRouter, Depends
   from hoa.api.deps import get_db, require_user
   from hoa.services.example_service import ExampleService
   from hoa.schemas.example import ExampleRequest, ExampleResponse

   router = APIRouter(prefix="/example", tags=["example"])

   @router.post("/process", response_model=ExampleResponse)
   def process_example(
       data: ExampleRequest,
       db: Session = Depends(get_db),
       current_user: User = Depends(require_user)
   ):
       """Process example data."""
       service = ExampleService(db)
       return service.process(data)
   ```

4. **Register router** in `hoa/app.py`:

   ```python
   from hoa.api import example

   app.include_router(example.router)
   ```

5. **Write tests** in `tests/`:
   ```python
   # tests/test_example_service.py
   def test_process_example(test_db):
       service = ExampleService(test_db)
       data = ExampleRequest(name="test", value=42)
       result = service.process(data)
       assert result.result == "Processed test"
   ```

### Working with WebAuthn

```python
from hoa.services.webauthn import WebAuthnService

# Initialize
webauthn_service = WebAuthnService(db, settings)

# Begin registration
options, user_id = await webauthn_service.begin_registration(
    user_data, rp_id
)

# Finish registration
await webauthn_service.finish_registration(
    user_id, credential, rp_id
)
```

### JWT Token Management

```python
from hoa.services.jwt_service import JWTService

# Initialize
jwt_service = JWTService(db, settings)

# Create tokens
access_token, access_expires = jwt_service.create_access_token(user.id)
refresh_token, refresh_expires = jwt_service.create_refresh_token(user.id)

# Validate token
payload = jwt_service.validate_token(token)
user_id = payload["sub"]
```

---

## Debugging

### Backend Debugging

1. **Add print statements**:

   ```python
   print(f"Debug: {variable}")
   ```

2. **Use Python debugger**:

   ```python
   import pdb; pdb.set_trace()
   ```

3. **Check logs**:

   ```bash
   # Server logs in terminal
   ```

4. **Interactive shell**:
   ```bash
   uv run python
   >>> from hoa.database import SessionLocal
   >>> from hoa.models.user import User
   >>> db = SessionLocal()
   >>> users = db.query(User).all()
   ```

### Frontend Debugging

1. **Browser DevTools** (F12):

   - Console for logs
   - Network tab for API requests
   - Application tab for cookies/storage

2. **Add console logs**:

   ```typescript
   console.log("Debug:", variable);
   ```

3. **React DevTools** (Chrome extension)

### Common Issues

**Issue**: 404 on API endpoints after code changes

- **Solution**: Restart dev server

**Issue**: Frontend not updating

- **Solution**: Rebuild frontend (`cd frontend && yarn build`)

**Issue**: Database errors

- **Solution**: Delete database and restart (`rm ~/.config/hoa/hoa.db`)

**Issue**: WebAuthn not working

- **Solution**: Use Chrome/Edge, check HTTPS/localhost, check console

---

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Implement changes
5. Ensure all tests pass (`uv run pytest`)
6. Commit with conventional commit message
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

### Code Review Checklist

- [ ] Tests written and passing
- [ ] Code follows style guide (ruff)
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow conventions
- [ ] Coverage maintained or improved

### Getting Help

- **Issues**: https://github.com/yourusername/hoa/issues
- **Discussions**: https://github.com/yourusername/hoa/discussions
- **Documentation**: See `docs/` directory

---

## Additional Resources

- [API Reference](api.md)
- [Deployment Guide](deployment.md)
- [Architecture Decisions](../AGENTS.md)
- [WebAuthn Specification](https://www.w3.org/TR/webauthn-2/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Preact Documentation](https://preactjs.com/)

---

**Happy Coding! 🚀**
