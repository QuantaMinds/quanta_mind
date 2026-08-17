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

`ray-project/ray#65505` — `doc/source/cluster/kubernetes/user-guides/kuberay-history-server.md:236`

```diff
 
+Check the RayJob status. The entrypoint script takes about a minute to finish:
+
+```sh
+kubectl get rayjob ${RAY_JOB}
+```
+
 ### Verify collector output in Google Cloud Storage
 
```

**CLAIM:** This command is missing the namespace flag `-n ${NAMESPACE}`, which will cause it to fail if the RayJob was deployed to a specific namespace as done in the preceding step.

**PROPOSED FIX:** `kubectl get rayjob ${RAY_JOB} -n ${NAMESPACE}`

## 2

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:109`

```diff
 [[packages.wheels]]
-name = "idna-3.15-py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/d2/23/408243171aa9aaba178d3e2559159c24c1171a641aa83b67bdd3394ead8e/idna-3.15-py3-none-any.whl"
+name = "idna-3.18-py3-none-any.whl"
+url = "https://files.pythonhosted.org/packages/1e/5e/d4e9f1a599fb8e573b7b87160658329fbf28d19eac2718f51fc3def3aa5a/idna-3.18-py3-none-any.whl"
 
 [packages.wheels.hashes]
-sha256 = "048adeaf8c2d788c40fee287673ccaa74c24ffd8dcf09ffa555a2fbb59f10ac8"
+sha256 = "7f952cbe720b688055e3f87de14f5c3e5fdaa8bc3928985c4077ca689de849a2"
```

**CLAIM:** This URL is invalid as version 3.18 of idna does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `url = "https://files.pythonhosted.org/packages/c2/e7/a82b05cf43a6e8725fd2e0d81c94de20c0437a3bb0886ea64b2db4a2c6d5/idna-3.7-py3-none-any.whl"`

## 3

`mitmproxy/mitmproxy#8350` — `uv.lock:1725`

```diff
 
 [[package]]
 name = "s3transfer"
-version = "0.17.1"
+version = "0.19.2"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "botocore" },
 ]
```

**CLAIM:** This lockfile entry for `s3transfer` specifies version `0.19.2`, which does not exist on PyPI and is a strong indicator of an attempt to inject a malicious dependency.

**PROPOSED FIX:** `version = "0.10.1"`

## 4

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:380`

```diff
 
 [[packages]]
 name = "tzdata"
-version = "2026.2"
+version = "2026.3"
 
 [[packages.wheels]]
-name = "tzdata-2026.2-py2.py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/ce/e4/dccd7f47c4b64213ac01ef921a1337ee6e30e8c6466046018326977efd95/tzdata-2026.2-py2.py3-none-any.whl"
```

**CLAIM:** This version of tzdata does not exist on PyPI, making the corresponding wheel URL invalid and breaking dependency installation.

**PROPOSED FIX:** `version = "2024.1"`

## 5

`mitmproxy/mitmproxy#8350` — `uv.lock:196`

```diff
 
 [[package]]
 name = "botocore"
-version = "1.43.12"
+version = "1.43.34"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "jmespath" },
     { name = "python-dateutil" },
```

**CLAIM:** This lockfile entry for `botocore` specifies version `1.43.34`, which does not exist on PyPI and is a strong indicator of an attempt to inject a malicious dependency.

**PROPOSED FIX:** `version = "1.34.131"`

## 6

`pydantic/pydantic#13667` — `pydantic-core/python/pydantic_core/core_schema.py:2764`

```diff
 class TaggedUnionSchema(TypedDict, total=False):
     type: Required[Literal['tagged-union']]
-    choices: Required[dict[Hashable, CoreSchema]]
-    discriminator: Required[str | list[str | int] | list[list[str | int]] | Callable[[Any], Hashable]]
+    choices: Required[dict[Any, CoreSchema]]
+    discriminator: Required[str | list[str | int] | list[list[str | int]] | Callable[[Any], Any]]
     custom_error_type: str
     custom_error_message: str
     custom_error_context: dict[str, str | int | float]
```

**CLAIM:** The keys of the `choices` dictionary must be hashable, but `Any` does not enforce this, making the type definition incorrect and misleading.

**PROPOSED FIX:** `choices: Required[dict[Hashable, CoreSchema]]`

## 7

`apache/superset#43252` — `superset/daos/dashboard.py:626`

```diff
 
+            # The client rebuilds its in-scope state from this response, so hand
+            # back derived scopes rather than the stored caches, which are stale
+            # for every filter the caller did not touch.
+            updated_configuration = derive_metadata_scopes(dashboard, metadata)[
+                "native_filter_configuration"
+            ]
+
         return updated_configuration
```

**CLAIM:** Deriving filter scopes on write using the persisted dashboard layout is incorrect, as the layout may be stale if the client has unsaved changes, causing the API to return misleading scope data.

**PROPOSED FIX:** `            pass`

## 8

`ray-project/ray#65505` — `doc/source/cluster/kubernetes/user-guides/kuberay-history-server.md:314`

```diff
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
+gs://BUCKET/cluster-metadata/rayjob/NAMESPACE_rayjob-historyserver-gcs_rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
 ```
 
-## Access a terminated RayCluster from the Ray Dashboard
+## Access a terminated RayJob from the Ray Dashboard
```

**CLAIM:** The example output incorrectly includes the literal string "NAMESPACE" instead of an example value like "default", which is inconsistent with other examples in the document and may confuse the user.

**PROPOSED FIX:** `gs://BUCKET/cluster-history/rayjob/default/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_eve`

## 9

`mitmproxy/mitmproxy#8347` — `pyproject.toml:69`

```diff
     "pdoc==16.0.0",
-    "pyinstaller==6.20.0",
-    "pyinstaller-hooks-contrib==2026.5",
+    "pyinstaller==6.21.0",
+    "pyinstaller-hooks-contrib==2026.6",
     "pytest-asyncio==1.2.0",
     "pytest-cov==7.0.0",
     "pytest-timeout==2.4.0",
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** The specified version `2026.6` for `pyinstaller-hooks-contrib` does not exist on the public PyPI repository, as this version number appears to be from the future.

**PROPOSED FIX:** `    "pyinstaller-hooks-contrib==2024.6",`

## 10

`PrefectHQ/prefect#22817` — `src/prefect/_internal/concurrency/cancellation.py:438`

```diff
+            if self._enforcer_thread:
+                logger.debug(
+                    "%r joining enforcer thread %r", self, self._enforcer_thread
+                )
+                self._enforcer_thread.join()
         return retval
 
     def _send_cancelled_error(self):
@@ -458,10 +465,6 @@ def _timeout_enforcer(self):
```

**CLAIM:** The call to join the enforcer thread does not have a timeout, creating a risk that the supervised thread will hang indefinitely if the enforcer thread fails to terminate as expected.

**PROPOSED FIX:** `self._enforcer_thread.join(timeout=10)`

## 11

`pydantic/pydantic#13674` — `.github/workflows/third-party.yml:941`

```diff
+          # stdio + uvicorn subprocesses, so we don't run it for third-party tests.
+          # test_modern_post_with_deeply_nested_body_is_parse_error_not_a_crash is somehow failing in third party tests:
           MCP_EXAMPLES_SMOKE: '0'
-        run: uv run --frozen --no-sync pytest -n auto tests/
+        run: uv run --frozen --no-sync pytest -n auto tests/ -k 'not test_modern_post_with_deeply_nested_body_is_parse_error_not_a_crash'
 
   test-fastmcp:
     name: Test FastMCP (main branch) on Python ${{ matrix.python-version }}
@@ -968,7 +974,7 @@ jobs:
```

