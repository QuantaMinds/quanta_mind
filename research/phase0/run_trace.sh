#!/usr/bin/env bash
set -euo pipefail
cd /w/research/phase0
export UV_PROJECT_ENVIRONMENT=/tmp/venv-linux
uv sync --quiet
exec uv run python scripts/trace_end_to_end.py "/tmp/trace_ws_${TRACE_TAG}" "${TRACE_PR}"
