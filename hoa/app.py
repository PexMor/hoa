"""
FastAPI application factory.
"""

from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from hoa.api import admin, auth, m2m, users
from hoa.config import get_settings
from hoa.database import init_db


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title="HOA - Heavily Over-engineered Authentication",
        description="WebAuthn/Passkey authentication with JWT tokens and multi-auth support",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Initialize database
    init_db(
        database_url=settings.database_url,
        echo=(settings.log_level == "DEBUG"),
    )

    # Add session middleware
    session_max_age = int(timedelta(days=settings.session_max_age_days).total_seconds())
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=session_max_age,
        https_only=settings.session_cookie_secure,
        same_site=settings.session_cookie_samesite,
    )

    # Add CORS middleware if enabled
    if settings.cors_enabled and settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API routers
    app.include_router(auth.router)
    app.include_router(m2m.router)
    app.include_router(users.router)
    app.include_router(admin.router)

    # Add utility endpoints
    from hoa.version import get_version_info

    @app.get("/api/health")
    def health_check():
        """Health check endpoint with version info."""
        return {
            "status": "healthy",
            **get_version_info()
        }

    @app.get("/api/version")
    def get_version():
        """Get version information."""
        return get_version_info()

    @app.get("/api/config")
    def get_frontend_config():
        """Get frontend configuration."""
        return {
            "allowed_rps": settings.parsed_rps,
            "require_auth_method_approval": settings.require_auth_method_approval,
            "environment": settings.environment,
            **get_version_info()
        }

    # Mount static files (built frontend) - must be last to avoid overriding API routes
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount(
            "/",
            StaticFiles(directory=str(static_dir), html=True),
            name="static",
        )

        # SPA fallback - serve index.html for all non-API routes
        from fastapi.responses import FileResponse

        @app.exception_handler(404)
        async def custom_404_handler(request, exc):
            # Only serve index.html for non-API routes
            if not request.url.path.startswith("/api/"):
                index_path = static_dir / "index.html"
                if index_path.exists():
                    return FileResponse(index_path)
            # Otherwise, return the original 404 response
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return app

