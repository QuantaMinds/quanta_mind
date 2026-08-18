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

`bokeh/bokeh#15346` — `tests/unit/bokeh/models/test_plots.py:441`

```diff
@@ -437,6 +438,7 @@ def test_add_tile(test_input, provider):
         plot2.add_tile(test_input, retina=True)
         tile_source2 = plot2.renderers[0].tile_source
         assert tile_source2.url == provider.build_url(scale_factor="@2x")
+        assert tile_source2.pixel_ratio == 2
 
 def test_add_tile_tilesource():
     mapnik = xyz.OpenStreetMap.Mapnik

```

**CLAIM:** This call will fail with an assertion or cause data loss if the buffer was not empty, because it overwrites the buffer instead of prepending the newly read data.

**PROPOSED FIX:** `        assert tile_source2.pixel_ratio == (2 if "{r}" in provider.url else 1)`

## 2

`huggingface/datasets#8367` — `tests/test_buckets.py:205`

```diff
+        features=Features({"x": Value("int64")}),
+        data_dir="data",
+        set_default=None,
+        uploaded_sizes=[40],
+        deleted_sizes=[0],
+        remove_other_splits=False,
+    )
+
+    data_files = MetadataConfigs.from_dataset_card_data(dataset_card.data)["default"]["data_files"]
```

**CLAIM:** The test is appending a new split and not deleting any data, so `deleted_sizes` should be an empty list `[]` rather than `[0]`.

**PROPOSED FIX:** `deleted_sizes=[],`

## 3

`bokeh/bokeh#15342` — `tests/integration/server_proxy/test_proxy.py:183`

```diff
+            marker = page.locator("#proxy-request")
+            marker.wait_for(state="visible", timeout=15_000)
+            assert marker.text_content() == "Bokeh reverse proxy ready"
+            assert marker.get_attribute("data-host") == "127.0.0.1:8080"
+            assert marker.get_attribute("data-root-path") == ""
+            assert page.evaluate("Bokeh.documents.length") == 1
+
+            # No application messages cross the websocket while idle, so the
+            # backend's keepalive traffic must keep it open past the proxy timeout.
```

**CLAIM:** This assertion is incorrect for the ASGI frontend, which correctly propagates the `root_path` from the reverse proxy and will cause this test to fail.

**PROPOSED FIX:** `assert marker.get_attribute("data-root-path") == ("/services/bokeh" if FRONTEND == "asgi" else "")`

## 4

`bokeh/bokeh#15350` — `tests/unit/bokeh/server/test_asgi.py:474`

```diff
+    assert point_draw.renderers[0].data_source is centers
+    assert center_hover is not None
+    assert center_hover.renderers == point_draw.renderers
+    assert cast(Any, point_draw.renderers[0].hover_glyph).line_width == 4
+    assert plot.toolbar.active_tap is point_draw
+    assert plot.toolbar.active_drag is point_draw
+    assert plot.toolbar.active_inspect is center_hover
+    assert plot.toolbar_location is None
+    assert plot.t
```

**CLAIM:** This line is an incomplete statement, which will cause a syntax error when the test is run.

**PROPOSED FIX:** `assert plot.title.text == "50,000 particles · Counter-rotating vortex flow"`

## 5

`dbt-labs/dbt-core#15935` — `.github/workflows/release.yml:105`

```diff
+          # them as integers. Comparing "major.minor" as a single decimal via `bc`
+          # is wrong here: e.g. 1.9 > 1.11 as decimals, even though minor version 9
+          # is less than minor version 11.
+          INPUT_MAJOR=$(echo "${{ inputs.version_number }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\1/')
+          INPUT_MINOR=$(echo "${{ inputs.version_number }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')
+          HATCH_MAJOR=$(echo "${{ env.MIN_HATCH_VERSION }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\1/')
+          HATCH_MINOR=$(echo "${{ env.MIN_HATCH_VERSION }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')
+
+          if [ "$INPUT_MAJOR" -gt "$HATCH_MAJOR" ] || { [ "$INPUT_MAJOR" -eq "$HATCH_MAJOR" ] && [ "$INPUT_MINOR" -ge "$HATCH_MINOR" ]; }; then
```

**CLAIM:** This command incorrectly parses the minor version if the input version string is just a major version number (e.g., "1"), as the `sed` expression does not match and the original string is assigned to the variable, effectively treating "1" as "1.1".

**PROPOSED FIX:** `INPUT_MINOR=$(echo "${{ inputs.version_number }}.0" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')`

## 6

`encode/httpx#3670` — `src/ahttpx/_streams.py:84`

```diff
-    async def open(self):
-        self._fileobj = open(self._path, 'rb')
-        self._size = os.path.getsize(self._path)
-        return self
+        return self._fin.read(size)
 
     async def close(self) -> None:
-        if self._fileobj is not None:
-            self._fileobj.close()
```

**CLAIM:** The `async def read` method performs a synchronous, blocking file read, which will block the event loop.

**PROPOSED FIX:** `The blocking `self._fin.read(size)` call should be executed in a thread pool to avoid blocking the event loop.`

## 7

`dagster-io/dagster#34075` — `js_modules/ui-core/src/graph/OpTags.tsx:190`

