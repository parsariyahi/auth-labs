import requests
from django.conf import settings
from django.core.exceptions import ValidationError

class OAuth2Client:
    def __init__(self):
        self.provider_url = settings.OAUTH2_PROVIDER_URL
        self.client_id = settings.OAUTH2_CLIENT_ID
        self.client_secret = settings.OAUTH2_CLIENT_SECRET
        self.redirect_uri = settings.OAUTH2_REDIRECT_URI

    def get_authorization_url(self, state=None):
        """Generate the authorization URL for the OAuth2 provider."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
        }
        if state:
            params['state'] = state

        return f"{self.provider_url}/authorize?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def get_token(self, code):
        """Exchange authorization code for access token."""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        response = requests.post(
            f"{self.provider_url}/token",
            data=data
        )

        if response.status_code != 200:
            raise ValidationError(f"Failed to get token: {response.text}")

        return response.json()

    def get_user_info(self, access_token):
        """Get user information using the access token."""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.get(
            f"{self.provider_url}/users/info",
            headers=headers
        )

        if response.status_code != 200:
            raise ValidationError(f"Failed to get user info: {response.text}")

        return response.json()

    def refresh_token(self, refresh_token):
        """Refresh the access token using refresh token."""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        response = requests.post(
            f"{self.provider_url}/token",
            data=data
        )

        if response.status_code != 200:
            raise ValidationError(f"Failed to refresh token: {response.text}")

        return response.json() 