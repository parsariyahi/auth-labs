FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OAUTH2_PROVIDER_URL=http://oauth2-provider:8000/oauth2
ENV OAUTH2_CLIENT_ID=your_client_id
ENV OAUTH2_CLIENT_SECRET=your_client_secret
ENV OAUTH2_REDIRECT_URI=http://localhost:8080/oauth2/callback
ENV DEBUG=False
ENV SECRET_KEY=your_django_secret_key

# Expose port 8080
EXPOSE 8080

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"] 