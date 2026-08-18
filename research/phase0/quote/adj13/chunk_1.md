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

## 46

`scikit-build/scikit-build-core#1521` — `src/scikit_build_core/file_api/reply.py:76`

```diff
+            with self.base_dir.joinpath(data["jsonFile"]).open(encoding="utf-8") as f:
+                file_data: InputDict = json.load(f)
+            # Keep members only present on the reference, like directoryIndex
+            # and projectIndex on codemodel target entries
+            data = {**file_data, **data}
 
         input_dict: Dict[str, Type[Any]] = {}
         exceptions: List[Exception] = []
diff --git a/tests/test_fileapi.py b/tests/test_fileapi.py
```

**CLAIM:** The dictionary merge incorrectly gives precedence to fields from the reference object (`data`) over those from the JSON file (`file_data`), but the file's content should be authoritative in case of conflicts.

**PROPOSED FIX:** `data = {**data, **file_data}`

## 47

`jazzband/pip-tools#2444` — `tests/conftest.py:124`

```diff
-    @property
+    @functools.cached_property
     def session(self) -> PipSession:
-        """Not used"""
+        return mock.Mock()
 
-    @property
+    @functools.cached_property
     def finder(self) -> PackageFinder:
```

**CLAIM:** The property is type-hinted to return a `PipSession`, but returning a generic `mock.Mock()` instance creates a type mismatch that will likely be flagged by a static type checker.

**PROPOSED FIX:** `return _t.cast(PipSession, mock.Mock())`

## 48

`jazzband/pip-tools#2446` — `tests/test_repository_pypi.py:411`

```diff
     assert actual_data is None
 
 
-def test_get_project__handles_404(from_line, tmpdir, monkeypatch, pypi_repository):
+def test_get_project__handles_404(from_line, monkeypatch, pypi_repository):
     """
     Test PyPIRepository._get_project() returns None if PyPI
     response's status code is 404.
@@ -429,7 +427,7 @@ def mock_get(*args, **kwargs):
```

**CLAIM:** The `tmpdir` fixture was removed from the function signature, but it was likely used by other fixtures or setup code within the test, and its removal could lead to failures.

**PROPOSED FIX:** `def test_get_project__handles_404(from_line, tmpdir, monkeypatch, pypi_repository):`

## 49

`scikit-build/scikit-build-core#1523` — `docs/conf.py:97`

```diff
@@ -94,6 +94,7 @@
     "sphinx_autodoc_typehints",
     "sphinx_copybutton",
     "sphinx_inline_tabs",
+    "sphinx_llm.txt",
     "sphinx_tippy",
     "sphinxcontrib.programoutput",
 ]
diff --git a/pyproject.toml b/pyproject.toml
```

**CLAIM:** The Sphinx extension name "sphinx_llm.txt" is invalid because it is not a valid Python module name, which will cause an ImportError during the documentation build.

**PROPOSED FIX:** `"sphinx_llm",`

## 50

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

**CLAIM:** The astral-sh/setup-uv@v9 action introduces a breaking change by no longer adding the 'uv' binary to the system PATH, which will cause the subsequent 'uv sync' command to fail.

**PROPOSED FIX:** `      - uses: astral-sh/setup-uv@fac544c07dec837d0ccb6301d7b5580bf5edae39 # v8.2.0`

## 51

`aws/aws-cli#10535` — `awscli/customizations/codeartifact/login.py:467`

```diff
         )
+
+        if not dry_run:
+            repo_uri = urlsplit(self.repository_endpoint)
+            auth_token_key = f'//{repo_uri.netloc}{repo_uri.path}:_authToken'
+            self._write_npmrc_value(
+                auth_token_key, self.auth_token, self.get_npmrc_path()
+            )
+
```

**CLAIM:** The repository path from the URL is used directly to build the configuration key, but if it lacks a trailing slash, `npm` may not find the token when it normalizes the registry URL by adding one.

**PROPOSED FIX:** `            path = repo_uri.path if repo_uri.path.endswith('/') else f'{repo_uri.path}/'
            auth_token_key = f'//{repo_uri.netloc}{path}:_authToken'`

## 52

`falconry/falcon#2697` — `.github/workflows/test-wheels.yaml:21`

