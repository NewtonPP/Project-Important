#!/bin/bash

echo "Running ClarityVoice Tests"
echo "=============================="
echo ""

if [ ! -d "venv" ]; then
    echo "WARNING: Virtual environment not found. Run ./start.sh first"
    exit 1
fi

source venv/bin/activate

echo "Running pytest..."
pytest tests/ -v --tb=short

echo ""
echo "Tests complete"
