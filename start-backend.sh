#!/bin/bash

# Script to start backend with virtual environment activated
cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Set production environment variables
export DEBUG=false
export ENVIRONMENT=production

# Verify we're in the right environment
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"
echo "Debug mode: $DEBUG"

# Change to backend directory and start the server
cd backend
python main.py 