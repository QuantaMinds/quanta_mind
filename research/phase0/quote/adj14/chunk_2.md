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

`Lightning-AI/pytorch-lightning#21743` — `src/lightning/fabric/utilities/throughput.py:424`

```diff
-        "int4": 619.3e12,
+        torch.float32: 3.87e13,
+        "tfloat32": 7.74e13,
+        torch.bfloat16: 3.87e13,
+        torch.float16: 3.87e13,
+        torch.int8: 3.097e14,
+        "int4": 6.193e14,
     },
+    # source: https://images.nvidia.com/content/Solutions/data-center/a40/nvidia-a40-datasheet.pdf
```

**CLAIM:** The float16 FLOPs for the A6000 GPU is incorrectly set to the FP32 rate, but it should be the higher dense Tensor Core rate.

**PROPOSED FIX:** `torch.float16: 7.74e13,`

## 92

`urllib3/urllib3#4967` — `src/urllib3/response.py:1106`

```diff
@@ -1102,6 +1103,8 @@ def read(
                 return self._decoded_buffer.get(amt)
 
         data = self._raw_read(amt)
+        if not cache_content:
+            self._uncached_read_occurred = True
 
         flush_decoder = amt is None or (amt != 0 and not data)
 
```

**CLAIM:** This condition is a logic error because it fails to prevent caching for a partial read when `cache_content` is true, which would lead to a partial response body being cached.

**PROPOSED FIX:** `        if not cache_content or amt is not None:`

## 93

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

**CLAIM:** This categorization is incorrect because it lumps new `useless-suppression` messages, which indicate fixed false-positives, into the generic `other_new` category.

**PROPOSED FIX:** `            "description":"In this course, I use the itables Python library inside a Jupyter notebook so that you can visualize the different spaCy document objects. This will provide a solid foundati`

## 94

`python-poetry/poetry#10906` — `tests/repositories/test_repository.py:111`

```diff
@@ -108,4 +108,5 @@ def test_search() -> None:
 
     assert repo.search("foo") == [package_foo1, package_foo2, package_foobar]
     assert repo.search("bar") == [package_foobar]
+    assert repo.search(["foo", "bar"]) == [package_foo1, package_foo2, package_foobar]
     assert repo.search("nothing") == []

```

**CLAIM:** This test incorrectly asserts OR logic for a multi-token search, whereas AND logic is the expected behavior and would only match packages containing both "foo" and "bar".

**PROPOSED FIX:** `assert repo.search(["foo", "bar"]) == [package_foobar]`

## 95

`pylint-dev/pylint#11232` — `pylint/checkers/base/name_checker/checker.py:594`

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

**CLAIM:** Checking for `TypedDict` by its simple name is fragile and can cause false positives on user-defined classes with the same name; the check should use the fully qualified name.

**PROPOSED FIX:** `            if inferred_assign_type._proxied.qname() == "typing.TypedDict":`

## 96

`explosion/spaCy#13621` — `spacy/strings.pyx:276`

```diff
-            return self._map.get(string_or_id) is not NULL
-
+            if self._map.get(string_or_id) is not NULL:
+                return True
+            elif self._transient_map is not None and self._transient_map.get(string_or_id) is not NULL:
+                return True
+            else:
+                return False
         if str_hash < len(SYMBOLS_BY_INT):
```

**CLAIM:** The lookup in the transient map incorrectly uses the original string `string_or_id` instead of its computed hash `str_hash`.

**PROPOSED FIX:** `elif self._transient_map is not None and self._transient_map.get(str_hash) is not NULL:`

## 97

`Lightning-AI/pytorch-lightning#21821` — `src/lightning/fabric/strategies/model_parallel.py:477`

```diff
     if _is_full_checkpoint(path):
-        checkpoint = torch.load(path, mmap=True, map_location="cpu", weights_only=weights_only)
+        weights_only = False if weights_only is None else weights_only
+        if _is_local_file_protocol(str(path)):
+            checkpoint = torch.load(path, mmap=True, map_location="cpu", weights_only=weights_only)
+        else:
+            checkpoint = _load(path, map_location="cpu", weights_only=weights_only)
         _load_raw_module_state(checkpoint.pop(module_key), module, strict=strict)
 
```

**CLAIM:** The `torch.load` function is called with `path`, which under the `if _is_local_file_protocol(str(path))` condition is an fsspec URL string that `torch.load` cannot handle.

**PROPOSED FIX:** `checkpoint = _load(path, map_location="cpu", weights_only=weights_only)`

## 98

`explosion/spaCy#13876` — `spacy/displacy/__init__.py:69`

```diff
     if jupyter or (jupyter is None and is_in_jupyter()):
         # return HTML rendered by IPython display()
         # See #4840 for details on span wrapper to disable mathjax
-        from IPython.core.display import HTML, display
+        from IPython.core.display import HTML
+        from IPython.display import display
 
         return display(HTML('<span class="tex2jax_ignore">{}</span>'.format(html)))
     return html
```

