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

## 1

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

**CLAIM:** The `resolve_ssl_version` function expects short protocol names (e.g. "TLSv1") and prepends "PROTOCOL_" itself, so this test case passing a prefixed string is incorrect and will fail.

**PROPOSED FIX:** `    assert list(downloader.download_with_progress(chunk_size=2)) == [2, 2]`

## 2

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:372`

```diff
-        torch.int8: 660.6e12,
-        "int4": 1321.2e12,
+        torch.float32: 8.26e13,
+        "tfloat32": 8.26e13,
+        torch.bfloat16: 8.26e13,
+        torch.float16: 8.26e13,
+        torch.int8: 6.606e14,
+        "int4": 1.3212e15,
     },
```

**CLAIM:** The bfloat16 FLOPs for the RTX 4090 is incorrectly set to the FP32 rate, but it should be the much higher dense Tensor Core rate.

**PROPOSED FIX:** `torch.bfloat16: 3.305e14,`

## 3

`pylint-dev/pylint#11258` — `tests/functional/c/consider/consider_using_generator_py315.txt:1`

```diff
index 00000000000..11a65a21495
--- /dev/null
+++ b/tests/functional/c/consider/consider_using_generator_py315.txt
@@ -0,0 +1,2 @@
+consider-using-generator:3:8:3:33::Consider using a generator instead 'sum(*x for x in NESTED)':UNDEFINED
+consider-using-generator:4:11:4:38::Consider using a generator instead 'tuple(*x for x in NESTED)':UNDEFINED
diff --git a/tests/functional/c/consider/consider_using_set_comprehension_py315.py b/tests/functional/c/consider/consider_using_set_comprehension_py315.py
new file mode 100644
index 00000000000..19df97f3c87
```

**CLAIM:** The suggested code `sum(*x for x in NESTED)` is syntactically invalid because a generator expression cannot contain a starred expression as its yielded element.

**PROPOSED FIX:** `consider-using-generator:3:8:3:33::Consider using a generator instead 'sum(item for sublist in NESTED for item in sublist)':UNDEFINED`

## 4

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

**CLAIM:** The expected error message is incorrect for an invalid string timeout and also nonsensical, as it claims the integer `1` is an invalid timeout value.

**PROPOSED FIX:** `                                py3_info.requires_python if py3_info.requires_python is not None else "^3"`

## 5

`pylint-dev/pylint#11206` — `tests/testutils/_primer/test_primer.py:29`

```diff
 
 # If you change this, also change DEFAULT_PYTHON in
 # ``.github/workflows/primer_comment.yaml``
-PRIMER_CURRENT_INTERPRETER = (3, 13)
+PRIMER_CURRENT_INTERPRETER = (3, 14)
 
 DEFAULT_ARGS = ["python tests/primer/__main__.py", "compare", "--commit=v2.14.2"]
 

```

**CLAIM:** The interpreter version is being set to 3.14, but the pull request title indicates the goal is to support Python 3.15.

**PROPOSED FIX:** `PRIMER_CURRENT_INTERPRETER = (3, 15)`

## 6

`python-poetry/poetry#10951` — `src/poetry/repositories/link_sources/base.py:108`

```diff
             name = m.group("name")
             version_string = m.group("ver")
         else:
-            info, _ext = link.splitext()
+            info, _ext = splitext(filename, is_filename=True)
             match = cls.VERSION_REGEX.match(info)
             if match:
                 name = match.group(1)
@@ -111,8 +118,8 @@ def _link_package_name_and_version(
```

**CLAIM:** This condition is incorrect because it prevents adding a missing optional dependency if another dependency for the same extra is already present, as it checks for the presence of the extra group as a whole rather than the specific dependency.

**PROPOSED FIX:** `info, _ext = splitext(filename)`

## 7

`Lightning-AI/pytorch-lightning#21701` — `requirements/collect_env_details.py:55`

```diff
-    for dist in pkg_resources.working_set:
-        package = dist.as_requirement()
-        packages[package.key] = package.specs[0][1]
-    return packages
+    return {dist.metadata["Name"]: dist.version for dist in distributions()}
 
 
 def nice_print(details: dict, level: int = 0) -> list:
diff --git a/requirements/pytorch/test.txt b/requirements/pytorch/test.txt
```

**CLAIM:** The specified commit SHA `75cd11691c0faa626561e295848008c8a7dddffe` does not exist in the `codecov/codecov-action` repository, which will cause the workflow to fail.

**PROPOSED FIX:** `    return {dist.metadata["Name"].lower(): dist.version for dist in distributions()}`

