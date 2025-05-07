FROM python:3.13.2-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=AbacuSync.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

RUN echo '#!/usr/bin/env python\nimport os\nimport django\n\nos.environ.setdefault("DJANGO_SETTINGS_MODULE", "AbacuSync.settings")\ndjango.setup()\n\nfrom django.contrib.auth import get_user_model\n\ndef create_superuser():\n phone = "12345678901"\n email = "jekwkjewkjew@example.com"\n password = "asdf"\n \n User = get_user_model()\n \n if User.objects.filter(phone_number=phone).exists():\n print(f"Superuser already exists")\n return\n \n User.objects.create_superuser(\n phone_number=phone,\n email=email,\n password=password\n )\n print(f"Superuser created successfully")\n\nif __name__ == "__main__":\n create_superuser()\n' > /app/create_superuser.py

RUN chmod +x /app/create_superuser.py

# Expose port
EXPOSE 8080

# Start server using ASGI with uvicorn
CMD python /app/manage.py migrate && uvicorn AbacuSync.asgi:application --host 0.0.0.0 --port 8080