```diff
       fail-fast: false
       matrix:
         platform:
-          - build: "cp314-manylinux_aarch64"
+          - build: "cp315-manylinux_aarch64"
             os: ubuntu-24.04-arm
           - build: "cp314-manylinux_s390x"
             os: ubuntu-latest
@@ -46,11 +46,11 @@ jobs:
```

**CLAIM:** This change incorrectly replaces the emulated wheel test for Python 3.14 on aarch64 instead of adding a new test for Python 3.15, thereby dropping test coverage for a supported Python version.

**PROPOSED FIX:** `          - build: "cp314-manylinux_aarch64"
            os: ubuntu-24.04-arm
          - build: "cp315-manylinux_aarch64"`

## 53

`pytest-dev/pluggy#698` — `.pre-commit-config.yaml:46`

```diff
         language: python
         additional_dependencies: [pygments, restructuredtext_lint]
 -   repo: https://github.com/pre-commit/mirrors-mypy
-    rev: v2.1.0
+    rev: v2.3.0
     hooks:
     -   id: mypy
         files: ^(src/|testing/)

```

**CLAIM:** The `rev` `v2.3.0` is invalid because this tag does not exist in the `pre-commit/mirrors-mypy` repository, which will cause pre-commit hook installation to fail.

**PROPOSED FIX:** `rev: v1.9.0`

## 54

`jazzband/pip-tools#2454` — `tests/test_utils.py:766`

```diff
+    piptools_config_file = make_config_file("verbose", True)
+
+    # the context already has a loaded default of False
+    ctx = Context(compile_cli)
+    ctx.default_map = {"verbose": False}
+
+    # when we load the config...
+    found_config_file = override_defaults_from_config_file(ctx, "config", None)
+    assert found_config_file == piptools_config_file
```

**CLAIM:** The test does not verify that existing keys in `default_map` are preserved when loading from a config file, so it would incorrectly pass if the implementation replaces the entire map instead of updating it.

**PROPOSED FIX:** `ctx.default_map = {"verbose": False, "dry-run": True}`

## 55

`scikit-build/scikit-build-core#1527` — `.github/workflows/cd.yml:23`

```diff
     name: Build distribution
     runs-on: ubuntu-latest
     steps:
-      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
+      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
         with:
           fetch-depth: 0
           persist-credentials: false
@@ -46,10 +46,10 @@ jobs:
```

**CLAIM:** The specified commit hash for the `actions/checkout` action does not exist in the public repository, which will cause the workflow to fail.

**PROPOSED FIX:** `      - uses: actions/checkout@v4`

## 56

`aws/aws-cli#10510` — `.github/workflows/sphinx-check.yml:13`

```diff
     runs-on: ubuntu-latest
     steps: 
     - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # version 7.0.0
-    - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # version 6.3.0
+    - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # version 7.0.0
       with:
         python-version: "3.12"
         cache: pip
diff --git a/.github/workflows/sphinx.yml b/.github/workflows/sphinx.yml
```

**CLAIM:** The commit hash `5fda3b95a4ea91299a34e894583c3862153e4b97` corresponds to `actions/setup-python@v5.0.0`, but the comment incorrectly states it is `version 7.0.0`, a version that does not exist.

**PROPOSED FIX:** `    - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v5.0.0`

## 57

`scikit-build/scikit-build-core#1528` — `src/scikit_build_core/file_api/reply.py:57`

```diff
         Load the newest index.json file and return the Index object.
         """
-        index_file = sorted(self.base_dir.glob("index-*"))[-1]
+        # max() would raise ValueError, not IndexError, when there is no index
+        index_file = sorted(self.base_dir.glob("index-*"))[-1]  # noqa: FURB192
         with index_file.open(encoding="utf-8") as f:
             data = json.load(f)
 
diff --git a/tests/test_cmake_config.py b/tests/test_cmake_config.py
```

**CLAIM:** The code will raise an `IndexError` if no index files are found, because it accesses the last element of a potentially empty list without checking if it is empty.

**PROPOSED FIX:** `try:
    index_file = sorted(self.base_dir.glob("index-*"))[-1]
except IndexError as e:
    raise FileNotFoundError("No index file found in reply directory") from e`

## 58

`scikit-build/scikit-build-core#1532` — `src/scikit_build_core/builder/builder.py:432`

