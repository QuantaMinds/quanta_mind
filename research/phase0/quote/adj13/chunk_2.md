# Adjudication — grade every finding against the rubric

Each finding is a claim an AI reviewer made about a MERGED pull request from a real
open-source project. You are given the quoted line, the diff around it, the claim, and
the fix the reviewer proposed.

**Buckets: CORRECT / WRONG / UNFALSIFIABLE / TRIVIAL.** Definitions in
`research/phase0/vertex/rater2/RUBRIC.md` — use them unchanged.

When a finding is WRONG, add one of these causes as the last word of your sentence:
`EXTERNAL` (deciding it needs a fact the diff cannot supply), `ABSENT` (the code it
describes is not there), `TRACE` (the supporting code IS shown and the reviewer did not
follow it), `OTHER`.

A claim that does not describe the quoted code is WRONG. These pull requests are MERGED,
so a claim that a passing test's assertion is wrong is false.

Output one line per finding: `<index> <BUCKET> <one sentence giving the deciding fact>`

---

## 91

`scikit-build/scikit-build-core#1527` — `.github/workflows/ci.yml:89`

```diff
+      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
         with:
           python-version: "3.13"
-      - uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
+      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
       - name: Install nox
         run: uv tool install nox
       - uses: pre-commit/action@2c7b3805fd2a0fd8c1884dcaebf91fc102a13ecd # v3.0.1
@@ -189,17 +189,17 @@ jobs:
```

**CLAIM:** The specified commit hash for the `astral-sh/setup-uv` action does not exist in the public repository, which will cause the workflow to fail.

**PROPOSED FIX:** `      - uses: astral-sh/setup-uv@v0.2`

## 92

`scikit-build/scikit-build-core#1535` — `tests/test_program_search.py:159`

```diff
+    monkeypatch.setattr("scikit_build_core.program_search.sys.platform", "linux")
+    compute_timeout.cache_clear()
+    try:
+        assert BASE_TIMEOUT == 5
+        assert compute_timeout(Path("cmake")) == 5
+    finally:
+        compute_timeout.cache_clear()
+
+
```

**CLAIM:** The code will raise an unhandled `IndexError` if `self.base_dir.glob("index-*")` finds no files, which can happen if the CMake configuration fails.

**PROPOSED FIX:** `assert compute_timeout(Path("cmake")) == BASE_TIMEOUT`

## 93

`scikit-build/scikit-build-core#1527` — `.github/workflows/ci.yml:89`

```diff
+      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
         with:
           python-version: "3.13"
-      - uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0
+      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
       - name: Install nox
         run: uv tool install nox
       - uses: pre-commit/action@2c7b3805fd2a0fd8c1884dcaebf91fc102a13ecd # v3.0.1
@@ -189,17 +189,17 @@ jobs:
```

**CLAIM:** The astral-sh/setup-uv@v9 action introduces a breaking change by no longer adding the 'uv' binary to the system PATH, which will cause subsequent 'uv tool install' commands to fail.

**PROPOSED FIX:** `      - uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0`

## 94

`jazzband/pip-tools#2447` — `.pre-commit-config.yaml:8`

```diff
       - id: black
         args: [--target-version=py39]
   - repo: https://github.com/PyCQA/isort
-    rev: 9.0.0b1
+    rev: 9.0.0b2
     hooks:
       - id: isort
   - repo: https://github.com/asottile/pyupgrade
@@ -15,7 +15,7 @@ repos:
```

**CLAIM:** The `isort` dependency is only partially updated, as another `isort` configuration in the same file is left unchanged at the old version `9.0.0b1`.

**PROPOSED FIX:** `rev: 9.0.0b1`

## 95

`pyca/cryptography#15456` — `.github/workflows/ci.yml:417`

```diff
           - DOWNSTREAM: scapy
             REPO: secdev/scapy
-            # Latest commit on the scapy master branch, as of Aug 14, 2026.
-            REF: faf9f10632a2f8397c9ae9a720c71e134cd2e0b2
+            # Latest commit on the scapy master branch, as of Aug 15, 2026.
+            REF: b36473a545164d7c2c3e622b28bdf93b7179fee4
             PATH: scapy
           - DOWNSTREAM: sigstore-python
             REPO: sigstore/sigstore-python
```

**CLAIM:** The comment refers to a date in the future (2026), which is a logical error as it's meant to document when the commit was pinned.

**PROPOSED FIX:** `            # Latest commit on the scapy master branch, as of Aug 15, 2024.`

## 96

`scikit-build/scikit-build-core#1535` — `tests/test_program_search.py:159`

```diff
+    monkeypatch.setattr("scikit_build_core.program_search.sys.platform", "linux")
+    compute_timeout.cache_clear()
+    try:
+        assert BASE_TIMEOUT == 5
+        assert compute_timeout(Path("cmake")) == 5
+    finally:
+        compute_timeout.cache_clear()
+
+
```

**CLAIM:** The test assertion hardcodes the expected timeout value, making the test brittle if the `BASE_TIMEOUT` constant changes.

**PROPOSED FIX:** `assert compute_timeout(Path("cmake")) == BASE_TIMEOUT`
