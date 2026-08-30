"""The serialised form is not covered by any check, so notice the moment it changes.

WHAT: Hashes the DDL in `store/tables.py` and compares it to the value recorded here. On a
      difference it fails, naming what the change requires: a SCHEMA_VERSION bump, a migration,
      and the byte-level golden that does not exist yet.
WHY:  **`just verify` SAYS IN ITS OWN BANNER WHAT IT CANNOT SEE.** It recomputes every pack row
      from git per path, which is a strong check on the VALUES and blind to the FORM -- column
      order, row ordering, path encoding. A byte-level golden would catch those and a
      recomputation looks straight past them.

      **THE GOLDEN IS NOT BUILT, AND THAT IS DELIBERATE.** Today the schema is fixed, so a golden
      would have nothing to catch, and **an unexercised snapshot is the one most likely to be
      regenerated without anyone reading the diff** -- which is worse than its absence, because it
      reads as coverage. So what is built is the TRIGGER rather than the artefact: the guard fires
      the first time the form actually moves, which is the moment the golden starts having a job.

      **A NOTE IN A DOCUMENT WOULD NOT HAVE SURVIVED.** The maintainer note in `AGENTS.md` says a
      rule that can be a check must be one, because a rule living only in prose is a wish. This is
      the check.
IMPORTS: scripts/guard/discovery.py; stdlib hashlib, re. No project imports.
CONSUMED BY: `just guards`; CI.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coverage import refuse_path_argument
from discovery import Violation, project_root, report

SCHEMA = "src/quantamind/store/tables.py"
VERSIONED = "src/quantamind/store/schema.py"

# The digest of the DDL as it stands. **Change this ONLY together with a SCHEMA_VERSION bump, a
# migration, and the golden described above** -- never to make the build green again.
#
# Updated on 2026-08-24, when version 3 added `lifecycle` and `prod_signal`. That change is what
# the guard was built for and it worked: it fired, named the three things required, and the golden
# it demanded caught a two-column swap that ten value-level schema tests passed straight through.
# -> tests/unit/layers/store/test_schema_golden.py
#
# Updated again on 2026-08-27 for version 4, `touch_watermark`. The guard fired in the same order
# and each thing it named was done before this line moved: SCHEMA_VERSION bumped, `_to_4` written,
# golden regenerated AND ITS DIFF READ -- one new table, no existing column order disturbed.
#
# Updated again on 2026-08-28 for version 5, `rule_check`, the audit trail. Same order, same
# evidence: SCHEMA_VERSION bumped, `_to_5` written in `store/migrations.py`, `STEPS` extended so
# `test_schema_golden.py` migrates a version-2 store through (3, 4, 5) and requires the result to
# equal a fresh one byte for byte, golden regenerated and its diff read -- one new table, no
# existing column order disturbed.
#
# **ADD A PARAGRAPH HERE, NEVER EDIT ONE.** The version-4 note above was briefly rewritten in
# place to describe version 5, which left a comment naming `_to_5` under a heading that said
# version 4 and destroyed the only record of what the version-4 bump did. The digest line moves
# once per bump; the reasons it moved are the thing worth keeping.
RECORDED_DIGEST = "352af1a6571350d0"
RECORDED_VERSION = 7


def ddl_of(text: str) -> str:
    """Every CREATE statement in the module, normalised for whitespace only.

    Whitespace is normalised because reformatting is not a schema change; anything else -- a column
    added, reordered, retyped, renamed -- moves the digest, which is the point.
    """
    statements = re.findall(r'"""(CREATE [^"]+)"""', text)
    return "\n".join(" ".join(s.split()) for s in statements)


def version_of(text: str) -> int:
    found = re.search(r"^SCHEMA_VERSION\s*=\s*(\d+)", text, re.M)
    return int(found.group(1)) if found else -1


def main() -> int:
    root = project_root()
    path = root / SCHEMA
    if not path.is_file():
        # **A MISSING SUBJECT IS A NAMED REFUSAL, NOT A TRACEBACK.** Pointed at any tree without
        # this file — a foreign repository, a partial checkout — `read_text` raised
        # `FileNotFoundError` and printed a stack trace, so a reader could not tell a missing
        # file from a crash in the guard. Found by running the suite against `pallets/flask`.
        print(f"[schema-shape] no schema at {path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    ddl = ddl_of(text)
    digest = hashlib.sha256(ddl.encode()).hexdigest()[:16]
    # **THE DDL AND THE VERSION LIVE IN DIFFERENT FILES SINCE THE SPLIT**, so the version is
    # read from where the version is. Reading it from the DDL file would find nothing and report
    # version 0, which reads as "no schema" rather than as "looked in the wrong place".
    versioned = root / VERSIONED
    version = version_of(versioned.read_text(encoding="utf-8")) if versioned.is_file() else 0

    if not ddl:
        print(f"[schema-shape] FAILED to find any CREATE statement in {SCHEMA}", file=sys.stderr)
        return 1

    if not RECORDED_DIGEST:
        print(
            f"[schema-shape] no digest recorded yet — set RECORDED_DIGEST = {digest!r} in "
            f"{Path(__file__).name}",
            file=sys.stderr,
        )
        return 1

    violations: list[Violation] = []
    if digest != RECORDED_DIGEST:
        violations.append(
            Violation(
                path,
                1,
                "schema-shape",
                f"the DDL changed (digest {RECORDED_DIGEST} -> {digest}). This is the moment the "
                f"serialised form starts needing a check `just verify` cannot give it: its "
                f"recomputation reads VALUES and is blind to column order, row ordering and path "
                f"encoding. Required now: bump SCHEMA_VERSION (currently {version}), write the "
                f"migration, ADD THE BYTE-LEVEL GOLDEN, and only then update RECORDED_DIGEST.",
            )
        )
    elif version != RECORDED_VERSION:
        violations.append(
            Violation(
                path,
                1,
                "schema-shape",
                f"SCHEMA_VERSION moved to {version} but the DDL is unchanged. A version bump with "
                f"no shape change means a migration exists for a schema that did not move — say "
                f"which is wrong.",
            )
        )

    print(f"[schema-shape] DDL digest {digest}, SCHEMA_VERSION {version}", flush=True)
    return report(violations, root, "schema-shape")


if __name__ == "__main__":
    # Refused HERE, not inside main(): inside, `sys.argv` belongs to whoever
    # imported this module -- under pytest that is pytest's own command line.
    sys.exit(refuse_path_argument(sys.argv, "schema-shape") or main())