**CLAIM:** A specific test is being skipped to make the CI pass, which hides a potential regression and defeats the purpose of the third-party test suite.

**PROPOSED FIX:** `run: uv run --frozen --no-sync pytest -n auto tests/`

## 12

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:226`

```diff
 
 [[packages]]
 name = "pytest"
-version = "9.0.3"
+version = "9.1.1"
 
 [[packages.wheels]]
-name = "pytest-9.0.3-py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/d4/24/a372aaf5c9b7208e7112038812994107bc65a84cd00e0354a88c2c77a617/pytest-9.0.3-py3-none-any.whl"
```

**CLAIM:** This version of pytest does not exist on PyPI, making the corresponding wheel URL invalid and breaking dependency installation.

**PROPOSED FIX:** `version = "8.2.2"`

## 13

`PrefectHQ/prefect#22821` — `src/prefect/runner/_control_channel.py:171`

```diff
-                try:
-                    reg.writer.close()
-                except Exception:
-                    pass
+                reg.writer.close()
         self._registrations.clear()
         self._tokens_to_id.clear()
 
@@ -168,7 +176,7 @@ async def __aexit__(self, *exc_info: object) -> None:
```

**CLAIM:** An unhandled exception from `writer.close()` will prevent `_reset_connection_state` from being called, leaving the registration in an inconsistent state.

**PROPOSED FIX:** `try:
    writer.close()
except OSError:
    pass`

## 14

`fastapi/fastapi#16216` — `scripts/translate.py:439`

```diff
-    branch_name += f"-{secrets.token_hex(4)}"
-    print(f"Creating a new branch {branch_name}")
-    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
+    current_branch = repo.active_branch.name
+    if current_branch == "master" and commit_in_place:
+        print("Can't commit directly to master")
+        raise typer.Exit(code=1)
+    if not commit_in_place:
+        branch_name = "translate"
```

**CLAIM:** The check to prevent direct commits to the main branch is brittle because it only checks for "master" and will not prevent commits if the main branch is named "main".

**PROPOSED FIX:** `if current_branch in ("master", "main") and commit_in_place:`

## 15

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:226`

```diff
 
 [[packages]]
 name = "pytest"
-version = "9.0.3"
+version = "9.1.1"
 
 [[packages.wheels]]
-name = "pytest-9.0.3-py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/d4/24/a372aaf5c9b7208e7112038812994107bc65a84cd00e0354a88c2c77a617/pytest-9.0.3-py3-none-any.whl"
```

**CLAIM:** The example output incorrectly includes the literal string "NAMESPACE" instead of an example value like "default", which is inconsistent with other examples in the document and may confuse the user.

**PROPOSED FIX:** `version = "8.2.2"`

## 16

`mitmproxy/mitmproxy#8349` — `uv.lock:1836`

```diff
-sdist = { url = "https://files.pythonhosted.org/packages/17/2c/7ca5edb5ecd6bcc5cc926fe87e62a84dcd3cbd03a32f9d0bee98d2bee7cf/tox-4.54.0.tar.gz", hash = "sha256:21e36fd8256590379620848d0b03b52f4d541b65b749de1a17c3e616978dad58", size = 279256, upload-time = "2026-05-12T19:13:05.937Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322ebc8cc5f3497627c00f4472", size = 280676, upload-time = "2026-06-03T20:01:03.487Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/26/18/20cf56a76c5d6117547179db9b5d31cc56e3e90507d1b0b748da74aa95c5/tox-4.54.0-py3-none-any.whl", hash = "sha256:a2d7c1177242ae9c3d9e404039e9f945ce16a3e5dfc66972c643e27d7e764f4b", size = 214527, upload-time = "2026-05-12T19:13:04.334Z" },
+    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613d6952e1477be5dca45653d4c053c8", size = 215360, upload-time = "2026-06-03T20:01:01.967Z" },
 ]
 
 [[package]]

```

**CLAIM:** The list of repositories is not sorted correctly by star count, as `HivisionIDPhotos` with 21351 stars is listed after `serve` which has only 21327 stars.

**PROPOSED FIX:** `    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613`

## 17

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:98`

```diff
 [[packages.wheels]]
-name = "hypothesis-6.152.7-py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/0a/1e/8222edaee03c37350eaa726213614e343a62f1e56396dd000ad9277bfa3d/hypothesis-6.152.7-py3-none-any.whl"
+name = "hypothesis-6.165.3-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
+url = "https://files.pythonhosted.org/packages/dc/56/8356dadf45e5c635b46aa2b57fa74f3210250a8e38b860b6b75f50ed0b42/hypothesis-6.165.3-cp314-cp314-pyemscripten_2026_0_wasm32.whl"
 
 [packages.wheels.hashes]
-sha256 = "c0b17dd428fcb6e962f60315f6f4a77816c72fbb281ce9ba73699dabead5ec82"
+sha256 = "53c56155f2cfbb45ec97fef9ea3b8453b4a34c48c3c5cacee16f97dd2a037994"
```

**CLAIM:** This URL is invalid as this specific wheel file does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `url = "https://files.pythonhosted.org/packages/8a/91/a4a6f9a2938082961634023893678236f905173615f5470138d1a69148d0/hypothesis-6.165.3-py3-none-any.whl"`

## 18

`PrefectHQ/prefect#22821` — `src/prefect/runner/_control_channel.py:225`

```diff
-            try:
-                reg_writer.close()
-            except Exception:
-                pass
+            reg_writer.close()
+        return reg.conclusion
 
-    async def signal(self, flow_run_id: uuid.UUID, intent: Intent) -> bool:
+    async def signal(
```

**CLAIM:** An unhandled `OSError` from `reg_writer.close()` will cause `unregister` to fail, preventing the caller from receiving the attempt conclusion and potentially disrupting runner shutdown.

**PROPOSED FIX:** `try:
    reg_writer.close()
except OSError:
    pass`

## 19

`apache/superset#43210` — `pyproject.toml:188`

```diff
 # installing this extra is only required to actually run exports.
 excel-export = ["boto3"]
 fastmcp = [
-    "fastmcp>=3.4.5,<4.0",
+    "fastmcp>=3.4.6,<4.0",
     # tiktoken backs the response-size-guard token estimator. Without
     # it, the middleware falls back to a coarser character-based
     # heuristic that under-counts JSON-heavy MCP responses.
diff --git a/requirements/development.txt b/requirements/development.txt
```

**CLAIM:** The minimum version for `fastmcp` is set to `3.4.6`, but the development requirements are pinned to `3.4.7`, which could lead to installing a different version in production than was used for testing.

**PROPOSED FIX:** `"fastmcp>=3.4.7,<4.0",`

## 20

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:87`

```diff
 [[packages.wheels]]
-name = "faker-40.18.0-py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/84/0b/5c0b2d3a4b7a715f1835dd3f963bfbe841a02ae5cad1df8ee0325dfad235/faker-40.18.0-py3-none-any.whl"
+name = "faker-40.36.0-py3-none-any.whl"
+url = "https://files.pythonhosted.org/packages/50/9a/b947ed175ce9a0dcb070ccf3607f0ce8720cfb5ed1a36166a150b2acd5af/faker-40.36.0-py3-none-any.whl"
 
 [packages.wheels.hashes]
