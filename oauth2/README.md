# OAuth2 Provider Documentation

## Overview
This is a complete OAuth2 provider implementation supporting all major OAuth2 flows:
- Authorization Code Flow (with PKCE for SPAs)
- Client Credentials Flow (for M2M)
- Device Flow (for smart devices/TVs)
- Refresh Token Flow

## Available Scopes

The OAuth2 provider implements OpenID Connect and supports the following scopes:

### Standard Scopes

1. `openid` (Required)
   - Required for OpenID Connect flows
   - Provides the `sub` (subject identifier) claim
   - Must be included in all OpenID Connect requests

2. `profile`
   - Provides access to basic profile information
   - Available claims:
     - `username`
     - `name` (if available)

3. `email`
   - Provides access to the user's email address
   - Available claims:
     - `email`
     - `email_verified` (if available)

### Scope Usage

Scopes can be requested in the following ways:

1. **Authorization Code Flow**:
```http
GET /authorize?scope=openid profile email
```

2. **Device Flow**:
```http
POST /device_authorize?scope=openid profile email
```

3. **Client Credentials Flow**:
- Typically doesn't use scopes as it's for machine-to-machine communication

### User Info Claims

The `/userinfo` endpoint returns different claims based on the granted scopes:

- With `openid` scope:
  - `sub` (always included)

- With `profile` scope:
  - `username`
  - `name` (if available)

- With `email` scope:
  - `email`
  - `email_verified` (if available)

## Project Structure
```
oauth2/
├── main.py              # Application entry point
├── config.py            # Configuration settings
├── database/
│   ├── __init__.py
│   ├── models.py        # Database models
│   └── operations.py    # Database operations
├── auth/
│   ├── __init__.py
│   ├── authorization.py # Authorization endpoints
│   ├── token.py        # Token endpoints
│   └── device.py       # Device flow endpoints
├── models/
│   ├── __init__.py
│   └── schemas.py      # Pydantic models
└── utils/
    ├── __init__.py
    ├── security.py     # Security utilities
    └── helpers.py      # Helper functions
```

## API Endpoints

### Authorization Code Flow (with PKCE for SPAs)

1. **Authorization Endpoint**
   - URL: `/authorize`
   - Method: GET
   - Parameters:
     - `response_type`: Must be "code"
     - `client_id`: Client identifier
     - `redirect_uri`: Callback URL
     - `scope`: Optional requested scopes
     - `state`: Optional state parameter
     - `code_challenge`: PKCE code challenge
     - `code_challenge_method`: PKCE method (S256)
   - Response: Redirects to redirect_uri with authorization code

2. **Token Endpoint**
   - URL: `/token`
   - Method: POST
   - Parameters:
     - `grant_type`: "authorization_code"
     - `code`: Authorization code
     - `redirect_uri`: Must match original
     - `client_id`: Client identifier
     - `code_verifier`: PKCE code verifier
   - Response: Access token and refresh token

### Client Credentials Flow (M2M)

1. **Token Endpoint**
   - URL: `/token`
   - Method: POST
   - Parameters:
     - `grant_type`: "client_credentials"
     - `client_id`: Client identifier
     - `client_secret`: Client secret
   - Response: Access token

### Device Flow

1. **Device Authorization Endpoint**
   - URL: `/device_authorize`
   - Method: POST
   - Parameters:
     - `client_id`: Client identifier
     - `scope`: Optional requested scopes
   - Response: Device code and user code

2. **Device Verification**
   - URL: `/device`
   - Method: GET
   - Parameters:
     - `user_code`: User verification code
   - Response: HTML verification page

3. **Device Approval**
   - URL: `/device/approve`
   - Method: POST
   - Parameters:
     - `user_code`: User verification code
   - Response: Success/failure status

### Refresh Token Flow

1. **Token Endpoint**
   - URL: `/token`
   - Method: POST
   - Parameters:
     - `grant_type`: "refresh_token"
     - `refresh_token`: Valid refresh token
     - `client_id`: Client identifier
   - Response: New access token and refresh token

### Additional Endpoints

1. **User Info**
   - URL: `/userinfo`
   - Method: GET
   - Authentication: Bearer token
   - Response: User information

2. **Client Registration**
   - URL: `/register_client`
   - Method: POST
   - Parameters: Client details
   - Response: Registered client information

3. **User Registration**
   - URL: `/register_user`
   - Method: POST
   - Parameters: User details
   - Response: Registered user information

4. **OpenID Configuration**
   - URL: `/.well-known/openid-configuration`
   - Method: GET
   - Response: OpenID Connect configuration

## Security Features

- PKCE support for SPA clients
- Secure token storage
- Client type validation (public/confidential)
- Redirect URI validation
- Token expiration and refresh
- Secure password hashing (bcrypt)

## Database Schema

### Users Table
- id (PRIMARY KEY)
- username (UNIQUE)
- hashed_password
- email (UNIQUE)
- is_active

### Clients Table
- id (PRIMARY KEY)
- client_id (UNIQUE)
- client_secret
- redirect_uris
- name
- client_type
- is_active

### Authorization Codes Table
- id (PRIMARY KEY)
- code (UNIQUE)
- client_id
- redirect_uri
- user_id
- expires_at
- scope
- code_challenge
- code_challenge_method

### Tokens Table
- id (PRIMARY KEY)
- access_token (UNIQUE)
- refresh_token (UNIQUE)
- token_type
- expires_at
- scope
- client_id
- user_id

### Device Codes Table
- id (PRIMARY KEY)
- device_code (UNIQUE)
- user_code (UNIQUE)
- client_id
- scope
- expires_at
- user_id
- verification_uri
- interval
- is_approved

## Getting Started

1. Install dependencies:
```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] python-multipart
```

2. Initialize the database:
```bash
python -m oauth2.main
```

3. Run the server:
```bash
uvicorn oauth2.main:app --reload
```

## Configuration

The application can be configured through environment variables or by modifying `config.py`:

- `SECRET_KEY`: JWT signing key
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime
- `DB_FILE`: SQLite database file path 