## 8

`pylint-dev/pylint#11264` — `pylint/message/_deleted_message_ids.py:134`

```diff
+        DeletedMessage("E1002", "super-on-old-class"),
+        DeletedMessage("W0110", "deprecated-lambda"),
+        DeletedMessage("W0332", "lowercase-l-suffix"),
+        DeletedMessage("W0710", "nonstandard-exception"),
+        DeletedMessage("W1001", "property-on-old-class"),
+    ],
 }
 MOVED_TO_EXTENSIONS = {
     "https://pylint.readthedocs.io/en/latest/whatsnew/2/2.14/summary.html#removed-checkers": [
```

**CLAIM:** The message ID for 'property-on-old-class' is incorrect, as the historical ID for this message was 'E1003', not 'W1001'.

**PROPOSED FIX:** `        DeletedMessage("E1003", "property-on-old-class"),`

## 9

`Lightning-AI/pytorch-lightning#21745` — `tests/tests_fabric/utilities/test_cloud_io.py:129`

```diff
+    fake_adlfs = types.ModuleType("adlfs")
+    fake_adlfs.AzureBlobFileSystem = AzureBlobFileSystem
+
+    mock_fs = mock.MagicMock()
+    mock_fs.__class__ = AzureBlobFileSystem
+
+    with (
+        mock.patch.dict(sys.modules, {"adlfs": fake_adlfs}),
+        mock.patch("lightning.fabric.utilities.cloud_io.module_available", return_value=True),
```

**CLAIM:** Assigning to `__class__` on a `MagicMock` instance does not make it pass an `isinstance` check, so this line is ineffective and the test fails to cover the intended code path for Azure filesystems.

**PROPOSED FIX:** `# This line is now redundant and should be removed.`

## 10

`urllib3/urllib3#5029` — `src/urllib3/util/url.py:59`

```diff
 _TARGET_RE = re.compile(r"^(/[^?#]*)(?:\?([^#]*))?(?:#.*)?$")
 
-_IPV4_RE = re.compile("^" + _IPV4_PAT + "$")
+_IPV4_RE = re.compile(
+    r"^(?:0[xX][0-9a-fA-F]+|[0-9]+)(?:\.(?:0[xX][0-9a-fA-F]+|[0-9]+)){0,3}$"
+)
 _IPV6_RE = re.compile("^" + _IPV6_PAT + "$")
 _IPV6_ADDRZ_RE = re.compile("^" + _IPV6_ADDRZ_PAT + "$")
 _BRACELESS_IPV6_ADDRZ_RE = re.compile("^" + _IPV6_ADDRZ_PAT[2:-2] + "$")
```

**CLAIM:** The regular expression is too permissive and incorrectly matches invalid IPv4 address strings, such as "256.0.0.0", because it does not validate that each part of a 4-part address is a valid octet.

**PROPOSED FIX:** `r"^((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:0[xX][0-9a-fA-F]{1,8}|[0-9]{1,10}))$"`

## 11

`pylint-dev/pylint#11245` — `pylint/checkers/base/name_checker/checker.py:594`

```diff
+            # The functional syntax `X = TypedDict("X", {...})` defines a new type,
+            # and is inferred as an instance of `TypedDict` itself. Instantiating a
+            # `TypedDict` subclass only builds a value, so its name is not a class
+            # name.
+            if inferred_assign_type._proxied.name == "TypedDict":
+                return True
         if (
             isinstance(inferred_assign_type, nodes.FunctionDef)
             and inferred_assign_type.qname() == "typing.Annotated"
```

**CLAIM:** The check for `TypedDict` is based on the unqualified class name, which will incorrectly trigger for any user-defined class that is also named `TypedDict`.

**PROPOSED FIX:** `if inferred_assign_type._proxied.qname() == "typing.TypedDict":`

## 12

`explosion/spaCy#13807` — `spacy/lang/ht/tokenizer_exceptions.py:10`

```diff
+            {ORTH: base.split("'")[0] + "'", NORM: first_norm},
+            {ORTH: second_orth, NORM: second_norm},
+        ],
+        base.capitalize(): [
+            {ORTH: base.split("'")[0].capitalize() + "'", NORM: first_norm.capitalize()},
+            {ORTH: second_orth, NORM: second_norm},
+        ]
+    }
+
```

**CLAIM:** This line incorrectly appends an apostrophe to the first token of a capitalized contraction, making it inconsistent with how non-apostrophe contractions are handled.

**PROPOSED FIX:** `{ORTH: base.split("'")[0].capitalize(), NORM: first_norm.capitalize()},`