-sha256 = "61a6b94b74605ddb090a065deb197a1c585ae7a874c094cf6693671d271e6083"
+sha256 = "82b9497d9cfe017048075bcf969298a74b1b6e39f5e4dad1211085d1133f7b62"
```

**CLAIM:** This URL is invalid as version 40.36.0 of faker does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `url = "https://files.pythonhosted.org/packages/33/e3/b33d681458433321215ddf99f549414495f85c74951fd977588c3a6f44c3/Faker-25.9.1-py3-none-any.whl"`

## 21

`mitmproxy/mitmproxy#8352` — `uv.lock:959`

```diff
+    { url = "https://files.pythonhosted.org/packages/3a/a4/c4d1a92839f8745ab4aab988a7db884a79d6d710bd3b286fcf9316dece1a/maturin-1.14.1-py3-none-manylinux_2_17_ppc64le.manylinux2014_ppc64le.musllinux_1_1_ppc64le.whl", hash = "sha256:994a0c8ba3ad8a92b3a9ee1b02645d200d610216b15cff5102b0fe65e8e08666", size = 13321347, upload-time = "2026-06-19T05:19:32.411Z" },
+    { url = "https://files.pythonhosted.org/packages/b3/fa/170f04624d03fd07d2a8b1b67de83a127af93aef9eaa425839553347297b/maturin-1.14.1-py3-none-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:be80866363e605d137991b491a741a84cde9ae350183c4c85f49690ca9aaaa65", size = 10877609, upload-time = "2026-06-19T05:19:35.448Z" },
+    { url = "https://files.pythonhosted.org/packages/61/ad/1ae2e1d0ded282bf2c55ac13f0811d87deb425e200ae64a15785675dede9/maturin-1.14.1-py3-none-manylinux_2_31_riscv64.musllinux_1_1_riscv64.whl", hash = "sha256:5282dffd4b539d2be245f4e5b1a5ab6bc1033b58f4a4872f5833f9d43c954aa4", size = 10417316, upload-time = "2026-06-19T05:19:38.28Z" },
+    { url = "https://files.pythonhosted.org/packages/fb/27/bf677183920718da49cd7982d6a3ffc440aad8919329f571d189f81b7bdf/maturin-1.14.1-py3-none-win32.whl", hash = "sha256:1a04de0a20188f95c721b5702eed18140bdcccb28c386797093eca3f62f4d4e0", size = 8931293, upload-time = "2026-06-19T05:19:41.183Z" },
+    { url = "https://files.pythonhosted.org/packages/63/4b/585adeb9167b08d3cdff0032a938b0e72655c92003df4f52c3f696a1bcc2/maturin-1.14.1-py3-none-win_amd64.whl", hash = "sha256:3c9f94640ecc4895e94abaf834a0684430032c865b2748a36c12461fd9252fdd", size = 10314067, upload-time = "2026-06-19T05:19:44.389Z" },
+    { url = "https://files.pythonhosted.org/packages/51/d4/dac8c0720ae246be1700afb6fbdbbea20fe35b13f6570b2f70faa005df77/maturin-1.14.1-py3-none-win_arm64.whl", hash = "sha256:15cea8fcb3ba47dd636f50092bb34baea8b04ac777392f23e6bf8a9a61efb894", size = 9718943, upload-time = "2026-06-19T05:19:47.49Z" },
 ]
 
 [[package]]
```

**CLAIM:** The `upload-time` metadata for this package wheel is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `{ url = "https://files.pythonhosted.org/packages/63/4b/585adeb9167b08d3cdff0032a938b0e72655c92003df4f52c3f696a1bcc2/maturin-1.14.1-py3-none-win_amd64.whl", hash = "sha256:3c9f94640ecc4895e94abaf834a06`

## 22

`PrefectHQ/prefect#22828` — `docs/v3/release-notes/oss/version-3-8.mdx:7`

```diff
 ---
 
+## 3.8.3 - Insert batching pun here
+
+*Released on August 13, 2026*
+
+**Enhancements ➕➕**
+
+* Stop fragmenting task run recorder bulk upserts by [@chuqCTC](https://github.com/chuqCTC) in [#22808](https://github.com/PrefectHQ/prefect/pull/22808)
```

**CLAIM:** The test's cleanup logic joins a thread without a timeout, which could cause the entire test suite to hang if the thread is unexpectedly blocked.

**PROPOSED FIX:** `*Released on August 13, 2024*`

## 23

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:10`

```diff
 [[packages.wheels]]
-name = "annotated_types-0.7.0-py3-none-any.whl"
-url = "https://cdn.jsdelivr.net/pyodide/v314.0.0a2/full/annotated_types-0.7.0-py3-none-any.whl"
+name = "annotated_types-0.8.0-py3-none-any.whl"
+url = "https://files.pythonhosted.org/packages/99/91/8acff4f5e50511b911bbccb72b8628a49c68ce14148cd9f6431094859a90/annotated_types-0.8.0-py3-none-any.whl"
 
 [packages.wheels.hashes]
-sha256 = "da2e754a2716155b60b5cc95027d36bc1b4efbfeb4aa477cca86700ce6b6d7a9"
+sha256 = "f072f4d804ea359e4eaf198b1af7a8b0943881a87f31bb764f8bf219bb9419e0"
```

**CLAIM:** This URL is invalid as version 0.8.0 of annotated-types does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `url = "https://files.pythonhosted.org/packages/28/07/d31334a1b76373520332690434345a82f2775001e873b837a36d253491a3/annotated_types-0.7.0-py3-none-any.whl"`

## 24

`ray-project/ray#65491` — `release/ray_release/command_runner/_anyscale_job_wrapper.py:397`

```diff
+        return 1
+
+    if threshold < 0:
+        logger.info(f"{check_name} skipped: {env_var} is {max_percent}.")
+        return 0
+
+    metrics = _load_metrics_for_check(check_name, env_var)
+    if metrics is None:
+        return 1
```

**CLAIM:** The function returns success when no metric samples are available, which masks potential metric collection issues and makes the check unreliable.

**PROPOSED FIX:** `return 1`

## 25

`mitmproxy/mitmproxy#8352` — `uv.lock:949`