```diff
                 cache_config[f"{prefix}_INCLUDE_DIR"] = python_include_dir
                 cache_config[f"{prefix}_FIND_REGISTRY"] = "NEVER"
+                # Interpreter-less FindPython rejects the free-threaded "t" ABI
+                # unless the 4-tuple (3.30+) FIND_ABI requests it.
+                if gil_disabled and self.config.cmake.version >= Version("3.30"):
+                    cache_config[f"{prefix}_FIND_ABI"] = "ANY;ANY;ANY;ON"
                 # On Windows the library is constructed and existence-checked,
                 # so this is reliable. On POSIX a library hint can break
                 # FindPython (which resolves it fine on its own), so this
```

**CLAIM:** This condition fails to detect free-threaded builds where `sysconfig.get_config_var("Py_GIL_DISABLED")` is 't', because the `gil_disabled` variable only checks for '1'.

**PROPOSED FIX:** `if sysconfig.get_config_var("Py_GIL_DISABLED") and self.config.cmake.version >= Version("3.30"):`

## 59

`falconry/falcon#2672` — `falcon/cyutil/uri.pyx:92`

```diff
-            if data[pos] == b'+' and unquote_plus:
-                result[dst_start] = b' '
-                dst_start += 1
-                src_start += 1
+            if data[pos] == b'+':
+                # NOTE(apoorva-01): A literal plus is only rewritten to a space
+                #   when unquote_plus is enabled; otherwise it is preserved
+                #   as-is and must not be mistaken for a percent sequence.
+                if unquote_plus:
```

**CLAIM:** The logic in this block causes an infinite loop when `unquote_plus` is false because it fails to copy the literal `+` character and advance the source pointer.

**PROPOSED FIX:** `            if data[pos] == b'+':
                if unquote_plus:
                    result[dst_start] = b' '
                else:
                    result[dst_start] = b'+'
                dst_s`

## 60

`aws/aws-cli#10511` — `.github/workflows/run-bundle-test.yml:27`

```diff
       with:
         persist-credentials: false
     - name: Set up Python ${{ matrix.python-version }}
-      uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
+      uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
       with:
         python-version: ${{ matrix.python-version }}
     - name: Install dependencies
diff --git a/.github/workflows/run-dep-tests.yml b/.github/workflows/run-dep-tests.yml
```

**CLAIM:** The version comment is incorrect, as this hash corresponds to v5.0.0 of `actions/setup-python`, not v7.0.0.

**PROPOSED FIX:** `      uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v5.0.0`

## 61

`jazzband/pip-tools#2446` — `tests/test_repository_pypi.py:372`

```diff
 
-def test_get_project__handles_http_error(
-    from_line, tmpdir, monkeypatch, pypi_repository
-):
+def test_get_project__handles_http_error(from_line, monkeypatch, pypi_repository):
     """
     Test PyPIRepository._get_project() returns None if HTTP error is raised.
     """
@@ -387,7 +385,7 @@ def mock_get(*args, **kwargs):
```

**CLAIM:** The `tmpdir` fixture was removed from the function signature, but it was likely used by other fixtures or setup code within the test, and its removal could lead to failures.

**PROPOSED FIX:** `def test_get_project__handles_http_error(from_line, tmpdir, monkeypatch, pypi_repository):`

## 62

`scikit-build/scikit-build-core#1535` — `tests/test_program_search.py:179`

```diff
+        "scikit_build_core.program_search._macos_binary_is_x86", lambda _path: False
+    )
+    compute_timeout.cache_clear()
+    try:
+        assert compute_timeout(Path("cmake")) == 10
+    finally:
+        compute_timeout.cache_clear()
+
+
```

**CLAIM:** The test assertion uses a hardcoded value, making it brittle to changes in the `BASE_TIMEOUT` constant.

**PROPOSED FIX:** `assert compute_timeout(Path("cmake")) == BASE_TIMEOUT * 2`

## 63

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

**CLAIM:** The specified revision '9.0.0b2' is not a valid git reference in the isort repository, which will cause the pre-commit hook to fail during installation.

**PROPOSED FIX:** `    rev: 5.13.2`

## 64

`pytest-dev/pluggy#717` — `.github/workflows/downstream.yml:50`

```diff
         with:
           python-version: "3.12"
           allow-prereleases: true
-      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
+      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
       - name: Run downstream recipe
         run: uv run downstream/run_downstream.py "${{ matrix.recipe }}"

```