## 13

`explosion/spaCy#13807` — `spacy/lang/ht/punctuation.py:29`

```diff
+TOKENIZER_SUFFIXES = LIST_PUNCT + LIST_QUOTES + LIST_ELLIPSES + [
+    r"(?<=[0-9])%",  # numbers like 10%
+    r"(?<=[0-9])(?:{h})".format(h=HYPHENS),  # hyphens after numbers
+    r"(?<=[{a}])['’]".format(a=ALPHA),  # apostrophes after letters
+    r"(?<=[{a}])['’][mwlnytk](?=\s|$)".format(a=ALPHA),  # contractions
+    r"(?<=[{a}0-9])\)",  # right parenthesis after letter/number
+    r"(?<=[{a}])\.(?=\s|$)".format(a=ALPHA),  # period after letter if space or end of string
+    r"(?<=\))[\.\?!]",  # punctuation immediately after right parenthesis
+]
```

**CLAIM:** The regex for suffix contractions is missing "p" for the negation "pa", which is treated as a contractable particle elsewhere in the code.

**PROPOSED FIX:** `r"(?<=[{a}])['’][mwlnytkp](?=\s|$)".format(a=ALPHA),  # contractions`

## 14

`python-poetry/poetry#10907` — `tests/config/test_config.py:58`

```diff
+def test_package_filter_policy_normalizes_and_matches_packages() -> None:
+    policy = PackageFilterPolicy("PyTest,black")
+
+    assert policy.packages == frozenset({"black", "pytest"})
+    assert policy.allows("Poetry")
+    assert not policy.allows("PyTest")
+    assert policy.has_exact_package("PyTest")
+    assert not policy.has_exact_package("Poetry")
+
```

**CLAIM:** The test incorrectly asserts that a package not in the policy is allowed, but the `allows` method should only permit packages that are explicitly in the policy list.

**PROPOSED FIX:** `assert not policy.allows("Poetry")`

## 15

`python-poetry/poetry#10917` — `src/poetry/installation/executor.py:945`

```diff
+    @staticmethod
+    def _path_to_file_url(path: str) -> str:
+        source = Path(path)
+        if not source.is_absolute():
+            source = source.resolve()
+
+        return source.as_uri()
+
     def _get_archive_info(self, package: Package) -> dict[str, Any]:
```

**CLAIM:** Resolving a relative path with `Path.resolve()` uses the current working directory, which can be incorrect if the command is run from a subdirectory of the project; it should be resolved relative to the project root.

**PROPOSED FIX:** `source = (self._config.cwd / source).resolve()`

## 16

`python-poetry/poetry#10951` — `src/poetry/repositories/link_sources/json.py:38`

```diff
-            )
-
-            if link.ext not in self.SUPPORTED_FORMATS:
+            filename = file["filename"]
+            if splitext(filename, is_filename=True)[1] not in self.SUPPORTED_FORMATS:
                 continue
 
-            name_and_version = self._link_package_name_and_version(link)
+            name_and_version = self._link_package_name_and_version(filename)
```

**CLAIM:** Calling `splitext` with `is_filename=True` likely disables special handling for compound extensions, causing valid formats like `.tar.gz` to be incorrectly identified as `.gz` and skipped.

**PROPOSED FIX:** `if splitext(filename)[1] not in self.SUPPORTED_FORMATS:`

## 17

`pylint-dev/pylint#11203` — `pylint/testutils/_primer/primer_compare_command.py:150`

```diff
+        fixed_fp = [m for m in missing_messages if m["symbol"] == "suppressed-message"]
+        reintroduced_fp = [
+            m for m in new_messages if m["symbol"] == "suppressed-message"
+        ]
+        other_new = [
+            m
+            for m in new_messages
+            if m["symbol"] not in {"astroid-error", "suppressed-message"}
+        ]
```

**CLAIM:** This categorization is incorrect because it lumps new `useless-suppression` messages, which indicate fixed false-positives, into the generic `other_new` category.

**PROPOSED FIX:** `other_new = [
            m
            for m in new_messages
            if m["symbol"] not in {"astroid-error", "suppressed-message", "useless-suppression"}
        ]`

## 18

`python-poetry/poetry#10900` — `tests/utils/test_threading.py:101`

```diff
     executor = ThreadPoolExecutor(max_workers=WORKER_COUNT)
     futures = [executor.submit(access_property) for _ in range(WORKER_COUNT)]
 
-    wait(futures)
+    wait(futures, 10)
     assert len(results) == WORKER_COUNT
     assert all(result == (EXPECTED_VALUE + instance.value) for result in results)
 

```