```diff
@@ -187,6 +187,7 @@ import shell from './kindtag-images/tool-shell-color.svg';
 import shopify from './kindtag-images/tool-shopify-color.svg';
 import slack from './kindtag-images/tool-slack-color.svg';
 import sling from './kindtag-images/tool-sling-color.svg';
+import slurm from './kindtag-images/tool-slurm-color.png';
 import snowflake from './kindtag-images/tool-snowflake-color.svg';
 import soda from './kindtag-images/tool-soda-color.svg';
 import spanner from './kindtag-images/tool-spanner-color.svg';
@@ -446,6 +447,7 @@ export type KnownTagType =
```

**CLAIM:** This imports a PNG file for an icon, but all other icons in this context are SVGs, which are preferred for scalability and rendering quality.

**PROPOSED FIX:** `import slurm from './kindtag-images/tool-slurm-color.svg';`

## 8

`encode/httpx#3672` — `src/ahttpx/_server.py:54`

```diff
                         await self._send_head(response)
                         await self._send_body(response)
+                if self._parser.is_keepalive():
+                    await stream.read()
+                await self._reset()
         except Exception:
             logger.error("Internal Server Error", exc_info=True)
 
@@ -88,8 +91,8 @@ async def _send_body(self, response: Response):
```

**CLAIM:** The `_reset` coroutine is explicitly awaited at the end of the request handling loop, but it is also passed as a callback to `HTTPStream` which is expected to be called when the request stream is closed, leading to `_reset` being called twice.

**PROPOSED FIX:** `pass`

## 9

`encode/httpx#3730` — `.github/workflows/test-suite.yml:17`

```diff
 
     strategy:
       matrix:
-        python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]
+        python-version: ["3.11", "3.12", "3.13", "3.14"]
 
     steps:
       - uses: "actions/checkout@v4"

```

**CLAIM:** The test matrix includes Python 3.14, which is a non-existent version and will cause the corresponding CI job to fail.

**PROPOSED FIX:** `python-version: ["3.11", "3.12", "3.13"]`

## 10

`encode/httpx#3690` — `src/ahttpx/_parsers.py:469`

```diff
+        Attempt a read, and return True if read succeeds or False if the
+        stream is closed. The data remains in the read buffer.
+        """
+        data = await self._read_some()
+        self._push_back(data)
+        return data != b''
+
     async def read(self, size: int) -> bytes:
         """
```

**CLAIM:** This call will fail with an assertion or cause data loss if the buffer was not empty, because it overwrites the buffer instead of prepending the newly read data.

**PROPOSED FIX:** `self._buffer = data + self._buffer`

## 11

`dbt-labs/dbt-core#15944` — `.github/actions/setup-postgres-linux/action.yml:14`

```diff
+        # Newer Ubuntu runner images restrict other-user traversal of
+        # /home/runner, so the postgres system user can no longer read a
+        # script path under $HOME directly. Read it as the runner user and
+        # pass the contents in instead.
+        sudo -u postgres bash -c "$(cat ${{ github.action_path }}/setup_db.sh)"
diff --git a/.github/actions/setup-postgres-macos/action.yml b/.github/actions/setup-postgres-macos/action.yml
index af9a9fe1657..f74e2c5d288 100644
--- a/.github/actions/setup-postgres-macos/action.yml
+++ b/.github/actions/setup-postgres-macos/action.yml
```

**CLAIM:** This command is not robust because it will fail if the script `setup_db.sh` contains certain shell metacharacters like double quotes, which would break the `bash -c "..."` command string.

**PROPOSED FIX:** `cat ${{ github.action_path }}/setup_db.sh | sudo -u postgres bash -s`

## 12

`encode/httpx#3677` — `.github/workflows/publish.yml:18`

```diff
 
     steps:
       - uses: "actions/checkout@v4"
-      - uses: "actions/setup-python@v5"
+      - uses: "actions/setup-python@v6"
         with:
           python-version: 3.9
       - name: "Install dependencies"
diff --git a/.github/workflows/test-suite.yml b/.github/workflows/test-suite.yml
```

**CLAIM:** This step uses the `allow-prereleases` input, which is an API contract violation as it was removed in v6 of the `actions/setup-python` action.

**PROPOSED FIX:** `      - uses: "actions/setup-python@v5"`

## 13

`huggingface/datasets#8369` — `.github/workflows/ci.yml:66`

```diff
           python-version: "3.10"
       - name: Setup FFmpeg (windows)
         if: ${{ matrix.os == 'windows-latest' }}
-        run: conda install "ffmpeg=7.0.1" -c conda-forge
+        run: conda install "ffmpeg=6.1.1"
       - name: Upgrade pip
         run: python -m pip install --upgrade pip
       - name: Install uv
@@ -114,7 +114,7 @@ jobs:
```

**CLAIM:** The conda install command is missing the `-c conda-forge` channel specification, which makes the package installation dependent on the default channel configuration and potentially brittle.

**PROPOSED FIX:** `run: conda install "ffmpeg=6.1.1" -c conda-forge`

## 14

`huggingface/datasets#8360` — `src/datasets/iterable_dataset.py:3715`

```diff
             ex_iterable = FormattedExamplesIterable(
                 ex_iterable,
                 formatting=self._formatting,
-                features=ex_iterable.features if ex_iterable.is_typed else self._info.features,
+                features=self._ex_iterable.features if self._ex_iterable.is_typed else self._info.features,
                 token_per_repo_id=self._token_per_repo_id,
             )
 
diff --git a/tests/test_iterable_dataset.py b/tests/test_iterable_dataset.py
```

