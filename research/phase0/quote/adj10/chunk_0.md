# Adjudication — grade every finding against the rubric

Each finding is a claim an AI reviewer made about a MERGED pull request from a real
open-source project. You are given the quoted line, the diff around it, the claim, and
the fix the reviewer proposed.

**Buckets: CORRECT / WRONG / UNFALSIFIABLE / TRIVIAL.** Definitions in
`research/phase0/vertex/rater2/RUBRIC.md` — use them unchanged.

A claim that does not describe the quoted code is WRONG. These pull requests are MERGED,
so a claim that a passing test's assertion is wrong is false.

Output one line per finding: `<index> <BUCKET> <one sentence giving the deciding fact>`

---

## 1

`aio-libs/aiohttp#13468` — `aiohttp/web_protocol.py:827`

```diff
             if self._message_tail:
-                messages, _upgraded, tail = self._parser.feed_data(self._message_tail)
+                messages, upgraded, tail = self._parser.feed_data(self._message_tail)
+                # A further upgrade request in the tail buffers its own remainder.
+                self._upgraded = upgraded
                 self._message_tail = tail
                 for msg, payload in messages:
                     self._request_count += 1
diff --git a/tests/test_web_websocket_functional.py b/tests/test_web_websocket_functional.py
```

**CLAIM:** This line prematurely updates the protocol's upgrade status, which can lead to a connection hang if processing the newly parsed messages fails, as the protocol state becomes inconsistent with the parser state.

**PROPOSED FIX:** `upgraded_after_loop = upgraded`

## 2

`python-attrs/attrs#1597` — `tox.ini:117`

```diff
 skip_install = true
-deps = prek
-commands = prek run --all-files
+commands =
+    uv run -m ruff check --fix --exit-non-zero-on-fix .
+    uv run -m ruff format --exit-non-zero-on-format .
+
+[testenv:lint-interrogate]
+runner = uv-venv-runner
```

**CLAIM:** The command `uv run -m ...` is invalid because `uv run` does not support the `-m` flag, and the `ruff` package is not installed in the tox environment due to missing `deps`.

**PROPOSED FIX:** `    ruff check --fix --exit-non-zero-on-fix .`

## 3

`python-attrs/attrs#1601` — `.github/workflows/codspeed.yml:33`

```diff
 jobs:
   codspeed:
     name: Run CodSpeed benchmarks
-    runs-on: codspeed-macro
+    runs-on: ubuntu-latest
 
     steps:
       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
@@ -49,7 +49,7 @@ jobs:
```

**CLAIM:** The main CodSpeed benchmark job is incorrectly configured to run on a standard `ubuntu-latest` runner instead of the specialized `codspeed-macro` runner, which will produce unreliable performance measurements and defeats the purpose of the tool.

**PROPOSED FIX:** `runs-on: codspeed-macro`

## 4

`aio-libs/aiohttp#13461` — `.github/workflows/ci-cd.yml:471`

```diff
     timeout-minutes: 15
     steps:
     - name: Checkout project
-      uses: actions/checkout@v6  # despite sdist, codspeed needs Git
+      uses: actions/checkout@v7  # despite sdist, codspeed needs Git
     - name: Retrieve the sdist and unpack it into the workspace
       uses: re-actors/checkout-python-sdist@release/v3
       with:
@@ -526,7 +526,7 @@ jobs:
```

**CLAIM:** The specified action version `v7` for `actions/checkout` is not a valid release, which will cause the workflow to fail.

**PROPOSED FIX:** `uses: actions/checkout@v4  # despite sdist, codspeed needs Git`

## 5

`psycopg/psycopg#1329` — `.github/workflows/build-and-cache-libpq.yml:53`

```diff
   # https://github.com/microsoft/vcpkg/discussions/25622
 
   # Latest release: https://www.openssl.org/source/
-  OPENSSL_VERSION: "3.5.6"
+  OPENSSL_VERSION: "3.5.7"
 
   # A string to differentiate build cacke keys to allow building different
   # flavours of libpq in different branches without mixups. Currently used to
diff --git a/.github/workflows/packages-bin.yml b/.github/workflows/packages-bin.yml
```

**CLAIM:** The specified OpenSSL version "3.5.7" does not exist, which will likely cause the build to fail when attempting to download it.

