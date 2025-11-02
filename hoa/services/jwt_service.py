"""
JWT service for token creation and validation.

Supports both RS256 (asymmetric) and HS256 (symmetric) algorithms.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.orm import Session

from hoa.config import Settings
from hoa.models.session import JWTKey


class JWTService:
    """Service for JWT token operations."""

    def __init__(self, settings: Settings, db: Session):
        self.settings = settings
        self.db = db
        self.algorithm = settings.jwt_algorithm

    def _generate_key_id(self) -> str:
        """Generate a unique key ID."""
        return secrets.token_urlsafe(16)

    def _get_or_create_key(self) -> JWTKey:
        """
        Get active JWT key or create new one.

        Returns:
            Active JWT key
        """
        # Try to get active key
        key = self.db.query(JWTKey).filter(
            JWTKey.is_active,
            JWTKey.algorithm == self.algorithm
        ).first()

        if key and (key.expires_at is None or key.expires_at > datetime.now(UTC)):
            return key

        # Create new key
        key_id = self._generate_key_id()

        if self.algorithm == "RS256":
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            new_key = JWTKey(
                algorithm=self.algorithm,
                key_id=key_id,
                public_key=public_pem,
                private_key_encrypted=private_pem,  # For testing, not encrypted
                is_active=True,
            )
        else:  # HS256
            # Generate random secret
            secret = secrets.token_urlsafe(32)

            new_key = JWTKey(
                algorithm=self.algorithm,
                key_id=key_id,
                public_key=None,
                private_key_encrypted=secret,  # For testing, not encrypted
                is_active=True,
            )

        # Deactivate old keys
        if key:
            key.is_active = False
            key.rotated_at = datetime.now(UTC)

        self.db.add(new_key)
        self.db.commit()
        self.db.refresh(new_key)

        return new_key

    def create_access_token(
        self,
        user_id: UUID,
        expires_delta: timedelta | None = None
    ) -> tuple[str, datetime]:
        """
        Create JWT access token.

        Args:
            user_id: User ID to encode in token
            expires_delta: Optional expiration delta, defaults to config setting

        Returns:
            Tuple of (JWT token string, expiration datetime)
        """
        key = self._get_or_create_key()

        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.jwt_expiration_minutes)

        expires_at = datetime.now(UTC) + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expires_at,
            "iat": datetime.now(UTC),
            "type": "access",
        }

        token = jwt.encode(
            payload,
            key.private_key_encrypted,  # Not actually encrypted in tests
            algorithm=self.algorithm,
            headers={"kid": key.key_id}
        )

        return token, expires_at

    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: timedelta | None = None
    ) -> tuple[str, datetime]:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID to encode in token
            expires_delta: Optional expiration delta, defaults to config setting

        Returns:
            Tuple of (JWT token string, expiration datetime)
        """
        key = self._get_or_create_key()

        if expires_delta is None:
            expires_delta = timedelta(days=self.settings.jwt_refresh_expiration_days)

        expires_at = datetime.now(UTC) + expires_delta

        payload = {
            "sub": str(user_id),
            "exp": expires_at,
            "iat": datetime.now(UTC),
            "type": "refresh",
        }

        token = jwt.encode(
            payload,
            key.private_key_encrypted,  # Not actually encrypted in tests
            algorithm=self.algorithm,
            headers={"kid": key.key_id}
        )

        return token, expires_at

    def verify_token(self, token: str, token_type: str | None = None) -> dict[str, Any] | None:
        """
        Verify JWT token and return payload.

        Args:
            token: JWT token to verify
            token_type: Optional expected token type (access or refresh)

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            # Decode without verification first to get key_id
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")

            if not key_id:
                return None

            # Get key from database
            key = self.db.query(JWTKey).filter(
                JWTKey.key_id == key_id,
                JWTKey.algorithm == self.algorithm
            ).first()

            if not key:
                return None

            # Verify token
            payload = jwt.decode(
                token,
                key.private_key_encrypted if self.algorithm == "HS256" else key.public_key,
                algorithms=[self.algorithm],
            )

            # Check token type if specified
            if token_type and payload.get("type") != token_type:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def validate_token(self, token: str, token_type: str = "access") -> dict | None:
        """
        Validate JWT token and return payload (alias for verify_token).

        Args:
            token: JWT token to validate
            token_type: Expected token type (access or refresh)

        Returns:
            Token payload if valid, None otherwise
        """
        return self.verify_token(token, token_type)

    def get_user_id_from_token(self, token: str) -> UUID | None:
        """
        Extract user ID from valid token.

        Args:
            token: JWT token

        Returns:
            User ID if token is valid, None otherwise
        """
        payload = self.validate_token(token)
        if not payload:
            return None

        try:
            return UUID(payload["sub"])
        except (KeyError, ValueError):
            return None

    def rotate_keys(self) -> JWTKey:
        """
        Rotate JWT keys by creating a new active key.

        Returns:
            New active key
        """
        # Deactivate current active key
        current_key = self.db.query(JWTKey).filter(
            JWTKey.is_active,
            JWTKey.algorithm == self.algorithm
        ).first()

        if current_key:
            current_key.is_active = False
            current_key.rotated_at = datetime.now(UTC)

        # Force creation of new key
        self.db.commit()
        return self._get_or_create_key()

    def get_jwks(self) -> list:
        """
        Get JSON Web Key Set for RS256 public keys.

        Returns:
            List of JWK dictionaries (empty for HS256)
        """
        # For HS256, we don't publish keys
        if self.algorithm == "HS256":
            return []

        # For RS256, return public keys
        active_keys = self.db.query(JWTKey).filter(
            JWTKey.is_active,
            JWTKey.algorithm == "RS256",
            JWTKey.public_key.isnot(None)
        ).all()

        jwks = []
        for key in active_keys:
            # For a full implementation, we'd properly serialize the public key to JWK format
            # For now, return a simplified version
            jwks.append({
                "kty": "RSA",
                "kid": key.key_id,
                "use": "sig",
                "alg": "RS256",
                # In production, would need to extract n and e from public_key PEM
            })

        return jwks
