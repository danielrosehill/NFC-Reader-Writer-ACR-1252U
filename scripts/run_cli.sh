#!/bin/bash

# Run the plain CLI variant
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [ ! -d .venv ]; then
  echo "❌ Virtual environment not found. Run ./scripts/install.sh first." >&2
  exit 1
fi

source .venv/bin/activate
python nfc_cli.py "$@"

