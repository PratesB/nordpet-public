# ==========================================
# STAGE 1: Build Tailwind CSS
# ==========================================
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the static folder (where tailwind config/input are)
COPY static/ ./static/

# Run the build command (minifies to static/css/output.css)
RUN npm run build


# ==========================================
# STAGE 2: Python App Setup
# ==========================================
FROM python:3.12-slim

# Prevent Python from writing pyc files and keep stdout unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the entire Django project
COPY . .

# Copy the built CSS from the tailwind-builder stage
COPY --from=tailwind-builder /app/static/css/output.css ./static/css/output.css

# Collect static files (whitenoise will serve them)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Default command (Web Server)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