**CLAIM:** The `FormattedExamplesIterable` is configured with features from the original `self._ex_iterable`, but it wraps the `ex_iterable` variable which may have been transformed; it should be configured using the features of the iterable it directly wraps to prevent a potential feature mismatch.

**PROPOSED FIX:** `                features=ex_iterable.features if ex_iterable.is_typed else self._info.features,`

## 15

`dbt-labs/dbt-core#15950` — `core/dbt/jsonschemas/resources/latest.json:1450`

```diff
-            {
-              "$ref": "#/definitions/IndexesConfig"
-            }
-          ]
+          "$ref": "#/definitions/IndexesConfig"
         },
         "initialize": {
           "type": [
@@ -1712,12 +1707,7 @@
```

**CLAIM:** The change removes the `"default": null` annotation for the `indexes` property, which is a loss of information about the property's default value and a potential breaking change for schema consumers.

**PROPOSED FIX:** `          "default": null,
          "allOf": [
            {
              "$ref": "#/definitions/IndexesConfig"
            }
          ]`

## 16

`encode/httpx#3672` — `src/httpx/_network.py:194`

```diff
+            self._streams = [
+                stream for stream in self._streams
+                if not stream.is_closed()
+            ]
+            self._streams.append(stream)
 
     def _handler(self, stream):
         try:
diff --git a/src/httpx/_parsers.py b/src/httpx/_parsers.py
```

**CLAIM:** The list of active streams is only pruned of closed streams when a new connection is accepted, which can lead to a memory leak of stream objects if the server experiences a burst of traffic followed by a period of inactivity.

**PROPOSED FIX:** `with self._streams_lock: self._streams.append(stream)`

## 17

`huggingface/datasets#8369` — `.github/workflows/ci.yml:66`

```diff
           python-version: "3.10"
       - name: Setup FFmpeg (windows)
         if: ${{ matrix.os == 'windows-latest' }}
-        run: conda install "ffmpeg=7.0.1" -c conda-forge
+        run: conda install "ffmpeg=6.1.1"
       - name: Upgrade pip
         run: python -m pip install --upgrade pip
       - name: Install uv
@@ -114,7 +114,7 @@ jobs:
```

**CLAIM:** The conda install command is missing the `-c conda-forge` channel specification, which makes the package installation dependent on the default channel configuration and potentially brittle.

**PROPOSED FIX:** `run: conda install "ffmpeg=6.1.1" -c conda-forge`

## 18

`bokeh/bokeh#15352` — `conda/environment-test-3.14t.yml:86`

```diff
+    # tests
+    - pandas-stubs >=2.2
+    - playwright
+    - pytest-playwright
+    - ruff ==0.15.*
+    - types-boto3
+    - types-docutils
+    - types-colorama
+    - types-mock
```

**CLAIM:** The version specifier '==0.15.*' for ruff is invalid because no version of ruff matching this prefix has ever been released, which will cause the dependency installation to fail.

**PROPOSED FIX:** `    - ruff ==0.4.*`

## 19

`bokeh/bokeh#15342` — `tests/integration/server_proxy/test_proxy.py:183`

```diff
+            marker = page.locator("#proxy-request")
+            marker.wait_for(state="visible", timeout=15_000)
+            assert marker.text_content() == "Bokeh reverse proxy ready"
+            assert marker.get_attribute("data-host") == "127.0.0.1:8080"
+            assert marker.get_attribute("data-root-path") == ""
+            assert page.evaluate("Bokeh.documents.length") == 1
+
+            # No application messages cross the websocket while idle, so the
+            # backend's keepalive traffic must keep it open past the proxy timeout.
```

**CLAIM:** The test matrix includes Python 3.14, which is a non-existent version and will cause the corresponding CI job to fail.

**PROPOSED FIX:** `assert marker.get_attribute("data-root-path") == ("/services/bokeh" if FRONTEND == "asgi" else "")`

## 20

`huggingface/datasets#8363` — `tests/features/test_array_xd.py:407`

```diff
+    # None, not cast the whole column to float to make room for np.nan.
+    features = datasets.Features({"foo": datasets.Array2D(dtype="int64", shape=(1, 2))})
+    dataset = datasets.Dataset.from_dict({"foo": [[[10, 20]], [[30, 40]], None]}, features=features)
+    assert dataset.to_dict()["foo"] == [[[10, 20]], [[30, 40]], None]
+    assert all(isinstance(v, int) for row in (dataset[0]["foo"], dataset[1]["foo"]) for v in row[0])
+
+    # Integers above 2**53 are not representable as float64, so the old float cast
+    # silently altered them; the python path must round-trip them exactly.
+    big = 9007199254740993  # 2**53 + 1
```

**CLAIM:** The list comprehension incorrectly assumes each 2D array element has only one row, as `for v in row[0]` only iterates over the first row, failing to check all values in an array with more than one row.

**PROPOSED FIX:** `assert all(isinstance(v, int) for item in (dataset[0]["foo"], dataset[1]["foo"]) for row in item for v in row)`

## 21

`encode/httpx#3670` — `src/ahttpx/_streams.py:190`

```diff
+        elif self._files_progress and self._fin is None:
             # return start of a file item
             key, value = self._files_progress.pop(0)
-            self._filestream = await FileStream(value).open()
+            self._fin = open(value, 'rb')
             name = key.translate({10: "%0A", 13: "%0D", 34: "%22"})
             filename = os.path.basename(value)
             return (
@@ -207,15 +195,15 @@ async def _read_next_section(self) -> bytes:
```

