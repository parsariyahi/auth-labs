#!/bin/bash

# Remove existing database if it exists
rm -f /app/oauth_provider.db

# Initialize the database
python -c "
from oauth2.database.operations import init_db
init_db()
"

# Start the application
exec uvicorn oauth2.main:app --host 0.0.0.0 --port 8000 