**PROPOSED FIX:** `OPENSSL_VERSION: "3.0.14"`

## 6

`tiangolo/sqlmodel#2069` — `.github/workflows/pre-commit.yml:78`

```diff
         run: |
-          git config user.name "github-actions[bot]"
-          git config user.email "github-actions[bot]@users.noreply.github.com"
+          git config user.name "pr-push[bot]"
+          git config user.email "pr-push[bot]@users.noreply.github.com"
           git remote set-url origin "https://x-access-token:${PR_PUSH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
           git add -A
           if git diff --staged --quiet; then

```

**CLAIM:** The git author email for a bot user is missing the required numeric ID prefix, which will prevent the resulting commit from being correctly attributed on GitHub.

**PROPOSED FIX:** `git config user.email "41898282+github-actions[bot]@users.noreply.github.com"`

## 7

`psycopg/psycopg#1369` — `tests/fix_faker.py:340`

```diff
         dtmin = dt.datetime.min + dt.timedelta(days=1)
-        delta = dt.datetime.max - dtmin
-        micros = randrange((delta.days + 1) * 24 * 60 * 60 * 1_000_000)
+        delta = dt.datetime.max - dt.timedelta(days=1) - dtmin
+        micros = randrange(int(delta.total_seconds() * 1_000_000))
         rv = dtmin + dt.timedelta(microseconds=micros)
         if spec[1]:
             rv = rv.replace(tzinfo=self._make_tz(spec))

```

**CLAIM:** This calculation is incorrect because `total_seconds()` loses precision on large intervals and the resulting range for `randrange` is off-by-one, excluding the upper bound.

**PROPOSED FIX:** `micros = randrange((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds + 1)`

## 8

`python-attrs/attrs#1597` — `tox.ini:128`

```diff
+
+[testenv:lint-pre-commit]
+runner = uv-venv-runner
+skip_install = true
+commands = uv run -m prek run --all-files
 
 
 [testenv:changelog]
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** The command `uv run -m ...` is invalid because `uv run` does not support the `-m` flag, and the `prek` package is not installed in the tox environment due to missing `deps`.

**PROPOSED FIX:** `commands = prek run --all-files`

## 9

`python-attrs/attrs#1600` — `src/attr/__init__.py:120`

```diff
 __getattr__ = _make_getattr(__name__)
+
+
+def __dir__() -> list[str]:
+    return sorted(set(globals()) | set(__all__))
diff --git a/src/attr/_compat.py b/src/attr/_compat.py
index bc68ed9ea..37e714857 100644
--- a/src/attr/_compat.py
+++ b/src/attr/_compat.py
```

**CLAIM:** The `__dir__` function fails to include the lazily-loaded submodules, breaking attribute discovery for "converters" and "validators".

**PROPOSED FIX:** `    return sorted(set(globals()) | set(__all__) | _LAZY_SUBMODULES)`

## 10

`psycopg/psycopg#1321` — `tests/constraints.txt:13`

```diff
 
 # From the 'test' extra
 anyio == 4.0
-mypy == 1.19.0
+mypy == 2.1.0
 pproxy == 2.7.0
 pytest == 6.2.5
 pytest-cov == 3.0.0

```

**CLAIM:** The specified version `2.1.0` for the `mypy` package does not exist, which will cause dependency installation to fail.

**PROPOSED FIX:** `mypy == 1.10.0`

## 11

`python-attrs/attrs#1608` — `.github/workflows/build-docset.yml:35`

```diff
       - uses: hynek/setup-cached-uv@34e35d30f1ebc7421a5cc733bca38dcc62603960 # v2.6.0
 
-      - run: uvx --with=tox-uv tox run -e docset
+      - run: >
+          uv run --only-group tox
+          tox run -e docset
 
       - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
         with:
```

**CLAIM:** The `uv run` command requires a command to execute, but none is provided, and it does not affect the environment of subsequent shell commands.

**PROPOSED FIX:** `uv run --only-group tox -- tox run -e docset`

## 12

`aio-libs/aiohttp#13460` — `.pre-commit-config.yaml:63`

```diff
       - flake8-no-implicit-concat==0.3.4
       - flake8-requirements==1.7.8
 - repo: https://github.com/PyCQA/isort
-  rev: '9.0.0b2'
+  rev: '9.0.0b5'
   hooks:
   - id: isort
 - repo: https://github.com/psf/black-pre-commit-mirror

```