```diff
-    { url = "https://files.pythonhosted.org/packages/97/c6/cbf8a51dde19c19aeba0d9b075095a2effb9b31fd312b1aae3ac79f8aea2/maturin-1.13.3-py3-none-win32.whl", hash = "sha256:0ef257e692cc756c87af5bea95ddfe7d3ac49d3376a7a87f728d63f06e7b6f8b", size = 8901838, upload-time = "2026-05-11T07:43:23.76Z" },
-    { url = "https://files.pythonhosted.org/packages/a1/ff/c6a50a59dc8313097d43ac5f4d74df6a500c8cb62b0dc9e054f53e203a48/maturin-1.13.3-py3-none-win_amd64.whl", hash = "sha256:def4a435ea9d2ee93b18ba579dc8c9cf898889a66f312cd379b5e374ec3e3ad6", size = 10340801, upload-time = "2026-05-11T07:43:29.239Z" },
-    { url = "https://files.pythonhosted.org/packages/6c/93/e32e79333f0902ba292b996f504f5f06be59587f7d02ab8d5ed1e3066445/maturin-1.13.3-py3-none-win_arm64.whl", hash = "sha256:2389fe92d017cea9d94e521fa0175314a4c52f79a1057b901fbc9f8686ef7d0b", size = 9706562, upload-time = "2026-05-11T07:43:31.743Z" },
+    { url = "https://files.pythonhosted.org/packages/f4/f0/97c5a5bd9c71653a066c0976a484eaaae50b9369557838a4176b7b0bdaa5/maturin-1.14.1-py3-none-linux_armv6l.whl", hash = "sha256:522292398945442cdafa9daeb2271b2340fbde57027b818f923f88eab04174f8", size = 10207496, upload-time = "2026-06-19T05:19:09.321Z" },
+    { url = "https://files.pythonhosted.org/packages/fe/83/294bca639b0e052f1e2f65199b3db258780c7d4e31408b934c9c974a1379/maturin-1.14.1-py3-none-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal2.whl", hash = "sha256:ffe5ad71f21d1e6603c4dd75f7fee34adf5ed5ebcebb692886549888ebb329ed", size = 19680113, upload-time = "2026-06-19T05:19:13.43Z" },
+    { url = "https://files.pythonhosted.org/packages/43/b6/79c881410a3b1c187f7eb3d407aecae646c6a4433d630d72200359015e83/maturin-1.14.1-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:f3306078070c1508fd715b9116070cbcaff5959024272a9f1e6f5cb29768b86c", size = 10169205, upload-time = "2026-06-19T05:19:16.615Z" },
+    { url = "https://files.pythonhosted.org/packages/93/9d/44b6f26dcb7f7a04c5501ac2dbb6ca1490150682baa525ca5860504f9eab/maturin-1.14.1-py3-none-manylinux_2_12_i686.manylinux2010_i686.musllinux_1_1_i686.whl", hash = "sha256:cd457cd88961156e26379e1155bd287cc0ec1c8b2f1582b0660fb31b87c8842d", size = 10188098, upload-time = "2026-06-19T05:19:19.736Z" },
+    { url = "https://files.pythonhosted.org/packages/1a/bd/9c0d5d6983905ce2c9edaa073a7e89355a9cf7f396988e05d32f1c37785d/maturin-1.14.1-py3-none-manylinux_2_12_x86_64.manylinux2010_x86_64.musllinux_1_1_x86_64.whl", hash = "sha256:dfc54ae32e6fcb18302193ab9a30b0b25eefffba994ae13238974805533ef75e", size = 10627576, upload-time = "2026-06-19T05:19:22.713Z" },
+    { url = "https://files.pythonhosted.org/packages/e5/33/b096412bd6a7cb399652b260666f901adf88a687181a6dbd6a3f89f0a94e/maturin-1.14.1-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.musllinux_1_1_aarch64.whl", hash = "sha256:a131d912b5267e640bc96d70f4914e10590aed64082ec9abacba7cea52004224", size = 10085181, upload-time = "2026-06-19T05:19:25.69Z" },
```

**CLAIM:** The `upload-time` metadata for this package wheel is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `{ url = "https://files.pythonhosted.org/packages/fe/83/294bca639b0e052f1e2f65199b3db258780c7d4e31408b934c9c974a1379/maturin-1.14.1-py3-none-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal`

## 26

`PrefectHQ/prefect#22828` — `docs/v3/release-notes/oss/version-3-8.mdx:7`

```diff
 ---
 
+## 3.8.3 - Insert batching pun here
+
+*Released on August 13, 2026*
+
+**Enhancements ➕➕**
+
+* Stop fragmenting task run recorder bulk upserts by [@chuqCTC](https://github.com/chuqCTC) in [#22808](https://github.com/PrefectHQ/prefect/pull/22808)
```

**CLAIM:** The release date is set to a future year 2026, which is incorrect.

**PROPOSED FIX:** `*Released on August 13, 2024*`

## 27

`PrefectHQ/prefect#22852` — `.github/workflows/python-tests.yaml:344`

```diff
+          fetch-depth: 0
+          filter: blob:none
+
+      - name: Set up uv and Python 3.12
+        uses: astral-sh/setup-uv@v9.0.0
+        with:
+          enable-cache: true
+          python-version: "3.12"
+          cache-dependency-glob: "pyproject.toml"
```

**CLAIM:** The specified action version `v9.0.0` does not exist for `astral-sh/setup-uv`, which will cause the workflow step to fail.

**PROPOSED FIX:** `uses: astral-sh/setup-uv@v1`

## 28

`mitmproxy/mitmproxy#8349` — `uv.lock:1834`

```diff
     { name = "tomli-w" },
     { name = "virtualenv" },
 ]
-sdist = { url = "https://files.pythonhosted.org/packages/17/2c/7ca5edb5ecd6bcc5cc926fe87e62a84dcd3cbd03a32f9d0bee98d2bee7cf/tox-4.54.0.tar.gz", hash = "sha256:21e36fd8256590379620848d0b03b52f4d541b65b749de1a17c3e616978dad58", size = 279256, upload-time = "2026-05-12T19:13:05.937Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322ebc8cc5f3497627c00f4472", size = 280676, upload-time = "2026-06-03T20:01:03.487Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/26/18/20cf56a76c5d6117547179db9b5d31cc56e3e90507d1b0b748da74aa95c5/tox-4.54.0-py3-none-any.whl", hash = "sha256:a2d7c1177242ae9c3d9e404039e9f945ce16a3e5dfc66972c643e27d7e764f4b", size = 214527, upload-time = "2026-05-12T19:13:04.334Z" },
+    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613d6952e1477be5dca45653d4c053c8", size = 215360, upload-time = "2026-06-03T20:01:01.967Z" },
 ]
```

**CLAIM:** The `upload-time` metadata for this package wheel is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322`

## 29

`fastapi/fastapi#16216` — `scripts/translate.py:473`

```diff
+        gh_repo = g.get_repo(github_repository)
+        body = (
+            message
+            + "\n\nThis PR was created automatically using LLMs."
+            + f"\n\nIt uses the prompt file https://github.com/fastapi/fastapi/blob/master/docs/{language}/llm-prompt.md."
+            + "\n\nIn most cases, it's better to make PRs updating that file so that the LLM can do a better job generating the translations than suggesting changes in this PR."
+        )
+        pr = gh_repo.create_pull(
+            title=message, body=body, base="master", head=branch_name
```

**CLAIM:** The generated pull request body contains a hardcoded repository name and branch name, which makes it incorrect when run on forks or repositories with a different main branch name.

**PROPOSED FIX:** `+ f"\n\nIt uses the prompt file https://github.com/{github_repository}/blob/{gh_repo.default_branch}/docs/{language}/llm-prompt.md."`

## 30

`mitmproxy/mitmproxy#8350` — `pyproject.toml:91`

```diff
     "ruff==0.15.11",
 ]
 deploy = [
-    "awscli==1.45.12",
+    "awscli==1.45.34",
     "twine==6.2.0",
 ]
 
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** This dependency specification is a security risk because version `1.45.34` of `awscli` does not exist on PyPI, suggesting this could be an attempt to install a malicious package.

**PROPOSED FIX:** `awscli==1.33.11`

## 31

`ray-project/ray#65505` — `doc/source/cluster/kubernetes/user-guides/kuberay-history-server.md:311`

```diff
-gs://BUCKET/cluster-metadata/raycluster/NAMESPACE_raycluster-historyserver/session_2026-02-20_13-03-16_320452_1
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
+gs://BUCKET/cluster-metadata/rayjob/NAMESPACE_rayjob-historyserver-gcs_rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
 ```
```

**CLAIM:** The example output incorrectly includes the literal string "NAMESPACE" instead of an example value like "default", which is inconsistent with other examples in the document and may confuse the user.

**PROPOSED FIX:** `gs://BUCKET/cluster-metadata/rayjob/default_rayjob-historyserver-gcs_rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1`

## 32

`mitmproxy/mitmproxy#8350` — `uv.lock:104`