**CLAIM:** The timeout for waiting on futures is the same as the barrier timeout within the threads, creating a race condition that can cause the test to fail spuriously if thread synchronization is slow.

**PROPOSED FIX:** `    wait(futures, 20)`

## 19

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:456`

```diff
-        torch.float16: 35.6e12,
-        torch.int8: 284e12,
-        "int4": 568e12,
+        torch.float32: 3.56e13,
+        "tfloat32": 3.56e13,
+        torch.bfloat16: 3.56e13,
+        torch.float16: 3.56e13,
+        torch.int8: 2.84e14,
+        "int4": 5.68e14,
```

**CLAIM:** The tfloat32 FLOPs for the RTX 3090 is incorrectly set to the FP32 rate, but Ampere GPUs support TF32 at twice the FP32 rate.

**PROPOSED FIX:** `"tfloat32": 7.12e13,`

## 20

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:432`

```diff
-        torch.int8: 299.3e12,
-        "int4": 598.7e12,
+        torch.float32: 3.74e13,
+        "tfloat32": 7.48e13,
+        torch.bfloat16: 1.497e14,
+        torch.float16: 1.497e14,
+        torch.int8: 2.993e14,
+        "int4": 5.987e14,
     },
```

**CLAIM:** The bfloat16 FLOPs for the A40 GPU is the sparse value, but it should be the dense value to be consistent with the new `using_sparse_model` flag.

**PROPOSED FIX:** `torch.bfloat16: 7.48e13,`

## 21

`explosion/spaCy#13561` — `spacy/lang/kmr/lex_attrs.py:85`

```diff
+    "sîyemîn",
+    "çilem",
+    "çilemîn",
+    "pêncîyem",
+    "pênciyemîn",
+    "şêstem",
+    "şêstemîn",
+    "heftêyem",
+    "heftêyemîn",
```

**CLAIM:** The word "pênciyemîn" is misspelled and should be "pêncîyemîn" to be consistent with the base number "pêncî" and the other ordinal form "pêncîyem".

**PROPOSED FIX:** `    "pêncîyemîn",`

## 22

`Lightning-AI/pytorch-lightning#21739` — `.github/workflows/tpu-tests.yml.disabled:53`

```diff
         with:
           python-version: "3.10"
 
-      - uses: google-github-actions/auth@v2
+      - uses: google-github-actions/auth@c200f3691d83b41bf9bbd8638997a462592937ed # v2.1.13
         with:
           credentials_json: ${{ secrets.GKE_SA_KEY_BASE64 }}
-      - uses: "google-github-actions/setup-gcloud@v2"
+      - uses: google-github-actions/setup-gcloud@e427ad8a34f8676edf47cf7d7925499adf3eb74f # v2.2.1
```

**CLAIM:** The specified commit SHA `c200f3691d83b41bf9bbd8638997a462592937ed` does not exist in the `google-github-actions/auth` repository, which will cause the workflow to fail.

**PROPOSED FIX:** `      - uses: google-github-actions/auth@2421820b45a7336c4513988b8d3c0947c3695c4b # v2.1.2`

## 23

`explosion/spaCy#13800` — `website/meta/universe.json:6`

```diff
     "resources": [
+        {
+            "id": "TeNs",
+            "title": "Temporal Expressions Normalization spaCy",
+            "thumb": "https://github-production-user-asset-6210df.s3.amazonaws.com/40547052/433595900-fae3c9d9-7181-4d8b-8b49-e6dc4fca930b.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20250414%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250414T235545Z&X-Amz-Expires=300&X-Amz-Signature=e21d3c06300ceb15fa1dadd7cb60081cc9f1b35e5a7bfd07f6e8b90dd7fad9d0&X-Amz-SignedHeaders=host",
+            "url": "https://pypi.org/project/temporal-normalization-spacy/",
+            "slogan": "A temporal expression normalization plugin for Romanian using rule-based methods and DBpedia mappings.",
+            "description": "**[Temporal Expressions Normalization spaCy (TeNs)](https://github.com/iliedorobat/timespan-normalization-spacy)** is a powerful pipeline component for spaCy that seamlessly identifies and parses date entities in text. It leverages the **[Temporal Expressions Normalization Framework]( https://github.com/iliedorobat/timespan-normalization)** to recognize a wide variety of date formats using an extensive set of regular expressions (RegEx), ensuring robust and adaptable date extraction across diverse textual sources.\n\nUnlike conventional solutions that primarily focus on well-structured date formats, TeNs excels in handling real-world text by **identifying** not only standard date representations but also **abbreviated, informal, or even misspelled temporal expressions.** This makes it particularly effective for processing noisy or unstructured data, such as historical records, user-generated content, and scanned documents with OCR inaccuracies.",
+            "github": "iliedorobat/timespan-normalization-spacy",
```

