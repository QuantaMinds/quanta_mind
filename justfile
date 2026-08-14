# Task runner for quantamind.
#
# WHAT: Defines the two gates every change passes through.
# WHY:  `check` is the fast loop you run constantly. `verify` is the honest one — it runs
#       the real pipeline against real repositories and diffs the output against reviewed
#       golden files. A green `check` means the code compiles and the units behave. Only
#       a green `verify` means the data is right. Those are different claims and the
#       distinction is the whole point of this project.
# CONSUMED BY: developers, .claude/settings.json hooks, .github/workflows/.
#
# REQUIRES: just 1.58.0, uv 0.12.1, and bash. On Windows that means Git Bash, which
#       ships with Git for Windows — see CONTRIBUTING.md. The recipes are not
#       cmd.exe-compatible and are not trying to be.

# -e -o pipefail, not just -u. `just check | tail` masked an exit 1 and a red commit
# went out: a pipeline's status is its LAST command's, so tail's 0 hid the failure.
# Verified against a recipe running `false | tail -1` -- it now fails, and the line
# after it does not run. A rule people must remember is a wish; a rule the shell
# enforces is a rule.
set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# ---------------------------------------------------------------- fast gate

# Everything that must pass before a commit. Target: under 60 seconds.
check: lint types guards test-unit test-property test-phase0
    @echo "✅ check passed — code is well-formed. This does NOT mean the data is right."
    @echo "   Run 'just verify' before opening a PR."

lint:
    uv run ruff format --check .
    uv run ruff check .
    cd research/phase0 && uv run ruff format --check .
    cd research/phase0 && uv run ruff check .

types:
    uv run mypy --strict src/ scripts/
    # The harness is checked, but not strictly: it is research code with a finite
    # life, and pandas/scipy/pycg ship no type information. Rationale in its pyproject.
    cd research/phase0 && uv run mypy src/

guards:
    uv run python scripts/guard/check_structure.py .
    uv run python scripts/guard/check_conventions.py .
    uv run python scripts/guard/check_assert_quality.py tests
    uv run python scripts/guard/check_assert_quality.py research/phase0/tests
    uv run python scripts/guard/check_agents_md.py AGENTS.md
    uv run python scripts/guard/check_enforcement_map.py .
    uv run python scripts/guard/check_no_research_imports.py .
    uv run python scripts/guard/check_no_vague_refs.py .
    uv run python scripts/guard/check_module_identity.py .
    uv run python scripts/guard/check_docs_sync.py .
    uv run python scripts/guard/check_documented_commands.py .
    uv run python scripts/guard/check_no_partial_clone.py .
    uv run python scripts/guard/check_withdrawn_amendments.py .
    uv run python scripts/guard/citations/resolve.py .
    uv run python scripts/guard/citations/freshness.py .

test-unit:
    uv run pytest tests/unit -x --timeout=60

test-property:
    uv run pytest tests/property -x --timeout=120

# The correlation-test harness runs in its own virtual environment, on its own interpreter
# (Python 3.10 — PyCG does not run on 3.11+). See research/phase0/ENVIRONMENT.lock.
test-phase0:
    cd research/phase0 && uv run pytest -x --timeout=120

# ------------------------------------------------- the 20-PR labelling gate (human)

# Draw the blind, stratified sample: 10 PRs the classifier called BROKE and 10 it
# called CLEAN, shuffled, exported as URLs only. The seed is required so the draw
# is reproducible and cannot be quietly redrawn. Seals the answers into _key.csv.
#
# ARM is required and should be `agent`: the gate certifies the outcome classifier for
# the population it will be applied to, and the study runs on agent PRs. A26's rules
# were tuned on human commits, so a human-arm gate would validate the wrong corpus.
label-draw ARM SEED:
    cd research/phase0 && uv run python -m phase0.sample_for_labelling --arm {{ARM}} --n-broke 10 --n-clean 10 --seed {{SEED}}

# Score the labels against the sealed key. Run this AFTER all twenty are filled in
# AND committed — the commit timestamp is what proves the labels predate the
# comparison. Refuses an incomplete sheet.
label-score:
    cd research/phase0 && uv run python -m phase0.score_labelling

# Branch naming needs a branch, so it runs in CI rather than on every local check.
check-branch:
    uv run python scripts/guard/check_branch_name.py .