```diff
 
 [[package]]
 name = "awscli"
-version = "1.45.12"
+version = "1.45.34"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "botocore" },
@@ -111,9 +111,9 @@ dependencies = [
```

**CLAIM:** This lockfile entry for `awscli` specifies version `1.45.34`, which does not exist on PyPI and is a strong indicator of an attempt to inject a malicious dependency.

**PROPOSED FIX:** `version = "1.33.11"`

## 33

`apache/superset#43252` — `superset-frontend/src/dashboard/actions/nativeFilters.ts:99`

```diff
+      // ones this save never touched, whose copy is whatever was stored when
+      // the dashboard was last saved. Dropping them lets the reducers keep the
+      // scopes calculateScopes already computed for this session.
+      const savedFilters = response.result.map(
+        filter => omit(filter, ['chartsInScope', 'tabsInScope']) as Filter,
+      );
       dispatch({
         type: SET_NATIVE_FILTERS_CONFIG_COMPLETE,
-        filterChanges: response.result,
```

**CLAIM:** The type assertion `as Filter` is incorrect because `omit` removes properties from the filter object, and the resulting object may no longer conform to the `Filter` type, potentially causing runtime errors.

**PROPOSED FIX:** `        filter => omit(filter, ['chartsInScope', 'tabsInScope']),`

## 34

`mitmproxy/mitmproxy#8348` — `pyproject.toml:40`

```diff
     "bcrypt>=5.0.0,<=5.0.0",
     "Brotli>=1.0,<=1.2.0",
     "certifi>=2019.9.11",  # no upper bound here to get latest CA bundle
-    "cryptography>=42.0,<=49.0.0",  # relaxed upper bound here to get security fixes
+    "cryptography>=42.0,<=50.0.0",  # relaxed upper bound here to get security fixes
     "flask>=3.0,<=3.1.3",
     "h11>=0.16.0,<=0.16.0",
     "h2>=4.3.0,<=4.3.0",
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** The updated dependency constraint allows `cryptography` version 50.0.0, which drops support for OpenSSL 1.1.1 and may break environments that have not been upgraded to OpenSSL 3.0 or newer.

**PROPOSED FIX:** `"cryptography>=42.0,<50.0.0",  # relaxed upper bound here to get security fixes`

## 35

`mitmproxy/mitmproxy#8347` — `pyproject.toml:69`

```diff
     "pdoc==16.0.0",
-    "pyinstaller==6.20.0",
-    "pyinstaller-hooks-contrib==2026.5",
+    "pyinstaller==6.21.0",
+    "pyinstaller-hooks-contrib==2026.6",
     "pytest-asyncio==1.2.0",
     "pytest-cov==7.0.0",
     "pytest-timeout==2.4.0",
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** This URL is invalid as this specific wheel file does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `    "pyinstaller-hooks-contrib==2024.6",`

## 36

`mitmproxy/mitmproxy#8347` — `pyproject.toml:69`

```diff
     "pdoc==16.0.0",
-    "pyinstaller==6.20.0",
-    "pyinstaller-hooks-contrib==2026.5",
+    "pyinstaller==6.21.0",
+    "pyinstaller-hooks-contrib==2026.6",
     "pytest-asyncio==1.2.0",
     "pytest-cov==7.0.0",
     "pytest-timeout==2.4.0",
diff --git a/uv.lock b/uv.lock
```

**CLAIM:** The `upload-time` field for the wheel package has an incorrect year of 2026, as the package was actually uploaded in 2024.

**PROPOSED FIX:** `    "pyinstaller-hooks-contrib==2024.6",`

## 37

`mitmproxy/mitmproxy#8352` — `uv.lock:948`

```diff
-    { url = "https://files.pythonhosted.org/packages/4b/ac/00c955c2ef134817b1a7bdaa76b0309e9c5291eb17d9ff88069eecd08bc2/maturin-1.13.3-py3-none-manylinux_2_31_riscv64.musllinux_1_1_riscv64.whl", hash = "sha256:b6741d7bf4af97da937528fd1e523c6ab54f53d9a21870fa735d6e67fd88e273", size = 10388661, upload-time = "2026-05-11T07:43:18.727Z" },
-    { url = "https://files.pythonhosted.org/packages/97/c6/cbf8a51dde19c19aeba0d9b075095a2effb9b31fd312b1aae3ac79f8aea2/maturin-1.13.3-py3-none-win32.whl", hash = "sha256:0ef257e692cc756c87af5bea95ddfe7d3ac49d3376a7a87f728d63f06e7b6f8b", size = 8901838, upload-time = "2026-05-11T07:43:23.76Z" },
-    { url = "https://files.pythonhosted.org/packages/a1/ff/c6a50a59dc8313097d43ac5f4d74df6a500c8cb62b0dc9e054f53e203a48/maturin-1.13.3-py3-none-win_amd64.whl", hash = "sha256:def4a435ea9d2ee93b18ba579dc8c9cf898889a66f312cd379b5e374ec3e3ad6", size = 10340801, upload-time = "2026-05-11T07:43:29.239Z" },
-    { url = "https://files.pythonhosted.org/packages/6c/93/e32e79333f0902ba292b996f504f5f06be59587f7d02ab8d5ed1e3066445/maturin-1.13.3-py3-none-win_arm64.whl", hash = "sha256:2389fe92d017cea9d94e521fa0175314a4c52f79a1057b901fbc9f8686ef7d0b", size = 9706562, upload-time = "2026-05-11T07:43:31.743Z" },
+    { url = "https://files.pythonhosted.org/packages/f4/f0/97c5a5bd9c71653a066c0976a484eaaae50b9369557838a4176b7b0bdaa5/maturin-1.14.1-py3-none-linux_armv6l.whl", hash = "sha256:522292398945442cdafa9daeb2271b2340fbde57027b818f923f88eab04174f8", size = 10207496, upload-time = "2026-06-19T05:19:09.321Z" },
+    { url = "https://files.pythonhosted.org/packages/fe/83/294bca639b0e052f1e2f65199b3db258780c7d4e31408b934c9c974a1379/maturin-1.14.1-py3-none-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal2.whl", hash = "sha256:ffe5ad71f21d1e6603c4dd75f7fee34adf5ed5ebcebb692886549888ebb329ed", size = 19680113, upload-time = "2026-06-19T05:19:13.43Z" },
+    { url = "https://files.pythonhosted.org/packages/43/b6/79c881410a3b1c187f7eb3d407aecae646c6a4433d630d72200359015e83/maturin-1.14.1-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:f3306078070c1508fd715b9116070cbcaff5959024272a9f1e6f5cb29768b86c", size = 10169205, upload-time = "2026-06-19T05:19:16.615Z" },
+    { url = "https://files.pythonhosted.org/packages/93/9d/44b6f26dcb7f7a04c5501ac2dbb6ca1490150682baa525ca5860504f9eab/maturin-1.14.1-py3-none-manylinux_2_12_i686.manylinux2010_i686.musllinux_1_1_i686.whl", hash = "sha256:cd457cd88961156e26379e1155bd287cc0ec1c8b2f1582b0660fb31b87c8842d", size = 10188098, upload-time = "2026-06-19T05:19:19.736Z" },
+    { url = "https://files.pythonhosted.org/packages/1a/bd/9c0d5d6983905ce2c9edaa073a7e89355a9cf7f396988e05d32f1c37785d/maturin-1.14.1-py3-none-manylinux_2_12_x86_64.manylinux2010_x86_64.musllinux_1_1_x86_64.whl", hash = "sha256:dfc54ae32e6fcb18302193ab9a30b0b25eefffba994ae13238974805533ef75e", size = 10627576, upload-time = "2026-06-19T05:19:22.713Z" },
```