**CLAIM:** The specified revision '9.0.0b5' is not a valid tag or reference in the isort repository, which will cause the pre-commit hook to fail upon installation.

**PROPOSED FIX:** `rev: '5.13.2'`

## 13

`pallets/quart#433` — `.github/workflows/publish.yaml:23`

```diff
   create-release:
-    # Upload the sdist, wheels, and provenance to a GitHub release. They remain
-    # available as build artifacts for a while as well.
-    needs: [provenance]
+    needs: [build]
     runs-on: ubuntu-latest
     permissions:
       contents: write
     steps:
```

**CLAIM:** The publish-pypi job should depend on a `provenance` job to ensure SLSA attestations are generated before publishing, but the `provenance` job was removed, which is a security regression.

**PROPOSED FIX:** `needs: [provenance]`

## 14

`pallets/quart#472` — `.github/workflows/tests.yaml:16`

```diff
@@ -13,6 +13,7 @@ jobs:
       fail-fast: false
       matrix:
         include:
+          - {python: '3.14t'}
           - {python: '3.14'}
           - {name: Windows, python: '3.14', os: windows-latest}
           - {name: Mac, python: '3.14', os: macos-latest}

```

**CLAIM:** The version string '3.14t' is invalid for specifying a free-threaded Python build with the setup-python action; it should be '3.14-t'.

**PROPOSED FIX:** `          - {python: '3.14-t'}`

## 15

`psycopg/psycopg#1326` — `psycopg/psycopg/_py_transformer.py:276`

```diff
+        if self._none_oid < 0:
+            try:
+                self._none_oid = self._adapters.get_dumper(NoneType, PY_TEXT).oid
+            except KeyError:
+                raise e.InterfaceError("None dumper not found")
+        return self._none_oid
 
     def get_dumper_by_oid(self, oid: int, format: pq.Format) -> abc.Dumper:
         """
```

**CLAIM:** The raised exception has the wrong type and a generic message, which is inconsistent with the new test that expects a `ProgrammingError` with a message containing "NoneType".

**PROPOSED FIX:** `                raise e.ProgrammingError("dumper for NoneType not found")`

## 16

`psycopg/psycopg#1365` — `psycopg/psycopg/_copy_base.py:354`

```diff
 def _parse_row_text(data: Buffer, tx: Transformer) -> tuple[Any, ...]:
     if not isinstance(data, bytes):
         data = bytes(data)
+    if not data.endswith(b"\n"):
+        raise e.DataError("bad copy data: field delimiter not found")
     fields = data.split(b"\t")
     fields[-1] = fields[-1][:-1]  # drop \n
     row = [None if f == b"\\N" else _load_re.sub(_load_sub, f) for f in fields]

```

**CLAIM:** This takes the first result, which is a change from the original logic of taking the last result and is inconsistent with the change in the `_deallocate` function.

**PROPOSED FIX:** `raise e.DataError("bad copy data: unterminated row: missing newline")`

## 17

`psycopg/psycopg#1321` — `tests/constraints.txt:13`

```diff
 
 # From the 'test' extra
 anyio == 4.0
-mypy == 1.19.0
+mypy == 2.1.0
 pproxy == 2.7.0
 pytest == 6.2.5
 pytest-cov == 3.0.0

```

**CLAIM:** The `uv run` command requires a command to execute, but none is provided, and it does not affect the environment of subsequent shell commands.

**PROPOSED FIX:** `mypy == 1.10.0`

## 18

`pallets/quart#432` — `src/quart/sessions.py:157`

```diff
 
         if fallbacks := app.config["SECRET_KEY_FALLBACKS"]:
             keys.extend(fallbacks)
 
+        keys.append(app.secret_key)  # itsdangerous expects current key at top
         options = {
             "key_derivation": self.key_derivation,
             "digest_method": self.digest_method,

```

**CLAIM:** The current secret key is appended to the end of the keys list, but it must be at the beginning to be used as the primary key for signing.

**PROPOSED FIX:** `keys.insert(0, app.secret_key)  # itsdangerous expects current key at top`

## 19

`pallets/quart#433` — `.readthedocs.yaml:8`

