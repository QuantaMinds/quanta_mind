"""The versioned SQLite schema, and the version gate that refuses to open a database it would break.

WHAT: `SCHEMA_VERSION`, the DDL for every table, `create()` to apply it, and `open_store()` which
      opens an existing database only when its version matches.
WHY:  **The outcome history is the asset.** Everything else here records what we did; `outcome`
      records whether it was right, and it accumulates over months of a customer's traffic. There
      is no delete-and-reindex path in production, so the schema is append-only and versioned, and
      opening a database written by a different version raises instead of guessing.

      **Three columns exist from the first row because append-only cannot backfill them:**

      - `shadow_pick` stores a RANKED LIST with scores and percentiles, never a top pick. The
        allocator funds ranks 1-3 and top-3 recall is what decides whether allocation loses
        defects — **top-3 for a candidate ranker cannot be computed from a top-1 record**, and the
        firing threshold cannot be re-derived without the percentile.
      - `request` stores token counts per call, including `cache_read_tokens`. **Cost is derived
        from them and never stored as cents**: prices change and token counts do not, cents cannot
        separate a cache read from fresh input, and they round away shallow calls costing fractions
        of a cent.
      - `outcome` carries `rule_version` and `fix_subject`, the inputs to re-derive it. The
        attribution rule has already been corrected once — file overlap to symbol overlap, which
        changed 67.9% of verdicts — and without a version stamp nobody can tell which rule labelled
        which row.

      **`ranked_unit` holds EVERY changed unit, including cold ones.** Cold rows are the coverage
      line's content and shadow evaluation's denominator; storing only the funded subset silently
      removes both.

      **No table stores source code.** `finding.body` quotes at most a few lines; `unit_path` and
      `unit_name` are identifiers. A telemetry table that accumulates customer source is a breach
      waiting for a date.
IMPORTS: types (nothing else; `store` sits second in the layer order).
CONSUMED BY: store.touches and every other store module; nothing outside `store/` opens a database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from quantamind.store import drift

# Bump on ANY change to the DDL below, and write a migration. There is no in-place edit.
SCHEMA_VERSION = 5

# `finding` and `claim` exist because adding a table later is a migration, and the schema is
# append-only. NOTHING WRITES TO THEM: `infer/` is closed on evidence and publishes no findings.
TABLES: tuple[str, ...] = (
    """CREATE TABLE IF NOT EXISTS repo (
        id INTEGER PRIMARY KEY, host TEXT NOT NULL, name TEXT NOT NULL,
        clone_filter TEXT NOT NULL DEFAULT '', first_seen INTEGER NOT NULL,
        languages_parsed TEXT NOT NULL DEFAULT '', UNIQUE (host, name))""",
    """CREATE TABLE IF NOT EXISTS review (
        id INTEGER PRIMARY KEY, repo_id INTEGER NOT NULL REFERENCES repo(id),
        pr_number INTEGER NOT NULL, head_sha TEXT NOT NULL, created_at INTEGER NOT NULL,
        fire_decision INTEGER NOT NULL, coverage_pct REAL, request_count INTEGER NOT NULL
        DEFAULT 0, tokens_in INTEGER NOT NULL DEFAULT 0, tokens_out INTEGER NOT NULL DEFAULT 0,
        latency_ms INTEGER, tier TEXT NOT NULL DEFAULT 'free',
        UNIQUE (repo_id, pr_number, head_sha))""",
    # Every changed unit, funded or not. `allocation` is deep | shallow | cold.
    """CREATE TABLE IF NOT EXISTS ranked_unit (
        review_id INTEGER NOT NULL REFERENCES review(id), unit_path TEXT NOT NULL,
        unit_name TEXT, rank INTEGER NOT NULL, score REAL NOT NULL, percentile REAL,
        allocation TEXT NOT NULL, PRIMARY KEY (review_id, unit_path, rank))""",
    # Every declared rule against every changed file, including the ones we could not decide.
    # **ALL FOUR OUTCOMES ARE STORED, OR THE DENOMINATOR IS A GUESS.** A trail holding only
    # violations cannot answer "was this rule enforced", only "did it fire", and a compliance rate
    # computed from it would be over whatever population the reader assumed.
    # `provenance` is what makes the trail worth reading: a parser's verdict can be re-run on the
    # same commit and shown to agree, and a model's cannot.
    """CREATE TABLE IF NOT EXISTS rule_check (
        review_id INTEGER NOT NULL REFERENCES review(id), rule_id TEXT NOT NULL,
        path TEXT NOT NULL, line INTEGER NOT NULL DEFAULT 0, outcome TEXT NOT NULL,
        evidence TEXT NOT NULL DEFAULT '', reason TEXT, provenance TEXT NOT NULL,
        PRIMARY KEY (review_id, rule_id, path))""",
    # What happened to the change AFTER we spoke. Separate from `review` because `review` records
    # a decision we made at one instant and this records facts that arrive later and change --
    # and because adding columns to an existing table by ALTER produces DDL text that differs from
    # a freshly created one in ways `drift` reports and nobody would predict.
    """CREATE TABLE IF NOT EXISTS lifecycle (
        review_id INTEGER PRIMARY KEY REFERENCES review(id), posted_at INTEGER,
        merge_state TEXT NOT NULL DEFAULT 'unknown', merged_at INTEGER,
        observed_at INTEGER NOT NULL)""",
    # One row per observation, never one row per review: "still running" is a statement about an
    # instant, and overwriting it would destroy the only evidence of what it said before it broke.
    """CREATE TABLE IF NOT EXISTS prod_signal (
        id INTEGER PRIMARY KEY, review_id INTEGER NOT NULL REFERENCES review(id),
        observed_at INTEGER NOT NULL, state TEXT NOT NULL, source TEXT NOT NULL,
        detail TEXT NOT NULL DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS finding (
        id INTEGER PRIMARY KEY, review_id INTEGER NOT NULL REFERENCES review(id),
        unit_path TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL,
        published INTEGER NOT NULL DEFAULT 0, confidence TEXT NOT NULL,
        provenance TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS claim (
        id INTEGER PRIMARY KEY, finding_id INTEGER NOT NULL REFERENCES finding(id),
        claim_kind TEXT NOT NULL, verdict TEXT NOT NULL, reason TEXT NOT NULL)""",
    # Typed silence. "No edge here" and "we failed here" are different rows, never the same absence.
    """CREATE TABLE IF NOT EXISTS unresolved (
        review_id INTEGER NOT NULL REFERENCES review(id), site TEXT NOT NULL,
        reason TEXT NOT NULL, construct TEXT NOT NULL)""",
    # The table the product exists to fill. `source` is git | datadog | manual.
    """CREATE TABLE IF NOT EXISTS outcome (
        review_id INTEGER NOT NULL REFERENCES review(id), unit_path TEXT NOT NULL,
        fix_sha TEXT NOT NULL, fix_at INTEGER NOT NULL, fix_subject TEXT NOT NULL,
        source TEXT NOT NULL, matched_rank INTEGER, rule_version INTEGER NOT NULL,
        PRIMARY KEY (review_id, unit_path, fix_sha))""",
    """CREATE TABLE IF NOT EXISTS reaction (
        review_id INTEGER NOT NULL REFERENCES review(id), finding_id INTEGER REFERENCES finding(id),
        kind TEXT NOT NULL, actor_hash TEXT NOT NULL, at INTEGER NOT NULL)""",
    # Ranks 1..k for k >= 3, with score and percentile. A top-1 row halves shadow evaluation.
    """CREATE TABLE IF NOT EXISTS shadow_pick (
        review_id INTEGER NOT NULL REFERENCES review(id), ranker_name TEXT NOT NULL,
        unit_path TEXT NOT NULL, rank INTEGER NOT NULL, score REAL NOT NULL, percentile REAL,
        PRIMARY KEY (review_id, ranker_name, rank))""",
    # Token counts, never cents. Cost is derived at read time from these.
    """CREATE TABLE IF NOT EXISTS request (
        id INTEGER PRIMARY KEY, review_id INTEGER NOT NULL REFERENCES review(id),
        ordinal INTEGER NOT NULL, model TEXT NOT NULL, model_version TEXT NOT NULL,
        effort TEXT, tokens_in INTEGER NOT NULL, tokens_out INTEGER NOT NULL,
        cache_read_tokens INTEGER NOT NULL DEFAULT 0,
        cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
        latency_ms INTEGER, stop_reason TEXT, UNIQUE (review_id, ordinal))""",
    # Webhook deliveries we have seen, keyed by GitHub's X-GitHub-Delivery GUID.
    # `completed_at` NULL means we started and did not finish: GitHub redelivers on failure and
    # REUSES the same GUID, so an unfinished attempt must be retryable while a finished one must
    # not be replayable.
    """CREATE TABLE IF NOT EXISTS delivery (
        delivery_id TEXT PRIMARY KEY, event TEXT NOT NULL, started_at INTEGER NOT NULL,
        completed_at INTEGER)""",
    # The touch index the ranker counts over. Written by store.touches from ingest.history.
    """CREATE TABLE IF NOT EXISTS touch (
        repo_id INTEGER NOT NULL REFERENCES repo(id), path TEXT NOT NULL,
        committed_at INTEGER NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS touch_lookup ON touch (repo_id, path, committed_at)",
    # How far the touch index was built, so the next review can extend it instead of re-reading
    # 338,907 touches. **`head_sha` IS A COMMIT, NOT A TIMESTAMP**: git history is not
    # chronologically ordered, so a rebase or cherry-pick lands commits whose committer date is
    # OLDER than rows already indexed, and a time watermark would skip them and read low forever.
    # `languages` is here because a suffix added to the product leaves every existing index
    # incomplete for it, and an incremental read would never backfill it -- the one staleness with
    # no natural symptom.
    """CREATE TABLE IF NOT EXISTS touch_watermark (
        repo_id INTEGER PRIMARY KEY REFERENCES repo(id), head_sha TEXT NOT NULL,
        languages TEXT NOT NULL, indexed_at INTEGER NOT NULL)""",
)


class SchemaVersionMismatch(RuntimeError):
    """The database on disk was written by a different schema version.

    Raised rather than migrated silently. A store opened under the wrong assumptions produces
    rankings that are wrong in ways no test downstream can see.
    """

    def __init__(self, path: Path, found: int, expected: int) -> None:
        self.path, self.found, self.expected = path, found, expected
        super().__init__(
            f"{path}: schema version {found}, this build expects {expected}. "
            "Write a migration; there is no delete-and-reindex path."
        )


def create(conn: sqlite3.Connection) -> None:
    """Apply the schema to a connection and stamp its version. Safe to call on an applied store."""
    conn.execute("PRAGMA foreign_keys = ON")
    for ddl in TABLES:
        conn.execute(ddl)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def version(conn: sqlite3.Connection) -> int:
    """The schema version stamped on this database. Zero means never initialised."""
    row = conn.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row else 0


def open_store(path: Path) -> sqlite3.Connection:
    """Open or create the store at `path`, refusing a database this build would corrupt.

    A fresh file is created and stamped. An existing file whose version differs raises
    `SchemaVersionMismatch` — it is never migrated in place and never opened anyway.
    """
    fresh = not path.exists()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    if fresh or version(conn) == 0:
        create(conn)
        return conn
    found = version(conn)
    if found != SCHEMA_VERSION:
        conn.close()
        raise SchemaVersionMismatch(path, found, SCHEMA_VERSION)
    # The version matching is not evidence the tables match: it is a number a human maintains.
    differences = drift.differences(conn)
    if differences:
        conn.close()
        raise drift.SchemaDrift(path, differences)
    return conn
