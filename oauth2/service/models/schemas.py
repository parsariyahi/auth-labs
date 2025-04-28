from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        orm_mode = True

class ClientCreate(BaseModel):
    name: str
    redirect_uris: Optional[str] = None
    client_type: str  # 'public' or 'confidential'

class ClientResponse(BaseModel):
    id: int
    client_id: str
    name: str
    client_type: str
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    # Depricate!!!!!
    pass

class TokenRequest(BaseModel):
    grant_type: str
    code: str = None
    redirect_uri: str = None
    client_id: str = None
    client_secret: str = None
    code_verifier: str = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class DeviceAuthorizationResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int

class UserInfoResponse(BaseModel):
    sub: str
    username: str
    email: str

class OpenIDConfiguration(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    device_authorization_endpoint: str
    jwks_uri: str
    response_types_supported: list
    subject_types_supported: list
    id_token_signing_alg_values_supported: list
    scopes_supported: list
    token_endpoint_auth_methods_supported: list
    claims_supported: list 