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

`python-poetry/poetry#10954` — `src/poetry/repositories/http_repository.py:80`

```diff
         )
         self._authenticator.add_repository(name, url)
-        self.get_page = functools.lru_cache(maxsize=None)(self._get_page)
+        self.get_page = functools.cache(self._get_page)
+        self._find_packages = functools.cache(self._find_packages_uncached)  # type: ignore[method-assign]
 
         self._lazy_wheel = config.get("solver.lazy-wheel", True)
         self._max_retries = config.get("requests.max-retries", 0)
@@ -178,7 +179,7 @@ def _is_version_too_recent(self, links: Iterable[Link]) -> bool:
```

**CLAIM:** Overwriting `self._find_packages` in the initializer breaks inheritance, as any subclass that overrides the original `_find_packages` method will have its implementation silently replaced by the base class's cached implementation.

**PROPOSED FIX:** `self._find_packages_cached = functools.cache(self._find_packages_uncached)  # type: ignore[method-assign]`

## 47

`explosion/spaCy#13510` — `spacy/lang/bo/lex_attrs.py:10`

```diff
+    "ཀླད་ཀོར་",
+    "གཅིག་", "གཉིས་", "གསུམ་", "བཞི་", "ལྔ་", "དྲུག་", "བདུན་", "བརྒྱད་", "དགུ་", "བཅུ་",
+    "བཅུ་གཅིག་", "བཅུ་གཉིས་", "བཅུ་གསུམ་", "བཅུ་བཞི་", "བཅུ་ལྔ་", "བཅུ་དྲུག་", "བཅུ་བདུན་", "བཅུ་པརྒྱད", "བཅུ་དགུ་", "ཉི་ཤུ་",
+    "སུམ་ཅུ", "བཞི་བཅུ", "ལྔ་བཅུ", "དྲུག་ཅུ", "བདུན་ཅུ", "བརྒྱད་ཅུ", "དགུ་བཅུ", "བརྒྱ་",
+    "སྟོང་", "ཁྲི་", "ས་ཡ་", "	བྱེ་བ་", "དུང་ཕྱུར་", "ཐེར་འབུམ་", "ཐེར་འབུམ་ཆེན་པོ་", "ཁྲག་ཁྲིག་", "ཁྲག་ཁྲིག་ཆེན་པོ་",
+]
+
+
+def like_num(text):
```

**CLAIM:** The number word "བྱེ་བ་" is preceded by a tab character, which will prevent it from being matched correctly.

**PROPOSED FIX:** `    "སྟོང་", "ཁྲི་", "ས་ཡ་", "བྱེ་བ་", "དུང་ཕྱུར་", "ཐེར་འབུམ་", "ཐེར་འབུམ་ཆེན་པོ་", "ཁྲག་ཁྲིག་", "ཁྲག་ཁྲིག་ཆེན་པོ་",`

## 48

`pylint-dev/pylint#11305` — `tests/functional/u/unspecified_encoding_py38.py:205`

```diff
+    open(FILENAME, mode)
+    open(FILENAME, mode=mode)
+    Path(FILENAME).open(mode)
+    Path(FILENAME).open(mode=mode)
+    open(FILENAME, mode, encoding=None)

```

**CLAIM:** This test case is ineffective because it provides an `encoding` argument, which already prevents the `unspecified-encoding` warning, making the check for an unknown `mode` irrelevant.

**PROPOSED FIX:** `    open(FILENAME, mode, None)`

## 49

`explosion/spaCy#13514` — `website/meta/universe.json:4565`

```diff
+            "code_example": [
+                "import spacy",
+                "import quelquhui",
+                "nlp = spacy.load('fr_core_news_lg')",
+                "nlp.tokenizer = quelquhui.Toquenizer(nlp.vocab)"
+            ],
+            "code_language": "python",
+            "author": "thjbdvlt",
+            "author_links": {
```

**CLAIM:** The class `Toquenizer` is misspelled and should be `Tokenizer`, causing the example code to fail.

**PROPOSED FIX:** `"nlp.tokenizer = quelquhui.Tokenizer(nlp.vocab)"`

## 50

`python-poetry/poetry#10909` — `src/poetry/console/commands/init.py:535`

```diff
+
+        try:
+            parse_constraint(constraint)
+        except ValueError as e:
+            raise ValueError(f"Invalid version constraint: {constraint}") from e
+
+        return constraint
+
     def _get_pool(self) -> RepositoryPool:
```

**CLAIM:** The raised `ValueError` discards the original error message from the caught exception, providing a less specific error message to the user than is available.