**CLAIM:** The `thumb` URL is a temporary, signed AWS S3 URL that will expire, causing the image to become a broken link.

**PROPOSED FIX:** `The `thumb` URL must be replaced with a permanent link to the image asset.`

## 24

`pylint-dev/pylint#11204` — `pylint/checkers/async_checker.py:50`

```diff
         for child in node.nodes_of_class(nodes.Yield):
-            if child.scope() is node and (
-                sys.version_info[:2] == (3, 5) or isinstance(child, nodes.YieldFrom)
-            ):
+            if child.scope() is node and isinstance(child, nodes.YieldFrom):
                 self.add_message("yield-inside-async-function", node=child)
 
     @checker_utils.only_required_for_messages("not-async-context-manager")

```

**CLAIM:** The full request `url` is passed as the service name for the keyring lookup, but this is not a meaningful service name and the lookup should use the `netloc` instead, as is done for git URLs in the function below.

**PROPOSED FIX:** `if child.scope() is node and (
    sys.version_info[:2] == (3, 5) or isinstance(child, nodes.YieldFrom)
):`

## 25

`python-poetry/poetry#10908` — `src/poetry/console/commands/add.py:447`

```diff
         self.line(
-            "The following packages are already present in the pyproject.toml and will"
-            " be skipped:\n"
+            f"The following packages are already present in the pyproject.toml"
+            f" (<c2>{self.poetry.file.path}</c2>) and will be skipped:\n"
         )
         for name in existing_packages:
             self.line(f"  - <c1>{name}</c1>")
diff --git a/tests/console/commands/self/test_add_plugins.py b/tests/console/commands/self/test_add_plugins.py
```

**CLAIM:** The file path is not escaped, which can lead to garbled output if the path contains special characters like '<' that are meaningful to the console formatter.

**PROPOSED FIX:** `f" (<c2>{self.escape(str(self.poetry.file.path))}</c2>) and will be skipped:\n"`

## 26

`pylint-dev/pylint#11258` — `tests/functional/c/consider/consider_using_generator_py315.txt:2`

```diff
--- /dev/null
+++ b/tests/functional/c/consider/consider_using_generator_py315.txt
@@ -0,0 +1,2 @@
+consider-using-generator:3:8:3:33::Consider using a generator instead 'sum(*x for x in NESTED)':UNDEFINED
+consider-using-generator:4:11:4:38::Consider using a generator instead 'tuple(*x for x in NESTED)':UNDEFINED
diff --git a/tests/functional/c/consider/consider_using_set_comprehension_py315.py b/tests/functional/c/consider/consider_using_set_comprehension_py315.py
new file mode 100644
index 00000000000..19df97f3c87
--- /dev/null
```

**CLAIM:** The suggested code `tuple(*x for x in NESTED)` is syntactically invalid because a generator expression cannot contain a starred expression as its yielded element.

**PROPOSED FIX:** `consider-using-generator:4:11:4:38::Consider using a generator instead 'tuple(item for sublist in NESTED for item in sublist)':UNDEFINED`

## 27

`explosion/spaCy#13807` — `spacy/lang/ht/stop_words.py:8`

```diff
+byen bò byenke
+
+chak
+
+de depi deja deja
+
+e en epi èske
+
+fò fòk
```

**CLAIM:** The stop word "deja" is duplicated in the list.

**PROPOSED FIX:** `de depi deja`

## 28

`python-poetry/poetry#10958` — `src/poetry/installation/wheel_installer.py:84`

```diff
+
+        # We do not need os.path.normcase() for this comparison
+        # because both paths are built from target_dir.
+        if target_path_str != target_dir and not target_path_str.startswith(
+            target_dir + os.sep
+        ):
             raise ValueError(
                 f"Attempting to write {path} outside of the target directory\n"
                 f"Target directory: {target_dir}\n"
```

**CLAIM:** On POSIX systems, if `target_dir` is the root ('/'), this expression becomes '//', which causes the `startswith` check to incorrectly pass for any absolute path, creating a path traversal vulnerability.

**PROPOSED FIX:** `os.path.join(target_dir, "")`

## 29

`sqlalchemy/sqlalchemy#12726` — `lib/sqlalchemy/ext/asyncio/result.py:857`

