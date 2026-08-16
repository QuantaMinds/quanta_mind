# Findings to adjudicate — chunk 1

There are 10 findings below, numbered by their global index.

### FINDING 10
repository: scrapy/scrapy   pull request #7986 (MERGED)
file: tests/test_http2_client_protocol.py
the model was shown this function: test_inactive_stream
claim_type: wrong_order   model_confidence: high
cited line_a: 616    cited line_b: 627

CLAIM: The test sends 100 requests to a fast endpoint, which can complete and free up a stream before the connection is closed, allowing one of the subsequent 10 requests that are expected to fail to instead succeed and trigger a test failure.

CODE AROUND line_a (616):
          608 |             from scrapy.core._http2.stream import InactiveStreamClosed  # noqa: PLC0415
          609 | 
          610 |             assert any(
          611 |                 isinstance(e, InactiveStreamClosed) for e in failure.value.reasons
          612 |             )
          613 | 
          614 |         # Send 100 request (we do not check the result)
          615 |         for _ in range(100):
    >>>   616 |             d = make_request_dfd(
          617 |                 client, Request(self.get_url(server_port, "/get-data-html-small"))
          618 |             )
          619 |             d.addBoth(lambda _: None)
          620 |             d_list.append(d)
          621 | 
          622 |         # Now send 10 extra request and save the response deferred in a list
          623 |         for _ in range(10):
          624 |             d = make_request_dfd(

CODE AROUND line_b (627):
          619 |             d.addBoth(lambda _: None)
          620 |             d_list.append(d)
          621 | 
          622 |         # Now send 10 extra request and save the response deferred in a list
          623 |         for _ in range(10):
          624 |             d = make_request_dfd(
          625 |                 client, Request(self.get_url(server_port, "/get-data-html-small"))
          626 |             )
    >>>   627 |             d.addCallback(lambda _: pytest.fail("This request should have failed"))
          628 |             d.addErrback(assert_inactive_stream)
          629 |             d_list.append(d)
          630 | 
          631 |         # Close the connection now to fire all the extra 10 requests errback
          632 |         # with InactiveStreamClosed
          633 |         assert client.transport
          634 |         client.transport.loseConnection()
          635 | 

---

### FINDING 11
repository: pandas-dev/pandas   pull request #65195 (MERGED)
file: pandas/tests/tools/test_to_datetime.py
the model was shown this function: test_dataframe_leap_year_valid
claim_type: contract_violation   model_confidence: high
cited line_a: 2394    cited line_b: 2395

CLAIM: The `expected` Series is created with a default `datetime64[ns]` dtype, but the implementation of `to_datetime` being tested now returns a `datetime64[us]` dtype for dataframe inputs without time components, causing `tm.assert_series_equal` to fail on a dtype mismatch.

CODE AROUND line_a (2394):
         2386 |             (
         2387 |                 {"year": [2001], "month": [2], "day": [28]},
         2388 |                 [Timestamp("2001-02-28")],
         2389 |             ),
         2390 |         ],
         2391 |     )
         2392 |     def test_dataframe_leap_year_valid(self, data, expected_ts):
         2393 |         result = to_datetime(DataFrame(data))
    >>>  2394 |         expected = Series(expected_ts)
         2395 |         tm.assert_series_equal(result, expected)
         2396 | 
         2397 |     @pytest.mark.parametrize(
         2398 |         "data",
         2399 |         [
         2400 |             {"year": [2001], "month": [2], "day": [29]},  # Feb 29 non-leap
         2401 |             {"year": [2020], "month": [4], "day": [31]},  # Apr 31
         2402 |             {"year": [2020], "month": [1], "day": [0]},  # day 0

CODE AROUND line_b (2395):
         2387 |                 {"year": [2001], "month": [2], "day": [28]},
         2388 |                 [Timestamp("2001-02-28")],
         2389 |             ),
         2390 |         ],
         2391 |     )
         2392 |     def test_dataframe_leap_year_valid(self, data, expected_ts):
         2393 |         result = to_datetime(DataFrame(data))
         2394 |         expected = Series(expected_ts)
    >>>  2395 |         tm.assert_series_equal(result, expected)
         2396 | 
         2397 |     @pytest.mark.parametrize(
         2398 |         "data",
         2399 |         [
         2400 |             {"year": [2001], "month": [2], "day": [29]},  # Feb 29 non-leap
         2401 |             {"year": [2020], "month": [4], "day": [31]},  # Apr 31
         2402 |             {"year": [2020], "month": [1], "day": [0]},  # day 0
         2403 |         ],

---

### FINDING 12
repository: ansible/ansible   pull request #87250 (MERGED)
file: lib/ansible/module_utils/basic.py
the model was shown this function: log
claim_type: missing_guard   model_confidence: high
cited line_a: 1243    cited line_b: 1257

CLAIM: The `log_args` parameter defaults to `None` at line 1243 and is passed to `_logging.log_to_system` at line 1258 without the prior code's guard to initialize it to a dictionary, likely causing a TypeError inside the called function.

CODE AROUND line_a (1243):
         1235 |         """
         1236 |         # debug overrides to read args from file or cmdline
         1237 |         self.params = _load_params()
         1238 | 
         1239 |     def debug(self, msg):
         1240 |         if self._debug:
         1241 |             self.log('[debug] %s' % msg)
         1242 | 
    >>>  1243 |     def log(self, msg, log_args=None):
         1244 | 
         1245 |         if self.no_log:
         1246 |             return
         1247 | 
         1248 |         if not isinstance(msg, (bytes, str)):
         1249 |             raise TypeError("msg should be a string (got %s)" % type(msg))
         1250 | 
         1251 |         if isinstance(msg, bytes):

CODE AROUND line_b (1257):
         1249 |             raise TypeError("msg should be a string (got %s)" % type(msg))
         1250 | 
         1251 |         if isinstance(msg, bytes):
         1252 |             msg = msg.decode('utf-8', 'replace')
         1253 | 
         1254 |         msg = remove_values(msg, self.no_log_values)
         1255 | 
         1256 |         try:
    >>>  1257 |             _logging.log_to_system(
         1258 |                 msg,
         1259 |                 module_name=self._name,
         1260 |                 log_args=log_args,
         1261 |                 syslog_facility=self._syslog_facility,
         1262 |                 target_log_info=self._target_log_info,
         1263 |             )
         1264 |         except (TypeError, ValueError) as e:
         1265 |             self.fail_json(

---

### FINDING 13
repository: django/django   pull request #21750 (MERGED)
file: tests/migrations/test_operations.py
the model was shown this function: test_alter_field_python_level_on_delete_noop
claim_type: wrong_order   model_confidence: high
cited line_a: 2598    cited line_b: 2600

CLAIM: The call to `database_forwards` at line 2598 incorrectly passes `project_state` as the `from_state` and `new_state` as the `to_state`, which causes the reverse call in `database_backwards` at line 2600 to fail with an `AttributeError` because its `from_state` and `to_state` arguments are then swapped, leading it to try to find a field on a model state where it no longer exists.

CODE AROUND line_a (2598):
         2590 |             .fields["pony"]
         2591 |             .remote_field.on_delete,
         2592 |             models.CASCADE,
         2593 |         )
         2594 |         self.assertIs(
         2595 |             new_state.models[app_label, "rider"].fields["pony"].remote_field.on_delete,
         2596 |             models.PROTECT,
         2597 |         )
    >>>  2598 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
         2599 |             operation.database_forwards(app_label, editor, project_state, new_state)
         2600 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
         2601 |             operation.database_backwards(app_label, editor, new_state, project_state)
         2602 | 
         2603 |     def test_alter_field_foreignobject_noop(self):
         2604 |         app_label = "test_alflfo_noop"
         2605 |         project_state = self.set_up_test_model(app_label)
         2606 |         project_state = self.apply_operations(

CODE AROUND line_b (2600):
         2592 |             models.CASCADE,
         2593 |         )
         2594 |         self.assertIs(
         2595 |             new_state.models[app_label, "rider"].fields["pony"].remote_field.on_delete,
         2596 |             models.PROTECT,
         2597 |         )
         2598 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
         2599 |             operation.database_forwards(app_label, editor, project_state, new_state)
    >>>  2600 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
         2601 |             operation.database_backwards(app_label, editor, new_state, project_state)
         2602 | 
         2603 |     def test_alter_field_foreignobject_noop(self):
         2604 |         app_label = "test_alflfo_noop"
         2605 |         project_state = self.set_up_test_model(app_label)
         2606 |         project_state = self.apply_operations(
         2607 |             app_label,
         2608 |             project_state,

---

### FINDING 14
repository: pandas-dev/pandas   pull request #66717 (MERGED)
file: pandas/core/indexes/multi.py
the model was shown this function: get_locs
claim_type: wrong_order   model_confidence: high
cited line_a: 4349    cited line_b: 4319

CLAIM: The check for unused codes at line 4351 is performed before handling duplicate codes in `k_codes`, causing it to incorrectly raise a `KeyError` if a label is duplicated in `k` and is used in `level_codes`, but not all of its duplicate appearances in `k_codes` are present in `used`.

CODE AROUND line_a (4349):
         4341 |                         # GH#64807 The non-NA labels the level does not have.
         4342 |                         #  Comparing the -1 count against na_count instead loses
         4343 |                         #  a missing label whenever the level carries an NA entry
         4344 |                         #  of its own, since get_indexer matches the NA label to
         4345 |                         #  it rather than returning -1.
         4346 |                         if (missing_mask & ~k_isna).any():
         4347 |                             raise KeyError(k) from None
         4348 |                         # NaN is in k but must also be present in the data
    >>>  4349 |                         if na_count and not lib.has_sentinel(level_codes, -1):
         4350 |                             raise KeyError(k) from None
         4351 |                         # GH#64807 Every missing non-NA label has raised by now,
         4352 |                         #  so the only -1 codes left stand for NA labels. Those
         4353 |                         #  are resolved by the (level_codes == -1) union below,
         4354 |                         #  never by a code: get_indexer may have matched one to
         4355 |                         #  an NA entry of the level, but the scalar path always
         4356 |                         #  resolves NA to -1, so drop them to agree with it.
         4357 |                         k_codes = k_codes[~k_isna]

CODE AROUND line_b (4319):
         4311 |                         #  DatetimeIndex/PeriodIndex) can map a single label to a
         4312 |                         #  *range* of positions (partial-string/partial-date
         4313 |                         #  slicing), and a level that is not unique for indexing
         4314 |                         #  purposes (e.g. an overlapping IntervalIndex, GH#27456)
         4315 |                         #  can map one label to several level entries. The
         4316 |                         #  exact-match vectorized path below cannot express
         4317 |                         #  either, so resolve each label individually.
         4318 |                         lvl_indexer = _resolve_each(k, i, indexer, err)
    >>>  4319 |                     elif len(k):
         4320 |                         # GH#55786 Vectorized path: use the level's hashtable to
         4321 |                         # map all labels to codes at once, then work in code
         4322 |                         # space instead of looping with per-element
         4323 |                         # _get_level_indexer.
         4324 |                         level_codes = self.codes[i]
         4325 |                         # get_indexer would redo the ensure_index above
         4326 |                         k_codes = level_index.get_indexer(target)
         4327 |                         # NaN labels are stored as code -1 and are absent

---

### FINDING 15
repository: scikit-learn/scikit-learn   pull request #34740 (MERGED)
file: sklearn/datasets/_lfw.py
the model was shown this function: _fetch_lfw_pairs
claim_type: unhandled_case   model_confidence: high
cited line_a: 432    cited line_b: 478

CLAIM: If the input index file contains no valid pair specifications, `n_pairs` will be 0 at line 445, leading `pairs` to be an empty array, which causes the in-place shape assignment at line 478 to raise a `ValueError`.

CODE AROUND line_a (432):
          424 |     )
          425 | 
          426 | 
          427 | #
          428 | # Task #2:  Face Verification on pairs of face pictures
          429 | #
          430 | 
          431 | 
    >>>   432 | def _fetch_lfw_pairs(
          433 |     index_file_path, data_folder_path, slice_=None, color=False, resize=None
          434 | ):
          435 |     """Perform the actual data loading for the LFW pairs dataset
          436 | 
          437 |     This operation is meant to be cached by a joblib wrapper.
          438 |     """
          439 |     # parse the index file to find the number of pairs to be able to allocate
          440 |     # the right amount of memory before starting to decode the jpeg files

CODE AROUND line_b (478):
          470 |             filenames = list(sorted(listdir(person_folder)))
          471 |             file_path = join(person_folder, filenames[idx])
          472 |             file_paths.append(file_path)
          473 | 
          474 |     pairs = _load_imgs(file_paths, slice_, color, resize)
          475 |     shape = list(pairs.shape)
          476 |     n_faces = shape.pop(0)
          477 |     shape.insert(0, 2)
    >>>   478 |     shape.insert(0, n_faces // 2)
          479 |     pairs = pairs.reshape(shape)
          480 | 
          481 |     return pairs, target, np.array(["Different persons", "Same person"])
          482 | 
          483 | 
          484 | @validate_params(
          485 |     {
          486 |         "subset": [StrOptions({"train", "test", "10_folds"})],

---

### FINDING 16
repository: django/django   pull request #21752 (MERGED)
file: tests/forms_tests/tests/test_media.py
the model was shown this function: test_html_safe_string_merging
claim_type: wrong_order   model_confidence: high
cited line_a: 902    cited line_b: 911

CLAIM: The JavaScript list for m1 is `["/path/to/js1", js_tag]`, which is reordered to `[js_tag, "/path/to/js1"]` during Media object construction, so the assertion for JavaScript order in the merged media is incorrect.

CODE AROUND line_a (902):
          894 |             '<script src="/path/to/js1"></script>',
          895 |         )
          896 | 
          897 |     def test_html_safe_string_merging(self):
          898 |         js_tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
          899 |         css_tag = mark_safe(
          900 |             '<link href="https://example.org/asset.css" rel="stylesheet">'
          901 |         )
    >>>   902 |         m1 = Media(
          903 |             css={"all": [css_tag, "/path/to/css1"]},
          904 |             js=["/path/to/js1", js_tag],
          905 |         )
          906 |         m2 = Media(
          907 |             css={"all": [css_tag]},
          908 |             js=[js_tag, Script("/path/to/js2")],
          909 |         )
          910 |         merged = m1 + m2

CODE AROUND line_b (911):
          903 |             css={"all": [css_tag, "/path/to/css1"]},
          904 |             js=["/path/to/js1", js_tag],
          905 |         )
          906 |         m2 = Media(
          907 |             css={"all": [css_tag]},
          908 |             js=[js_tag, Script("/path/to/js2")],
          909 |         )
          910 |         merged = m1 + m2
    >>>   911 |         self.assertHTMLEqual(
          912 |             str(merged),
          913 |             '<link href="https://example.org/asset.css" rel="stylesheet">\n'
          914 |             '<link href="/path/to/css1" media="all" rel="stylesheet">\n'
          915 |             '<script src="/path/to/js1"></script>\n'
          916 |             '<script defer src="https://example.org/asset.js"></script>\n'
          917 |             '<script src="/path/to/js2"></script>',
          918 |         )
          919 | 

---

### FINDING 17
repository: celery/celery   pull request #10420 (MERGED)
file: celery/schedules.py
the model was shown this function: remaining_delta
claim_type: unhandled_case   model_confidence: high
cited line_a: 627    cited line_b: 627

CLAIM: When `self.day_of_week` is an empty set, the expression `[day for day in self.day_of_week if day > dow_num] or self.day_of_week` evaluates to an empty set, causing `min()` to be called on an empty sequence which raises a `ValueError`.

CODE AROUND line_a (627):
          619 |                                 if hour > last_run_at.hour)
          620 |                 delta = ffwd(hour=next_hour, minute=next_minute,
          621 |                              second=0, microsecond=0)
          622 |             else:
          623 |                 next_hour = min(self.hour)
          624 |                 all_dom_moy = (self._orig_day_of_month == '*' and
          625 |                                self._orig_month_of_year == '*')
          626 |                 if all_dom_moy:
    >>>   627 |                     next_day = min([day for day in self.day_of_week
          628 |                                     if day > dow_num] or self.day_of_week)
          629 |                     add_week = next_day == dow_num
          630 | 
          631 |                     delta = ffwd(
          632 |                         weeks=add_week and 1 or 0,
          633 |                         weekday=(next_day - 1) % 7,
          634 |                         hour=next_hour,
          635 |                         minute=next_minute,

CODE AROUND line_b (627):
          619 |                                 if hour > last_run_at.hour)
          620 |                 delta = ffwd(hour=next_hour, minute=next_minute,
          621 |                              second=0, microsecond=0)
          622 |             else:
          623 |                 next_hour = min(self.hour)
          624 |                 all_dom_moy = (self._orig_day_of_month == '*' and
          625 |                                self._orig_month_of_year == '*')
          626 |                 if all_dom_moy:
    >>>   627 |                     next_day = min([day for day in self.day_of_week
          628 |                                     if day > dow_num] or self.day_of_week)
          629 |                     add_week = next_day == dow_num
          630 | 
          631 |                     delta = ffwd(
          632 |                         weeks=add_week and 1 or 0,
          633 |                         weekday=(next_day - 1) % 7,
          634 |                         hour=next_hour,
          635 |                         minute=next_minute,

---

### FINDING 18
repository: scrapy/scrapy   pull request #7986 (MERGED)
file: tests/test_http2_client_protocol.py
the model was shown this function: test_connection_timeout
claim_type: contract_violation   model_confidence: high
cited line_a: 734    cited line_b: 743

CLAIM: Setting a 1-second timeout at line 734 triggers a generic transport timeout, but the assertion at line 744 incorrectly checks for an error message specific to the much longer application-level idle timeout.

CODE AROUND line_a (734):
          726 | 
          727 |     @inlineCallbacks
          728 |     def test_connection_timeout(
          729 |         self, server_port: int, client: H2ClientProtocol
          730 |     ) -> Generator[Deferred[Any], Any, None]:
          731 |         request = Request(self.get_url(server_port, "/timeout"))
          732 | 
          733 |         # Update the timer to 1s to test connection timeout
    >>>   734 |         client.setTimeout(1)  # type: ignore[no-untyped-call]
          735 | 
          736 |         with pytest.raises(ResponseFailed) as exc_info:
          737 |             yield make_request_dfd(client, request)
          738 | 
          739 |         for err in exc_info.value.reasons:
          740 |             from scrapy.core._http2.protocol import H2ClientProtocol  # noqa: PLC0415
          741 | 
          742 |             if isinstance(err, DownloadTimeoutError):

CODE AROUND line_b (743):
          735 | 
          736 |         with pytest.raises(ResponseFailed) as exc_info:
          737 |             yield make_request_dfd(client, request)
          738 | 
          739 |         for err in exc_info.value.reasons:
          740 |             from scrapy.core._http2.protocol import H2ClientProtocol  # noqa: PLC0415
          741 | 
          742 |             if isinstance(err, DownloadTimeoutError):
    >>>   743 |                 assert (
          744 |                     f"Connection was IDLE for more than {H2ClientProtocol.IDLE_TIMEOUT}s"
          745 |                     in str(err)
          746 |                 )
          747 |                 break
          748 |         else:
          749 |             pytest.fail("No TimeoutError raised.")
          750 | 
          751 |     @deferred_f_from_coro_f

---

### FINDING 19
repository: django/django   pull request #21750 (MERGED)
file: tests/schema/tests.py
the model was shown this function: test_fk_alter_on_delete_python_level_noop
claim_type: unhandled_case   model_confidence: high
cited line_a: 655    cited line_b: 655

CLAIM: The test `test_fk_alter_on_delete_python_level_noop` wrongly asserts that changing a ForeignKey's `on_delete` from `PROTECT` back to `CASCADE` results in zero database queries, but this change requires altering the foreign key constraint which is not a no-op.

CODE AROUND line_a (655):
          647 |             editor.create_model(Book)
          648 |         old_field = Book._meta.get_field("author")
          649 |         new_field = ForeignKey(Author, PROTECT)
          650 |         new_field.set_attributes_from_name("author")
          651 |         # Changing between Python-level on_delete options doesn't require
          652 |         # database changes.
          653 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
          654 |             editor.alter_field(Book, old_field, new_field, strict=True)
    >>>   655 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
          656 |             editor.alter_field(Book, new_field, old_field, strict=True)
          657 | 
          658 |     @isolate_apps("schema")
          659 |     @skipUnlessDBFeature("supports_foreign_keys", "can_introspect_foreign_keys")
          660 |     def test_fk_alter_on_delete_db_level(self):
          661 |         class DBOnDeleteParent(Model):
          662 |             class Meta:
          663 |                 app_label = "schema"

CODE AROUND line_b (655):
          647 |             editor.create_model(Book)
          648 |         old_field = Book._meta.get_field("author")
          649 |         new_field = ForeignKey(Author, PROTECT)
          650 |         new_field.set_attributes_from_name("author")
          651 |         # Changing between Python-level on_delete options doesn't require
          652 |         # database changes.
          653 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
          654 |             editor.alter_field(Book, old_field, new_field, strict=True)
    >>>   655 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
          656 |             editor.alter_field(Book, new_field, old_field, strict=True)
          657 | 
          658 |     @isolate_apps("schema")
          659 |     @skipUnlessDBFeature("supports_foreign_keys", "can_introspect_foreign_keys")
          660 |     def test_fk_alter_on_delete_db_level(self):
          661 |         class DBOnDeleteParent(Model):
          662 |             class Meta:
          663 |                 app_label = "schema"
