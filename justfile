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
    uv run python scripts/guard/check_branch_name.py . "$(git branch --show-current)"
    uv run python scripts/guard/check_structure.py .
    uv run python scripts/guard/check_conventions.py .
    uv run python scripts/guard/check_assert_quality.py tests
    uv run python scripts/guard/check_assert_quality.py research/phase0/tests
    uv run python scripts/guard/check_agents_md.py AGENTS.md
    uv run python scripts/guard/check_enforcement_map.py .
    uv run python scripts/guard/check_no_research_imports.py .
    uv run python scripts/guard/records/check_no_vague_refs.py .
    uv run python scripts/guard/check_module_identity.py .
    uv run python scripts/guard/records/check_docs_sync.py .
    uv run python scripts/guard/records/check_documented_commands.py .
    uv run python scripts/guard/records/check_documented_recipes.py .
    uv run python scripts/guard/records/check_decided_vocabulary.py .
    uv run python scripts/guard/check_no_partial_clone.py .
    uv run python scripts/guard/check_constant_time_compare.py .
    uv run python scripts/guard/check_subprocess_timeouts.py .
    uv run python scripts/guard/records/check_burned_corpora.py .
    uv run python scripts/guard/records/check_plan_state.py .
    uv run python scripts/guard/records/check_stage_table.py .
    uv run python scripts/guard/records/check_withdrawn_amendments.py .
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
# `just verify` runs everything that CAN be run against real data today. What it does not yet
# cover is named in scripts/verify/README.md rather than left to be discovered: there is no
# golden PACK to diff against, so `verify-data` is not part of it.
#
# The previous gate here refused to run anything at all, on the grounds that product code was
# blocked behind the correlation test reporting a verdict. That test reported one -- it was NULL,
# it killed the earlier product, and this one inherits none of it. The gate outlived its reason
# by long enough to make the project's own definition of done unsatisfiable by anyone.

# Everything in `check`, plus real runs against real repositories. Target: under 10 minutes.
verify: check test-live verify-no-source-leak verify-pack-vs-git verify-determinism
    @echo ""
    @echo "✅ verify passed — the pipeline ran against real repositories and the pack holds no source."
    @echo "   Every pack row was recomputed from git per path, so this is not a self-comparison."
    @echo "   NOT covered: the SERIALISED form -- schema shape, row ordering, path encoding --"
    @echo "   which a byte-level golden would catch and a recomputation looks straight past."

# Runs the full pipeline against real repositories. No mocks, by guard rule.
test-live:
    uv run pytest tests/live -x --timeout=900 -m "not pinned_corpus"

# Gate 2b. Needs `just fixtures` first (~1.3 GB of bare clones). Kept out of `just verify`
# so the default path does not require the corpus; the plan records its status from a real run.
gate-2b:
    uv run pytest tests/live/test_gate_2b_pinned_corpus.py -m pinned_corpus -x --timeout=3600 -s

# Proves — does not assert — that no source text made it into the pack.
# ARCHITECTURE.md invariant 6, and a contractual claim we make to customers.
verify-no-source-leak:
    uv run python scripts/verify/build_pack.py --out .verify-pack.db --clone .verify-clone
    uv run python scripts/verify/assert_no_source_in_pack.py --pack .verify-pack.db --repo .verify-clone


# Recomputes every row of the pack from git, per path, and requires the same answer. This is the
# research's model -- `claims/verify.py` recomputes rather than citing -- applied to the pack, and
# it is what a golden pack would otherwise be trusted to have established once.
verify-pack-vs-git:
    uv run python scripts/verify/build_pack.py --out .verify-pack.db --clone .verify-clone
    uv run python scripts/verify/assert_pack_matches_git.py --pack .verify-pack.db --clone .verify-clone

# Diffs a produced pack against a reviewed golden pack. NOT part of `verify`, because there is no
# golden pack yet -- and a recipe that silently passed would be worse than one that says so.
# It refuses with the real reason: the pack format is days old and nobody has reviewed one.
verify-data:
    #!/usr/bin/env bash
    set -uo pipefail
    echo "" >&2
    echo "⛔ 'just verify-data' has nothing to compare against." >&2
    echo "" >&2
    echo "   It diffs a produced pack against a REVIEWED golden pack. store/ now produces a" >&2
    echo "   pack, but no human has reviewed one, so there is no golden to diff against." >&2
    echo "   Committing a pack generated by the code under test would make this recipe" >&2
    echo "   compare the output to itself -- green forever, proving nothing." >&2
    echo "" >&2
    echo "   To close this: run scripts/verify/build_pack.py, read the pack, and commit it" >&2
    echo "   as the golden with the review recorded. Until then 'just verify' runs without" >&2
    echo "   it and says so." >&2
    echo "" >&2
    exit 1

# Determinism: indexing the same history twice must produce the same pack content.
verify-determinism:
    uv run python scripts/verify/assert_deterministic.py --runs 3 \
        --clone .verify-clone --out .verify-pack.db

# ---------------------------------------------------------------- setup

# Fetch the pinned real repositories used by live tests. Large; run once.
# Clone the six repositories that produced the ranker's validated result, at the exact
# commits it was measured at. Needed by gate 2b only; `just check` does not touch them.
fixtures:
    uv run python scripts/fixtures/clone_pinned.py

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