```diff
             """
             ...
 
-        async def __aiter__(self) -> AsyncIterator[_R]: ...
+        def __aiter__(self) -> AsyncIterator[_R]: ...
 
         async def __anext__(self) -> _R: ...
 

```

**CLAIM:** Changing the `__aiter__` type stub to be synchronous is an API contract violation if the runtime implementation remains `async`, as `__aiter__()` would then return a coroutine instead of the declared iterator type, breaking consumers of the typed API.

**PROPOSED FIX:** `async def __aiter__(self) -> AsyncIterator[_R]: ...`

## 30

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:433`

```diff
-        "int4": 598.7e12,
+        torch.float32: 3.74e13,
+        "tfloat32": 7.48e13,
+        torch.bfloat16: 1.497e14,
+        torch.float16: 1.497e14,
+        torch.int8: 2.993e14,
+        "int4": 5.987e14,
     },
     # source: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a10/pdf/a10-datasheet.pdf
```

**CLAIM:** The float16 FLOPs for the A40 GPU is the sparse value, but it should be the dense value to be consistent with the new `using_sparse_model` flag.

**PROPOSED FIX:** `torch.float16: 7.48e13,`

## 31

`Lightning-AI/pytorch-lightning#21707` — `src/lightning/pytorch/callbacks/device_stats_monitor.py:171`

```diff
+                from lightning.pytorch.accelerators.cpu import get_cpu_stats
+
+                device_stats.update(get_cpu_stats())
+
+            unrecognized = self._filter_keys - device_stats.keys()
+            if unrecognized:
+                rank_zero_warn(
+                    f"`DeviceStatsMonitor` filter_keys contains keys not found in device stats and will be ignored:"
+                    f" {unrecognized}"
```

**CLAIM:** This check for unrecognized keys is unreliable because it runs in `setup` where the full set of device statistic keys may not be available, leading to spurious warnings for valid keys that appear later during execution.

**PROPOSED FIX:** `unrecognized = set()`

## 32

`Lightning-AI/pytorch-lightning#21701` — `requirements/collect_env_details.py:55`

```diff
-    for dist in pkg_resources.working_set:
-        package = dist.as_requirement()
-        packages[package.key] = package.specs[0][1]
-    return packages
+    return {dist.metadata["Name"]: dist.version for dist in distributions()}
 
 
 def nice_print(details: dict, level: int = 0) -> list:
diff --git a/requirements/pytorch/test.txt b/requirements/pytorch/test.txt
```

**CLAIM:** The package name used as a dictionary key is not normalized to lowercase, which is a regression from the previous implementation and changes the data contract of the function.

**PROPOSED FIX:** `    return {dist.metadata["Name"].lower(): dist.version for dist in distributions()}`

## 33

`python-poetry/poetry#10907` — `tests/config/test_config.py:58`

```diff
+def test_package_filter_policy_normalizes_and_matches_packages() -> None:
+    policy = PackageFilterPolicy("PyTest,black")
+
+    assert policy.packages == frozenset({"black", "pytest"})
+    assert policy.allows("Poetry")
+    assert not policy.allows("PyTest")
+    assert policy.has_exact_package("PyTest")
+    assert not policy.has_exact_package("Poetry")
+
```

**CLAIM:** The int8 FLOPs for the A40 GPU is the sparse value, but it should be the dense value to be consistent with the new `using_sparse_model` flag.

**PROPOSED FIX:** `assert not policy.allows("Poetry")`

## 34

`Lightning-AI/pytorch-lightning#21739` — `.github/workflows/tpu-tests.yml.disabled:56`

```diff
+      - uses: google-github-actions/auth@c200f3691d83b41bf9bbd8638997a462592937ed # v2.1.13
         with:
           credentials_json: ${{ secrets.GKE_SA_KEY_BASE64 }}
-      - uses: "google-github-actions/setup-gcloud@v2"
+      - uses: google-github-actions/setup-gcloud@e427ad8a34f8676edf47cf7d7925499adf3eb74f # v2.2.1
 
       - name: Time-based job cleanup
         if: always()
@@ -165,7 +165,7 @@ jobs:
```

**CLAIM:** The specified commit SHA `e427ad8a34f8676edf47cf7d7925499adf3eb74f` does not exist in the `google-github-actions/setup-gcloud` repository, which will cause the workflow to fail.

**PROPOSED FIX:** `      - uses: google-github-actions/setup-gcloud@52d34c34e93b29c603c20585433352b09e1504d9 # v2.1.0`

