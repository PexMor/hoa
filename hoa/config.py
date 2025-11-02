"""
Configuration management for HOA using configargparse.

Configuration precedence: CLI arguments > Environment variables > Config file
Config file location: ~/.config/hoa/config.yaml
"""

import os
import secrets
from pathlib import Path
from typing import Literal

import configargparse
import yaml
from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


def get_config_dir() -> Path:
    """Get the configuration directory (~/.config/hoa/)."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        config_dir = Path(config_home) / "hoa"
    else:
        config_dir = Path.home() / ".config" / "hoa"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def generate_admin_token() -> str:
    """Generate a secure admin token using base58 encoding."""
    # Base58 alphabet (excludes confusing characters: 0, O, I, l)
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    # Generate 32 random characters
    token = "".join(secrets.choice(alphabet) for _ in range(32))
    return token


def ensure_admin_token() -> str:
    """Ensure admin token exists, generate if not."""
    config_dir = get_config_dir()
    admin_token_file = config_dir / "admin.txt"

    if admin_token_file.exists():
        return admin_token_file.read_text().strip()

    # Generate new token
    token = generate_admin_token()
    admin_token_file.write_text(token + "\n")
    # Set restrictive permissions (0600)
    admin_token_file.chmod(0o600)

    print(f"Generated new admin token: {token}")
    print(f"Saved to: {admin_token_file}")
    print("Keep this token secure!")

    return token


def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)


def ensure_config_file() -> Path:
    """Ensure config file exists, create from example if not."""
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"

    if config_file.exists():
        return config_file

    # Create default config with hyphens to match CLI args
    default_config = {
        "host": "127.0.0.1",
        "port": 8000,
        "reload": False,
        "database-url": f"sqlite:///{config_dir}/hoa.db",
        "secret-key": generate_secret_key(),
        "jwt-algorithm": "RS256",
        "jwt-expiration-minutes": 60,
        "jwt-refresh-expiration-days": 30,
        "allowed-rps": "localhost|Local Development|http://localhost:8000;http://127.0.0.1:8000",
        "require-auth-method-approval": False,
        "allow-self-service-auth": True,
        "environment": "development",
        "log-level": "INFO",
        "session-max-age-days": 14,
        "session-cookie-secure": False,
        "session-cookie-httponly": True,
        "session-cookie-samesite": "lax",
        "cors-enabled": False,
        "cors-origins": [],
    }

    with open(config_file, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    print(f"Created default configuration file: {config_file}")

    return config_file


def get_config_parser() -> configargparse.ArgumentParser:
    """Create and configure the argument parser."""
    config_file = ensure_config_file()

    parser = configargparse.ArgumentParser(
        default_config_files=[str(config_file)],
        description="HOA - Heavily Over-engineered Authentication",
        config_file_parser_class=configargparse.YAMLConfigFileParser,
        # Allow abbreviations for config file keys (database_url -> database-url)
        args_for_setting_config_path=[],  # Disable -c for config path
        ignore_unknown_config_file_keys=False,
    )

    # Server configuration
    parser.add_argument(
        "--host",
        env_var="HOA_HOST",
        default="127.0.0.1",
        help="Host to bind the server to",
    )
    parser.add_argument(
        "--port",
        env_var="HOA_PORT",
        type=int,
        default=8000,
        help="Port to bind the server to",
    )
    parser.add_argument(
        "--reload",
        env_var="HOA_RELOAD",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # Database
    parser.add_argument(
        "--database-url",
        env_var="HOA_DATABASE_URL",
        default=f"sqlite:///{get_config_dir()}/hoa.db",
        help="Database connection URL",
    )

    # Security
    parser.add_argument(
        "--secret-key",
        env_var="HOA_SECRET_KEY",
        help="Secret key for session management",
    )

    # JWT
    parser.add_argument(
        "--jwt-algorithm",
        env_var="HOA_JWT_ALGORITHM",
        choices=["RS256", "HS256"],
        default="RS256",
        help="JWT signing algorithm",
    )
    parser.add_argument(
        "--jwt-expiration-minutes",
        env_var="HOA_JWT_EXPIRATION_MINUTES",
        type=int,
        default=60,
        help="JWT access token expiration in minutes",
    )
    parser.add_argument(
        "--jwt-refresh-expiration-days",
        env_var="HOA_JWT_REFRESH_EXPIRATION_DAYS",
        type=int,
        default=30,
        help="JWT refresh token expiration in days",
    )

    # WebAuthn
    parser.add_argument(
        "--allowed-rps",
        env_var="HOA_ALLOWED_RPS",
        default="localhost|Local Development|http://localhost:8000;http://127.0.0.1:8000",
        help="Allowed Relying Parties (format: rp_id|rp_name|origin1;origin2,...)",
    )

    # Auth
    parser.add_argument(
        "--require-auth-method-approval",
        env_var="HOA_REQUIRE_AUTH_METHOD_APPROVAL",
        action="store_true",
        help="Require admin approval for new auth methods",
    )
    parser.add_argument(
        "--allow-self-service-auth",
        env_var="HOA_ALLOW_SELF_SERVICE_AUTH",
        action="store_true",
        default=True,
        help="Allow users to add auth methods themselves",
    )

    # OAuth2
    parser.add_argument(
        "--oauth2-google-client-id",
        env_var="HOA_OAUTH2_GOOGLE_CLIENT_ID",
        help="Google OAuth2 client ID",
    )
    parser.add_argument(
        "--oauth2-google-client-secret",
        env_var="HOA_OAUTH2_GOOGLE_CLIENT_SECRET",
        help="Google OAuth2 client secret",
    )
    parser.add_argument(
        "--oauth2-github-client-id",
        env_var="HOA_OAUTH2_GITHUB_CLIENT_ID",
        help="GitHub OAuth2 client ID",
    )
    parser.add_argument(
        "--oauth2-github-client-secret",
        env_var="HOA_OAUTH2_GITHUB_CLIENT_SECRET",
        help="GitHub OAuth2 client secret",
    )

    # Application
    parser.add_argument(
        "--environment",
        env_var="HOA_ENVIRONMENT",
        choices=["development", "production"],
        default="development",
        help="Application environment",
    )
    parser.add_argument(
        "--log-level",
        env_var="HOA_LOG_LEVEL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level",
    )

    # Session
    parser.add_argument(
        "--session-max-age-days",
        env_var="HOA_SESSION_MAX_AGE_DAYS",
        type=int,
        default=14,
        help="Session maximum age in days",
    )
    parser.add_argument(
        "--session-cookie-secure",
        env_var="HOA_SESSION_COOKIE_SECURE",
        action="store_true",
        help="Use secure cookies (HTTPS only)",
    )
    parser.add_argument(
        "--session-cookie-httponly",
        env_var="HOA_SESSION_COOKIE_HTTPONLY",
        action="store_true",
        default=True,
        help="Use HTTP-only cookies",
    )
    parser.add_argument(
        "--session-cookie-samesite",
        env_var="HOA_SESSION_COOKIE_SAMESITE",
        choices=["strict", "lax", "none"],
        default="lax",
        help="Cookie SameSite policy",
    )

    # CORS
    parser.add_argument(
        "--cors-enabled",
        env_var="HOA_CORS_ENABLED",
        action="store_true",
        help="Enable CORS",
    )
    parser.add_argument(
        "--cors-origins",
        env_var="HOA_CORS_ORIGINS",
        nargs="*",
        default=[],
        help="Allowed CORS origins",
    )

    return parser


class Settings(BaseSettings):
    """Application settings loaded from config parser."""

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False

    # Database
    database_url: str

    # Security
    secret_key: str
    admin_token: str

    # JWT
    jwt_algorithm: Literal["RS256", "HS256"] = "RS256"
    jwt_expiration_minutes: int = 60
    jwt_refresh_expiration_days: int = 30

    # WebAuthn
    allowed_rps: str

    # Auth
    require_auth_method_approval: bool = False
    allow_self_service_auth: bool = True

    # OAuth2
    oauth2_google_client_id: str | None = None
    oauth2_google_client_secret: str | None = None
    oauth2_github_client_id: str | None = None
    oauth2_github_client_secret: str | None = None

    # Application
    environment: Literal["development", "production"] = "development"
    log_level: str = "INFO"

    # Session
    session_max_age_days: int = 14
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: Literal["strict", "lax", "none"] = "lax"

    # CORS
    cors_enabled: bool = False
    cors_origins: list[str] = Field(default_factory=list)

    @field_validator("database_url")
    @classmethod
    def expand_database_path(cls, v: str) -> str:
        """Expand ~ and environment variables in database URL."""
        if v.startswith("sqlite:///"):
            path = v[10:]  # Remove sqlite:///
            expanded = os.path.expanduser(os.path.expandvars(path))
            return f"sqlite:///{expanded}"
        return v

    @property
    def parsed_rps(self) -> list[dict[str, any]]:
        """Parse allowed RPs configuration."""
        items = []
        for block in [b.strip() for b in self.allowed_rps.split(",") if b.strip()]:
            parts = block.split("|", 2)
            if len(parts) == 3:
                rp_id, rp_name, origins = parts
                items.append({
                    "rp_id": rp_id.strip(),
                    "rp_name": rp_name.strip(),
                    "origins": [o.strip() for o in origins.split(";") if o.strip()],
                })
        return items

    model_config = ConfigDict(
        env_prefix="HOA_",
        case_sensitive=False,
    )


def load_settings() -> Settings:
    """Load settings from config parser."""
    # Ensure admin token exists
    admin_token = ensure_admin_token()

    # Parse configuration
    parser = get_config_parser()
    args = parser.parse_args()

    # Convert argparse namespace to dict
    config_dict = vars(args)

    # Add admin token
    config_dict["admin_token"] = admin_token

    # Generate secret key if not provided
    if not config_dict.get("secret_key"):
        config_dict["secret_key"] = generate_secret_key()

    # Create settings instance
    return Settings(**config_dict)


# Global settings instance
settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global settings
    if settings is None:
        settings = load_settings()
    return settings

