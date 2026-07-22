#!/usr/bin/env bash
set -e

# Enforce Vertex AI mode & Google Cloud ADC Authentication
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION:-"global"}
unset GEMINI_API_KEY

echo "=== Initializing ADK ECG Supervisor Agent with uv (Vertex AI Mode) ==="
uv run python3 -m agent_ecg.agent

echo ""
echo "=== Running ADK CLI Web / Interactive Server with uv ==="
if [ "$1" == "--cli" ]; then
    uv run adk run .
else
    echo "Starting ADK web server..."
    uv run adk web .
fi