**CLAIM:** The `upload-time` metadata for this package wheel is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `{ url = "https://files.pythonhosted.org/packages/f4/f0/97c5a5bd9c71653a066c0976a484eaaae50b9369557838a4176b7b0bdaa5/maturin-1.14.1-py3-none-linux_armv6l.whl", hash = "sha256:522292398945442cdafa9daeb2`

## 38

`fastapi/fastapi#16196` — `docs/en/overrides/main.html:48`

```diff
   {% endif %}
 {% endblock %}
 
+{% block content %}
+  {% if not page.url %}
+    {% set conf_rail_mobile = true %}
+    {% include "partials/conf-rail.html" %}
+  {% endif %}
+  {% include "partials/content.html" %}
```

**CLAIM:** This condition incorrectly restricts the mobile conference rail to being rendered only on the homepage, creating an inconsistent UI on mobile where it is missing from all other pages.

**PROPOSED FIX:** `  {% if page %}`

## 39

`mitmproxy/mitmproxy#8347` — `pyproject.toml:68`

```diff
     "maturin==1.13.3",
     "pdoc==16.0.0",
-    "pyinstaller==6.20.0",
-    "pyinstaller-hooks-contrib==2026.5",
+    "pyinstaller==6.21.0",
+    "pyinstaller-hooks-contrib==2026.6",
     "pytest-asyncio==1.2.0",
     "pytest-cov==7.0.0",
     "pytest-timeout==2.4.0",
```

**CLAIM:** The specified version `6.21.0` for the `pyinstaller` package does not exist on the public PyPI repository, which will cause dependency installation to fail.

**PROPOSED FIX:** `    "pyinstaller==6.8.0",`

## 40

`mitmproxy/mitmproxy#8352` — `uv.lock:946`

```diff
-version = "1.13.3"
+version = "1.14.1"
 source = { registry = "https://pypi.org/simple" }
-sdist = { url = "https://files.pythonhosted.org/packages/9c/1c/612d23d33ec21b9ae7ece7b3f0dd5f9dfd57b4009e9d2938165869ebd6ae/maturin-1.13.3.tar.gz", hash = "sha256:771e1e9e71a278e56db01552e0d1acfd1464259f9575b6e72842f893cd299079", size = 357934, upload-time = "2026-05-11T07:43:39.027Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/e7/b3/addd877f871fb1860d46d3a4f206ecb10b946c85846805e6367631926fd3/maturin-1.14.1.tar.gz", hash = "sha256:9d6577a62cd08e0ceba7a0db06fb098e0c9b1b3429bad747a4f3a18215a1b3df", size = 369637, upload-time = "2026-06-19T05:19:49.774Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/71/66/18c2aaac0b2a5dea9f1db5984ce83b905ad205cfc7c02d0091e707c0c2e7/maturin-1.13.3-py3-none-linux_armv6l.whl", hash = "sha256:3cc13929ca82aefa4adbf0f2c35419369796213c6fb0eb24e914945f50ef5d8c", size = 10190971, upload-time = "2026-05-11T07:43:10.431Z" },
-    { url = "https://files.pythonhosted.org/packages/bc/71/26a988d092e4fd6a9523d46d44400a46cad7cdf3fd206ce702240c748aee/maturin-1.13.3-py3-none-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal2.whl", hash = "sha256:53b08bd075649ce96513ad9abf241a43cb685ed6e9e7790f8dbc2d66e95d8323", size = 19716714, upload-time = "2026-05-11T07:43:36.911Z" },
-    { url = "https://files.pythonhosted.org/packages/82/5c/f3fd0e184255d9fc7e272c62af3dfa84c617b2577ef83af9ce615f5279cc/maturin-1.13.3-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:4cd478e6e4c56251e48ed079b8efd55b30bc5c09cf695a1bdafaeb582ee735a0", size = 10194726, upload-time = "2026-05-11T07:43:07.05Z" },
```

**CLAIM:** The `upload-time` metadata for the package's source distribution is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `sdist = { url = "https://files.pythonhosted.org/packages/e7/b3/addd877f871fb1860d46d3a4f206ecb10b946c85846805e6367631926fd3/maturin-1.14.1.tar.gz", hash = "sha256:9d6577a62cd08e0ceba7a0db06fb098e0c9b1`

## 41

`mitmproxy/mitmproxy#8349` — `uv.lock:1834`

```diff
     { name = "tomli-w" },
     { name = "virtualenv" },
 ]
-sdist = { url = "https://files.pythonhosted.org/packages/17/2c/7ca5edb5ecd6bcc5cc926fe87e62a84dcd3cbd03a32f9d0bee98d2bee7cf/tox-4.54.0.tar.gz", hash = "sha256:21e36fd8256590379620848d0b03b52f4d541b65b749de1a17c3e616978dad58", size = 279256, upload-time = "2026-05-12T19:13:05.937Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322ebc8cc5f3497627c00f4472", size = 280676, upload-time = "2026-06-03T20:01:03.487Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/26/18/20cf56a76c5d6117547179db9b5d31cc56e3e90507d1b0b748da74aa95c5/tox-4.54.0-py3-none-any.whl", hash = "sha256:a2d7c1177242ae9c3d9e404039e9f945ce16a3e5dfc66972c643e27d7e764f4b", size = 214527, upload-time = "2026-05-12T19:13:04.334Z" },
+    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613d6952e1477be5dca45653d4c053c8", size = 215360, upload-time = "2026-06-03T20:01:01.967Z" },
 ]
```

**CLAIM:** The `upload-time` field for the sdist package has an incorrect year of 2026, as the package was actually uploaded in 2024.

**PROPOSED FIX:** `sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322`

## 42

`pydantic/pydantic#13667` — `pydantic-core/python/pydantic_core/core_schema.py:2765`

```diff
     type: Required[Literal['tagged-union']]
-    choices: Required[dict[Hashable, CoreSchema]]
-    discriminator: Required[str | list[str | int] | list[list[str | int]] | Callable[[Any], Hashable]]
+    choices: Required[dict[Any, CoreSchema]]
+    discriminator: Required[str | list[str | int] | list[list[str | int]] | Callable[[Any], Any]]
     custom_error_type: str
     custom_error_message: str
     custom_error_context: dict[str, str | int | float]
diff --git a/pydantic/_internal/_discriminated_union.py b/pydantic/_internal/_discriminated_union.py
```

**CLAIM:** A discriminator callable must return a hashable value to be used as a key in the `choices` map, but the `Any` return type in `Callable[[Any], Any]` does not enforce this.

**PROPOSED FIX:** `discriminator: Required[str | list[str | int] | list[list[str | int]] | Callable[[Any], Hashable]]`

## 43

`fastapi/fastapi#16185` — `.github/latest-changes.yml:6`

```diff
+  docs:
+    - docs/en/docs/**
+    - docs_src/**
+  lang-all:
+    - exclude: docs/*/**/_*.md
+    - docs/*/docs/**
+  internal:
+    - .github/**
+    - scripts/**
```

**CLAIM:** The exclusion rules for the `lang-all` label are incomplete, as they are missing a rule to exclude English documentation files (`docs/en/docs/**`), which will cause pull requests modifying only English docs to be incorrectly labeled as translation changes.

**PROPOSED FIX:** `    - exclude: docs/*/**/_*.md
    - exclude: docs/en/docs/**`