**PROPOSED FIX:** `raise ValueError(f"Invalid version constraint '{constraint}': {e}") from e`

## 51

`urllib3/urllib3#5093` — `src/urllib3/connection.py:932`

```diff
+            ssl_minimum_version = None
+            ssl_maximum_version = None
+        else:
+            # Otherwise we inherit the pool's cert policies
+            ssl_context = self.ssl_context if self.proxy_is_forwarding else None
+            cert_reqs = self.cert_reqs
+            ca_certs = self.ca_certs
+            ca_cert_dir = self.ca_cert_dir
+            ca_cert_data = self.ca_cert_data
```

**CLAIM:** This line incorrectly prevents the use of a pool-supplied `ssl_context` for tunneling proxies by setting it to `None` when `self.proxy_is_forwarding` is false.

**PROPOSED FIX:** `            ssl_context = self.ssl_context`

## 52

`python-poetry/poetry#10926` — `tests/utils/test_helpers.py:155`

```diff
+
+    downloader = Downloader(url, dest)
+
+    assert downloader.total_size == 0
+    assert list(downloader.download_with_progress(chunk_size=2)) == [2, 4]
+    assert dest.read_bytes() == b"demo"
+
+
 def test_download_file_recover_from_error(
```

**CLAIM:** The test assertion is incorrect because it expects progress values of `[2, 4]` for a 4-byte download, but the generator yields the chunk size, not the cumulative total.

**PROPOSED FIX:** `    assert list(downloader.download_with_progress(chunk_size=2)) == [2, 2]`

## 53

`urllib3/urllib3#4970` — `src/urllib3/poolmanager.py:547`

```diff
         proxy = urllib3.ProxyManager("https://localhost:3128/")
 
-        resp1 = proxy.request("GET", "https://google.com/")
-        resp2 = proxy.request("GET", "https://httpbin.org/")
+        resp1 = proxy.request("GET", "http://google.com/")
+        resp2 = proxy.request("GET", "http://httpbin.org/")
 
+        # One pool was shared by both plain HTTP requests.
         print(len(proxy.pools))
```

**CLAIM:** The request to `http://google.com/` redirects to HTTPS, which causes an extra connection pool to be created for the tunneled connection, making the example's subsequent pool count of 1 incorrect.

**PROPOSED FIX:** `resp1 = proxy.request("GET", "http://example.com/")`

## 54

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:434`

```diff
+        torch.float32: 3.74e13,
+        "tfloat32": 7.48e13,
+        torch.bfloat16: 1.497e14,
+        torch.float16: 1.497e14,
+        torch.int8: 2.993e14,
+        "int4": 5.987e14,
     },
     # source: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a10/pdf/a10-datasheet.pdf
     "a10g": {
```

**CLAIM:** The int8 FLOPs for the A40 GPU is the sparse value, but it should be the dense value to be consistent with the new `using_sparse_model` flag.

**PROPOSED FIX:** `torch.int8: 1.4965e14,`

## 55

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:373`

```diff
-        "int4": 1321.2e12,
+        torch.float32: 8.26e13,
+        "tfloat32": 8.26e13,
+        torch.bfloat16: 8.26e13,
+        torch.float16: 8.26e13,
+        torch.int8: 6.606e14,
+        "int4": 1.3212e15,
     },
     "rtx 4080": {
```

**CLAIM:** The float16 FLOPs for the RTX 4090 is incorrectly set to the FP32 rate, but it should be the much higher dense Tensor Core rate.

**PROPOSED FIX:** `torch.float16: 3.305e14,`

## 56

`Lightning-AI/pytorch-lightning#21701` — `src/lightning_fabric/__setup__.py:51`

```diff
+        req_str_clean = req_str.split("#")[0].strip()
+        if not req_str_clean:  # Skip empty lines
+            continue
+        req = Requirement(req_str_clean)
+        extras[req.name.lower().replace("-", "_")] = [req_str]
     extras["all"] = extras["extra"] + extras["strategies"] + extras["examples"]
     extras["dev"] = extras["all"] + extras["test"]
     return extras
diff --git a/src/pytorch_lightning/__setup__.py b/src/pytorch_lightning/__setup__.py
```

**CLAIM:** The code assumes the "filename" key is always present in the file dictionary, which will cause a KeyError if the JSON source is not compliant with PEP 691.

**PROPOSED FIX:** `        extras[req.name.lower().replace("-", "_")] = [str(req)]`

## 57

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:425`

```diff
+        torch.float32: 3.87e13,
+        "tfloat32": 7.74e13,
+        torch.bfloat16: 3.87e13,
+        torch.float16: 3.87e13,
+        torch.int8: 3.097e14,
+        "int4": 6.193e14,
     },
