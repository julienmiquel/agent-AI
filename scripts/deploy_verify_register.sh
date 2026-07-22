#!/usr/bin/env bash
set -e

PYTHON_BIN=".venv/bin/python3"

if [ ! -f "${PYTHON_BIN}" ]; then
  PYTHON_BIN="python3"
fi

exec ${PYTHON_BIN} scripts/pipeline.py "$@"
