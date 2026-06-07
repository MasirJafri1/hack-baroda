#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$BACKEND_DIR/venv}"
CREATE_VENV="${CREATE_VENV:-1}"
SCENARIO="${SCENARIO:-4}"

echo "[setup] Backend directory: $BACKEND_DIR"

if [[ "$CREATE_VENV" == "1" ]]; then
  if [[ ! -d "$VENV_DIR" ]]; then
    echo "[setup] Creating virtual environment at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  PYTHON_BIN="python"
  PIP_INSTALL_ARGS=()
else
  PIP_INSTALL_ARGS=(--break-system-packages)
fi

if [[ -f "$BACKEND_DIR/.env" ]]; then
  echo "[setup] Loading environment from .env"
  # shellcheck disable=SC1090
  set -a
  source "$BACKEND_DIR/.env"
  set +a
else
  echo "[setup] No .env found. The test harness will still run, but LLM-backed nodes may warn or fail without GROQ_API_KEY."
fi

echo "[setup] Installing requirements"
if [[ "$CREATE_VENV" == "1" ]]; then
  "$PYTHON_BIN" -m pip install --upgrade pip
fi
"$PYTHON_BIN" -m pip install "${PIP_INSTALL_ARGS[@]}" -r "$BACKEND_DIR/requirements.txt"

echo "[run] Starting backend test harness (scenario $SCENARIO)"
printf "%s\n" "$SCENARIO" | "$PYTHON_BIN" "$BACKEND_DIR/test_pipeline.py"