**CLAIM:** The version comment `# v9.0.0` is incorrect, as the commit hash `c771a70e6277c0a99b617c7a806ffedaca235ff9` corresponds to version `v0.1.23` of the `astral-sh/setup-uv` action.

**PROPOSED FIX:** `      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v0.1.23`

## 65

`jazzband/pip-tools#2444` — `tests/conftest.py:124`

```diff
-    @property
+    @functools.cached_property
     def session(self) -> PipSession:
-        """Not used"""
+        return mock.Mock()
 
-    @property
+    @functools.cached_property
     def finder(self) -> PackageFinder:
```

**CLAIM:** The property is type-hinted to return an `InstallCommand`, but returning a generic `mock.Mock()` instance creates a type mismatch that will likely be flagged by a static type checker.

**PROPOSED FIX:** `return _t.cast(InstallCommand, mock.Mock())`

## 66

`pytest-dev/pluggy#698` — `.pre-commit-config.yaml:3`

```diff
@@ -1,6 +1,6 @@
 repos:
 - repo: https://github.com/astral-sh/ruff-pre-commit
-  rev: "v0.15.20"
+  rev: "v0.15.21"
   hooks:
     - id: ruff-check
       args: ["--fix"]
@@ -43,7 +43,7 @@ repos:
```

**CLAIM:** The `rev` `v0.15.21` is invalid because this tag does not exist in the `astral-sh/ruff-pre-commit` repository, which will cause pre-commit hook installation to fail.

**PROPOSED FIX:** `rev: "v0.4.4"`

## 67

`falconry/falcon#2672` — `falcon/cyutil/uri.pyx:96`

```diff
+            if data[pos] == b'+':
+                # NOTE(apoorva-01): A literal plus is only rewritten to a space
+                #   when unquote_plus is enabled; otherwise it is preserved
+                #   as-is and must not be mistaken for a percent sequence.
+                if unquote_plus:
+                    result[dst_start] = b' '
+                    dst_start += 1
+                    src_start += 1
                 continue
```

**CLAIM:** This conditional block is incomplete; when `unquote_plus` is false, it causes an infinite loop by failing to process the `+` character or advance the source pointer.

**PROPOSED FIX:** `                if unquote_plus:
                    result[dst_start] = b' '
                    dst_start += 1
                    src_start += 1
                else:
                    result[dst`

## 68

`scikit-build/scikit-build-core#1515` — `tests/test_program_search.py:113`

```diff
 
     best_none = best_program(programs, version=None)
     assert best_none
-    assert best_none.path.name == "cmake3"
+    assert best_none.path.name == "cmake"
 
     best_3_15 = best_program(programs, version=SpecifierSet(">=3.15"))
     assert best_3_15

```

**CLAIM:** The test incorrectly asserts that a program with an unknown version is selected as "best" over a program with a known version.

**PROPOSED FIX:** `    assert best_none.path.name == "cmake3"`

## 69

`aws/aws-cli#10519` — `awscli/telemetry.py:317`

```diff
 
+def is_telemetry_disabled(env=None):
+    if env is None:
+        env = os.environ
+    return ensure_boolean(env.get(_SESSION_ID_DISABLED_ENV_VAR, 'false'))
+
+
 def register_session_id_event(session, orchestrator_factory=None):
+    if is_telemetry_disabled():
```

**CLAIM:** The test assertion uses a hardcoded value, making it brittle to changes in the `BASE_TIMEOUT` constant.

**PROPOSED FIX:** `return env.get(_SESSION_ID_DISABLED_ENV_VAR, 'false').lower() == 'true'`

## 70

`jazzband/pip-tools#2444` — `tests/conftest.py:124`

```diff
-    @property
+    @functools.cached_property
     def session(self) -> PipSession:
-        """Not used"""
+        return mock.Mock()
 
-    @property
+    @functools.cached_property
     def finder(self) -> PackageFinder:
```

**CLAIM:** The property is type-hinted to return a `PackageFinder`, but returning a generic `mock.Mock()` instance creates a type mismatch that will likely be flagged by a static type checker.

**PROPOSED FIX:** `return _t.cast(PackageFinder, mock.Mock())`

## 71

`aws/aws-cli#10511` — `.github/workflows/run-bundle-test.yml:27`

```diff
       with:
         persist-credentials: false
     - name: Set up Python ${{ matrix.python-version }}
-      uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6
+      uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
       with:
         python-version: ${{ matrix.python-version }}
     - name: Install dependencies
diff --git a/.github/workflows/run-dep-tests.yml b/.github/workflows/run-dep-tests.yml
```