```diff
-  fail_on_warning: false
+    python: '3.13'
+  commands:
+    - asdf plugin add uv
+    - asdf install uv latest
+    - asdf global uv latest
+    # TODO fix warnings and add -W
+    - uv run --group docs sphinx-build -b dirhtml docs $READTHEDOCS_OUTPUT/html
diff --git a/pyproject.toml b/pyproject.toml
```

**CLAIM:** Installing the `latest` version of `uv` can lead to non-reproducible documentation builds and unexpected failures if a new version introduces breaking changes.

**PROPOSED FIX:** `asdf install uv 0.2.1`

## 20

`tiangolo/sqlmodel#2069` — `.github/workflows/pre-commit.yml:77`

```diff
           PR_PUSH_TOKEN: ${{ steps.pr-push.outputs.token }}
         run: |
-          git config user.name "github-actions[bot]"
-          git config user.email "github-actions[bot]@users.noreply.github.com"
+          git config user.name "pr-push[bot]"
+          git config user.email "pr-push[bot]@users.noreply.github.com"
           git remote set-url origin "https://x-access-token:${PR_PUSH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
           git add -A
           if git diff --staged --quiet; then
```

**CLAIM:** This git author name is paired with an invalid bot email address, which will prevent the resulting commit from being correctly attributed to a user on GitHub.

**PROPOSED FIX:** `git config user.name "github-actions[bot]"`

## 21

`aio-libs/aiohttp#13465` — `.github/workflows/ci-cd.yml:235`

```diff
+            --jq '.[] | select(.status=="added") | .filename' \
+          | grep '^CHANGES/' || true
+        )
+        failed=0
+        for f in $added; do
+          num=$(basename "$f" | cut -d. -f1)
+          [[ "$num" =~ ^[0-9]+$ ]] || continue
+          if [[ "$num" == "$PR_NUMBER" ]]; then continue; fi
+          if grep -qE "(^|[^0-9])#${num}([^0-9]|$)" <<<"$PR_BODY"; then continue; fi
```

**CLAIM:** The unquoted variable in the `for` loop is subject to word splitting by spaces, which will cause the script to fail if a filename contains a space.

**PROPOSED FIX:** `while IFS= read -r f; do`

## 22

`aio-libs/aiohttp#13461` — `.github/workflows/ci-cd.yml:62`

```diff
     timeout-minutes: 5
     steps:
     - name: Checkout
-      uses: actions/checkout@v6
+      uses: actions/checkout@v7
       with:
         submodules: true
     - name: Cache llhttp generated files
@@ -468,7 +468,7 @@ jobs:
```

**CLAIM:** The specified action version `v7` for `actions/checkout` is not a valid release, which will cause the workflow to fail.

**PROPOSED FIX:** `uses: actions/checkout@v4`

## 23

`pallets/quart#452` — `src/quart/testing/connections.py:148`

```diff
             ):
                 raise data
 
-    async def receive(self) -> AnyStr:
+    async def receive(self) -> str | bytes:
         data = await self._receive_queue.get()
         if isinstance(data, Exception):
             raise data
         else:
```

**CLAIM:** The function implementation returns a raw ASGI event dictionary, but the return type is declared as `str | bytes`, which is a contract violation.

**PROPOSED FIX:** `async def receive(self) -> dict:`

## 24

`python-attrs/attrs#1597` — `tox.ini:123`

```diff
+
+[testenv:lint-interrogate]
+runner = uv-venv-runner
+skip_install = true
+commands = uv run -m interrogate tests
+
+[testenv:lint-pre-commit]
+runner = uv-venv-runner
+skip_install = true
```

**CLAIM:** The command `uv run -m ...` is invalid because `uv run` does not support the `-m` flag, and the `interrogate` package is not installed in the tox environment due to missing `deps`.

**PROPOSED FIX:** `commands = interrogate tests`

## 25

`psycopg/psycopg#1374` — `psycopg/psycopg/types/multirange.py:358`

```diff
+                pos += 4
+                out.append(load_range_binary(data[pos : pos + length], self._load))
+                pos += length
+        except Exception as ex:
+            raise e.DataError(f"invalid multirange data: {type(ex).__name__} - {ex}")
 
         if pos != len(data):
             raise e.DataError("unexpected trailing data in multirange")

```

