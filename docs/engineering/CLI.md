# The command line

**Every command this project ships** — the ten `quantamind` subcommands and every `just` recipe —
with its syntax, what it does, what it returns, and what a healthy run looks like. The HTTP surface
is documented separately in `docs/engineering/API.md`.

**A command that is not built says so and exits non-zero.** It never exits 0 having done nothing,
because that is how a runbook comes to report work it never did.

**Exit codes are uniform:** **0** success · **1** the command ran and something was wrong ·
**2** the command is not built yet.

---

## Contents

| Command | One line |
|---|---|
| [`--version`](#quantamind---version) | the package version |
| [`config`](#quantamind-config) | the resolved configuration, before anything runs |
| [`migrate`](#quantamind-migrate) | bring an existing store up to this build's schema |
| [`reconcile`](#quantamind-reconcile---account-name) | correct stored entitlement against the forge |
| [`scan`](#quantamind-scan-clone---explain-gcp_project) | walk a clone's history; say where rework lands |
| [`review`](#quantamind-review-clone---repo-r---sha-sha---json) | rank one change and print what we would say |
| [`retrospective`](#quantamind-retrospective-clone-clone----repo-name) | replay the ranker over a clone's own history |
| [`compliance`](#quantamind-compliance---repo-r---export-path) | every declared rule and what happened to it |
| [`cost`](#quantamind-cost---repo-r) | what this repository's reviews spent |
| [`dashboard`](#quantamind-dashboard-repo---limit-n) | what we commented on, and what became of it |
| [`standards`](#quantamind-standards---repo-r---pulls-n-) | what reviewers said more than once |
| [`serve`](#quantamind-serve---port-n---host-addr) | the HTTP endpoint |
| [`just` recipes](#just--the-development-commands) | build, test, verify, deploy |

---

# `quantamind` — the product

```
usage: quantamind [-h] [--version]
                  {config,migrate,dashboard,standards,compliance,cost,serve,review,scan,retrospective}
```

Installed by `uv sync --all-extras`. Every example below is written as `uv run quantamind …`
because that is how it runs from a checkout; an installed wheel drops the `uv run`.

---

## `quantamind --version`

**Syntax:** `quantamind --version`

**What:** prints the package version and exits 0.

> **It stays `0.0.0` on purpose**, until the ranker reproduces its research number inside this
> package. A version number that moves before the thing it names works is a claim.

---

## `quantamind config`

**Syntax:** `quantamind config`

**What:** prints every setting after environment variables are applied, and exits 0.

**Why:** a misconfiguration should be visible *before* a run, not inferred from a strange result
afterwards. **This is the command to run first on a new machine**, and the one to run on a server
when an answer looks wrong.

```
$ uv run quantamind config
deployment_shape           cloud
database_path              quantamind.db
max_requests               3
threshold_percentile       0.9
inference_enabled          False
inference_project          (unset)
gcloud_path                gcloud
model                      claude-opus-5
subprocess_timeout_seconds 30
clone_root                 .quantamind-clones
app_id                     4743262
app_key_path               /Users/you/.quantamind/app.pem
oauth_client_id            (unset)
oauth_client_secret        (unset)
public_read_token          set
posting_enabled            False

runs a model on a review:  False
```

**A secret is never printed.** `oauth_client_secret` and `public_read_token` render as `set` or
`(unset)` — enough to debug a missing value, not enough to leak one into a terminal recording.

**A malformed value raises `SettingsError` naming the variable and the value, and exits 1.** It
never falls back to a default silently.

> **`threshold_percentile` is printed and governs nothing.** No firing rule consumes it; setting it
> to 0.1 or 0.99 changes no output. It is listed because it appears in the output, and a reader
> would otherwise reasonably assume it does something.

**Settings** are read with a `QUANTAMIND_` prefix. The full table is in `docs/engineering/API.md`.

---

## `quantamind migrate`

**Syntax:** `quantamind migrate`

**What:** brings an existing store up to this build's `SCHEMA_VERSION`. Exits 0 when the store is
already current.

**Why it is a separate command and not automatic:** `store/schema.open_store()` **refuses** a
database this build would corrupt rather than migrating it in place. A read path that silently
migrated would rewrite a customer's audit trail as a side effect of somebody opening a dashboard.

**Expected:** one line per migration applied, or a line saying the store is already at the current
version. Exits 1 if the store cannot be read at all.

---

## `quantamind reconcile [--account NAME]`

**Syntax:** `quantamind reconcile` · `quantamind reconcile --account acme`

**What:** asks the forge which repositories each installation still covers, and marks removed any
we hold that it no longer lists. With no argument it walks every account holding at least one
live repository; `--account` narrows it to one.

**Why it exists:** `installation_repositories` sends a **delta**, not a list. An `installation`
event carries the full set and is therefore self-healing — re-provisioning six existing tenants
does nothing — but a dropped *removal* delivery leaves a repository entitled forever, reviewed and
billed, with nothing recording that we are wrong. This is the only thing that notices.

**What it will not do:** withdraw anything on a failure. A timeout, a rate limit, a 500 and a
revoked key all mean *we could not ask*, which is not the fact *the forge says this is gone*. Only
an answer withdraws, and an installation that lists **no** repositories at all is read as a shape
we misunderstood rather than as an instruction — obeying it would empty an account on a parsing
mistake.

**Expected:** one line per account and a total. **Exits 1 when any account could not be asked**,
because a run that reached nothing and a run that confirmed everything both withdraw zero and both
print a total — on a schedule the exit code is the only difference a human ever sees.

```
acme: withdrew 1/4 — acme/gadget
zeta: 2 repository(ies), all still covered
2 account(s): withdrew 1, could not ask about 0
```

**Run it on a schedule.** Nothing invokes it automatically; a scheduler calling it is an
operator's decision, the same argument `migrate` makes.

---

## `quantamind scan <clone> [--explain GCP_PROJECT]`

**Syntax:** `quantamind scan <clone>`

**What:** walks a clone's whole git history into a scratch index and prints where a later commit
has come back most often. **This is the first thing to run on a repository you have never seen.**

**Arguments**

| | |
|---|---|
| `clone` | a full clone. **Not** `--filter=blob:none`; see below |
| `--explain GCP_PROJECT` | *(suppressed from `--help`)* append a model's reading of the counts |

**What leaves the machine:** by default, **nothing**. The walk shells out to `git` in your clone,
the index is a `TemporaryDirectory`, and the report is printed. No account, no install, no socket.

```
$ uv run quantamind scan .verify-clone
QuantaMind -- first scan of pallets/flask

9,093 file-touches across 642 file(s), spanning 5,797 day(s) of history.

Where a later commit has come back most often:

   1. flask/app.py            354 touch(es)
   2. CHANGES.rst             328 touch(es)
   3. CHANGES                 317 touch(es)
   4. flask/helpers.py        204 touch(es)
   5. docs/quickstart.rst     183 touch(es)
   6. docs/api.rst            154 touch(es)
   7. docs/config.rst         132 touch(es)
   8. tests/test_basic.py     130 touch(es)
   9. requirements/dev.txt    129 touch(es)
  10. src/flask/app.py        128 touch(es)

The top 10 file(s) carry 23% of all file-touches in this repository.
This is a count of commits, not a judgement about the code. Run it again on the
same clone and it returns the same table.

[scan] 9,093 touch(es) indexed; newest commit read: 2026-02-19
```

**The heading is what the repository calls itself**, read from its `origin` remote — a clone in
`/tmp/x` is still `pallets/flask`. A clone with no origin reports `local/<directory>`, which says
which case you are in rather than guessing.

**Two things the output makes visible, deliberately:**

**The window.** Three weeks of history and seven years produce the same shape of table. Without
`spanning N day(s)` a reader will read a young repository's noise as a hotspot.

**A moved file reads as two rows.** `flask/app.py` at 354 and `src/flask/app.py` at 128 are the
same file before and after a directory move. `docs/product/evidence-ledger.md` measures that blind
spot — rename-blinded targets are 13.6× enriched among misses — and leaves it unfixed on purpose.
The scan inherits it and does not hide it.

**No risk word appears in this output.** Not "risky", not "problem", not "hotspot" as a verdict. A
file that has been fixed often is a file that has been fixed often; whether that is bad is a
judgement a count cannot support, and a unit test asserts none of those words can reach the reader.

### `--explain` — the model half, off by default

Appends one paragraph from Gemini, **below** the table and labelled.

```
$ uv run quantamind scan .verify-clone --explain my-gcp-project
… the table as above …
[scan] --explain is on: 10 file path(s) and their commit counts will be sent to
Vertex AI in project my-gcp-project. Your source code will not be.

--- a model's reading of the table above ---
The commit history shows that rework is highly concentrated in a small number of
files. These files represent a mix of core application logic, project-level
bookkeeping such as changelogs and dependency lists, and high-traffic
documentation. The distribution is not flat.
--- end of the model's reading ---
Written by a model from the counts above and nothing else -- it was not shown
your code. Published findings from this product's model half are 25.0% correct;
treat the paragraph as a prompt to look, never as a finding.
```

**Only paths and counts cross the boundary — never file content.** The scan already holds the whole
clone; sending it would be trivial and is refused. A file *path* is still the customer's
information, which is why the line above prints **before** the call, in time to interrupt it.

**The model is asked to describe, never to diagnose.** Its prompt bans naming a bug, a risk or a
fix, because it has not seen a line of code and any such sentence would be invention.

**A transport failure returns a sentence, never an exception.** The table is the product and has
already printed; an unreachable model must not take the report down with it.

> **Why it is off by default:** `docs/product/PITCH_DECK.md` sells the replay on one asymmetry — a
> prospect's history costs us CPU and costs a model-per-change reviewer an inference pass per
> change. **A narration that ran by default would delete that claim.**

**Exit codes:** `0` scanned · `1` the path is not a git clone.

---

## `quantamind review <clone> [--repo R] [--sha SHA] [--json]`

**Syntax:** `quantamind review <clone> [--repo owner/name] [--sha SHA] [--json]`

**What:** ranks one change's files against history and prints the comment we would post.

**Arguments**

| | |
|---|---|
| `clone` | a full clone; nothing is sent anywhere |
| `--repo` | `owner/name`, for the store key. Default `local/clone` |
| `--sha` | the commit to review. **Omit it** to review uncommitted work, and commits on this branch that are not on the default one |
| `--json` | print the review as JSON for a tool |
| `--deep GCP_PROJECT` | *(suppressed)* turn on model findings. See the warning below |

**Omitting `--sha` is the review worth having** — it reads what you have not committed yet,
**including untracked files**, which `git diff` omits and which are usually the new code.

```
$ uv run quantamind review .verify-clone --sha c17f3793
[review] 5 file(s) ranked, 1 skipped as unsupported
[review] 1 of your last 19 changes reached your top decile — 5%. Every change is
reviewed; that fraction is flagged.
### QuantaMind

⚠️ **Needs a human.** No model read this change; the checks below still ran.

**Start here**

- `src/flask/sessions.py`
- `src/flask/app.py`
- `src/flask/ctx.py`

_This change touches **5** file(s). **3** were read line by line._

- `src/flask/app.py` ⟵ read closely
- `src/flask/ctx.py` ⟵ read closely
- `src/flask/sessions.py` ⟵ read closely
- `src/flask/templating.py`
- `tests/test_basic.py`
```

### `--json`

```json
{
  "files": {
    "changed": ["src/flask/sessions.py", "src/flask/app.py", "src/flask/ctx.py",
                "src/flask/templating.py", "tests/test_basic.py"],
    "reviewed": ["src/flask/sessions.py", "src/flask/app.py", "src/flask/ctx.py"],
    "unread": ["src/flask/templating.py", "tests/test_basic.py"]
  },
  "findings": [],
  "history": {"src/flask/app.py": 3, "src/flask/ctx.py": 1,
              "src/flask/sessions.py": 4, "src/flask/templating.py": 1,
              "tests/test_basic.py": 1},
  "not_reviewed_because": null,
  "origin": "commit c17f3793",
  "rule_checks": [],
  "schema": 1,
  "verdicts": null
}
```

| Key | Meaning |
|---|---|
| `files.changed` | every changed file in a language we read |
| `files.reviewed` | the files the ranker funded. **These were looked at** |
| `files.unread` | changed and **not** looked at |
| `history` | prior-fix count per file — the ranking signal |
| `not_reviewed_because` | `null` when a ranking ran; otherwise `nothing_pending` or `no_supported_language` |
| `findings` | usually empty. Present only if a model ran, which it does not by default |
| `rule_checks` | one row per rule × file |
| `schema` | the JSON contract version |

**Consumed by `/qm-review`**, the editor command in `.claude/commands/qm-review.md`, which hands
this object to the agent in your editor and instructs it to **lead with what was not read**.

> **`--deep` is suppressed from `--help` and off unless named.** Raw model findings are
> **66.7–82.1% wrong**. It exists because the measurement half needs it; it is not a capability to
> put in front of a customer.

**Exit codes:** `0` printed · `1` not a clone, or nothing to review.

---

## `quantamind retrospective <clone> [<clone> ...] [--repo NAME]`

**Syntax:** `quantamind retrospective <clone> [<clone> …] [--repo owner/name]`

**What:** replays the ranker over a repository's own history and reports what it would have said —
the ranker, the alphabetical control, and exact hypergeometric chance, stratified.

**This is the sales instrument and the first thing a sceptic runs.** It needs a clone and nothing
else: no App install, no webhook, no token, **no code leaving the machine.**

```
$ uv run quantamind retrospective .verify-clone
Measured ELSEWHERE: on six repositories the method never saw, top-three-by-fix-history
missed 1.21% of the changes a later fix returned to, against an alphabetical control's
3.12% (n = 2,400, McNemar p < 1e-6, 6 of 6 positive).

THIS IS NOT THAT NUMBER. Below is a first measurement of one repository, unreplicated,
on history chosen by whoever ran it. It cannot confirm or refute the figure above, and
the two must not be combined, averaged or compared.

local/clone
-----------
  INCONCLUSIVE — 10 discordant pairs, floor is 20.
  all events       n=   531   ranker   0.38%   alphabetical   1.51%   chance   3.42%
  >3 files         n=   122   ranker   1.64%   alphabetical   6.56%   chance  14.89%
  <=3 files        n=   409   ranker   0.00%   alphabetical   0.00%   chance   0.00%
  77.0% of events touch <=3 files, which a budget of three reads entirely — no ordering
  could have missed them, so they decide nothing and the headline belongs to the row above.
  discordant pairs: ranker 8, control 2; exact McNemar p = 0.10938
```

**Four things this output does that are worth copying:**

**It refuses to be confused with the published figure.** The banner is not decoration — combining a
one-repository run with the replicated number is the misuse this report exists to prevent.

**`INCONCLUSIVE` is a verdict.** Below the pre-registered floor an impressive-looking number is
most likely noise, and the report says so rather than printing it bare.

**The degenerate stratum is reported separately.** Events touching ≤3 files are read entirely by a
budget of three, so **no ordering could have missed them.** Pooling them dilutes the effect
threefold; the headline belongs to the informative row.

**The control is checked too.** `alphabetical vs chance` near zero means the control was genuinely
uninformative; well above it means directory layout made it a poor one.

**The bound is the product.** Each event is scored over `[at − 365d, at)`, half-open, so a change
cannot see itself or anything after it. `tests/live/test_retrospective_leakage.py` rebuilds the
index from only pre-event commits, requires an identical ranking, **then sabotages the bound and
requires that to fail.**

**Several clones** are pooled, and the pooled figure is reported beside the individual ones.

**Exit codes:** `0` reported · `1` a path is not a git clone.

---

## `quantamind compliance --repo R [--export PATH]`

**Syntax:** `quantamind compliance --repo owner/name [--export trail.json]`

**What:** every declared rule and what happened to it, for one repository. With `--export`, writes
the whole audit trail as JSON.

**Why JSON and not CSV:** a CSV opens more easily and **cannot carry the four sentences that make
the document honest**:

1. nothing is backfilled;
2. an absent row means the check did not run;
3. `uncheckable` and `deferred` are **not** passes;
4. only a `parser` row re-runs.

**`limits` comes first in the file**, so a reader who stops after the first object has read the
part that stops them over-reading the rest.

**The window is read from the rows, never assumed.** The trail begins when rule checking was
installed, not when the repository was created. **An export implying otherwise would be the most
dangerous document this product can produce.** An empty export is a document, not an error, and it
says it covers nothing.

```
$ uv run quantamind compliance --repo pallets/flask
pallets/flask has no store under quantamind.db.
```

**Exit codes:** `0` printed or written · `1` no store for that repository.

---

## `quantamind cost --repo R`

**Syntax:** `quantamind cost --repo owner/name`

**What:** what this repository's reviews spent, from the rows that recorded it.

**When part of a review's cost was never metered it says so**, rather than writing a floor as a
total: *"cost not recorded — part of it was never metered, and a floor written as a total would be
priced from."*

**Exit codes:** `0` printed · `1` no store for that repository.

---

## `quantamind dashboard <repo> [--limit N]`

**Syntax:** `quantamind dashboard owner/name [--limit 100]`

**What:** for each thing we commented on — did the pull request merge? Did a later fix come back to
that file? `prod_signal` is where an incident or a rollback attaches.

**This answers the question the comment cannot: did any of this matter?**

**It states when the numbers cannot yet be read as a rate.** A dashboard showing "100% accurate"
over four reviews is worse than one showing nothing.

**Exit codes:** `0` printed · `1` no store for that repository.

---

## `quantamind standards --repo R --pulls N […]`

**Syntax:** `quantamind standards --repo owner/name --pulls 12 34 56`

**What:** mines the named pull requests for points a reviewer made **more than once**, and proposes
them as candidate rules.

**A proposal is not a rule and never becomes one here.** A human accepts or refuses it.

**The pull requests are named, never crawled.** This product has never run a "recent changes"
search and will not pretend to.

**Three filters do the real work:**

**The acknowledgement filter.** Without it the largest clusters in a real corpus are `done` ×6,
`fixed` ×6, `ditto` ×4 and `nit: suggestion` ×11.

**Repetition inside one pull request is not a standard.** A standard is something said again on a
*different* change, so `Comment.pull` is required to count — and when a source cannot supply it,
`distinct_pulls` is `None` rather than a number, because "said twice on two changes" and "we could
not tell" must not read alike.

**A bot's comment is not a team's standard.** Pointed at this repository's own pull requests, the
miner proposed three "standards" and **all three were our own review comments** repeated across
heads. Machine-authored comments are refused, and the caller is told how many were dropped.

> **The measured yield is thin and was measured before this was built:** ~1.62 candidate clusters
> per repository, of which roughly five of thirteen were generalisable — **under one real rule per
> repository per ~150 comments.**

**Exit codes:** `0` printed · `1` the repository or pull requests could not be read.

---

## `quantamind serve [--port N] [--host ADDR]`

**Syntax:** `quantamind serve [--port 7331] [--host 127.0.0.1]`

**What:** binds the HTTP endpoint. Routes are documented in `docs/engineering/API.md`.

**`--host` must be asked for.** Loopback by default so a developer does not expose an endpoint to
their network by omission; the container passes `0.0.0.0` deliberately.

```
$ uv run quantamind serve --port 7331
[serve] listening on 127.0.0.1:7331
[serve] POST /webhook  — verifies the signature, refuses a replay, answers 202
[serve] GET  /health   — opens the store and reports what is wrong, never raises
[serve] GET  /         — the dashboard: sign in, then a repository's reports
[serve] GET  /r/<owner>/<name> — compliance, outcomes and cost for one repository
[serve] GET  /scan?repo=owner/name — what the first history walk found, as JSON
[serve] It REVIEWS: clone, rank, render. Posting is OFF — it prints the comment it would have posted and writes nothing.
[serve] http.server is not a hardened edge — run it behind a TLS-terminating proxy.
```

**Every line of that banner is pinned by a test.** `tests/unit/layers/serve/test_serve_banner.py`
sizes its read window from the required lines, so **a banner line added without a line there pushes
the lines after it past the end of the window and fails.** That is how the browser routes were
caught: they were announced and not required.

**The posting line is the only warning an operator gets**, and it names the state rather than
describing the flag.

**Exit codes:** `0` on a clean `Ctrl-C` · `1` the port is in use or settings are invalid.

---

# `just` — the development commands

## The two that matter

### `just check` — before every commit

Runs, in order: **`lint` → `types` → `guards` → `test-unit` → `test-property` → `test-phase0`.**
Any step failing stops the run.

```
$ just check
All checks passed!                      ← ruff format + ruff check
Success: no issues found                ← mypy --strict
[structure] ok                          ← ≤200 lines/file, ≤15 files/dir
[plan-state] ok — the plan's state block matches the filesystem
…
1103 passed, 2 skipped                  ← tests/unit
6 passed                                ← tests/property
375 passed, 19 skipped                  ← research/phase0
✅ check passed — code is well-formed. This does NOT mean the data is right.
```

> **Read all three test lines.** `tail` shows only the last, which is the **research** suite, not
> the unit suite. Quoting "375 passed" as the project's test count is wrong by a factor of three.

### `just verify` — before every PR

Everything in `check`, plus real runs against real repositories. **~4½ minutes.**

```
$ just verify
50 passed, 1 deselected in 268.22s            ← tests/live, no mocks
[no-source-leak] ok — no stored value appears in any source file
[pack-vs-git] self-test ok — a one-second move is detected
[pack-vs-git] ok — 261 path(s) recomputed from git; 100 short by a deletion
               commit, each one verified to BE a deletion rather than assumed
[determinism] ok — 3 runs, 4,282 rows, one digest 4ae0422b7a18564f
[determinism] exclusion proven live: mutating those columns did not move the digest
✅ verify passed
```

**`[determinism]` is the artefact behind the product's strongest claim.** Three runs of the same
commit produce one digest, and the wall-clock columns excluded from it are **sabotaged to prove the
exclusion is real** rather than asserted.

**It clones `.verify-clone` itself and needs no setup.**

---

## Gate 2b — the ranker's strongest check

**Separate from `just verify` because it needs ~1.3 GB of pinned corpora.**

```bash
just fixtures    # once — clones the six repositories at pinned commits
just gate-2b     # re-proves the shipped ranker reproduces the research ranker
```

`tests/fixtures/pinned.json` holds the commits. **A repository used to measure something may not be
reused** — `scripts/guard/records/check_burned_corpora.py` tracks which are spent.

---

## The narrower recipes

Each is a step of `check` or `verify`, runnable alone while iterating.

| Recipe | What it runs |
|---|---|
| `just lint` | `ruff format --check` and `ruff check`, for `src/` and `research/phase0/` |
| `just types` | `mypy --strict src/ scripts/` |
| `just guards` | every script in `scripts/guard/` |
| `just test-unit` | `pytest tests/unit -x --timeout=60` |
| `just test-property` | `pytest tests/property -x --timeout=120` |
| `just test-phase0` | the research suite, on Python 3.10 |
| `just test-live` | `pytest tests/live` — **the full pipeline against real repositories. No mocks, by guard rule** |
| `just verify-data` | the live data verification |
| `just verify-determinism` | indexing the same history twice must produce the same pack |
| `just verify-no-source-leak` | no stored value appears in any source file |
| `just verify-pack-vs-git` | every pack row recomputed from git per path |
| `just check-branch` | branch naming. **Runs in CI, not on every local check** |
| `just install` | `uv sync --all-extras` |
| `just index PATH="."` | build a touch index for a clone |
| `just view` | **BROKEN — it invokes `quantamind view`, which is not a subcommand.** `argparse` answers *"invalid choice: 'view'"*. Recorded rather than deleted: the recipe exists, so `check_documented_recipes.py` passes it, and **no guard reads a recipe's body** <!-- documented-command:unbuilt --> |
| `just clean` | delete regenerable caches and corpora, **printing the bytes freed** |
| `just default` | `just --list` — every recipe with its one-line description |
| `just serve` | `quantamind serve --host 127.0.0.1 --port 7331`, the loopback default |

## Deployment

| Recipe | What it does |
|---|---|
| `just deploy` | `gcloud run deploy quantamind-reviewer --source .`, then **curls `/health`** |
| `just storage-setup` | **one-time.** Creates the bucket, grants the service's identity object access, mounts it at `/data`, sets `QUANTAMIND_DATABASE_PATH`, caps at one instance |
| `just storage-check` | read-only: what is actually mounted, where the store root points, how many writers there can be |

**The health check is part of the deploy, not a separate habit.** A revision that serves 100% of
traffic and answers nothing looks identical to a good one in the deploy output.

**`storage-setup` caps the service at one instance, and that is a correctness setting.** Cloud
Storage FUSE provides **no file locking** — Google's own wording is that "the last write wins and
all previous writes are lost" — and Cloud Run mounts NFS in no-lock mode. SQLite is safe on either
only when nothing else is writing. → `docs/plans/ops-store-persistence.md`

## The research recipes

Used only when running a measurement. They read `research/phase0/`, which is a **separate uv
project on a different interpreter** — nothing in `src/` may import its dependencies.

| Recipe | What it does |
|---|---|
| `just pilot REPOS="10"` | the pilot run |
| `just findings-draw HARVEST SEED` | draw a blind sample. **SEED is required so a draw is reproducible and cannot be quietly redrawn** |
| `just findings-score` | score the drawn sheet; a TRUE/FALSE verdict must cite a deciding line |
| `just findings-agree FIRST` | inter-rater agreement. **The first rater's sheet lives outside the working tree so a second rater cannot read it by accident** |
| `just label-draw ARM SEED` | draw a labelling arm |
| `just label-score` | score it. **Refuses an incomplete sheet** |

---

# The editor command

## `/qm-review`

**Not a `quantamind` subcommand** — a slash command at `.claude/commands/qm-review.md`, which runs
`quantamind review . --repo local/working-tree --json` over your working tree and hands the JSON to
the agent in your editor.

**It carries the refusal the comment renderer carries.** Its instructions say: *"Lead with what was
not read… The ranker decides where to look — it does not look. If you skip this step the command
has told the developer nothing they could not get from `git status`."*

**It must not run with `--deep`**, and it says why: that flag turns on model findings that are
66.7–82.1% wrong.

**If `quantamind` is not installed it says so and stops** — it does not fall back to reviewing the
diff itself and presenting that as this tool's output.