**CLAIM:** The `path_to_url` function expects a string path, but `tmp_path` is a `pathlib.Path` object, which needs to be converted to a string before being passed.

**PROPOSED FIX:** `      uses: actions/setup-python@v5`

## 72

`aws/aws-cli#10534` — `awscli/customizations/codeartifact/login.py:540`

```diff
+
+    def _create_npmrc_file(self, npmrc_path, new_entry):
+        dirname = os.path.split(npmrc_path)[0] or '.'
+        os.makedirs(dirname, exist_ok=True)
+        with os.fdopen(os.open(npmrc_path,
+                               os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
+            f.write(new_entry + '\n')
+
+    def _append_npmrc_entry(self, contents, new_entry):
```

**CLAIM:** Creating the file without the `O_EXCL` flag after an existence check constitutes a TOCTOU race condition, which can be exploited via a symlink attack to create or overwrite a file at an arbitrary location.

**PROPOSED FIX:** `        with os.fdopen(os.open(npmrc_path,
                               os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:`

## 73

`falconry/falcon#2672` — `falcon/cyutil/uri.pyx:96`

```diff
+            if data[pos] == b'+':
+                # NOTE(apoorva-01): A literal plus is only rewritten to a space
+                #   when unquote_plus is enabled; otherwise it is preserved
+                #   as-is and must not be mistaken for a percent sequence.
+                if unquote_plus:
+                    result[dst_start] = b' '
+                    dst_start += 1
+                    src_start += 1
                 continue
```

**CLAIM:** The Sphinx extension name is invalid because it includes a file extension `.txt`, which will cause an import error as it is not a valid Python module name.

**PROPOSED FIX:** `                if unquote_plus:
                    result[dst_start] = b' '
                    dst_start += 1
                    src_start += 1
                else:
                    result[dst`

## 74

`jazzband/pip-tools#2457` — `tests/unit/scripts/test_options.py:24`

```diff
+    result = runner.invoke(my_command, ["--help"])
+    assert result.exit_code == 0
+    assert result.stdout.startswith("Usage: my-command")
+    # --help option helptext should be last, whitespace aside
+    assert result.stdout.rstrip().endswith("Show this message and exit.")
+
+
+def test_help_opt_with_epilog(runner: CliRunner) -> None:
+    """
```

**CLAIM:** This assertion is fragile because it assumes the help text for the `--help` option is the last part of the output, which is not guaranteed if other options are present.

**PROPOSED FIX:** `assert "--help" in result.stdout and "Show this message and exit." in result.stdout`

## 75

`aws/aws-cli#10540` — `.github/workflows/stale_community_prs.yml:12`

```diff
     permissions:
       pull-requests: write
     steps:
-      - uses: actions/stale@1e223db275d687790206a7acac4d1a11bd6fe629
+      - uses: actions/stale@4391f3da665fdf50b6810c1a66712fb9ba21aa93
         with:
           debug-only: true
           repo-token: ${{ secrets.GITHUB_TOKEN }}
@@ -31,7 +31,7 @@ jobs:
```

**CLAIM:** This upgrade to `actions/stale` v11 is incomplete because it does not update the action's input parameters to use the new API, instead relying on deprecated parameters that will be removed in a future version.

**PROPOSED FIX:** `      - uses: actions/stale@1e223db275d687790206a7acac4d1a11bd6fe629`

## 76

`jazzband/pip-tools#2446` — `tests/test_repository_pypi.py:106`

```diff
     Test the `open_local_or_remote_file` raises a ValueError for a given `Link`
     to a directory.
     """
-    link = Link(path_to_url(tmpdir.strpath))
+    link = Link(path_to_url(str(tmp_path)))
     session = Session()
 
     with (
@@ -151,19 +151,19 @@ def test_relative_path_cache_dir_is_normalized(from_line):
```

**CLAIM:** The `path_to_url` function expects a string path, but `tmp_path` is a `pathlib.Path` object, which needs to be converted to a string before being passed.

**PROPOSED FIX:** `    link = Link(path_to_url(os.fspath(tmp_path)))`

## 77

`jazzband/pip-tools#2425` — `.github/ISSUE_TEMPLATE/bug-report.yaml:36`