## 35

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

**CLAIM:** The specified commit SHA `a26af69be951a213d495a4c3e4e4022e16d87065` does not exist in the `actions/setup-python` repository, which will cause the workflow to fail.

**PROPOSED FIX:** `      - uses: actions/setup-python@82c7e631bb3cdc910f68e0081d67478d79c6982d # v5.1.0`

## 36

`Lightning-AI/pytorch-lightning#21858` — `src/lightning/fabric/plugins/precision/bitsandbytes.py:269`

```diff
             return int8params
 
-        def to_empty(self, *, device: _DEVICE, recurse: bool = True) -> Self:
+        def to_empty(self, *, device: Optional[_DEVICE], recurse: bool = True) -> Self:
+            assert device is not None
             if self.weight.device.type == "meta":
                 # need custom logic if int8params is on meta device
                 raise NotImplementedError
@@ -311,9 +310,9 @@ class _Linear4bit(bnb.nn.Linear4bit):
```

**CLAIM:** Using `assert` for API input validation is incorrect as assertions can be disabled, which would allow a `None` device to be passed to downstream code that does not expect it.

**PROPOSED FIX:** `if device is None:
    raise ValueError("to_empty() requires a 'device' but got None")`

## 37

`explosion/spaCy#13823` — `spacy/pipeline/factories.py:901`

```diff
+
+def make_nn_labeller(
+    nlp: Language, name: str, model: Model, labels: Optional[dict], target: str
+):
+    return MultitaskObjective(nlp.vocab, model, name, target=target)
+
+
+def make_morphologizer(
+    nlp: Language,
```

**CLAIM:** The `labels` parameter from the factory is ignored and not passed to the `MultitaskObjective` component, even though the `target` parameter is now correctly passed.

**PROPOSED FIX:** `    return MultitaskObjective(nlp.vocab, model, name, labels=labels, target=target)`

## 38

`explosion/spaCy#13627` — `website/meta/universe.json:294`

```diff
+                "nlp = spacy.load('fr_solipcysme')",
+                "for i in nlp(",
+                "'la MACHINE à (b)rouiller le temps s'est peut-être déraillée..?'",
+                "):",
+                "    print(",
+                "        i, ",
+                "        i.norm_, ",
+                "        i.pos_, ",
+                "        i.morph, ",
```

**CLAIM:** This line begins a `print` call that is split across multiple strings in the JSON array, resulting in syntactically invalid Python code.

**PROPOSED FIX:** `"    print(i, i.norm_, i.pos_, i.morph, i.lemma_, i.dep_, i._.tokentype, i._.vv_pos, i._.vv_morph)",`

## 39

`python-poetry/poetry#10881` — `src/poetry/repositories/http_repository.py:374`

```diff
                     info.requires_python = str(
-                        parse_constraint(info.requires_python or "^2.7").union(
-                            parse_constraint(py3_info.requires_python or "^3")
+                        parse_marker_version_constraint(
+                            info.requires_python or "^2.7"
+                        ).union(
+                            parse_marker_version_constraint(
+                                py3_info.requires_python or "^3"
+                            )
```

**CLAIM:** Using `or` to provide a default incorrectly treats an empty `requires_python` string, which signifies compatibility with any Python version, as a falsy value and wrongly applies the default constraint `^2.7`.

**PROPOSED FIX:** `                            info.requires_python if info.requires_python is not None else "^2.7"`

## 40

`python-poetry/poetry#10973` — `tests/masonry/builders/test_editable_builder.py:300`

```diff
+        assert f'"{tmp_venv.python}"' in console_cmd
+        assert f'"{tmp_venv.python.with_name("pythonw.exe")}"' in gui_cmd
+
+    dist_info = tmp_venv.site_packages.find(Path("simple_project-1.2.3.dist-info"))[0]
+    assert "[gui_scripts]\nfoo-gui=foo:bar\n" in dist_info.joinpath(
+        "entry_points.txt"
+    ).read_text(encoding="utf-8")
+
+    with dist_info.joinpath("RECORD").open(encoding="utf-8", newline="") as f:
```

**CLAIM:** The test assertion for the content of `entry_points.txt` is incorrect because it omits the spaces around the equals sign, which are present in the actual generated file.

**PROPOSED FIX:** `    assert "[gui_scripts]\nfoo-gui = foo:bar\n" in dist_info.joinpath(`

## 41

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

**CLAIM:** The requirement string assigned as the value in the `extras` dictionary is the raw string from the requirements file, which can include comments, making it an invalid requirement specifier for setuptools.