**CLAIM:** The new `DataError` should be raised from the original exception to preserve the original traceback for easier debugging.

**PROPOSED FIX:** `raise e.DataError(f"invalid multirange data: {type(ex).__name__} - {ex}") from ex`

## 26

`psycopg/psycopg#1344` — `psycopg/psycopg/_connection_base.py:481`

```diff
             self.pgconn.send_query_params(command, None, result_format=result_format)
 
-        result: PGresult = (yield from generators.execute(self.pgconn))[-1]
+        results: list[PGresult] = (yield from generators.execute(self.pgconn))
+        if len(results) != 1:
+            raise e.InternalError(
+                f"received {len(results)} results from command {command.decode()!r}"
+            )
+
```

**CLAIM:** The specified revision '9.0.0b5' is not a valid tag or reference in the isort repository, which will cause the pre-commit hook to fail upon installation.

**PROPOSED FIX:** `if not results:`

## 27

`aio-libs/aiohttp#13464` — `.github/workflows/ci-cd.yml:235`

```diff
+            --jq '.[] | select(.status=="added") | .filename' \
+          | grep '^CHANGES/' || true
+        )
+        failed=0
+        for f in $added; do
+          num=$(basename "$f" | cut -d. -f1)
+          [[ "$num" =~ ^[0-9]+$ ]] || continue
+          if [[ "$num" == "$PR_NUMBER" ]]; then continue; fi
+          if grep -qE "(^|[^0-9])#${num}([^0-9]|$)" <<<"$PR_BODY"; then continue; fi
```

**CLAIM:** The unquoted variable `$added` is subject to word-splitting, which will cause the script to fail on filenames containing spaces.

**PROPOSED FIX:** `IFS=$'\n'; for f in $added; do`

## 28

`psycopg/psycopg#1365` — `psycopg/psycopg/_copy_base.py:354`

```diff
 def _parse_row_text(data: Buffer, tx: Transformer) -> tuple[Any, ...]:
     if not isinstance(data, bytes):
         data = bytes(data)
+    if not data.endswith(b"\n"):
+        raise e.DataError("bad copy data: field delimiter not found")
     fields = data.split(b"\t")
     fields[-1] = fields[-1][:-1]  # drop \n
     row = [None if f == b"\\N" else _load_re.sub(_load_sub, f) for f in fields]

```

**CLAIM:** The error message is incorrect because the code checks for a missing newline row terminator, not a missing field delimiter.

**PROPOSED FIX:** `raise e.DataError("bad copy data: unterminated row: missing newline")`

## 29

`psycopg/psycopg#1369` — `tests/fix_faker.py:340`

```diff
         dtmin = dt.datetime.min + dt.timedelta(days=1)
-        delta = dt.datetime.max - dtmin
-        micros = randrange((delta.days + 1) * 24 * 60 * 60 * 1_000_000)
+        delta = dt.datetime.max - dt.timedelta(days=1) - dtmin
+        micros = randrange(int(delta.total_seconds() * 1_000_000))
         rv = dtmin + dt.timedelta(microseconds=micros)
         if spec[1]:
             rv = rv.replace(tzinfo=self._make_tz(spec))

```

**CLAIM:** The publish-pypi job should depend on a `provenance` job to ensure SLSA attestations are generated before publishing, but the `provenance` job was removed, which is a security regression.

**PROPOSED FIX:** `micros = randrange((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds + 1)`

## 30

`pallets/quart#433` — `.github/workflows/publish.yaml:23`

```diff
   create-release:
-    # Upload the sdist, wheels, and provenance to a GitHub release. They remain
-    # available as build artifacts for a while as well.
-    needs: [provenance]
+    needs: [build]
     runs-on: ubuntu-latest
     permissions:
       contents: write
     steps:
```

**CLAIM:** The command `uv run -m ...` is invalid because `uv run` does not support the `-m` flag, and the `interrogate` package is not installed in the tox environment due to missing `deps`.

**PROPOSED FIX:** `needs: [provenance]`

## 31

`psycopg/psycopg#1329` — `.github/workflows/build-and-cache-libpq.yml:53`