+    # source: https://images.nvidia.com/content/Solutions/data-center/a40/nvidia-a40-datasheet.pdf
     "a40": {
```

**CLAIM:** The int8 FLOPs for the A6000 GPU is the sparse value, but it should be the dense value to be consistent with the new `using_sparse_model` flag.

**PROPOSED FIX:** `torch.int8: 1.5485e14,`

## 58

`python-poetry/poetry#10987` — `src/poetry/puzzle/provider.py:588`

```diff
@@ -571,6 +585,8 @@ def complete_package(
                         stack += sorted(extra_dependency.extras)
                     else:
                         optional_dependencies.add(extra_dependency.name)
+                        if is_direct_origin and extra not in requires_extras:
+                            requires.append(extra_dependency)
 
             # If some extras/features were required, we need to add a special dependency
             # representing the base package to the current package.
```

**CLAIM:** This condition is incorrect because it prevents adding a missing optional dependency if another dependency for the same extra is already present, as it checks for the presence of the extra group as a whole rather than the specific dependency.

**PROPOSED FIX:** `                        if is_direct_origin and extra_dependency not in requires:`

## 59

`python-poetry/poetry#10959` — `src/poetry/utils/authenticator.py:330`

```diff
+
+        # No configured repository matches: fall back to a keyring lookup by
+        # the request url and netloc.
+        parsed_url = urllib.parse.urlsplit(url)
+        credential = self._password_manager.get_credential(url, parsed_url.netloc)
 
-        return credential
+        return HTTPAuthCredential(
+            username=credential.username, password=credential.password
```

**CLAIM:** The full request `url` is passed as the service name for the keyring lookup, but this is not a meaningful service name and the lookup should use the `netloc` instead, as is done for git URLs in the function below.

**PROPOSED FIX:** `credential = self._password_manager.get_credential(parsed_url.netloc, parsed_url.netloc)`

## 60

`explosion/spaCy#13807` — `spacy/lang/ht/tokenizer_exceptions.py:6`

```diff
+
+def make_variants(base, first_norm, second_orth, second_norm):
+    return {
+        base: [
+            {ORTH: base.split("'")[0] + "'", NORM: first_norm},
+            {ORTH: second_orth, NORM: second_norm},
+        ],
+        base.capitalize(): [
+            {ORTH: base.split("'")[0].capitalize() + "'", NORM: first_norm.capitalize()},
```

**CLAIM:** This line incorrectly appends an apostrophe to the first token of a contraction, making it inconsistent with how non-apostrophe contractions like "map" are handled, which are split into "m" and "ap".

**PROPOSED FIX:** `{ORTH: base.split("'")[0], NORM: first_norm},`

## 61

`explosion/spaCy#13760` — `spacy/util.py:161`

```diff
+    "tr": ["tur"],
+    "tt": ["tat"],
+    "uk": ["ukr"],
+    "ur": ["urd"],
+    "vi": ["viw"],
+    "yo": ["yor"],
+    "zh": ["zho", "chi"],
+
+    "xx": ["mul"],
```

**CLAIM:** The alias "viw" for Vietnamese is not a valid ISO language code; the correct ISO 639-3 code is "vie".

**PROPOSED FIX:** `    "vi": ["vie"],`

## 62

`python-poetry/poetry#10881` — `src/poetry/repositories/http_repository.py:377`

```diff
+                        parse_marker_version_constraint(
+                            info.requires_python or "^2.7"
+                        ).union(
+                            parse_marker_version_constraint(
+                                py3_info.requires_python or "^3"
+                            )
                         )
                     )
 
```

**CLAIM:** Using `or` to provide a default incorrectly treats an empty `requires_python` string, which signifies compatibility with any Python version, as a falsy value and wrongly applies the default constraint `^3`.

**PROPOSED FIX:** `                                py3_info.requires_python if py3_info.requires_python is not None else "^3"`

## 63

`python-poetry/poetry#10958` — `src/poetry/installation/wheel_installer.py:83`

```diff
+        target_path_str = os.path.abspath(os.path.join(target_dir, path))
+
+        # We do not need os.path.normcase() for this comparison
+        # because both paths are built from target_dir.
+        if target_path_str != target_dir and not target_path_str.startswith(
+            target_dir + os.sep
+        ):
             raise ValueError(
                 f"Attempting to write {path} outside of the target directory\n"
```

**CLAIM:** The case-sensitive string comparison is incorrect on case-insensitive filesystems (like Windows and default macOS), and will reject valid paths that `pathlib.Path.is_relative_to()` would have correctly accepted.

**PROPOSED FIX:** `if os.path.normcase(target_path_str) != os.path.normcase(target_dir) and not os.path.normcase(target_path_str).startswith(`

## 64

`urllib3/urllib3#5097` — `test/test_util.py:1228`

```diff
+    if hasattr(ssl, "PROTOCOL_TLSv1"):
+        candidate_version.extend(
+            [
+                (ssl.PROTOCOL_TLSv1, ssl.PROTOCOL_TLSv1),
+                ("PROTOCOL_TLSv1", ssl.PROTOCOL_TLSv1),
+                ("TLSv1", ssl.PROTOCOL_TLSv1),
+            ]
+        )
+
```

**CLAIM:** The `resolve_ssl_version` function expects short protocol names (e.g. "TLSv1") and prepends "PROTOCOL_" itself, so this test case passing a prefixed string is incorrect and will fail.

**PROPOSED FIX:** `                # ("PROTOCOL_TLSv1", ssl.PROTOCOL_TLSv1),  # This test case is incorrect.`

## 65

`explosion/spaCy#13807` — `spacy/lang/ht/stop_words.py:38`

```diff
+y y' yo yon yonn
+
+non o oh eh
+
+sa san si swa si
+
+men mèsi oswa osinon
+
+"""
```

**CLAIM:** The stop word "si" is duplicated in the list.

**PROPOSED FIX:** `sa san si swa`

## 66

`urllib3/urllib3#4967` — `test/test_response.py:2046`

```diff
 
-    def readline(self) -> bytes:
-        return self.pop_current_chunk(till_crlf=True)
+    def readline(self, amt: int = -1) -> bytes:
+        return self.pop_current_chunk(amt, till_crlf=amt < 0)
 
     def read(self, amt: int = -1) -> bytes:
         return self.pop_current_chunk(amt)

```

**CLAIM:** This implementation of `readline(amt)` is incorrect because it disables line-based reading when a positive `amt` is provided, violating the method's contract which should only limit the number of bytes read from a line.

**PROPOSED FIX:** `        return self.pop_current_chunk(amt, till_crlf=True)`

## 67

`python-poetry/poetry#10895` — `src/poetry/repositories/link_sources/json.py:52`

```diff
 
+            # use filename for performance (and strictly speaking also for correctness)
             link = Link(
                 url,
+                filename=file["filename"],
                 requires_python=requires_python,
                 hashes=hashes,
                 yanked=yanked,
diff --git a/tests/repositories/link_sources/test_json.py b/tests/repositories/link_sources/test_json.py
```

**CLAIM:** The code assumes the "filename" key is always present in the file dictionary, which will cause a KeyError if the JSON source is not compliant with PEP 691.

**PROPOSED FIX:** `filename=file.get("filename"),`

## 68

`urllib3/urllib3#5062` — `test/test_connectionpool.py:284`

```diff
+    def test_urlopen_invalid_timeout_raises_value_error(self) -> None:
+        with HTTPConnectionPool(host="localhost", maxsize=1, block=True) as pool:
+            with pytest.raises(
+                ValueError,
+                match="Timeout value connect was 1, but it must be an int, float or None",
+            ):
+                pool.urlopen("GET", "/", timeout="1")  # type: ignore[arg-type]
+
     def test_put_conn_closed_pool(self) -> None:
```

**CLAIM:** The expected error message is incorrect for an invalid string timeout and also nonsensical, as it claims the integer `1` is an invalid timeout value.

**PROPOSED FIX:** `match=r"Timeout value connect was 'invalid', but it must be an int, float or None\.",`

## 69

`pylint-dev/pylint#11213` — `pylint/checkers/classes/class_checker.py:1414`

```diff
+                or (
+                    meth_node.args.args is None
+                    and (
+                        function.argnames() != ["self"]
+                        or util.safe_infer(call.func) is None
+                    )
+                )
             ):
                 return
```

**CLAIM:** The logic incorrectly assumes that if `super()` delegation can be inferred for a C-level method, it must be `object.__init__`, which can lead to false positives if `astroid` improves and learns to infer other C-level methods like `dict.__init__`.

**PROPOSED FIX:** `or (inferred_call := util.safe_infer(call.func)) is None or inferred_call.qname() != "builtins.object.__init__"`

## 70

`urllib3/urllib3#5093` — `test/with_dummyserver/test_proxy_poolmanager.py:850`

```diff
@@ -821,6 +847,23 @@ def test_forwarding_proxy_ssl_context_fallback(self) -> None:
                 conn.connect()
                 assert isinstance(conn.sock, ssl.SSLSocket)
                 assert conn.sock.context is ssl_context
+                assert ssl_context.verify_mode == ssl.CERT_REQUIRED
+
+    @requires_network()
+    def test_https_proxy_to_http_target_ssl_context_fallback(self) -> None:
+        ssl_context = create_urllib3_context()
```

**CLAIM:** This assertion will fail because the `ssl_context` object was created with `cert_reqs=ssl.CERT_NONE` and its `verify_mode` is not modified by the code under test.

**PROPOSED FIX:** `                assert conn.sock.context.verify_mode == ssl.CERT_REQUIRED`

## 71

`Lightning-AI/pytorch-lightning#21775` — `src/lightning/fabric/utilities/cloud_io.py:193`

```diff
+    """
+    if _is_local_file_protocol(str(path)):
+        _, urlpath = url_to_fs(str(path))
+        return Path(urlpath)
+    return str(path)
+
+
+def _checkpoint_join(path: Union[str, Path], name: str) -> Union[str, Path]:
+    """Join ``name`` onto a checkpoint ``path`` without corrupting remote URLs."""
```

**CLAIM:** When given a `pathlib.Path` object created from a remote URL string (e.g., `Path("s3://...")`), the function returns a corrupted URL string instead of treating it as a local path.

**PROPOSED FIX:** `    return path`

## 72

`Lightning-AI/pytorch-lightning#21745` — `tests/tests_fabric/utilities/test_cloud_io.py:102`

```diff
+    """Test that _atomic_save uses fs.pipe() for S3 filesystems."""
+    checkpoint = {"key": torch.tensor([1, 2, 3])}
+    filepath = "s3://bucket/checkpoint.ckpt"
+
+    mock_fs = mock.MagicMock()
+    mock_fs.__class__.__name__ = "S3FileSystem"
+
+    with (
+        mock.patch("lightning.fabric.utilities.cloud_io._is_object_storage", return_value=True),
```

**CLAIM:** A `MagicMock` created this way will not pass the `isinstance` check in the code under test, even with the subsequent `__class__` assignment, causing the test to incorrectly exercise the non-Azure code path and fail.

**PROPOSED FIX:** `mock_fs = mock.MagicMock(spec=AzureBlobFileSystem())`

## 73

`explosion/spaCy#13632` — `website/meta/universe.json:2595`

```diff
+            "type": "education",
+            "id": "spacy-quickstart",
+            "title": "spaCy Quickstart",
+            "slogan": "Learn spaCy basics quickly by visualizing various Doc objects",
+            "description":"In this course, I use the itables Python library inside a Jupyter notebook so that you can visualize the different spaCy document objects. This will provide a solid foundation for people who wish to learn the spaCy NLP library."
+            "url": "https://learnspacy.com/courses/spacy-quickstart/",
+            "image": "https://learnspacy.com/wp-content/uploads/2024/09/custom_search_builder_spacy-2048x1202.png",
+            "thumb": "https://learnspacy.com/wp-content/uploads/2024/09/learnspacy_logo.png",
+            "author": "Aravind Mohanoor",
```

**CLAIM:** This line is missing a trailing comma, which results in invalid JSON syntax.

**PROPOSED FIX:** `            "description":"In this course, I use the itables Python library inside a Jupyter notebook so that you can visualize the different spaCy document objects. This will provide a solid foundati`

## 74

`explosion/spaCy#13621` — `spacy/strings.pyx:162`

```diff
                 return SYMBOLS_BY_INT[str_hash]
             else:
                 utf8str = <Utf8Str*>self._map.get(str_hash)
+                if utf8str is NULL and self._transient_map is not None:
+                    utf8str = <Utf8Str*>self._transient_map.get(str_hash)
         else:
             # TODO: Raise an error instead
             utf8str = <Utf8Str*>self._map.get(string_or_id)
-
```

**CLAIM:** The variable `str_hash` is not defined in this code path; the lookup should use `string_or_id` which holds the hash value.

**PROPOSED FIX:** `utf8str = <Utf8Str*>self._transient_map.get(string_or_id)`

## 75

`sqlalchemy/sqlalchemy#13271` — `noxfile.py:26`

```diff
     from tools.toxnox import tox_parameters
 
 
-PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.13t", "3.14", "3.14t"]
+PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14", "3.14t"]
 DATABASES = ["sqlite", "sqlite_file", "postgresql", "mysql", "oracle", "mssql"]
 CEXT = ["_auto", "cext", "nocext"]
 GREENLET = ["_greenlet", "nogreenlet"]

```

**CLAIM:** The removal of the "3.13t" version is inconsistent as the corresponding "3.14t" version for the next Python release was not also removed.

**PROPOSED FIX:** `PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]`

## 76

`explosion/spaCy#13713` — `spacy/morphology.pyx:60`

```diff
@@ -57,16 +57,20 @@ cdef class Morphology:
         field_feature_pairs = []
         for field in sorted(string_features):
             values = string_features[field]
+            self.strings.add(field, allow_transient=False),
+            field_id = self.strings[field]
             for value in values.split(self.VALUE_SEP):
+                field_sep_value = field + self.FIELD_SEP + value
+                self.strings.add(field_sep_value, allow_transient=False),
```

**CLAIM:** The trailing comma creates a tuple that is immediately discarded, which is a logic error.

**PROPOSED FIX:** `self.strings.add(field, allow_transient=False)`

## 77

`pylint-dev/pylint#11258` — `tests/functional/u/use/use_a_generator_py315.txt:1`

```diff
index 00000000000..8c6d9c34b08
--- /dev/null
+++ b/tests/functional/u/use/use_a_generator_py315.txt
@@ -0,0 +1,2 @@
+use-a-generator:3:6:3:31::Use a generator instead 'any(*x for x in NESTED)':UNDEFINED
+use-a-generator:4:6:4:31::Use a generator instead 'all(*x for x in NESTED)':UNDEFINED
diff --git a/tests/functional/u/use/use_implicit_booleaness_not_len_py315.py b/tests/functional/u/use/use_implicit_booleaness_not_len_py315.py
new file mode 100644
index 00000000000..36802158515
```

**CLAIM:** The suggested code `any(*x for x in NESTED)` is syntactically invalid because a generator expression cannot contain a starred expression as its yielded element.

**PROPOSED FIX:** `use-a-generator:3:6:3:31::Use a generator instead 'any(item for sublist in NESTED for item in sublist)':UNDEFINED`

## 78

`urllib3/urllib3#5095` — `src/urllib3/util/url.py:374`

```diff
@@ -362,11 +371,17 @@ def _normalize_host(host: str | None, scheme: str | None) -> str | None:
                         zone_id = zone_id[3:]
                     else:
                         zone_id = zone_id[1:]
+                    zone_id = _PERCENT_RE.sub(
+                        partial(_normalize_zone_id_percent_encoding, error_host=host),
+                        zone_id,
+                    )
                     zone_id = _encode_invalid_chars(zone_id, _UNRESERVED_CHARS)
```

**CLAIM:** This line uses a regex that fails to detect and reject malformed percent-encodings like a lone '%' in an IPv6 zone identifier.

**PROPOSED FIX:** `zone_id = _HOST_PERCENT_RE.sub(`

## 79

`Lightning-AI/pytorch-lightning#21739` — `.github/workflows/tpu-tests.yml.disabled:168`

```diff
           gcloud compute tpus tpu-vm list
 
       - name: Upload coverage to Codecov
-        uses: codecov/codecov-action@v5
+        uses: codecov/codecov-action@75cd11691c0faa626561e295848008c8a7dddffe # v5.5.4
         continue-on-error: true
         with:
           token: ${{ secrets.CODECOV_TOKEN }}

```

**CLAIM:** The specified commit SHA `75cd11691c0faa626561e295848008c8a7dddffe` does not exist in the `codecov/codecov-action` repository, which will cause the workflow to fail.

**PROPOSED FIX:** `        uses: codecov/codecov-action@894ff025c7b54507a923d41c98286076f30b5b73 # v4.1.0`

## 80

`Lightning-AI/pytorch-lightning#21739` — `.github/workflows/tpu-tests.yml.disabled:49`

```diff
+      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4.3.1
         with:
           ref: ${{ github.event.pull_request.head.sha }}
-      - uses: actions/setup-python@v5
+      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
         with:
           python-version: "3.10"
 
-      - uses: google-github-actions/auth@v2
```

**CLAIM:** This implementation of `readline(amt)` is incorrect because it disables line-based reading when a positive `amt` is provided, violating the method's contract which should only limit the number of bytes read from a line.

**PROPOSED FIX:** `      - uses: actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d # v5.1.0`

## 81

`Lightning-AI/pytorch-lightning#21708` — `src/lightning/pytorch/utilities/combined_loader.py:400`

```diff
 def _shutdown_workers_and_reset_iterator(dataloader: object) -> None:
     if hasattr(dataloader, "_iterator"):
         if isinstance(dataloader._iterator, _MultiProcessingDataLoaderIter):
-            dataloader._iterator._shutdown_workers()
+            del dataloader._iterator
         dataloader._iterator = None
 
 
diff --git a/tests/tests_pytorch/loops/test_loops.py b/tests/tests_pytorch/loops/test_loops.py
```

**CLAIM:** This explicit deletion is redundant because the subsequent assignment `dataloader._iterator = None` is sufficient to dereference the old iterator object, which is what triggers its finalizer for garbage collection.

**PROPOSED FIX:** `pass`

## 82

`explosion/spaCy#13643` — `website/meta/sidebars.json:59`

```diff
                     {
                         "text": "Large Language Models",
-                        "url": "/usage/large-language-models",
-                        "tag": "new"
+                        "url": "/usage/large-language-models"
+                    },
+                    {
+                        "text": "Training Models",
+                        "url": "/usage/training"
```

**CLAIM:** The `"tag": "new"` property was accidentally removed from the 'Large Language Models' sidebar item during reformatting.

**PROPOSED FIX:** `                        "url": "/usage/large-language-models",
                        "tag": "new"`

## 83

`pylint-dev/pylint#11258` — `tests/functional/n/nested_min_max_py315.txt:1`

```diff
index 00000000000..8c3f9d48bb7
--- /dev/null
+++ b/tests/functional/n/nested_min_max_py315.txt
@@ -0,0 +1,2 @@
+consider-using-generator:3:18:3:43::Consider using a generator instead 'min(*x for x in NESTED)':UNDEFINED
+nested-min-max:3:11:3:44::Do not use nested call of 'min'; it's possible to do 'min(1, *[*x for x in NESTED])' instead:INFERENCE
diff --git a/tests/functional/u/undefined/undefined_variable_py315.py b/tests/functional/u/undefined/undefined_variable_py315.py
new file mode 100644
index 00000000000..13a90f5ebb6
```

**CLAIM:** The suggested code `min(*x for x in NESTED)` is syntactically invalid because a generator expression cannot contain a starred expression as its yielded element.

**PROPOSED FIX:** `consider-using-generator:3:18:3:43::Consider using a generator instead 'min(item for sublist in NESTED for item in sublist)':UNDEFINED`

## 84

`explosion/spaCy#13800` — `website/meta/universe.json:9`

```diff
+            "title": "Temporal Expressions Normalization spaCy",
+            "thumb": "https://github-production-user-asset-6210df.s3.amazonaws.com/40547052/433595900-fae3c9d9-7181-4d8b-8b49-e6dc4fca930b.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20250414%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250414T235545Z&X-Amz-Expires=300&X-Amz-Signature=e21d3c06300ceb15fa1dadd7cb60081cc9f1b35e5a7bfd07f6e8b90dd7fad9d0&X-Amz-SignedHeaders=host",
+            "url": "https://pypi.org/project/temporal-normalization-spacy/",
+            "slogan": "A temporal expression normalization plugin for Romanian using rule-based methods and DBpedia mappings.",
+            "description": "**[Temporal Expressions Normalization spaCy (TeNs)](https://github.com/iliedorobat/timespan-normalization-spacy)** is a powerful pipeline component for spaCy that seamlessly identifies and parses date entities in text. It leverages the **[Temporal Expressions Normalization Framework]( https://github.com/iliedorobat/timespan-normalization)** to recognize a wide variety of date formats using an extensive set of regular expressions (RegEx), ensuring robust and adaptable date extraction across diverse textual sources.\n\nUnlike conventional solutions that primarily focus on well-structured date formats, TeNs excels in handling real-world text by **identifying** not only standard date representations but also **abbreviated, informal, or even misspelled temporal expressions.** This makes it particularly effective for processing noisy or unstructured data, such as historical records, user-generated content, and scanned documents with OCR inaccuracies.",
+            "github": "iliedorobat/timespan-normalization-spacy",
+            "pip": "temporal-normalization-spacy",
+            "code_example": [
+                "import subprocess",
```

**CLAIM:** There is a leading space in the URL of a markdown link, which may cause it to render incorrectly.

**PROPOSED FIX:** `"description": "**[Temporal Expressions Normalization spaCy (TeNs)](https://github.com/iliedorobat/timespan-normalization-spacy)** is a powerful pipeline component for spaCy that seamlessly identifies`

## 85

`urllib3/urllib3#5095` — `src/urllib3/util/url.py:418`

```diff
+
+def _normalize_zone_id_percent_encoding(
+    match: re.Match[str], *, error_host: str
+) -> str:
+    _decode_percent_encoding(match, error_host=error_host)
+    return match.group(0).upper()
+
+
 def _idna_encode(name: str) -> bytes:
```

**CLAIM:** The decoded value from this function is discarded, which prevents the normalization of percent-encoded unreserved characters in IPv6 zone identifiers.

**PROPOSED FIX:** `decoded_octet = _decode_percent_encoding(match, error_host=error_host)`

## 86

`explosion/spaCy#13740` — `website/meta/site.json:78`

```diff
         {
             "label": "Connect",
             "items": [
-                { "text": "Twitter", "url": "https://twitter.com/spacy_io" },
+                { "text": "Bluesky", "url": "https://bsky.app/profile/explosion-ai.bsky.social" },
                 { "text": "GitHub", "url": "https://github.com/explosion/spaCy" },
                 { "text": "YouTube", "url": "https://youtube.com/c/ExplosionAI" },
                 { "text": "Blog", "url": "https://explosion.ai/blog" }

```

**CLAIM:** This line replaces the Twitter link with a Bluesky link, which contradicts the pull request's stated goal of changing "Twitter" to "X".

**PROPOSED FIX:** `{ "text": "X", "url": "https://x.com/spacy_io" },`

## 87

`urllib3/urllib3#5062` — `test/test_connectionpool.py:286`

```diff
+            with pytest.raises(
+                ValueError,
+                match="Timeout value connect was 1, but it must be an int, float or None",
+            ):
+                pool.urlopen("GET", "/", timeout="1")  # type: ignore[arg-type]
+
     def test_put_conn_closed_pool(self) -> None:
         with HTTPConnectionPool(host="localhost", maxsize=1, block=True) as pool:
             conn1 = pool._get_conn()
```

**CLAIM:** This test is incorrect as `timeout="1"` is a valid value that can be coerced to a float, so `urlopen` will not raise a `ValueError` as the test expects.

**PROPOSED FIX:** `pool.urlopen("GET", "/", timeout="invalid")  # type: ignore[arg-type]`

## 88

`pylint-dev/pylint#11245` — `pylint/checkers/base/name_checker/checker.py:585`

```diff
-            "TypedDict",
-        }.intersection(
-            {
+        if isinstance(inferred_assign_type, bases.Instance):
+            if "EnumMeta" in {
                 ancestor.name
                 for ancestor in cast(InferenceResult, inferred_assign_type).mro()
-            }
-        ):
```

**CLAIM:** The check for `EnumMeta` uses an unqualified name, which is not robust against user-defined classes that might share the same name.

**PROPOSED FIX:** `if "enum.EnumMeta" in {`

## 89

`explosion/spaCy#13800` — `website/meta/universe.json:27`

```diff
+                "    nlp = spacy.load('ro_core_news_sm')",
+                "except OSError:",
+                "    console.warning(f'Started downloading ro_core_news_sm...')",
+                "    # Download the Romanian model if it wasn't already downloaded",
+                "    subprocess.run(['python', '-m', 'spacy', 'download', 'ro_core_news_sm'])",
+                "    # Load the spaCy model",
+                "    nlp = spacy.load('ro_core_news_sm')",
+                "",
+                "# Add 'temporal_normalization' component to the spaCy pipeline",
```

**CLAIM:** The `subprocess.run` call does not check for errors, so if the model download fails, the script will proceed and crash on the subsequent `spacy.load` call.

**PROPOSED FIX:** `"    subprocess.run(['python', '-m', 'spacy', 'download', 'ro_core_news_sm'], check=True)",`

## 90

`python-poetry/poetry#10944` — `src/poetry/puzzle/provider.py:603`

```diff
+            # When this run is restricted to a set of markers (see MARKER_SPLIT),
+            # skip any dependency that cannot apply within that set; otherwise its
+            # requirements would leak into a run where it never applies (see
+            # #5506).
+            if self._overrides_marker_intersection.intersect(dep.marker).is_empty():
+                continue
+
             if self._env:
                 marker_values = (
```

**CLAIM:** This check for pruning a dependency is incomplete because it does not consider the marker of the parent package, potentially leaving dependencies that can never be used and whose constraints might cause spurious conflicts.

**PROPOSED FIX:** `if self._overrides_marker_intersection.intersect(dep.marker.intersect(dep.transitive_marker)).is_empty():`