```diff
+          1. ...
+          2. ...
+          3. ...
+    validations:
+      required: false
+
+  - type: textarea
+    id: environment
+    attributes:
```

**CLAIM:** The environment versions are critical for debugging as many issues are environment-specific, so this field should be mandatory.

**PROPOSED FIX:** `required: true`

## 78

`jazzband/pip-tools#2425` — `.github/ISSUE_TEMPLATE/bug-report.yaml:36`

```diff
+          1. ...
+          2. ...
+          3. ...
+    validations:
+      required: false
+
+  - type: textarea
+    id: environment
+    attributes:
```

**CLAIM:** The steps to reproduce a bug are essential for maintainers to investigate and fix it, so this field should be mandatory.

**PROPOSED FIX:** `required: true`

## 79

`aws/aws-cli#10535` — `awscli/customizations/codeartifact/login.py:553`

```diff
+    def _create_npmrc_file(self, npmrc_path, new_entry):
+        dirname = os.path.split(npmrc_path)[0] or '.'
+        os.makedirs(dirname, exist_ok=True)
+        with os.fdopen(
+            os.open(npmrc_path, os.O_WRONLY | os.O_CREAT, 0o600), 'w'
+        ) as f:
+            f.write(new_entry + '\n')
+
+    def _append_npmrc_entry(self, contents, new_entry):
```

**CLAIM:** This file creation is not atomic due to the lack of `O_EXCL`, and it is part of a time-of-check-to-time-of-use (TOCTOU) race condition that can lead to data loss through file truncation if run concurrently.

**PROPOSED FIX:** `os.open(npmrc_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w'`

## 80

`scikit-build/scikit-build-core#1521` — `src/scikit_build_core/file_api/_cattrs_converter.py:77`

```diff
         path = base_dir / Path(with_path["jsonFile"])
         raw = json.loads(path.read_text(encoding="utf-8"))
+        # Keep members only present on the reference, like directoryIndex and
+        # projectIndex on codemodel target entries
+        raw.update(with_path)
         return converter.structure_attrs_fromdict(raw, t)
 
     converter.register_structure_hook(CodeModel, from_json_file)
@@ -79,6 +82,7 @@ def from_json_file(with_path: Dict[str, Any], t: Type[T]) -> T:
```

**CLAIM:** The dictionary update incorrectly gives precedence to fields from the reference object (`with_path`) over those from the JSON file (`raw`), but the file's content should be authoritative in case of conflicts.

**PROPOSED FIX:** `raw = {**with_path, **raw}`

## 81

`jazzband/pip-tools#2429` — `piptools/repositories/pypi.py:537`

```diff
+    It is not possible to accommodate all users perfectly -- we can ensure proper
+    behavior for pypi.org and test.pypi.org , and try not to break anyone else in the
+    process.
+    """
+    if url.endswith("/simple/"):
+        return url.removesuffix("simple/")
+    elif url.endswith("/simple"):
+        return url.removesuffix("simple")
+
```

**CLAIM:** This condition is too broad because it incorrectly matches any URL where a path segment ends with "/simple/", such as ".../not-so-simple/", leading to a malformed URL.

**PROPOSED FIX:** `if url.endswith("/simple/") and url.split('/')[-2] == 'simple':`

## 82

`jazzband/pip-tools#2425` — `.github/ISSUE_TEMPLATE/bug-report.yaml:36`

```diff
+          1. ...
+          2. ...
+          3. ...
+    validations:
+      required: false
+
+  - type: textarea
+    id: environment
+    attributes:
```

**CLAIM:** The date in the comment is in the future, which is a data error as it incorrectly documents when the commit was chosen.

**PROPOSED FIX:** `required: true`

## 83

`aws/aws-cli#10548` — `requirements/download-deps/portable-exe-lock.txt:87`

```diff
     # via pyinstaller
-packaging==26.2 \
-    --hash=sha256:5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e \
-    --hash=sha256:ff452ff5a3e828ce110190feff1178bb1f2ea2281fa2075aadb987c2fb221661
+packaging==26.3 \
+    --hash=sha256:94edc256424af38762eb31306eed28beb9f0efc50a8837492c9d6fd6004aed79 \
+    --hash=sha256:d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c
     # via
     #   pyinstaller
```

**CLAIM:** The `packaging` dependency is updated to version 26.3 in `portable-exe-lock.txt` and `portable-exe-win-lock.txt`, but remains at an older version in other lock files, creating an inconsistency that could lead to environment-specific bugs.