```diff
   # https://github.com/microsoft/vcpkg/discussions/25622
 
   # Latest release: https://www.openssl.org/source/
-  OPENSSL_VERSION: "3.5.6"
+  OPENSSL_VERSION: "3.5.7"
 
   # A string to differentiate build cacke keys to allow building different
   # flavours of libpq in different branches without mixups. Currently used to
diff --git a/.github/workflows/packages-bin.yml b/.github/workflows/packages-bin.yml
```

**CLAIM:** The specified OpenSSL version "3.5.7" does not exist, which will likely cause the build to fail when attempting to download it.

**PROPOSED FIX:** `OPENSSL_VERSION: "3.0.14"`

## 32

`pallets/quart#433` — `.github/workflows/publish.yaml:23`

```diff
   create-release:
-    # Upload the sdist, wheels, and provenance to a GitHub release. They remain
-    # available as build artifacts for a while as well.
-    needs: [provenance]
+    needs: [build]
     runs-on: ubuntu-latest
     permissions:
       contents: write
     steps:
```

**CLAIM:** The create-release job should depend on a `provenance` job to ensure SLSA attestations are included in the release, but the `provenance` job was removed, which is a security regression.

**PROPOSED FIX:** `needs: [provenance]`

## 33

`python-attrs/attrs#1600` — `src/attr/__init__.py:120`

```diff
 __getattr__ = _make_getattr(__name__)
+
+
+def __dir__() -> list[str]:
+    return sorted(set(globals()) | set(__all__))
diff --git a/src/attr/_compat.py b/src/attr/_compat.py
index bc68ed9ea..37e714857 100644
--- a/src/attr/_compat.py
+++ b/src/attr/_compat.py
```

**CLAIM:** The `__dir__` function fails to include the lazily-loaded submodules, breaking attribute discovery for "converters" and "validators".

**PROPOSED FIX:** `    return sorted(set(globals()) | set(__all__) | {"converters", "validators"})`

## 34

`psycopg/psycopg#1369` — `tests/fix_faker.py:340`

```diff
         dtmin = dt.datetime.min + dt.timedelta(days=1)
-        delta = dt.datetime.max - dtmin
-        micros = randrange((delta.days + 1) * 24 * 60 * 60 * 1_000_000)
+        delta = dt.datetime.max - dt.timedelta(days=1) - dtmin
+        micros = randrange(int(delta.total_seconds() * 1_000_000))
         rv = dtmin + dt.timedelta(microseconds=micros)
         if spec[1]:
             rv = rv.replace(tzinfo=self._make_tz(spec))

```

**CLAIM:** The command `uv run -m ...` is invalid because `uv run` does not support the `-m` flag, and the `interrogate` package is not installed in the tox environment due to missing `deps`.

**PROPOSED FIX:** `micros = randrange((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds + 1)`

## 35

`psycopg/psycopg#1344` — `psycopg/psycopg/_connection_base.py:486`

```diff
+            raise e.InternalError(
+                f"received {len(results)} results from command {command.decode()!r}"
+            )
+
+        result = results[0]
         if result.status != COMMAND_OK and result.status != TUPLES_OK:
             if result.status == FATAL_ERROR:
                 raise e.error_from_result(result, encoding=self.pgconn._encoding)
@@ -514,7 +520,10 @@ def _deallocate(self, name: bytes | None) -> PQGen[None]:
```

**CLAIM:** This takes the first result, which is a change from the original logic of taking the last result and is inconsistent with the change in the `_deallocate` function.

**PROPOSED FIX:** `result = results[-1]`

## 36

`psycopg/psycopg#1344` — `psycopg/psycopg/_connection_base.py:486`

```diff
+            raise e.InternalError(
+                f"received {len(results)} results from command {command.decode()!r}"
+            )
+
+        result = results[0]
         if result.status != COMMAND_OK and result.status != TUPLES_OK:
             if result.status == FATAL_ERROR:
                 raise e.error_from_result(result, encoding=self.pgconn._encoding)
@@ -514,7 +520,10 @@ def _deallocate(self, name: bytes | None) -> PQGen[None]:
```

**CLAIM:** The specified OpenSSL version "3.5.7" does not exist, which will likely cause the build to fail when attempting to download it.

**PROPOSED FIX:** `result = results[-1]`

## 37

`python-attrs/attrs#1597` — `.github/workflows/ci.yml:198`

