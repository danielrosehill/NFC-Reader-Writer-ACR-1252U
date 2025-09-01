#!/bin/bash

# NFC CLI ACR1252 Installation Script
# Installs dependencies and sets up virtual environment

set -euo pipefail

# Resolve repository root (one level up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "🔧 NFC CLI ACR1252 Installation"
echo "================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "Please install pip and try again"
    exit 1
fi

# Check if uv is available, fallback to venv
if command -v uv &> /dev/null; then
    echo "📦 Creating virtual environment with uv..."
    uv venv .venv
    VENV_CREATED=true
    VENV_TYPE="uv"
else
    echo "📦 Creating virtual environment with venv..."
    python3 -m venv .venv
    VENV_CREATED=true
    VENV_TYPE="venv"
fi

if [ "${VENV_CREATED}" = true ]; then
    echo "✅ Virtual environment created successfully"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
if [ "${VENV_TYPE}" = "uv" ]; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "  1. Connect your ACS ACR1252 NFC reader"
echo "  2. Run: ./scripts/run.sh"
echo "  3. Or manually: source .venv/bin/activate && python main.py"
echo ""
echo "🔧 If you encounter permission issues:"
echo "  sudo usermod -a -G dialout \$USER"
echo "  sudo usermod -a -G plugdev \$USER"
echo "  (then log out and back in)"
echo ""

