# OAuth2 API Documentation

## Base URL
All endpoints are relative to the base URL: `http://localhost:8000/oauth2`

## Available Scopes

The OAuth2 provider supports the following scopes:

1. `openid` (Required for OpenID Connect)
   - Required for OpenID Connect flows
   - Provides the `sub` (subject identifier) claim

2. `profile`
   - Provides access to basic profile information
   - Includes the following claims:
     - `username`
     - `name` (if available)

3. `email`
   - Provides access to the user's email address
   - Includes the following claims:
     - `email`
     - `email_verified` (if available)

### Scope Usage Examples

1. Requesting multiple scopes:
```http
GET /authorize?scope=openid profile email
```

2. Requesting minimal scope:
```http
GET /authorize?scope=openid
```

3. Requesting specific scopes:
```http
GET /authorize?scope=openid email
```

Note: The `openid` scope is required for OpenID Connect flows. Other scopes are optional and can be combined as needed.

## 1. Authorization Code Flow (for Web Applications)

This flow is recommended for web applications that can securely store client secrets.

### Step 1: Register Client
First, register your client application:

```http
POST /client/oauth/register
Content-Type: application/json

{
    "name": "Your App Name",
    "client_type": "confidential",
    "redirect_uris": "https://your-app.com/callback"
}
```

Response:
```json
{
    "id": 1,
    "client_id": "generated_client_id",
    "name": "Your App Name",
    "client_type": "confidential",
    "is_active": true
}
```

### Step 2: Initiate Authorization
Redirect the user to the authorization endpoint:

```http
GET /authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=openid&state=YOUR_STATE
```

Parameters:
- `response_type`: Must be "code"
- `client_id`: Your registered client ID
- `redirect_uri`: Must match registered redirect URI
- `scope`: Optional, space-separated scopes
- `state`: Optional, for CSRF protection

### Step 3: Exchange Code for Token
After user authorization, exchange the code for tokens:

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=RECEIVED_CODE&redirect_uri=YOUR_REDIRECT_URI&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

Response:
```json
{
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_token": "generated_refresh_token",
    "scope": "openid"
}
```

## 2. Client Credentials Flow (for Machine-to-Machine)

This flow is for server-to-server communication where no user is involved.

### Step 1: Register Client
Register your client with confidential type:

```http
POST /client/oauth/register
Content-Type: application/json

{
    "name": "Your Service",
    "client_type": "confidential",
    "redirect_uris": ""
}
```

### Step 2: Get Access Token
Request an access token:

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET
```

Response:
```json
{
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_token": "generated_refresh_token"
}
```

## 3. Device Flow (for Smart Devices/TVs)

This flow is designed for devices with limited input capabilities.

### Step 1: Request Device Authorization
```http
POST /device_authorize
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID&scope=openid
```

Response:
```json
{
    "device_code": "device_code",
    "user_code": "user_code",
    "verification_uri": "http://localhost:8000/device",
    "verification_uri_complete": "http://localhost:8000/device?user_code=user_code",
    "expires_in": 1800,
    "interval": 5
}
```

### Step 2: User Verification
1. Display the `user_code` to the user
2. User visits `verification_uri_complete` in a browser
3. User approves the device

### Step 3: Poll for Token
Poll the token endpoint until the user approves:

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=DEVICE_CODE&client_id=YOUR_CLIENT_ID
```

Response:
```json
{
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_token": "generated_refresh_token",
    "scope": "openid"
}
```

## 4. Refresh Token Flow

Use this to obtain a new access token when the current one expires.

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=YOUR_REFRESH_TOKEN&client_id=YOUR_CLIENT_ID
```

Response:
```json
{
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_token": "new_refresh_token",
    "scope": "openid"
}
```

## 5. User Management

### Register a New User
```http
POST /users/register
Content-Type: application/json

{
    "username": "newuser",
    "password": "securepassword",
    "email": "user@example.com"
}
```

Response:
```json
{
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "is_active": true
}
```

### Get User Information
```http
GET /users/info
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Response:
```json
{
    "sub": "user_id",
    "username": "username",
    "email": "email@example.com"
}
```

### List All Users (Admin Only)
```http
GET /users
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Response:
```json
[
    {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "is_active": true
    },
    {
        "id": 2,
        "username": "user2",
        "email": "user2@example.com",
        "is_active": true
    }
]
```

## 6. OpenID Connect Configuration

Get the OpenID Connect configuration:

```http
GET /.well-known/openid-configuration
```

Response:
```json
{
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
```

## Important Notes

1. **Token Expiration**:
   - Access tokens expire in 30 minutes (configurable)
   - Refresh tokens expire in 7 days (configurable)

2. **Security**:
   - Always use HTTPS in production
   - Store client secrets securely
   - Implement PKCE for public clients
   - Validate all redirect URIs

3. **Error Handling**:
   - All endpoints return appropriate HTTP status codes
   - Error responses include detailed error information:
     ```json
     {
         "error_type": "ErrorType",
         "error_message": "Detailed error message",
         "error_code": "ErrorCode"  // If applicable
     }
     ``` 