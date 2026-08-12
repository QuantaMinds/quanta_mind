#!/usr/bin/env bash
# One shard of the exposure pass under the pinned linux image. Sharded BY REPOSITORY:
# group_by_repo clones once per repo, and `cloned()` strictly removes workspace/<repo>
# first, so two shards sharing a repo would delete each other's clone. Each shard gets its
# own records file, output file and workspace; nothing is shared but the read-only mount.
set -euo pipefail
cd /w/research/phase0
export UV_PROJECT_ENVIRONMENT=/tmp/venv-linux
uv sync --quiet
exec uv run python -m phase0.exposure_run \
  --records "results/shard${SHARD}_records.jsonl" \
  --out "results/exposure_shard${SHARD}.jsonl" \
  --workspace "/tmp/ws${SHARD}"
