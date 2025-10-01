#!/bin/bash

# lsec CLI Installation Script
# This script installs the lsec CLI tool system-wide

set -e

echo "🔐 Installing lsec CLI..."

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: setup.py not found. Please run this script from the cli directory."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is required but not installed."
    exit 1
fi

# Install the CLI tool
echo "📦 Installing lsec CLI tool..."
pip3 install -e .

# Verify installation
if command -v lsec &> /dev/null; then
    echo "✅ lsec CLI installed successfully!"
    echo ""
    echo "🎉 You can now use the lsec command:"
    echo "   lsec --help"
    echo ""
    echo "📝 Example commands:"
    echo "   lsec projects                    # List all projects"
    echo "   lsec export --project MyProject  # Export project variables"
    echo "   lsec import-env --project MyProject --env-file .env  # Import variables"
    echo ""
    echo "⚙️  Configuration:"
    echo "   export LSEC_API_URL=\"http://localhost:8088\""
    echo "   export LSEC_DEFAULT_PROJECT=\"MyProject\""
    echo ""
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