**CLAIM:** A synchronous, blocking `open()` call is used inside an `async` method, which will block the event loop.

**PROPOSED FIX:** `The blocking `open(value, 'rb')` call should be executed in a thread pool to avoid blocking the event loop.`

## 22

`bokeh/bokeh#15344` — `bokehjs/src/lib/models/widgets/tables/table_column.ts:68`

```diff
+    this.title_view = undefined
+
+    const {title} = this.model
+    if (title instanceof HTML) {
+      this.title_view = await build_view(title, {parent: this.parent})
+      this.title_view.render()
+    }
+  }
+
```

**CLAIM:** The created `title_view` is assigned a parent that is the grandparent view, but is then listed as a direct child of the current view, violating the parent-child view hierarchy contract.

**PROPOSED FIX:** `      this.title_view = await build_view(title, {parent: this})`

## 23

`encode/httpx#3670` — `src/ahttpx/_streams.py:87`

```diff
 
     async def close(self) -> None:
-        if self._fileobj is not None:
-            self._fileobj.close()
+        self._fin.close()
 
     @property
     def size(self) -> int | None:
-        return self._size
```

**CLAIM:** The `async def close` method performs a synchronous, blocking file close operation, which will block the event loop.

**PROPOSED FIX:** `The blocking `self._fin.close()` call should be executed in a thread pool to avoid blocking the event loop.`

## 24

`bokeh/bokeh#15346` — `tests/unit/bokeh/models/test_plots.py:441`

```diff
@@ -437,6 +438,7 @@ def test_add_tile(test_input, provider):
         plot2.add_tile(test_input, retina=True)
         tile_source2 = plot2.renderers[0].tile_source
         assert tile_source2.url == provider.build_url(scale_factor="@2x")
+        assert tile_source2.pixel_ratio == 2
 
 def test_add_tile_tilesource():
     mapnik = xyz.OpenStreetMap.Mapnik

```

**CLAIM:** This test assertion is incorrect because it assumes `pixel_ratio` will be 2 for any provider when `retina=True`, but the implementation correctly sets it to 1 if the provider does not support retina tiles.

**PROPOSED FIX:** `        assert tile_source2.pixel_ratio == (2 if "{r}" in provider.url else 1)`

## 25

`encode/httpx#3690` — `src/ahttpx/_parsers.py:469`

```diff
+        Attempt a read, and return True if read succeeds or False if the
+        stream is closed. The data remains in the read buffer.
+        """
+        data = await self._read_some()
+        self._push_back(data)
+        return data != b''
+
     async def read(self, size: int) -> bytes:
         """
```

**CLAIM:** This call will fail with an assertion or cause data loss if the buffer was not empty, because it overwrites the buffer instead of prepending the newly read data.

**PROPOSED FIX:** `self._buffer = data + self._buffer`

## 26

`bokeh/bokeh#15352` — `conda/environment-test-3.14t.yml:77`

```diff
+    # docs
+    - bokeh_sampledata
+    - pydata_sphinx_theme
+    - requests-unixsocket >= 0.3.0
+    - sphinx ==9.*
+    - sphinx-copybutton
+    - sphinx-design
+    - sphinx-favicon
+    - sphinxext-opengraph >= 0.11.0
```

**CLAIM:** The version specifier '==9.*' for Sphinx is invalid because no version of Sphinx matching this prefix has been released, which will cause the dependency installation to fail.

**PROPOSED FIX:** `    - sphinx ==7.*`

## 27

`encode/httpx#3690` — `src/ahttpx/_parsers.py:470`

```diff
+        stream is closed. The data remains in the read buffer.
+        """
+        data = await self._read_some()
+        self._push_back(data)
+        return data != b''
+
     async def read(self, size: int) -> bytes:
         """
         Read and return up to 'size' bytes from the stream, with I/O buffering provided.
```

**CLAIM:** This incorrectly signals that no data is ready if the read operation returned no new data, even if data was already present in the buffer.

**PROPOSED FIX:** `return bool(self._buffer)`

## 28

`bokeh/bokeh#15348` — `bokehjs/test/unit/document/document.ts:748`

```diff
+    expect(doc.roots().length).to.be.equal(1)
+    const [root] = doc.roots()
+    expect_instanceof(root, ColumnDataSource)
+    expect(root.data.values).to.be.instanceof(Float64NDArray)
+    expect(root.data.values).to.be.equal(values)
+  })
+
   it("can serialize excluding defaults", () => {
     const d = new Document()
```

**CLAIM:** When parsing the `splits` from YAML fails, the malformed data is not ignored but is passed to the `DatasetInfo` constructor, which will likely cause a crash or incorrect behavior.

**PROPOSED FIX:** `    expect(root.data.values).to.deep.equal(values)`

## 29

`bokeh/bokeh#15353` — `bokehjs/test/unit/document/document.ts:748`

```diff
+    expect(doc.roots().length).to.be.equal(1)
+    const [root] = doc.roots()
+    expect_instanceof(root, ColumnDataSource)
+    expect(root.data.values).to.be.instanceof(Float64NDArray)
+    expect(root.data.values).to.be.equal(values)
+  })
+
   it("can serialize excluding defaults", () => {
     const d = new Document()
```

**CLAIM:** This assertion incorrectly compares a `Float64NDArray` instance with a `Float64Array` instance, which will always fail because they are instances of different classes.

**PROPOSED FIX:** `expect([...root.data.values]).to.deep.equal([...values])`