**PROPOSED FIX:** `packaging==26.2 \
    --hash=sha256:5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e \
    --hash=sha256:ff452ff5a3e828ce110190feff1178bb1f2ea2281fa2075aadb987c2fb221661`

## 84

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

**CLAIM:** The test assertion uses a hardcoded value, making it brittle to changes in the `BASE_TIMEOUT` constant.

**PROPOSED FIX:** `assert compute_timeout(Path("cmake")) == BASE_TIMEOUT`

## 85

`pytest-dev/pluggy#692` — `.github/workflows/deploy.yml:19`

```diff
       id-token: write
       attestations: write
     steps:
-      - uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
+      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
         with:
           fetch-depth: 0
           persist-credentials: false
diff --git a/.github/workflows/downstream.yml b/.github/workflows/downstream.yml
```

**CLAIM:** This is a security vulnerability, as the commit hash `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` and version `v7.0.0` do not exist in the official `actions/checkout` repository and likely point to malicious code.

**PROPOSED FIX:** `      - uses: actions/checkout@v4`

## 86

`falconry/falcon#2682` — `tests/test_request_attrs.py:64`

```diff
 
+def test_root_path_non_ascii_wsgi():
+    env = testing.create_environ()
+
+    script_name = '/café'.encode().decode('iso-8859-1')
+    env['SCRIPT_NAME'] = script_name
+
+    req = Request(env)
+
```

**CLAIM:** The call to `.encode()` uses the system's default string encoding which is not guaranteed to be UTF-8, making the test brittle.

**PROPOSED FIX:** `script_name = '/café'.encode('utf-8').decode('iso-8859-1')`

## 87

`jazzband/pip-tools#2438` — `piptools/sync.py:40`

```diff
+# similarly, this set is lifted out of pip for a simpler future-facing compatibility
+# story
+_DEV_PKGS: set[str] = set()
+if sys.version_info < (3, 12):  # older python build backend inclusions
+    _DEV_PKGS |= {"setuptools", "distribute", "wheel"}
+
 PACKAGES_TO_IGNORE = [
     "-markerlib",
     "pip",
```

**CLAIM:** This logic for determining development packages is an incorrect simplification of pip's internal logic, as it wrongly includes "wheel" for Python versions older than 3.10.

**PROPOSED FIX:** `_DEV_PKGS |= {"setuptools", "distribute"} | ({"wheel"} if sys.version_info >= (3, 10) else set())`

## 88

`jazzband/pip-tools#2425` — `.github/ISSUE_TEMPLATE/bug-report.yaml:36`

```diff
+          1. ...
+          2. ...
+          3. ...
+    validations:
+      required: false
+
+  - type: textarea
+    id: environment
+    attributes:
```

**CLAIM:** The steps to reproduce a bug are essential for maintainers to investigate and fix it, so this field should be mandatory.

**PROPOSED FIX:** `required: true`

## 89

`falconry/falcon#2682` — `tests/test_request_attrs.py:64`

```diff
 
+def test_root_path_non_ascii_wsgi():
+    env = testing.create_environ()
+
+    script_name = '/café'.encode().decode('iso-8859-1')
+    env['SCRIPT_NAME'] = script_name
+
+    req = Request(env)
+
```

**CLAIM:** If the `.npmrc` file is empty, this line of code will prepend an unnecessary leading newline before the new entry.

**PROPOSED FIX:** `script_name = '/café'.encode('utf-8').decode('iso-8859-1')`

## 90

`jazzband/pip-tools#2446` — `tests/test_cli_compile.py:257`

```diff
+    proj_dir = tmp_path / "proj"
+    proj_dir.mkdir()
 
-    with open(str(proj_dir / "setup.py"), "w") as package:
+    with open(proj_dir / "setup.py", "w") as package:
         package.write(dedent("""\
                 from setuptools import setup
                 setup(install_requires=[])
@@ -266,14 +267,14 @@ def test_command_line_setuptools_nested_output_file(tmpdir, runner):
```

**CLAIM:** The `open` function is called on a `Path` object, but the `proj_dir` object from `tmpdir.mkdir` was a `py.path.local` object which does not support the `/` operator for path joining.

**PROPOSED FIX:** `    with open(str(proj_dir / "setup.py"), "w") as package:`