```diff
+
+      - run: >
+          uvx --with=tox-uv
+          --python $(cat .python-version-default)
+          tox run -e lint
+
   typing:
     name: Check types using supported type checkers
     runs-on: ubuntu-latest
```

**CLAIM:** The `lint` tox environment is not defined in `tox.ini`, which will cause this step to fail.

**PROPOSED FIX:** `          tox run -e lint-ruff,lint-interrogate,lint-pre-commit`

## 38

`psycopg/psycopg#1326` — `psycopg/psycopg/_py_transformer.py:276`

```diff
+        if self._none_oid < 0:
+            try:
+                self._none_oid = self._adapters.get_dumper(NoneType, PY_TEXT).oid
+            except KeyError:
+                raise e.InterfaceError("None dumper not found")
+        return self._none_oid
 
     def get_dumper_by_oid(self, oid: int, format: pq.Format) -> abc.Dumper:
         """
```

**CLAIM:** This check incorrectly rejects cases where multiple results are returned, which the original code handled by taking the last result and is inconsistent with the parallel change in the `_deallocate` function.

**PROPOSED FIX:** `                raise e.ProgrammingError("dumper for NoneType not found")`

## 39

`pallets/quart#436` — `docs/_static/quart-icon.svg:8`

```diff
+    <rect id="Icon" x="0" y="0" width="500" height="500" style="fill:none;"/>
+    <clipPath id="_clip1">
+        <rect x="0" y="0" width="500" height="500"/>
+    </clipPath>
+    <g clip-path="url(#_clip1)">
+        <path d="M415.574,136.117l-50.302,58.634c53.079,70.053 52.154,169.732 -7.407,238.859c-68.509,79.928 -188.864,88.877 -268.484,20.368c-79.928,-68.51 -88.878,-188.557 -20.368,-268.485c54.623,-63.88 142.266,-82.397 216.022,-52.462l54.006,-62.955c1.543,-1.852 4.629,-2.16 6.789,-0.617l69.435,59.56c1.852,2.469 2.161,5.246 0.309,7.098Zm-37.032,181.458c-27.157,-93.506 -122.207,-14.504 -187.013,-54.931c-64.498,-40.427 -33.638,-108.628 -33.638,-108.628c-27.157,9.875 -51.228,26.231 -70.053,48.142c-59.252,69.127 -51.228,173.743 17.899,232.995c69.127,59.252 173.435,51.537 232.995,-17.899c24.997,-29.009 49.685,-65.732 39.81,-99.679Z" style="fill:#2952e1;"/>
+        <path d="M422.363,121.613l-71.287,-61.104c-5.863,-4.937 -6.172,-13.578 -1.543,-19.442c4.938,-5.863 13.579,-6.172 19.442,-1.543l71.287,61.104c5.864,4.937 6.172,13.578 1.543,19.442c-4.937,5.863 -13.578,6.48 -19.442,1.543Z" style="fill:#2952e1;fill-rule:nonzero;"/>
+        <path d="M446.126,88.283l-62.647,-53.388c-3.394,-2.777 -3.703,-8.023 -0.925,-11.418l17.59,-20.676c2.777,-3.395 8.024,-3.704 11.418,-0.926l62.647,53.388c3.394,2.777 3.703,8.024 0.925,11.418l-17.59,20.677c-3.086,3.394 -8.024,4.012 -11.418,0.925Z" style="fill:#2952e1;fill-rule:nonzero;"/>
+    </g>
```

**CLAIM:** The `clip-path` applied to this group is redundant because it clips to the `viewBox` dimensions, which is the default behavior for SVG.

**PROPOSED FIX:** `    <g>`

## 40

`psycopg/psycopg#1344` — `psycopg/psycopg/_connection_base.py:481`

```diff
             self.pgconn.send_query_params(command, None, result_format=result_format)
 
-        result: PGresult = (yield from generators.execute(self.pgconn))[-1]
+        results: list[PGresult] = (yield from generators.execute(self.pgconn))
+        if len(results) != 1:
+            raise e.InternalError(
+                f"received {len(results)} results from command {command.decode()!r}"
+            )
+
```

**CLAIM:** This check incorrectly rejects cases where multiple results are returned, which the original code handled by taking the last result and is inconsistent with the parallel change in the `_deallocate` function.

**PROPOSED FIX:** `if not results:`