## 30

`huggingface/datasets#8355` — `src/datasets/packaged_modules/hdf5/hdf5.py:392`

```diff
+def _safe_open_h5py(file, mode):
+    """Open an HDF5 file, rejecting any external file references."""
+    import h5py
+
+    f = h5py.File(file, mode)
+
+    def _check_obj(name, obj):
+        if isinstance(obj, h5py.Dataset):
+            # Check for external file references (HDF5 external storage)
```

**CLAIM:** The version specifier '>=1.20' for mypy is invalid because mypy does not use this versioning scheme and no such version exists, which will cause the dependency installation to fail.

**PROPOSED FIX:** `if any(c in mode for c in "wax"): raise ValueError(f"Write mode '{mode}' is not supported."); f = h5py.File(file, mode)`

## 31

`bokeh/bokeh#15348` — `bokehjs/test/unit/document/document.ts:748`

```diff
+    expect(doc.roots().length).to.be.equal(1)
+    const [root] = doc.roots()
+    expect_instanceof(root, ColumnDataSource)
+    expect(root.data.values).to.be.instanceof(Float64NDArray)
+    expect(root.data.values).to.be.equal(values)
+  })
+
   it("can serialize excluding defaults", () => {
     const d = new Document()
```

**CLAIM:** This assertion incorrectly uses strict equality to compare a `Float64NDArray` instance to a `Float64Array`, which will always fail because they are different objects.

**PROPOSED FIX:** `    expect(root.data.values).to.deep.equal(values)`

## 32

`bokeh/bokeh#15337` — `tests/tools/backport/test_interactive.py:133`

```diff
+                    outcome = interactive.run_plan_session(MagicMock(), state, checkpoint)
+
+                self.assertEqual(outcome, expected)
+
+        checkpoint.assert_called_once()
+
+    def test_reports_an_action_error_and_keeps_prompting(self) -> None:
+        item = candidate(15233, status="review", backport_sha="a" * 40)
+        state = state_with([item])
```

**CLAIM:** The `checkpoint` mock is called within a loop that runs twice, so this assertion will fail because the mock is called twice in total.

**PROPOSED FIX:** `self.assertEqual(checkpoint.call_count, 2)`

## 33

`streamlit/streamlit#16522` — `.github/workflows/update-python-lock.yml:40`

```diff
           persist-credentials: true
 
       - name: Set up uv
-        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0
+        uses: astral-sh/setup-uv@ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d # v10.0.0
         with:
           enable-cache: true
 

```

**CLAIM:** The specified commit hash `ae62891fec2bb8e7d6c99fc78c9fec3a63790f8d` does not exist in the `astral-sh/setup-uv` repository, which will cause this workflow step to fail.

**PROPOSED FIX:** `uses: astral-sh/setup-uv@v0.2.1`

## 34

`encode/httpx#3673` — `src/ahttpx/_pool.py:240`

```diff
-    async def _complete(self) -> None:
-        await self._parser.complete()
+    # Request/response cycle reset...
+    async def _reset(self) -> None:
+        await self._parser.reset()
         self._idle_expiry = time.monotonic() + self._keepalive_duration
 
     async def _close(self) -> None:
diff --git a/src/ahttpx/_server.py b/src/ahttpx/_server.py
```

**CLAIM:** The boolean return value from `self._parser.reset()` is ignored, causing `_idle_expiry` to be updated even if the parser has closed the connection.

**PROPOSED FIX:** `if not await self._parser.reset():
            return`

## 35

`huggingface/datasets#8369` — `.github/workflows/ci.yml:66`

```diff
           python-version: "3.10"
       - name: Setup FFmpeg (windows)
         if: ${{ matrix.os == 'windows-latest' }}
-        run: conda install "ffmpeg=7.0.1" -c conda-forge
+        run: conda install "ffmpeg=6.1.1"
       - name: Upgrade pip
         run: python -m pip install --upgrade pip
       - name: Install uv
@@ -114,7 +114,7 @@ jobs:
```

**CLAIM:** The conda install command is missing the `-c conda-forge` channel specification, which makes the package installation dependent on the default channel configuration and potentially brittle.

**PROPOSED FIX:** `run: conda install "ffmpeg=6.1.1" -c conda-forge`

## 36

`encode/httpx#3673` — `src/httpx/_network.py:190`

```diff
 
     def _serve(self):
         while stream := self.listener.accept():
             self._executor.submit(self._handler, stream)
+            self._streams = [
+                stream for stream in self._streams
+                if not stream.is_closed()
+            ]
+            self._streams.append(stream)
```

**CLAIM:** Rebuilding the list of streams on every new connection is an O(N) operation, where N is the number of past connections, causing a memory leak and performance degradation.

**PROPOSED FIX:** `# This approach is not scalable and should be replaced with a thread-safe collection that active streams are added to and removed from.`

## 37

`bokeh/bokeh#15327` — `bokehjs/test/integration/regressions.ts:5341`

```diff
+      const space_B = new Spacer()
+
+      const layout = new Row({children: [button, space_A, table]})
+      button.on_click(() => {
+        layout.children = [layout.children[0], space_B, layout.children[2]]
+      })
+
+      const {view} = await display(layout, [700, 450])
+      const button_view = view.owner.get_one(button)
```

**CLAIM:** The logic for updating the children is brittle because it relies on hardcoded indices, making the test fragile to future changes in the layout's children.

**PROPOSED FIX:** `layout.children = [button, space_B, table]`