## 44

`ray-project/ray#65472` — `doc/source/ray-overview/index.md:73`

```diff
+:color: primary
+:outline:
+:expand:
+
+Ray AI Libraries
 ```
+:::
+
+:::{grid-item-card}
```

**CLAIM:** The `button-ref` directive is not closed with '```', which is a syntax error that will cause the document to render incorrectly.

**PROPOSED FIX:** `Ray AI Libraries
````

## 45

`PrefectHQ/prefect#22811` — `ui-v2/src/components/flow-runs/flow-run-details-page/flow-run-header.tsx:211`

```diff
 						<span>
-							{secondsToApproximateString(flowRun.total_run_time ?? 0)}
+							{secondsToApproximateString(
+								isRunningState(flowRun.state_type)
+									? (flowRun.estimated_run_time ?? 0)
+									: (flowRun.total_run_time ?? 0),
+							)}
 						</span>
 					</div>
```

**CLAIM:** This is a logic error because it uses `estimated_run_time`, which is the estimated total duration, instead of calculating the actual elapsed time for a running flow.

**PROPOSED FIX:** `									? (flowRun.start_time ? (Date.now() - new Date(flowRun.start_time).getTime()) / 1000 : 0)`

## 46

`ray-project/ray#65505` — `doc/source/cluster/kubernetes/user-guides/kuberay-history-server.md:313`

```diff
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
+gs://BUCKET/cluster-metadata/rayjob/NAMESPACE_rayjob-historyserver-gcs_rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
 ```
 
-## Access a terminated RayCluster from the Ray Dashboard
```

**CLAIM:** The example output incorrectly includes the literal string "NAMESPACE" instead of an example value like "default", which is inconsistent with other examples in the document and may confuse the user.

**PROPOSED FIX:** `gs://BUCKET/cluster-history/rayjob/default/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_ev`

## 47

`fastapi/fastapi#16173` — `docs/en/data/topic_repos.yml:24`

```diff
   owner_html_url: https://github.com/jina-ai
 - name: HivisionIDPhotos
   html_url: https://github.com/Zeyi-Lin/HivisionIDPhotos
-  stars: 21327
+  stars: 21351
   owner_login: Zeyi-Lin
   owner_html_url: https://github.com/Zeyi-Lin
 - name: Douyin_TikTok_Download_API
   html_url: https://github.com/Evil0ctal/Douyin_TikTok_Download_API
```

**CLAIM:** The list of repositories is not sorted correctly by star count, as `HivisionIDPhotos` with 21351 stars is listed after `serve` which has only 21327 stars.

**PROPOSED FIX:** `# This line is correct, but the entire HivisionIDPhotos entry must be moved before the 'serve' entry to fix the sort order.`

## 48

`pydantic/pydantic#13665` — `tests/test_json_schema.py:878`

```diff
+        assert properties[field_name]['type'] == expected_type
+        if ser_json_temporal == 'iso8601':
+            assert isinstance(value, str)
+        else:
+            assert isinstance(value, float)
+
+
+@pytest.mark.parametrize(
+    'config,expected_schema',
```

**CLAIM:** A discriminator callable must return a hashable value to be used as a key in the `choices` map, but the `Any` return type in `Callable[[Any], Any]` does not enforce this.

**PROPOSED FIX:** `            assert isinstance(value, (int, float))`

## 49

`PrefectHQ/prefect#22852` — `.github/workflows/python-tests.yaml:365`

```diff
+            vcs.repository.url.full=${{ github.server_url }}/${{ github.repository }},
+            cicd.pipeline.run.id=${{ github.run_id }},
+            github.actions.run.attempt=${{ github.run_attempt }},
+            cicd.pipeline.run.url.full=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }},
+            github.actions.job.check_run_id=${{ job.check_run_id }},
+            prefect.pytest.shard.id=${{ matrix.test-type.id }}
+          LOGFIRE_TOKEN: ${{ secrets.LOGFIRE_TEST_PROFILE_TOKEN }}
+          PREFECT_LOGFIRE_ENABLED: "false"
+        run: |
```

**CLAIM:** The context variable `job.check_run_id` is not available and will be empty, which creates a malformed key-value pair in the `LOGFIRE_RESOURCE_ATTRIBUTES` environment variable.

**PROPOSED FIX:** `github.actions.job.id=${{ github.job }},`

## 50

`apache/superset#43255` — `superset-frontend/src/components/Datasource/components/Fieldset/index.tsx:48`

```diff
+  // earlier render. Spreading that render's `item` rebuilds the whole record
+  // from a snapshot taken before a sibling field committed, dropping the value
+  // the user typed first. Reading off a ref merges into the latest commit.
+  const itemRef = useRef(item);
+  useEffect(() => {
+    itemRef.current = item;
+  }, [item]);
+
   const handleChange = useCallback(
```

**CLAIM:** Using `useEffect` to update the ref creates a race condition because the effect runs asynchronously after render, allowing a debounced callback to access a stale value before the ref is updated.

**PROPOSED FIX:** `itemRef.current = item;`

## 51

`ray-project/ray#65505` — `doc/source/cluster/kubernetes/user-guides/kuberay-history-server.md:312`

```diff
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
-gs://BUCKET/cluster-history/raycluster/NAMESPACE/raycluster-historyserver/session_2026-02-20_13-03-16_320452_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-02-20-13
+gs://BUCKET/cluster-metadata/rayjob/NAMESPACE_rayjob-historyserver-gcs_rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/dashboard_agent.log
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/node_events/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
+gs://BUCKET/cluster-history/rayjob/NAMESPACE/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/job_events/AQAAAA==/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace-2026-07-28-17
 ```
 
```

**CLAIM:** The example output incorrectly includes the literal string "NAMESPACE" instead of an example value like "default", which is inconsistent with other examples in the document and may confuse the user.

**PROPOSED FIX:** `gs://BUCKET/cluster-history/rayjob/default/rayjob-historyserver-gcs/rayjob-historyserver-gcs-lz9xt/session_2026-07-28_17-07-51_736134_1/0a46878b6f144cdb0ed62e9871caaeb16083547bf34acb5025832ace/logs/da`

## 52

`PrefectHQ/prefect#22811` — `ui-v2/src/components/flow-runs/flow-run-details-page/flow-run-header.tsx:211`

```diff
 						<span>
-							{secondsToApproximateString(flowRun.total_run_time ?? 0)}
+							{secondsToApproximateString(
+								isRunningState(flowRun.state_type)
+									? (flowRun.estimated_run_time ?? 0)
+									: (flowRun.total_run_time ?? 0),
+							)}
 						</span>
 					</div>
```

**CLAIM:** The `upload-time` metadata for this package wheel is set to a future date in 2026, which is a data handling error.

**PROPOSED FIX:** `									? (flowRun.start_time ? (Date.now() - new Date(flowRun.start_time).getTime()) / 1000 : 0)`

## 53

`pydantic/pydantic#13659` — `pydantic/experimental/pipeline.py:485`

```diff
 
+# Core schema types with native support for the `gt`/`ge`/`lt`/`le` constraints:
+_ORDERING_SCHEMA_TYPES = frozenset({'int', 'float', 'decimal', 'fraction', 'date', 'time', 'datetime', 'timedelta'})
+# Core schema types with native support for the `min_length`/`max_length` constraints:
+_LENGTH_SCHEMA_TYPES = frozenset({'str', 'bytes', 'list', 'tuple', 'set', 'frozenset', 'dict', 'generator'})
+
+
 def _apply_constraint(  # noqa: C901
     s: cs.CoreSchema | None, constraint: _ConstraintAnnotation
```

