#!/bin/bash

# Entrypoint script for Docker container
# Handles database migrations and starts the API server

set -e  # Exit on error

echo "🚀 Starting E-commerce API..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U ecommerce_user > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "📦 Running database migrations..."
python init_db.py

# Start the API server
echo "🌐 Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

