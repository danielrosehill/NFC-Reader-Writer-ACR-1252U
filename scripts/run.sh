#!/bin/bash

# NFC CLI ACR1252 Runner Script
# Activates virtual environment and runs the application

set -euo pipefail

# Resolve repository root (one level up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run ./scripts/install.sh first to set up the environment"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    echo "Please ensure you're in the repository root"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import textual" 2>/dev/null; then
    echo "❌ Dependencies not installed"
    echo "Please run ./scripts/install.sh first to install dependencies"
    exit 1
fi

# Run the application
echo "🚀 Starting NFC CLI ACR1252..."
echo "Press Ctrl+Q to quit the application"
echo ""

# Pass any command line arguments to the Python script
python main.py "$@"

