# HOA Frontend

Vite + Preact + TypeScript frontend for HOA authentication system.

## Setup

```bash
# Install dependencies (using yarn v2)
cd frontend
yarn install

# Run development server
yarn dev

# Build for production
yarn build

# Preview production build
yarn preview
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx          # Entry point
│   ├── app.tsx           # Main app with routing
│   ├── pages/            # Page components
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   └── NotFound.tsx
│   ├── services/         # API client & utilities
│   │   └── api.ts
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   └── styles/           # CSS styles
│       └── main.css
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## Development

The frontend proxies API requests to `http://localhost:8000` during development.

Make sure the backend is running:

```bash
# In project root
cd ..
uv run python -m hoa
```

Then start the frontend dev server:

```bash
yarn dev
```

Visit `http://localhost:5173`

## Build

The frontend builds to `../hoa/static/` so FastAPI can serve it:

```bash
yarn build
```

Then the FastAPI server will serve the built frontend at `/`.

## TODO

### Core Infrastructure
- [ ] Implement WebAuthn helpers
- [ ] Create auth context provider
- [ ] Implement IndexedDB storage wrapper
- [ ] Add error boundary
- [ ] Add loading states

### Pages
- [ ] Complete Login page with WebAuthn
- [ ] Complete Register page with WebAuthn
- [ ] Complete Dashboard with user info
- [ ] Add Auth Methods management page
- [ ] Add Admin panel

### Features
- [ ] One-click login with stored credentials
- [ ] Token-based fallback login
- [ ] Profile editing
- [ ] Auth method management
- [ ] Admin user management

### Polish
- [ ] Modern UI design
- [ ] Responsive layout
- [ ] Dark mode toggle
- [ ] Accessibility improvements
- [ ] Error handling
- [ ] Form validation

