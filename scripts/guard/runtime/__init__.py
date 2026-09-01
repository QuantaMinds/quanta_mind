"""Guards about what the code DOES at run time, not how it is shaped.

WHAT: no partial clones, timeouts on every subprocess, constant-time comparison of secrets, and
      no outbound call without asking the deployment shape's permission.
WHY:  **`scripts/guard/` REACHED ITS 15-FILE CAP AND THIS IS THE HONEST SEAM.** The rest of that
      directory checks structure, convention, docs and records — properties of the source. These
      four check behaviour a reader cannot see by looking: a clone that silently truncates history,
      a subprocess that hangs forever, a token compared byte-by-byte, a socket opened in an
      air-gapped deployment. Every one of them was added after the behaviour bit somebody.
IMPORTS: nothing itself.
CONSUMED BY: justfile (`just check`), .github/workflows/guards.yml.
"""