**PROPOSED FIX:** `        extras[req.name.lower().replace("-", "_")] = [str(req)]`

## 42

`explosion/spaCy#13510` — `spacy/lang/bo/lex_attrs.py:8`

```diff
+
+_num_words = [
+    "ཀླད་ཀོར་",
+    "གཅིག་", "གཉིས་", "གསུམ་", "བཞི་", "ལྔ་", "དྲུག་", "བདུན་", "བརྒྱད་", "དགུ་", "བཅུ་",
+    "བཅུ་གཅིག་", "བཅུ་གཉིས་", "བཅུ་གསུམ་", "བཅུ་བཞི་", "བཅུ་ལྔ་", "བཅུ་དྲུག་", "བཅུ་བདུན་", "བཅུ་པརྒྱད", "བཅུ་དགུ་", "ཉི་ཤུ་",
+    "སུམ་ཅུ", "བཞི་བཅུ", "ལྔ་བཅུ", "དྲུག་ཅུ", "བདུན་ཅུ", "བརྒྱད་ཅུ", "དགུ་བཅུ", "བརྒྱ་",
+    "སྟོང་", "ཁྲི་", "ས་ཡ་", "	བྱེ་བ་", "དུང་ཕྱུར་", "ཐེར་འབུམ་", "ཐེར་འབུམ་ཆེན་པོ་", "ཁྲག་ཁྲིག་", "ཁྲག་ཁྲིག་ཆེན་པོ་",
+]
+
```

**CLAIM:** The word for eighteen, "བཅུ་པརྒྱད", is misspelled, which will prevent it from being matched as a number.

**PROPOSED FIX:** `    "བཅུ་གཅིག་", "བཅུ་གཉིས་", "བཅུ་གསུམ་", "བཅུ་བཞི་", "བཅུ་ལྔ་", "བཅུ་དྲུག་", "བཅུ་བདུན་", "བཅོ་བརྒྱད་", "བཅུ་དགུ་", "ཉི་ཤུ་",`

## 43

`pylint-dev/pylint#11258` — `tests/functional/u/use/use_a_generator_py315.txt:2`

```diff
--- /dev/null
+++ b/tests/functional/u/use/use_a_generator_py315.txt
@@ -0,0 +1,2 @@
+use-a-generator:3:6:3:31::Use a generator instead 'any(*x for x in NESTED)':UNDEFINED
+use-a-generator:4:6:4:31::Use a generator instead 'all(*x for x in NESTED)':UNDEFINED
diff --git a/tests/functional/u/use/use_implicit_booleaness_not_len_py315.py b/tests/functional/u/use/use_implicit_booleaness_not_len_py315.py
new file mode 100644
index 00000000000..36802158515
--- /dev/null
```

**CLAIM:** The suggested code `all(*x for x in NESTED)` is syntactically invalid because a generator expression cannot contain a starred expression as its yielded element.

**PROPOSED FIX:** `use-a-generator:4:6:4:31::Use a generator instead 'all(item for sublist in NESTED for item in sublist)':UNDEFINED`

## 44

`urllib3/urllib3#5095` — `src/urllib3/util/url.py:412`

```diff
+        raise LocationParseError(f"{match.string!r} is not a valid host")
+    decoded_octet = _decode_percent_encoding(match, error_host=match.string)
+    if decoded_octet in _UNRESERVED_CHARS:
+        return decoded_octet
+    return match.group(0).upper()
+
+
+def _normalize_zone_id_percent_encoding(
+    match: re.Match[str], *, error_host: str
```

**CLAIM:** This line returns the original percent-encoded string instead of the decoded character, which prevents normalization of percent-encoded unreserved characters in IPv6 zone identifiers and can lead to double-encoding.

**PROPOSED FIX:** `if decoded_octet in _UNRESERVED_CHARS:
    return decoded_octet
return match.group(0).upper()`

## 45

`explosion/spaCy#13807` — `spacy/lang/ht/punctuation.py:16`

```diff
+)
+
+ELISION = "'’".replace(" ", "")
+
+_prefixes_elision = "m n l y t k w"
+_prefixes_elision += " " + _prefixes_elision.upper()
+
+TOKENIZER_PREFIXES = LIST_PUNCT + LIST_QUOTES + [
+    r"(?:({pe})[{el}])(?=[{a}])".format(
```

**CLAIM:** The list of elided prefixes is missing "p" for the negation "pa", which is included in tokenizer exceptions and normalization maps.

**PROPOSED FIX:** `_prefixes_elision = "m n l y t k p w"`
