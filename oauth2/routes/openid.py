from fastapi import APIRouter
from ..models.schemas import OpenIDConfiguration

router = APIRouter(tags=["openid"])

@router.get("/.well-known/openid-configuration", response_model=OpenIDConfiguration)
async def openid_configuration():
    return {
        "issuer": "http://localhost:8000",
        "authorization_endpoint": "http://localhost:8000/oauth2/authorize",
        "token_endpoint": "http://localhost:8000/oauth2/token",
        "userinfo_endpoint": "http://localhost:8000/oauth2/userinfo",
        "device_authorization_endpoint": "http://localhost:8000/oauth2/device_authorize",
        "jwks_uri": "http://localhost:8000/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "none"],
        "claims_supported": ["sub", "username", "email"]
    } 