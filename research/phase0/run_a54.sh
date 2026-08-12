#!/usr/bin/env bash
set -euo pipefail
cd /w/research/phase0
export UV_PROJECT_ENVIRONMENT=/tmp/venv-linux
uv sync --quiet
exec uv run python scripts/a54_confound_check.py /tmp/a54_ws
