#!/bin/bash
# Script to start the API server with proper configuration

cd /Users/bilguundavaa/underwriting-copilot/softmax-underwriting-copilot

# Use in-memory SQLite database for local testing
export DATABASE_URL="sqlite+pysqlite:///:memory:"
export SANDBOX_MODE="true"
export REDIS_URL="redis://localhost:6379/0"

echo "======================================"
echo "Starting Underwriting API Server"
echo "======================================"
echo "Database: In-memory SQLite (no persistence)"
echo "Port: 8000"
echo "Docs: http://localhost:8000/docs"
echo "======================================"
echo ""

# Start the server
uvicorn app.main:app --reload --port 8000