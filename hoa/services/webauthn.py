"""
WebAuthn service for passkey registration and authentication.

Based on the Duo Labs webauthn library, supporting multi-RP and multi-origin.
"""

import base64

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from hoa.config import Settings


class WebAuthnService:
    """Service for WebAuthn/Passkey operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.allowed_rps = settings.parsed_rps

    def get_rp_for(self, rp_id: str, origin: str) -> dict | None:
        """
        Get RP configuration for given rp_id and origin.

        Args:
            rp_id: Relying Party ID
            origin: Origin URL

        Returns:
            RP configuration dict if valid, None otherwise
        """
        for rp in self.allowed_rps:
            if rp["rp_id"] == rp_id and origin in rp["origins"]:
                return rp
        return None

    def begin_registration(
        self,
        rp_id: str,
        origin: str,
        user_id: str,
        username: str,
        display_name: str,
        exclude_credentials: list[str] | None = None
    ) -> tuple[dict, str]:
        """
        Begin WebAuthn registration ceremony.

        Args:
            rp_id: Relying Party ID
            origin: Origin URL
            user_id: User ID (will be encoded in credential)
            username: Username
            display_name: Display name
            exclude_credentials: List of credential IDs to exclude

        Returns:
            Tuple of (registration options dict, challenge string)
        """
        rp = self.get_rp_for(rp_id, origin)
        if not rp:
            raise ValueError(f"Invalid RP/origin combination: {rp_id}/{origin}")

        # Convert excluded credential IDs to proper format
        excluded_creds = []
        if exclude_credentials:
            for cred_id in exclude_credentials:
                try:
                    # Decode base64url credential ID
                    cred_bytes = base64.urlsafe_b64decode(cred_id + "==")
                    excluded_creds.append(
                        PublicKeyCredentialDescriptor(id=cred_bytes)
                    )
                except Exception:
                    pass  # Skip invalid credential IDs

        # Generate registration options
        options = generate_registration_options(
            rp_id=rp["rp_id"],
            rp_name=rp["rp_name"],
            user_id=user_id.encode("utf-8"),
            user_name=username,
            user_display_name=display_name,
            exclude_credentials=excluded_creds if excluded_creds else None,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            attestation=AttestationConveyancePreference.NONE,
            timeout=60000,
        )

        # Store challenge for verification
        challenge = bytes_to_base64url(options.challenge)

        # Convert to dict for JSON serialization
        options_dict = {
            "rp": {
                "id": options.rp.id,
                "name": options.rp.name,
            },
            "user": {
                "id": bytes_to_base64url(options.user.id),
                "name": options.user.name,
                "displayName": options.user.display_name,
            },
            "challenge": challenge,
            "pubKeyCredParams": [
                {"type": p.type, "alg": p.alg}
                for p in options.pub_key_cred_params
            ],
            "timeout": options.timeout,
            "excludeCredentials": [
                {
                    "type": c.type,
                    "id": bytes_to_base64url(c.id),
                    "transports": c.transports if c.transports else []
                }
                for c in (options.exclude_credentials or [])
            ],
            "authenticatorSelection": {
                "residentKey": options.authenticator_selection.resident_key.value,
                "userVerification": options.authenticator_selection.user_verification.value,
            },
            "attestation": options.attestation.value,
        }

        return options_dict, challenge

    def finish_registration(
        self,
        credential: dict,
        expected_challenge: str,
        expected_rp_id: str,
        expected_origin: str,
    ) -> dict:
        """
        Finish WebAuthn registration ceremony.

        Args:
            credential: Credential response from client
            expected_challenge: Expected challenge (from begin_registration)
            expected_rp_id: Expected RP ID
            expected_origin: Expected origin

        Returns:
            Dict with credential information
        """
        rp = self.get_rp_for(expected_rp_id, expected_origin)
        if not rp:
            raise ValueError(f"Invalid RP/origin combination: {expected_rp_id}/{expected_origin}")

        # Verify registration response (credential can be dict, str, or RegistrationCredential)
        try:
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(expected_challenge),
                expected_rp_id=expected_rp_id,
                expected_origin=expected_origin,
                require_user_verification=False,
            )
        except Exception as e:
            raise ValueError(f"Registration verification failed: {e}") from e

        # Return credential information
        # Extract transports from credential if available
        transports = []
        if isinstance(credential, dict):
            transports = credential.get("response", {}).get("transports", [])
        
        return {
            "credential_id": bytes_to_base64url(verification.credential_id),
            "public_key": base64.b64encode(verification.credential_public_key).decode(),
            "sign_count": verification.sign_count,
            "transports": transports,
        }

    def begin_authentication(
        self,
        rp_id: str,
        origin: str,
        allow_credentials: list[str] | None = None
    ) -> tuple[dict, str]:
        """
        Begin WebAuthn authentication ceremony.

        Args:
            rp_id: Relying Party ID
            origin: Origin URL
            allow_credentials: List of allowed credential IDs (optional)

        Returns:
            Tuple of (authentication options dict, challenge string)
        """
        rp = self.get_rp_for(rp_id, origin)
        if not rp:
            raise ValueError(f"Invalid RP/origin combination: {rp_id}/{origin}")

        # Convert allowed credential IDs to proper format
        allowed_creds = []
        if allow_credentials:
            for cred_id in allow_credentials:
                try:
                    # Decode base64url credential ID
                    cred_bytes = base64.urlsafe_b64decode(cred_id + "==")
                    allowed_creds.append(
                        PublicKeyCredentialDescriptor(id=cred_bytes)
                    )
                except Exception:
                    pass  # Skip invalid credential IDs

        # Generate authentication options
        options = generate_authentication_options(
            rp_id=rp["rp_id"],
            allow_credentials=allowed_creds if allowed_creds else None,
            user_verification=UserVerificationRequirement.PREFERRED,
            timeout=60000,
        )

        # Store challenge for verification
        challenge = bytes_to_base64url(options.challenge)

        # Convert to dict for JSON serialization
        options_dict = {
            "challenge": challenge,
            "rpId": options.rp_id,
            "allowCredentials": [
                {
                    "type": c.type,
                    "id": bytes_to_base64url(c.id),
                    "transports": c.transports if c.transports else []
                }
                for c in (options.allow_credentials or [])
            ],
            "timeout": options.timeout,
            "userVerification": options.user_verification.value,
        }

        return options_dict, challenge

    def finish_authentication(
        self,
        credential: dict,
        expected_challenge: str,
        expected_rp_id: str,
        expected_origin: str,
        credential_public_key: str,
        credential_current_sign_count: int,
    ) -> dict:
        """
        Finish WebAuthn authentication ceremony.

        Args:
            credential: Credential response from client
            expected_challenge: Expected challenge (from begin_authentication)
            expected_rp_id: Expected RP ID
            expected_origin: Expected origin
            credential_public_key: Stored public key (base64 encoded)
            credential_current_sign_count: Current sign count

        Returns:
            Dict with authentication result and new sign count
        """
        rp = self.get_rp_for(expected_rp_id, expected_origin)
        if not rp:
            raise ValueError(f"Invalid RP/origin combination: {expected_rp_id}/{expected_origin}")

        # Decode public key
        try:
            public_key_bytes = base64.b64decode(credential_public_key)
        except Exception as e:
            raise ValueError(f"Invalid public key format: {e}") from e

        # Verify authentication response (credential can be dict, str, or AuthenticationCredential)
        try:
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(expected_challenge),
                expected_rp_id=expected_rp_id,
                expected_origin=expected_origin,
                credential_public_key=public_key_bytes,
                credential_current_sign_count=credential_current_sign_count,
                require_user_verification=False,
            )
        except Exception as e:
            raise ValueError(f"Authentication verification failed: {e}") from e

        # Return authentication result
        return {
            "credential_id": bytes_to_base64url(verification.credential_id),
            "new_sign_count": verification.new_sign_count,
        }

