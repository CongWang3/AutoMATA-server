#!/bin/bash

# Start the FastAPI application
echo "Starting Model Training API..."

# Run database migrations
echo "Running database migrations..."
python run_migrations.py

# Start the application server
echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload