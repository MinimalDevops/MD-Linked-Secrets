#!/bin/bash

# lsec CLI Uninstallation Script
# This script uninstalls the lsec CLI tool

set -e

echo "🔐 Uninstalling lsec CLI..."

# Check if lsec is installed
if ! command -v lsec &> /dev/null; then
    echo "❌ lsec CLI is not installed."
    exit 1
fi

# Uninstall the package
echo "📦 Uninstalling lsec CLI tool..."
pip3 uninstall -y lsec

# Verify uninstallation
if ! command -v lsec &> /dev/null; then
    echo "✅ lsec CLI uninstalled successfully!"
    echo ""
    echo "🗑️  The lsec command has been removed from your system."
    echo ""
    echo "💡 If you want to reinstall later, run:"
    echo "   cd cli && ./install.sh"
else
    echo "❌ Uninstallation failed. Please check the error messages above."
    exit 1
fi
