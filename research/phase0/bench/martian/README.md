# Martian's offline benchmark, copied into the repository on purpose

**This was read from `/private/tmp/claude-501/.../6063c1dc-.../scratchpad/` — a scratchpad
belonging to a session that ended.** `research/phase0/bench/corpus.py` hardcoded that path.

**A `/private/tmp` path does not fail loudly when it disappears. The file is simply gone**, and
whatever depended on it reports a smaller denominator or a clean skip. This project has already
lost measurements to a truncated read, a blob-filtered clone, a wall-clock column and a
gitignored directory that regenerated itself — every one of them the same shape.

**Only the four artefacts we actually read are kept** — the golden comments, and the
candidates and evaluations under the Claude-Opus judge. Their source tree, tests and
lockfile were copied first and removed: 54 MB of a third party's code inside this
repository is scanned by our own guards, which flagged their commit messages.

`CHECKSUM` holds a SHA-256 over every `.json` under `data/`, and `corpus.py` asserts
it before reading. **That converts "the file might vanish or change" into "the run refuses."**

Regenerate deliberately, never to make a failing assertion pass:

    cd research/phase0/bench/martian && \
      find data -type f -name "*.json" | sort | \
      xargs shasum -a 256 | shasum -a 256 | awk '{print $1}' > CHECKSUM
