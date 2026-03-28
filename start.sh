#!/bin/bash

echo "ClarityVoice Backend - Quick Start Script"
echo "=========================================="
echo ""

if [ ! -f .env ]; then
    echo "WARNING: .env file not found. Creating from template..."
    cp .env.example .env
    echo "Created .env file"
    echo "IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo ""
    exit 1
fi

if ! grep -q "sk-proj-" .env; then
    echo "WARNING: OpenAI API key not configured in .env"
    echo "Please edit .env and add your API key"
    echo ""
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Dependencies installed"
echo ""
echo "Starting ClarityVoice backend..."
echo "API docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