**CLAIM:** The `HTML` class is imported from an internal IPython API (`IPython.core.display`), which is not guaranteed to be stable, when it is available from the public API (`IPython.display`).

**PROPOSED FIX:** `from IPython.display import HTML, display`

## 99

`urllib3/urllib3#5140` — `src/urllib3/connectionpool.py:878`

```diff
+                # rewrite this warning. Ideally, we'd go with a better solution,
+                # but backwards compatibility and other constraints make those
+                # unfeasible, so this is the least bad option.
+                # See also: https://github.com/urllib3/urllib3/issues/2580.
+                extra={"__urllib3-retry-warning": {"host": self.host}},
             )
             return self.urlopen(
                 method,

```

**CLAIM:** The dictionary key `__urllib3-retry-warning` contains hyphens, making it an invalid Python identifier and preventing consumers from accessing it as a standard attribute on the log record.

**PROPOSED FIX:** `extra={"urllib3_retry_warning": {"host": self.host}},`

## 100

`explosion/spaCy#13603` — `spacy/about.py:3`

```diff
@@ -1,5 +1,5 @@
 # fmt: off
 __title__ = "spacy"
-__version__ = "3.7.5"
+__version__ = "3.7.6a"
 __download_url__ = "https://github.com/explosion/spacy-models/releases/download"
 __compatibility__ = "https://raw.githubusercontent.com/explosion/spacy-models/master/compatibility.json"

```

**CLAIM:** The version string "3.7.6a" is not compliant with PEP 440, as it is missing the required number after the 'a' pre-release identifier.

**PROPOSED FIX:** `__version__ = "3.7.6a0"`

## 101

`explosion/spaCy#13713` — `spacy/morphology.pyx:64`

```diff
+            self.strings.add(field, allow_transient=False),
+            field_id = self.strings[field]
             for value in values.split(self.VALUE_SEP):
+                field_sep_value = field + self.FIELD_SEP + value
+                self.strings.add(field_sep_value, allow_transient=False),
                 field_feature_pairs.append((
-                    self.strings.add(field),
-                    self.strings.add(field + self.FIELD_SEP + value),
+                    field_id,
```

**CLAIM:** The trailing comma creates a tuple that is immediately discarded, which is a logic error.

**PROPOSED FIX:** `self.strings.add(field_sep_value, allow_transient=False)`

## 102

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

**CLAIM:** The `labels` parameter from the factory is ignored and not passed to the `MultitaskObjective` component, even though the `target` parameter is now correctly passed.

**PROPOSED FIX:** `sa san si swa`

## 103

`urllib3/urllib3#5097` — `test/test_util.py:1221`

```diff
-        ],
-    )
+    candidate_version = [
+        (ssl.PROTOCOL_SSLv23, ssl.PROTOCOL_SSLv23),
+        ("PROTOCOL_SSLv23", ssl.PROTOCOL_SSLv23),
+        ("SSLv23", ssl.PROTOCOL_SSLv23),
+    ]
+    if hasattr(ssl, "PROTOCOL_TLSv1"):
+        candidate_version.extend(
```

**CLAIM:** The `resolve_ssl_version` function expects short protocol names (e.g. "SSLv23") and prepends "PROTOCOL_" itself, so this test case passing a prefixed string is incorrect and will fail.

**PROPOSED FIX:** `        # ("PROTOCOL_SSLv23", ssl.PROTOCOL_SSLv23),  # This test case is incorrect.`

## 104

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

**CLAIM:** The word for eighteen, "བཅུ་པརྒྱད", is misspelled, which will prevent it from being matched as a number.

**PROPOSED FIX:** `self.strings.add(field, allow_transient=False)`

## 105

`python-poetry/poetry#10907` — `tests/config/test_config.py:60`

```diff
+
+    assert policy.packages == frozenset({"black", "pytest"})
+    assert policy.allows("Poetry")
+    assert not policy.allows("PyTest")
+    assert policy.has_exact_package("PyTest")
+    assert not policy.has_exact_package("Poetry")
+
+
 @pytest.mark.parametrize(
```

**CLAIM:** The test incorrectly asserts that `has_exact_package("PyTest")` is true, but package names are stored in a normalized (lowercase) form, so an exact, case-sensitive match for "PyTest" should fail.

**PROPOSED FIX:** `assert not policy.has_exact_package("PyTest")`

## 106

`sqlalchemy/sqlalchemy#13351` — `test/orm/test_bind.py:528`

```diff
         )
 
+        assert_raises_message(
+            sa.exc.ArgumentError,
+            "Not an acceptable bind target: User()",
+            sess.bind_table,
+            u_object,
+            testing.db,
+        )
```

**CLAIM:** The test asserts an incorrect error message, as the string representation of a `User` instance (`u_object`) is not the hardcoded string "User()".

**PROPOSED FIX:** `f"Not an acceptable bind target: {u_object}",`

## 107

`urllib3/urllib3#5093` — `src/urllib3/connection.py:844`

