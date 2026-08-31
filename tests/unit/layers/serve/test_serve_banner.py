"""The startup banner must reach a PIPE, while the process is still running.

WHAT: Launches the real `quantamind serve` as a subprocess with its stdout on a pipe, reads the
      banner before sending any request, and requires every line `docs/engineering/CLI.md` quotes
      to arrive. Then kills the process with SIGTERM and requires the lines to have arrived
      already.
WHY:  **THIS IS A REGRESSION TEST FOR A BUG THAT EVERY IN-PROCESS TEST MISSES.** The banner was
      written with a plain `print()`. Python line-buffers stdout to a terminal and BLOCK-buffers it
      to a pipe -- and a pipe is every real deployment: systemd, Docker, CI, a redirect to a log
      file. `serve_forever()` never returns, the buffer never fills, and SIGTERM ends the process
      without flushing. The banner was not late. **It was lost**, and the endpoint sat there
      listening and silent.

      The line that cost is the one that mattered most: the posting state is the only thing
      telling an operator that a delivery is authenticated, acknowledged and then dropped. It was
      invisible to precisely the person who needed it.

      **A `capsys` test would pass against the broken code**, because pytest's capture replaces
      stdout with an object that has no pipe behind it. So this pays for a subprocess: the buffering
      mode is a property of the REAL file descriptor, and nothing that stubs it can see the fault.
IMPORTS: nothing from the product -- it runs the installed entry point. stdlib subprocess, os.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from quantamind.types.settings import load

# Generous: the banner is printed before serve_forever(), so a healthy start answers in
# milliseconds. Long enough that a loaded CI box is not the reason this fails.
BANNER_DEADLINE_SECONDS = 30.0
ROOT = Path(__file__).resolve().parents[4]
ENTRY_POINT = Path(sys.executable).parent / "quantamind"
# Quoted verbatim in docs/engineering/CLI.md under "Healthy startup". A line changed here without
# changing the document leaves the reference describing output the command does not produce.
REQUIRED = (
    "[serve] POST /webhook",
    "[serve] GET  /health",
    "[serve] GET  /         — the dashboard",
    "[serve] GET  /r/<owner>/<name>",
    "[serve] It REVIEWS: clone, rank, render. Posting is",
    "[serve] http.server is not a hardened edge",
)
"""**THE READ WINDOW BELOW IS SIZED FROM THIS TUPLE**, so a banner line added without a line here
is not merely unpinned -- it pushes the lines after it past the end of the window and fails this
test. That is how the browser routes were caught: they were announced and not required."""


@pytest.mark.skipif(not ENTRY_POINT.exists(), reason="the console script is not installed")
def test_the_banner_arrives_through_a_pipe_before_anything_is_sent(tmp_path: Path) -> None:
    environment = dict(
        os.environ,
        QUANTAMIND_WEBHOOK_SECRET="banner-test-secret",
        QUANTAMIND_DATABASE_PATH=str(tmp_path / "store.db"),
    )
    # port 0: the OS picks a free one, so a developer already serving on 7331 does not fail this.
    running = subprocess.Popen(
        [str(ENTRY_POINT), "serve", "--port", "0"],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert running.stdout is not None
    seen: list[str] = []

    def drain() -> None:
        assert running.stdout is not None
        for _ in range(len(REQUIRED) + 1):
            line = running.stdout.readline()
            if not line:
                return
            seen.append(line.rstrip("\n"))

    # **THE READ IS BOUNDED, AND THAT IS THE POINT.** Against the unflushed code `readline()` blocks
    # FOREVER: nothing has been requested of the endpoint, so nothing else will ever be written and
    # `serve_forever()` never returns to flush. A bare loop here does not fail, it HANGS -- which in
    # CI burns the job's whole timeout and reads as "stuck" rather than "broken". Verified by
    # sabotage: removing the flushes hung this test until the deadline was added.
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    reader.join(timeout=BANNER_DEADLINE_SECONDS)
    blocked = reader.is_alive()
    running.kill()  # SIGKILL, which cannot flush anything still sitting in a buffer
    running.wait(timeout=30)
    reader.join(timeout=10)

    assert not blocked or seen, (
        f"nothing arrived on the pipe in {BANNER_DEADLINE_SECONDS}s. The endpoint binds and then "
        f"says nothing: stdout is block-buffered to a pipe and serve_forever() never flushes it."
    )

    printed = "\n".join(seen)
    assert "[serve] listening on 127.0.0.1:" in printed, (  # default bind is loopback
        f"the endpoint bound but announced nothing through a pipe. Buffered output is LOST when "
        f"serve_forever() never returns. Read: {printed!r}"
    )
    missing = [line for line in REQUIRED if line not in printed]
    assert not missing, (
        f"the banner is missing {missing}. These lines are quoted in docs/engineering/CLI.md, and "
        f"the posting line is the only warning an operator gets. Read: {printed!r}"
    )
    # **AND IT MUST BE TRUE, NOT MERELY PRESENT.** The banner announced "IT DOES NOT REVIEW" long
    # after `deliver()` was wired, and this test passed throughout -- because it asked whether the
    # line existed and never whether it described the process. Asserting against the SETTING is
    # what makes the banner unable to drift from the behaviour again.
    assert ("Posting is OFF" in printed) is not load().posting_enabled, (
        f"the banner's posting state disagrees with settings.posting_enabled. A startup line that "
        f"misreports what the endpoint will do to a customer's pull requests is worse than none. "
        f"Read: {printed!r}"
    )
