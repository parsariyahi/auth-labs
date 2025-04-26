# OAuth2 API Documentation

## Base URL
All endpoints are relative to the base URL: `http://localhost:8000/oauth2`

## 1. Authorization Code Flow (for Web Applications)

This flow is recommended for web applications that can securely store client secrets.

### Step 1: Register Client
First, register your client application:

```http
POST /register_client
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
POST /register_client
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

## 5. User Info Endpoint

Get information about the authenticated user:

```http
GET /userinfo
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
   - Error responses include a `detail` field with the error message

4. **Configuration**:
   - Token expiration times can be configured in `config.py`
   - Base URLs can be configured in the OpenID configuration

5. **OpenID Configuration**:
   - Available at `/.well-known/openid-configuration`
   - Lists all supported endpoints and features 