## 38

`huggingface/datasets#8355` — `src/datasets/packaged_modules/hdf5/hdf5.py:392`

```diff
+def _safe_open_h5py(file, mode):
+    """Open an HDF5 file, rejecting any external file references."""
+    import h5py
+
+    f = h5py.File(file, mode)
+
+    def _check_obj(name, obj):
+        if isinstance(obj, h5py.Dataset):
+            # Check for external file references (HDF5 external storage)
```

**CLAIM:** The function is unsafe when opening a file in a write-like mode, as the security scan on existing content is bypassed, allowing subsequent unsafe operations.

**PROPOSED FIX:** `if any(c in mode for c in "wax"): raise ValueError(f"Write mode '{mode}' is not supported."); f = h5py.File(file, mode)`

## 39

`bokeh/bokeh#15352` — `conda/environment-test-3.14t.yml:71`

```diff
+
+  # pip dependencies
+  - pip
+  - pip:
+    - mypy >=1.20
+    - pyright
+    # docs
+    - bokeh_sampledata
+    - pydata_sphinx_theme
```

**CLAIM:** The version specifier '>=1.20' for mypy is invalid because mypy does not use this versioning scheme and no such version exists, which will cause the dependency installation to fail.

**PROPOSED FIX:** `    - mypy >=1.10`

## 40

`dbt-labs/dbt-core#15965` — `core/dbt/utils/artifact_upload.py:78`

```diff
+def _format_error(result) -> str:
+    """Add the provider's error code, since the status code alone is rarely actionable."""
+    # Azure sets the code in a header; S3/GCS only in the XML body
+    code = result.headers.get("x-ms-error-code") or result.headers.get("x-amz-error-code")
+    if not code and isinstance(result.text, str):
+        match = _ERROR_CODE_PATTERN.search(result.text)
+        code = match.group(1) if match else None
+    return f"{result} {code}" if code else str(result)
+
```

**CLAIM:** This command incorrectly parses the minor version if the input version string is just a major version number (e.g., "1"), as the `sed` expression does not match and the original string is assigned to the variable, effectively treating "1" as "1.1".

**PROPOSED FIX:** `if code is None and isinstance(result.text, str):`

## 41

`dbt-labs/dbt-core#15935` — `.github/workflows/release.yml:107`

```diff
+          # is less than minor version 11.
+          INPUT_MAJOR=$(echo "${{ inputs.version_number }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\1/')
+          INPUT_MINOR=$(echo "${{ inputs.version_number }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')
+          HATCH_MAJOR=$(echo "${{ env.MIN_HATCH_VERSION }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\1/')
+          HATCH_MINOR=$(echo "${{ env.MIN_HATCH_VERSION }}" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')
+
+          if [ "$INPUT_MAJOR" -gt "$HATCH_MAJOR" ] || { [ "$INPUT_MAJOR" -eq "$HATCH_MAJOR" ] && [ "$INPUT_MINOR" -ge "$HATCH_MINOR" ]; }; then
             echo "use_hatch=true" >> $GITHUB_OUTPUT
           else
```

**CLAIM:** This command incorrectly parses the minor version if the input version string is just a major version number (e.g., "1"), as the `sed` expression does not match and the original string is assigned to the variable, effectively treating "1" as "1.1".

**PROPOSED FIX:** `HATCH_MINOR=$(echo "${{ env.MIN_HATCH_VERSION }}.0" | sed -E 's/^([0-9]+)\.([0-9]+).*/\2/')`

## 42

`dbt-labs/dbt-core#15965` — `core/dbt/utils/artifact_upload.py:77`

```diff
+
+def _format_error(result) -> str:
+    """Add the provider's error code, since the status code alone is rarely actionable."""
+    # Azure sets the code in a header; S3/GCS only in the XML body
+    code = result.headers.get("x-ms-error-code") or result.headers.get("x-amz-error-code")
+    if not code and isinstance(result.text, str):
+        match = _ERROR_CODE_PATTERN.search(result.text)
+        code = match.group(1) if match else None
+    return f"{result} {code}" if code else str(result)
```

**CLAIM:** This logic incorrectly uses the `x-amz-error-code` if the `x-ms-error-code` header is present but has an empty string value, rather than correctly prioritizing the `x-ms-error-code` header.

**PROPOSED FIX:** `code = result.headers.get("x-ms-error-code") if "x-ms-error-code" in result.headers else result.headers.get("x-amz-error-code")`

## 43

`encode/httpx#3672` — `src/ahttpx/_server.py:54`

```diff
                         await self._send_head(response)
                         await self._send_body(response)
+                if self._parser.is_keepalive():
+                    await stream.read()
+                await self._reset()
         except Exception:
             logger.error("Internal Server Error", exc_info=True)
 
@@ -88,8 +91,8 @@ async def _send_body(self, response: Response):
```

**CLAIM:** The `_reset` method is explicitly called at the end of the request handling loop, but it is also passed as a callback to `HTTPStream` which is expected to be called when the request stream is closed, leading to `_reset` being called twice.

**PROPOSED FIX:** `pass`

## 44

`huggingface/datasets#8363` — `tests/features/test_array_xd.py:407`

