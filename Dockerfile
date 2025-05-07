FROM python:3.13.2-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=AbacuSync.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files
COPY . .

# Create script to create superuser with hardcoded values
RUN echo '#!/usr/bin/env python\n\
import os\n\
import django\n\
\n\
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AbacuSync.settings")\n\
django.setup()\n\
\n\
from django.contrib.auth import get_user_model\n\
\n\
def create_superuser():\n\
    # Hardcoded credentials\n\
    phone = "12345678901"\n\
    email = "jekwkjewkjew@example.com"\n\
    password = "asdf"\n\
    \n\
    User = get_user_model()\n\
    \n\
    # Check if user already exists\n\
    if User.objects.filter(phone_number=phone).exists():\n\
        print(f"Superuser already exists")\n\
        return\n\
        \n\
    # Create superuser\n\
    User.objects.create_superuser(\n\
        phone_number=phone,\n\
        email=email,\n\
        password=password\n\
    )\n\
    print(f"Superuser created successfully")\n\
\n\
if __name__ == "__main__":\n\
    create_superuser()\n\
' > /app/create_superuser.py

# Make script executable
RUN chmod +x /app/create_superuser.py

# Expose port
EXPOSE 8080
# python /app/create_superuser.py && 
# Run superuser creation script and start server
CMD python /app/manage.py migrate && uvicorn AbacuSync.asgi:application --host 0.0.0.0 --port 8080