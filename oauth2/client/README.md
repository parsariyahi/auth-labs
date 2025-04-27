# OAuth2 Client Application

A Django application that demonstrates OAuth2 authentication with an OAuth2 provider.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install django requests python-dotenv
```

3. Create a `.env` file in the project root with the following variables:
```env
OAUTH2_PROVIDER_URL=http://localhost:8000/oauth2
OAUTH2_CLIENT_ID=your_client_id
OAUTH2_CLIENT_SECRET=your_client_secret
OAUTH2_REDIRECT_URI=http://localhost:8001/oauth2/callback
SECRET_KEY=your_django_secret_key
DEBUG=True
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver 8001
```

## Usage

1. Register a client application with the OAuth2 provider:
```http
POST http://localhost:8000/oauth2/client/oauth/register
Content-Type: application/json

{
    "name": "OAuth2 Client",
    "client_type": "confidential",
    "redirect_uris": "http://localhost:8001/oauth2/callback"
}
```

2. Update the `.env` file with the received client ID and secret.

3. Access the application at http://localhost:8001

## Features

- OAuth2 Authorization Code Flow
- User authentication and session management
- Profile information display
- Secure token handling
- CSRF protection with state parameter

## Security Notes

- Always use HTTPS in production
- Keep your client secret secure
- Store tokens securely
- Implement proper session management
- Use secure cookie settings in production 