```diff
+    # None, not cast the whole column to float to make room for np.nan.
+    features = datasets.Features({"foo": datasets.Array2D(dtype="int64", shape=(1, 2))})
+    dataset = datasets.Dataset.from_dict({"foo": [[[10, 20]], [[30, 40]], None]}, features=features)
+    assert dataset.to_dict()["foo"] == [[[10, 20]], [[30, 40]], None]
+    assert all(isinstance(v, int) for row in (dataset[0]["foo"], dataset[1]["foo"]) for v in row[0])
+
+    # Integers above 2**53 are not representable as float64, so the old float cast
+    # silently altered them; the python path must round-trip them exactly.
+    big = 9007199254740993  # 2**53 + 1
```

**CLAIM:** The conda install command is missing the `-c conda-forge` channel specification, which makes the package installation dependent on the default channel configuration and potentially brittle.

**PROPOSED FIX:** `assert all(isinstance(v, int) for item in (dataset[0]["foo"], dataset[1]["foo"]) for row in item for v in row)`

## 45

`huggingface/datasets#8356` — `src/datasets/builder.py:362`

```diff
+        # Ensure files are in the repo
+        if repo_id is not None and self.config.data_files is not None:
+            for split in self.config.data_files:
+                for data_file in self.config.data_files[split]:
+                    if not posixpath.relpath(data_file, start="hf://").startswith(f"datasets/{repo_id}@"):
+                        raise ValueError(
+                            f"Data files don't belong to {repo_id}. "
+                            "Make sure the dataset `data_files` (e.g. in the config README.md) are valid. "
+                            "They should be relative paths to the dataset repository root."
```

**CLAIM:** This check incorrectly rejects valid relative file paths because `posixpath.relpath` with a `start` argument of `hf://` produces a path with `..` components for any input that is not a `hf://` URI, causing the `startswith` check to fail.

**PROPOSED FIX:** `if data_file.startswith("hf://") and not data_file.removeprefix("hf://").startswith(f"datasets/{repo_id}@"):`

## 46

`huggingface/datasets#8462` — `src/datasets/info.py:322`

```diff
-            yaml_data["splits"] = SplitDict._from_yaml_list(yaml_data["splits"])
+            try:
+                yaml_data["splits"] = SplitDict._from_yaml_list(yaml_data["splits"])
+            except ValueError as e:
+                logger.warning(f"Ignoring part of dataset_info from the dataset card: {e}")
         field_names = {f.name for f in dataclasses.fields(cls)}
         return cls(**{k: v for k, v in yaml_data.items() if k in field_names})
 
diff --git a/src/datasets/load.py b/src/datasets/load.py
```

**CLAIM:** When parsing the `splits` from YAML fails, the malformed data is not ignored but is passed to the `DatasetInfo` constructor, which will likely cause a crash or incorrect behavior.

**PROPOSED FIX:** `logger.warning(f"Ignoring part of dataset_info from the dataset card: {e}")
                yaml_data["splits"] = None`

## 47

`dbt-labs/dbt-core#15950` — `core/dbt/jsonschemas/resources/latest.json:1710`

```diff
-            {
-              "$ref": "#/definitions/PrimaryKeyConfig"
-            }
-          ]
+          "$ref": "#/definitions/PrimaryKeyConfig"
         },
         "query_settings": {
           "type": [
@@ -3725,12 +3715,7 @@
```

**CLAIM:** The change removes the `"default": null` annotation for the `primary_key` property, which is a loss of information about the property's default value and a potential breaking change for schema consumers.

**PROPOSED FIX:** `          "default": null,
          "allOf": [
            {
              "$ref": "#/definitions/PrimaryKeyConfig"
            }
          ]`

## 48

`encode/httpx#3670` — `src/ahttpx/_streams.py:87`

```diff
 
     async def close(self) -> None:
-        if self._fileobj is not None:
-            self._fileobj.close()
+        self._fin.close()
 
     @property
     def size(self) -> int | None:
-        return self._size
```

**CLAIM:** The change removes the `"default": null` annotation for the `primary_key` property, which is a loss of information about the property's default value and a potential breaking change for schema consumers.

**PROPOSED FIX:** `The blocking `self._fin.close()` call should be executed in a thread pool to avoid blocking the event loop.`

## 49

`huggingface/datasets#8354` — `src/datasets/arrow_dataset.py:6995`

```diff
     if legacy_dataset_info:
         legacy_dataset_infos: dict = json.loads(fs.read_text(config.DATASETDICT_INFOS_FILENAME, encoding="utf-8"))
         legacy_dataset_infos[config_name] = asdict(info_to_dump)
-        new_legacy_dataset_infos = json.dumps(dataset_infos, indent=4)
+        new_legacy_dataset_infos = legacy_dataset_infos
     else:
         new_legacy_dataset_infos = None
     # push to README
diff --git a/src/datasets/iterable_dataset.py b/src/datasets/iterable_dataset.py
```

**CLAIM:** Returning a direct reference to a mutable dictionary can lead to unexpected mutations if the caller passes the returned object to multiple places.

**PROPOSED FIX:** `        new_legacy_dataset_infos = legacy_dataset_infos.copy()`

## 50

`encode/httpx#3690` — `src/ahttpx/_parsers.py:470`

```diff
+        stream is closed. The data remains in the read buffer.
+        """
+        data = await self._read_some()
+        self._push_back(data)
+        return data != b''
+
     async def read(self, size: int) -> bytes:
         """
         Read and return up to 'size' bytes from the stream, with I/O buffering provided.
```

**CLAIM:** This incorrectly signals that no data is ready if the read operation returned no new data, even if data was already present in the buffer.

**PROPOSED FIX:** `return bool(self._buffer)`

