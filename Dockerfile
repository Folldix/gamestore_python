FROM python:3.11-slim

# Env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create media dir
RUN mkdir -p /app/media

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["gunicorn", "gamestore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
