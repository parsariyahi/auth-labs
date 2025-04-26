from datetime import timedelta
import os

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-very-secure-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Database
DB_FILE = os.getenv("DB_FILE", "oauth_provider.db")

# Token Settings
TOKEN_EXPIRATION = {
    "access_token": timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    "refresh_token": timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
}

# Device Flow Settings
DEVICE_FLOW = {
    "verification_uri": "http://localhost:8000/device",
    "interval": 5  # Polling interval in seconds
} 