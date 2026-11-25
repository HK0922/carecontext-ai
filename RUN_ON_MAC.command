#!/bin/zsh
# CareContext v0.4.0a1 for Apple Silicon and Intel macOS
# Open Terminal in this folder and run: zsh RUN_ON_MAC.command
set -euo pipefail
cd "$(dirname "$0")"

echo "CareContext v0.4.0a1 - Python 3.14/3.15 setup"
PYTHON_BIN=""
for candidate in python3.14 python3.15 python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; assert (3,11) <= sys.version_info[:2] <= (3,15)' >/dev/null 2>&1; then
      PYTHON_BIN="$(command -v "$candidate")"
      break
    fi
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.11-3.15 not found. On macOS run: brew install python@3.14"
  exit 1
fi
"$PYTHON_BIN" --version
if [[ -x .venv/bin/python ]]; then
  CURRENT_VERSION="$(.venv/bin/python -c 'import sys;print(".".join(map(str,sys.version_info[:2])))' || true)"
  SELECTED_VERSION="$("$PYTHON_BIN" -c 'import sys;print(".".join(map(str,sys.version_info[:2])))')"
  if [[ "$CURRENT_VERSION" != "$SELECTED_VERSION" ]]; then
    BACKUP_NAME=".venv.previous.$(date +%Y%m%d%H%M%S)"
    echo "Existing .venv uses Python $CURRENT_VERSION; preserving it as $BACKUP_NAME"
    mv .venv "$BACKUP_NAME"
  fi
fi
if [[ ! -x .venv/bin/python ]]; then
  echo "Creating virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi
source .venv/bin/activate
echo "Installing Python dependencies (internet required on first run)..."
python -m pip install -r requirements.txt
python -m pip check
printf '\nStarting CareContext at http://127.0.0.1:8000\n'
printf 'Use Control+C to stop. Research mode accepts authorized de-identified documents only.\n'
printf 'Research Lab: http://127.0.0.1:8000/research (enable with CARECONTEXT_RESEARCH_MODE=1).\n\n'
python -m carecontext.cli serve
