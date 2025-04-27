#!/bin/bash

# Change to the oauth2 directory where the Python module structure exists
cd "$(dirname "$0")/.." || exit 1

# Create database directory if it doesn't exist
mkdir -p service

# Initialize the database
if python -c "
from service.database.create_db import init_db
init_db()
"; then
echo "Database initialized successfully!" 
else
    echo "Failed to initialize database"
    exit 1
fi 