# ---------------------------------------------------------------- honest gate

# ⚠️  CALL-SITE CENSUS GATE — not runnable yet, and that is deliberate.
#
# Every recipe below operates on the SQLite pack, which does not exist: docs/BUILD_PLAN.md
# gates all product code on the correlation test reporting a verdict, and the three scripts under
# scripts/verify/ cannot be written before the format they verify exists. They are listed
# here rather than deleted so the gap is documented instead of silent — see
# scripts/verify/README.md. `just check` is the gate that must be green today.

# Refuses with an explanation rather than an opaque pytest exit 4 or a FileNotFoundError.
# A gate that fails confusingly gets worked around; one that says why does not.
_phase1-gate:
    #!/usr/bin/env bash
    set -uo pipefail
    if [ ! -f scripts/verify/compare_golden.py ]; then
      echo "" >&2
      echo "⛔ 'just verify' gates on the call-site census layer and is not runnable yet." >&2
      echo "" >&2
      echo "   It operates on the SQLite pack, and there is no pack. docs/BUILD_PLAN.md" >&2
      echo "   gates every layer of product code on the correlation test reporting a verdict, and" >&2
      echo "   docs/findings/PHASE0_PREREGISTRATION.md “Results” is still empty." >&2
      echo "" >&2
      echo "   This is not a broken checkout. See scripts/verify/README.md." >&2
      echo "   Run 'just check' — that is the gate that must be green today." >&2
      echo "" >&2
      exit 1
    fi

# Everything in `check`, plus real runs against real data. Target: under 10 minutes.
verify: _phase1-gate check test-live verify-data verify-no-source-leak
    @echo "✅ verify passed — output was produced by a real run and matches golden data."

# Runs the full pipeline against pinned real repositories. No mocks, by guard rule.
test-live: _phase1-gate
    uv run pytest tests/live -x --timeout=900

# Re-runs the pipeline and diffs the produced pack against the reviewed golden pack.
# A test that passes while the data silently changed is the failure mode we exist to stop.
verify-data: _phase1-gate
    uv run python scripts/verify/compare_golden.py \
        --fixtures tests/fixtures/repos \
        --golden   tests/fixtures/golden \
        --strict

# Proves — does not assert — that no source text made it into the pack.
# Invariant 6 in ARCHITECTURE.md. This is a contractual claim we make to customers.
verify-no-source-leak: _phase1-gate
    uv run python scripts/verify/assert_no_source_in_pack.py \
        --fixtures tests/fixtures/repos \
        --min-match-length 40

# Determinism: indexing the same commit twice must produce byte-identical packs.
verify-determinism: _phase1-gate
    uv run python scripts/verify/assert_deterministic.py --runs 3

# ---------------------------------------------------------------- setup

# Fetch the pinned real repositories used by live tests. Large; run once.
fixtures:
    git submodule update --init --recursive tests/fixtures/repos
    @echo "Fixtures ready. 'just verify' will now run."

install:
    uv sync --all-extras
    cd research/phase0 && uv sync
    uv run pre-commit install
    @echo "Installed. CLAUDE.md is committed and imports AGENTS.md — no symlink needed."

# ---------------------------------------------------------------- product

index PATH=".":
    uv run quantamind review {{PATH}}

serve:
    uv run quantamind serve --host 127.0.0.1 --port 7331

# Read-only local inspection view. Debugging aid, not a product surface.
view:
    uv run quantamind view --host 127.0.0.1 --port 7332

# ---------------------------------------------------------------- golden files

# One-shot authorisation for a single golden-file update. hook_pre_edit.py deletes
# the sentinel after one use, so it cannot be left enabled.
allow-golden:
    touch .quantamind-allow-golden
    @echo "Next golden-file write is authorised. State in the PR why the output changed."

# ---------------------------------------------------------------- pilot

# Build records from the corpus and report where rows are lost and why. Needs a
# GitHub token; require_token fails loudly rather than dropping to 60/hour.
# Stops at record construction on purpose: a pilot that produced a relative risk
# would invite reading it.
pilot REPOS="10":
    cd research/phase0 && GITHUB_TOKEN="$(gh auth token)" uv run python -m phase0.pilot.run --repos {{REPOS}}
