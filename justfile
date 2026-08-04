# Task runner for qmctx.
#
# WHAT: Defines the two gates every change passes through.
# WHY:  `check` is the fast loop you run constantly. `verify` is the honest one — it runs
#       the real pipeline against real repositories and diffs the output against reviewed
#       golden files. A green `check` means the code compiles and the units behave. Only
#       a green `verify` means the data is right. Those are different claims and the
#       distinction is the whole point of this project.
# CONSUMED BY: developers, .claude/settings.json hooks, .github/workflows/.

set shell := ["bash", "-uc"]

default:
    @just --list

# ---------------------------------------------------------------- fast gate

# Everything that must pass before a commit. Target: under 60 seconds.
check: lint types guards test-unit test-property
    @echo "✅ check passed — code is well-formed. This does NOT mean the data is right."
    @echo "   Run 'just verify' before opening a PR."

lint:
    uv run ruff format --check .
    uv run ruff check .

types:
    uv run mypy --strict src/ scripts/

guards:
    uv run python scripts/guard/check_structure.py .
    uv run python scripts/guard/check_conventions.py .
    uv run python scripts/guard/check_assert_quality.py tests
    uv run python scripts/guard/check_agents_md.py AGENTS.md
    uv run python scripts/guard/check_docs_sync.py .

test-unit:
    uv run pytest tests/unit -x --timeout=60

test-property:
    uv run pytest tests/property -x --timeout=120

# ---------------------------------------------------------------- honest gate

# Everything in `check`, plus real runs against real data. Target: under 10 minutes.
verify: check test-live verify-data verify-no-source-leak
    @echo "✅ verify passed — output was produced by a real run and matches golden data."

# Runs the full pipeline against pinned real repositories. No mocks, by guard rule.
test-live:
    uv run pytest tests/live -x --timeout=900

# Re-runs the pipeline and diffs the produced pack against the reviewed golden pack.
# A test that passes while the data silently changed is the failure mode we exist to stop.
verify-data:
    uv run python scripts/verify/compare_golden.py \
        --fixtures tests/fixtures/repos \
        --golden   tests/fixtures/golden \
        --strict

# Proves — does not assert — that no source text made it into the pack.
# Invariant 6 in ARCHITECTURE.md. This is a contractual claim we make to customers.
verify-no-source-leak:
    uv run python scripts/verify/assert_no_source_in_pack.py \
        --fixtures tests/fixtures/repos \
        --min-match-length 40

# Determinism: indexing the same commit twice must produce byte-identical packs.
verify-determinism:
    uv run python scripts/verify/assert_deterministic.py --runs 3

# ---------------------------------------------------------------- setup

# Fetch the pinned real repositories used by live tests. Large; run once.
fixtures:
    git submodule update --init --recursive tests/fixtures/repos
    @echo "Fixtures ready. 'just verify' will now run."

install:
    uv sync --all-extras
    pre-commit install
    ln -sf AGENTS.md CLAUDE.md

# ---------------------------------------------------------------- product

index PATH=".":
    uv run qmctx index {{PATH}}

serve:
    uv run qmctx serve --host 127.0.0.1 --port 7331

# Read-only local inspection view. Debugging aid, not a product surface.
view:
    uv run qmctx view --host 127.0.0.1 --port 7332

# ---------------------------------------------------------------- docs

# Regenerates the folder-wise map in docs/CODEBASE.md from the actual tree.
docs-sync:
    uv run python scripts/docs/regenerate_codebase_map.py > docs/CODEBASE.md
    @echo "docs/CODEBASE.md regenerated — review the diff before committing."