**CLAIM:** The 'generator' core schema type does not support `min_length` or `max_length` constraints, so including it will cause an error when applying these constraints.

**PROPOSED FIX:** `_LENGTH_SCHEMA_TYPES = frozenset({'str', 'bytes', 'list', 'tuple', 'set', 'frozenset', 'dict'})`

## 54

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:21`

```diff
 [[packages.wheels]]
-name = "asttokens-3.0.1-py3-none-any.whl"
-url = "https://cdn.jsdelivr.net/pyodide/v314.0.0a2/full/asttokens-3.0.1-py3-none-any.whl"
+name = "asttokens-3.0.2-py3-none-any.whl"
+url = "https://files.pythonhosted.org/packages/d4/2b/04b8a15f3a1c77bc79ddf5c73875327f34b4fa75982df2b76e45e402d364/asttokens-3.0.2-py3-none-any.whl"
 
 [packages.wheels.hashes]
-sha256 = "fd8b163abcbaad2a68a41fdf11a33e3c92404b66e3ecb42093ad8b17bbca353e"
+sha256 = "9da13157f5b28becde0bd374fc677dcd3c290614264eff096f167c469cd9f933"
```

**CLAIM:** This URL is invalid as version 3.0.2 of asttokens does not exist on PyPI, which will cause dependency installation to fail.

**PROPOSED FIX:** `url = "https://files.pythonhosted.org/packages/a9/a9/84f2a096e16d38834494222163825a94b9df795958fa6d33a73e3143d042/asttokens-2.4.1-py2.py3-none-any.whl"`

## 55

`mitmproxy/mitmproxy#8350` — `uv.lock:114`

```diff
     { name = "rsa" },
     { name = "s3transfer" },
 ]
-sdist = { url = "https://files.pythonhosted.org/packages/58/f8/edbed27a775308de72a79d68e5f0f30616455437cd1d2c8744773820be14/awscli-1.45.12.tar.gz", hash = "sha256:d0105fe0478d190f645bb20339db504030a09bf0234bd29078ab677f5ae52a37", size = 1894918, upload-time = "2026-05-20T19:38:07.56Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/7d/e5/0553e8be70a25cb60bb5c7ac55eca667e1c9ffe5c48b9cde1949731deba5/awscli-1.45.34.tar.gz", hash = "sha256:026d19a308fc105adb9e509747c43760604f51d9f8427937407d4a3d24203829", size = 1896765, upload-time = "2026-06-19T19:33:35.662Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/5f/88/7de56a8d130eb5f5d623af5b616d5648ff234a63cd3a8a161c21d94483d9/awscli-1.45.12-py3-none-any.whl", hash = "sha256:37ff93782909668c8d3b2342d310cb9e3548c537ec357c85f4f6b1359e8d3af6", size = 4646320, upload-time = "2026-05-20T19:38:03.363Z" },
+    { url = "https://files.pythonhosted.org/packages/a8/48/3821c825db63b6c7f54175788449917115c501613163382034dd38827dcf/awscli-1.45.34-py3-none-any.whl", hash = "sha256:9ec29f811c659171d0d3278e83bd779c8e8ad84ad1809df6d9a5955aa7dd8d92", size = 4649725, upload-time = "2026-06-19T19:33:32.673Z" },
 ]
```

**CLAIM:** This `sdist` entry for `awscli` has a future `upload-time` and corresponds to a package version that does not exist on PyPI, indicating a severe security risk.

**PROPOSED FIX:** `This line should be removed and the lock file regenerated after correcting `pyproject.toml` to use a valid, existing package version.`

## 56

`pydantic/pydantic#13665` — `tests/test_json_schema.py:878`

```diff
+        assert properties[field_name]['type'] == expected_type
+        if ser_json_temporal == 'iso8601':
+            assert isinstance(value, str)
+        else:
+            assert isinstance(value, float)
+
+
+@pytest.mark.parametrize(
+    'config,expected_schema',
```

**CLAIM:** The test incorrectly assumes that temporal types serialized as numbers will always be floats, but they can be integers depending on the value.

**PROPOSED FIX:** `            assert isinstance(value, (int, float))`

## 57

`PrefectHQ/prefect#22817` — `tests/_internal/concurrency/test_cancellation.py:172`

```diff
+    try:
+        assert not scope._enforcer_thread.is_alive()
+    finally:
+        scope._event.set()
+        scope._enforcer_thread.join()
+
+
 @pytest.mark.timeout(method="thread")  # alarm-based pytest-timeout will interfere
 def test_cancel_sync_after_manual_in_main_thread():
```

**CLAIM:** The test's cleanup logic joins a thread without a timeout, which could cause the entire test suite to hang if the thread is unexpectedly blocked.

**PROPOSED FIX:** `scope._enforcer_thread.join(timeout=5)`

## 58

`mitmproxy/mitmproxy#8349` — `uv.lock:1836`

```diff
-sdist = { url = "https://files.pythonhosted.org/packages/17/2c/7ca5edb5ecd6bcc5cc926fe87e62a84dcd3cbd03a32f9d0bee98d2bee7cf/tox-4.54.0.tar.gz", hash = "sha256:21e36fd8256590379620848d0b03b52f4d541b65b749de1a17c3e616978dad58", size = 279256, upload-time = "2026-05-12T19:13:05.937Z" }
+sdist = { url = "https://files.pythonhosted.org/packages/79/5b/4f09156a3f7bf3c4fa23212717f097c59126d81e2c557e6fd872a62db38a/tox-4.55.1.tar.gz", hash = "sha256:0678fbf26dd5b559b1ef128fa4388325920219322ebc8cc5f3497627c00f4472", size = 280676, upload-time = "2026-06-03T20:01:03.487Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/26/18/20cf56a76c5d6117547179db9b5d31cc56e3e90507d1b0b748da74aa95c5/tox-4.54.0-py3-none-any.whl", hash = "sha256:a2d7c1177242ae9c3d9e404039e9f945ce16a3e5dfc66972c643e27d7e764f4b", size = 214527, upload-time = "2026-05-12T19:13:04.334Z" },
+    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613d6952e1477be5dca45653d4c053c8", size = 215360, upload-time = "2026-06-03T20:01:01.967Z" },
 ]
 
 [[package]]

```

**CLAIM:** The `upload-time` field for the wheel package has an incorrect year of 2026, as the package was actually uploaded in 2024.

**PROPOSED FIX:** `    { url = "https://files.pythonhosted.org/packages/bb/fd/394f00f3d3e23d87eb7b20276d88fe835e48780d3eb30e6f362428bb80c8/tox-4.55.1-py3-none-any.whl", hash = "sha256:e2084be6dfdef96ba1bed4948e6a1f73613`

## 59

`pydantic/pydantic#13649` — `.github/pyodide/pylock.31x.toml:292`

```diff
 
 [[packages]]
 name = "pytz"
-version = "2026.2"
+version = "2026.3.post1"
 
 [[packages.wheels]]
-name = "pytz-2026.2-py2.py3-none-any.whl"
-url = "https://files.pythonhosted.org/packages/ec/dd/96da98f892250475bdf2328112d7468abdd4acc7b902b6af23f4ed958ea0/pytz-2026.2-py2.py3-none-any.whl"
```

**CLAIM:** This version of pytz does not exist on PyPI, making the corresponding wheel URL invalid and breaking dependency installation.

**PROPOSED FIX:** `version = "2024.1"`