## 51

`bokeh/bokeh#15353` — `.github/workflows/bokeh-ci-full.yml:356`

```diff
+          test-env: '3.13'
+          source-tree: 'delete'
+
+      - name: Install ASGI example dependencies
+        run: python -m pip install 'uvicorn[standard]' hypercorn 'streamlit==1.57.*' fastapi starlette django
+
+      - name: Install Playwright browser
+        run: playwright install chromium
+
```

**CLAIM:** The version specifier 'streamlit==1.57.*' is invalid for pip and will cause the installation to fail.

**PROPOSED FIX:** `run: python -m pip install 'uvicorn[standard]' hypercorn 'streamlit~=1.57.0' fastapi starlette django`

## 52

`dbt-labs/dbt-core#15965` — `core/dbt/utils/artifact_upload.py:78`

```diff
+def _format_error(result) -> str:
+    """Add the provider's error code, since the status code alone is rarely actionable."""
+    # Azure sets the code in a header; S3/GCS only in the XML body
+    code = result.headers.get("x-ms-error-code") or result.headers.get("x-amz-error-code")
+    if not code and isinstance(result.text, str):
+        match = _ERROR_CODE_PATTERN.search(result.text)
+        code = match.group(1) if match else None
+    return f"{result} {code}" if code else str(result)
+
```

**CLAIM:** This condition incorrectly treats a present-but-empty error code from a header as "not found", causing it to fall back to parsing the response body.

**PROPOSED FIX:** `if code is None and isinstance(result.text, str):`

## 53

`dbt-labs/dbt-core#15964` — `core/dbt/utils/artifact_upload.py:77`

```diff
+
+def _format_error(result) -> str:
+    """Add the provider's error code, since the status code alone is rarely actionable."""
+    # Azure sets the code in a header; S3/GCS only in the XML body
+    code = result.headers.get("x-ms-error-code") or result.headers.get("x-amz-error-code")
+    if not code and isinstance(result.text, str):
+        match = _ERROR_CODE_PATTERN.search(result.text)
+        code = match.group(1) if match else None
+    return f"{result} {code}" if code else str(result)
```

**CLAIM:** The use of `or` for chaining `get` calls is incorrect because an empty string value for `x-ms-error-code` would be treated as false, causing the code to incorrectly fall back to `x-amz-error-code` or body parsing.

**PROPOSED FIX:** `code = result.headers.get("x-ms-error-code") if "x-ms-error-code" in result.headers else result.headers.get("x-amz-error-code")`

## 54

`dagster-io/dagster#34075` — `js_modules/ui-core/src/graph/OpTags.tsx:190`

```diff
@@ -187,6 +187,7 @@ import shell from './kindtag-images/tool-shell-color.svg';
 import shopify from './kindtag-images/tool-shopify-color.svg';
 import slack from './kindtag-images/tool-slack-color.svg';
 import sling from './kindtag-images/tool-sling-color.svg';
+import slurm from './kindtag-images/tool-slurm-color.png';
 import snowflake from './kindtag-images/tool-snowflake-color.svg';
 import soda from './kindtag-images/tool-soda-color.svg';
 import spanner from './kindtag-images/tool-spanner-color.svg';
@@ -446,6 +447,7 @@ export type KnownTagType =
```

**CLAIM:** The `_reset` coroutine is explicitly awaited at the end of the request handling loop, but it is also passed as a callback to `HTTPStream` which is expected to be called when the request stream is closed, leading to `_reset` being called twice.

**PROPOSED FIX:** `import slurm from './kindtag-images/tool-slurm-color.svg';`

## 55

`encode/httpx#3673` — `src/httpx/_network.py:183`

```diff
@@ -177,11 +180,18 @@ def __enter__(self):
 
     def __exit__(self, exc_type, exc_val, exc_tb):
         self.listener.close()
+        for stream in self._streams:
+            stream.close()
         self._executor.shutdown(wait=True)
 
     def _serve(self):
```

**CLAIM:** Closing streams from the main thread while worker threads may still be actively using them creates a race condition that can lead to I/O errors in the worker threads.

**PROPOSED FIX:** `self._executor.shutdown(wait=True)
for stream in self._streams:
    if not stream.is_closed():
        stream.close()`

## 56

`encode/httpx#3673` — `src/ahttpx/_pool.py:240`

```diff
-    async def _complete(self) -> None:
-        await self._parser.complete()
+    # Request/response cycle reset...
+    async def _reset(self) -> None:
+        await self._parser.reset()
         self._idle_expiry = time.monotonic() + self._keepalive_duration
 
     async def _close(self) -> None:
diff --git a/src/ahttpx/_server.py b/src/ahttpx/_server.py
```

**CLAIM:** The boolean return value from `self._parser.reset()` is ignored, causing `_idle_expiry` to be updated even if the parser has closed the connection.

**PROPOSED FIX:** `if not self._parser.reset():
    return`

## 57

`huggingface/datasets#8355` — `src/datasets/packaged_modules/hdf5/hdf5.py:413`

```diff
+                raise ValueError(
+                    f"Dataset '{obj.name}' uses unknown storage. Refused to open HDF5 file with unknown layout"
+                )
+
+    f.visititems(_check_obj)
+    return f

```

**CLAIM:** An exception raised during this call will cause a file handle leak because the h5py.File object is not closed on the error path.

**PROPOSED FIX:** `try:
        f.visititems(_check_obj)
    except:
        f.close()
        raise`