```diff
+            wrapped_socket: ssl.SSLSocket | SSLTransport
             if self.proxy_is_forwarding and self.proxy_config is not None:
-                ssl_context = self.proxy_config.ssl_context
+                wrapped_socket = self._connect_tls_proxy(self.host, sock)
+                is_verified = self.proxy_is_verified is True
             else:
-                ssl_context = self.ssl_context
-
-            sock_and_verified = _ssl_wrap_socket_and_match_hostname(
```

**CLAIM:** This line causes the proxy's certificate verification status to be incorrectly reported as `False` because `self.proxy_is_verified` is `None` at this point in execution.

**PROPOSED FIX:** `# This logic is flawed. The verification status from `_connect_tls_proxy` is lost.
                # The line below will always evaluate to `False`.
                is_verified = self.proxy_is_verifie`

## 108

`sqlalchemy/sqlalchemy#12726` — `lib/sqlalchemy/ext/asyncio/result.py:857`

```diff
             """
             ...
 
-        async def __aiter__(self) -> AsyncIterator[_R]: ...
+        def __aiter__(self) -> AsyncIterator[_R]: ...
 
         async def __anext__(self) -> _R: ...
 

```

**CLAIM:** The word "pênciyemîn" is misspelled and should be "pêncîyemîn" to be consistent with the base number "pêncî" and the other ordinal form "pêncîyem".

**PROPOSED FIX:** `async def __aiter__(self) -> AsyncIterator[_R]: ...`

## 109

`explosion/spaCy#13760` — `spacy/util.py:120`

```diff
+    "hi": ["hin"],
+    "hr": ["hrv", "scr"], # "scr" is the deprecated ISO 639-2/B for Croatian
+    "hu": ["hun"],
+    "hy": ["hye"],
+    "id": ["ind", "in"], # "in" is the obsolete ISO 639-1 code for Hebrew
+    "is": ["isl", "ice"],
+    "it": ["ita"],
+    "ja": ["jpn"],
+    "kn": ["kan"],
```

**CLAIM:** The comment incorrectly states that "in" is an obsolete code for Hebrew, when it is actually the obsolete code for Indonesian.

**PROPOSED FIX:** `    "id": ["ind", "in"], # "in" is the obsolete ISO 639-1 code for Indonesian`

## 110

`explosion/spaCy#13922` — `spacy/cli/_util.py:71`

```diff
 Arg = typer.Argument
 Opt = typer.Option
 
-app = typer.Typer(name=NAME, help=HELP)
+app = typer.Typer(name=NAME, help=HELP, rich_markup_mode=None)
 benchmark_cli = typer.Typer(name="benchmark", help=BENCHMARK_HELP, no_args_is_help=True)
 debug_cli = typer.Typer(name="debug", help=DEBUG_HELP, no_args_is_help=True)
 init_cli = typer.Typer(name="init", help=INIT_HELP, no_args_is_help=True)

```

**CLAIM:** This change ineffectively disables rich text features because `rich_markup_mode=None` is the default value, and other rich features like pretty exceptions and help panels remain enabled.

**PROPOSED FIX:** `app = typer.Typer(name=NAME, help=HELP, pretty_exceptions_enable=False, rich_help_panel=None)`

## 111

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

**CLAIM:** Calling `splitext` with `is_filename=True` likely disables the special handling for compound extensions like `.tar.gz`, which will cause package name and version parsing to fail for some sdist formats.

**PROPOSED FIX:** `info, _ext = splitext(filename)`

## 112

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

**CLAIM:** This change introduces a logic error by removing the check for a simple `yield` inside an async function, which is a syntax error on Python 3.5 and was correctly flagged by the original code.

**PROPOSED FIX:** `if child.scope() is node and (
    sys.version_info[:2] == (3, 5) or isinstance(child, nodes.YieldFrom)
):`

## 113

`explosion/spaCy#13627` — `website/meta/universe.json:291`

```diff
+                "",
+                "import spacy",
+                "",
+                "nlp = spacy.load('fr_solipcysme')",
+                "for i in nlp(",
+                "'la MACHINE à (b)rouiller le temps s'est peut-être déraillée..?'",
+                "):",
+                "    print(",
+                "        i, ",
```

**CLAIM:** This line begins a `for` loop that is split across multiple strings in the JSON array, resulting in syntactically invalid Python code.

**PROPOSED FIX:** `"for i in nlp(\"la MACHINE à (b)rouiller le temps s'est peut-être déraillée..?\"):",`

## 114

`pylint-dev/pylint#11260` — `doc/exts/pylint_messages.py:504`

```diff
 
+def _get_newest_mtime(path: Path) -> float:
+    """Return the mtime of 'path', or the newest mtime it contains if it's a dir."""
+    if path.is_dir():
+        return max(
+            (_get_newest_mtime(child) for child in path.iterdir()),
+            default=path.stat().st_mtime,
+        )
+    return path.stat().st_mtime
```

**CLAIM:** The modification time of the directory itself is only considered when the directory is empty, but it should always be included as actions like file deletion update the directory's modification time.

**PROPOSED FIX:** `        child_mtimes = [_get_newest_mtime(child) for child in path.iterdir()]
        return max([path.stat().st_mtime] + child_mtimes)`
