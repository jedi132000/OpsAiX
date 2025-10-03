#!/bin/bash

# OpsAiX Development Startup Script

set -e

echo "🚨 Starting OpsAiX - AI-Powered Incident Response Platform 🚀"

# Set environment
export PYTHONPATH=$(pwd)

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

echo "🌐 Starting OpsAiX server..."
echo "📊 Dashboard will be available at: http://localhost:8080"
echo "🔧 API docs will be available at: http://localhost:8080/docs"
echo ""

# Start the application
python src/main.py