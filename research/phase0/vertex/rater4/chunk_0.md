# Findings to adjudicate — chunk 0

There are 10 findings below, numbered by their global index.

### FINDING 0
repository: django/django   pull request #21773 (MERGED)
file: django/db/models/fields/tuple_lookups.py
the model was shown this function: check_rhs_is_supported_expression
claim_type: contract_violation   model_confidence: high
cited line_a: 77    cited line_b: 80

CLAIM: The check at line 77 is updated to allow `ColPairs` as a valid type for the right-hand side, but the error message raised at line 80 for invalid types was not updated to mention `ColPairs` as a supported type.

CODE AROUND line_a (77):
           69 |         len_lhs = len(self.lhs)
           70 |         if len_lhs != len(self.rhs):
           71 |             lhs_str = self.get_lhs_str()
           72 |             raise ValueError(
           73 |                 f"{self.lookup_name!r} lookup of {lhs_str} must have {len_lhs} elements"
           74 |             )
           75 | 
           76 |     def check_rhs_is_supported_expression(self):
    >>>    77 |         if not isinstance(self.rhs, (ColPairs, ResolvedOuterRef, Query)):
           78 |             lhs_str = self.get_lhs_str()
           79 |             rhs_cls = self.rhs.__class__.__name__
           80 |             raise ValueError(
           81 |                 f"{self.lookup_name!r} subquery lookup of {lhs_str} "
           82 |                 f"only supports OuterRef and QuerySet objects (received {rhs_cls!r})"
           83 |             )
           84 | 
           85 |     def get_lhs_str(self):

CODE AROUND line_b (80):
           72 |             raise ValueError(
           73 |                 f"{self.lookup_name!r} lookup of {lhs_str} must have {len_lhs} elements"
           74 |             )
           75 | 
           76 |     def check_rhs_is_supported_expression(self):
           77 |         if not isinstance(self.rhs, (ColPairs, ResolvedOuterRef, Query)):
           78 |             lhs_str = self.get_lhs_str()
           79 |             rhs_cls = self.rhs.__class__.__name__
    >>>    80 |             raise ValueError(
           81 |                 f"{self.lookup_name!r} subquery lookup of {lhs_str} "
           82 |                 f"only supports OuterRef and QuerySet objects (received {rhs_cls!r})"
           83 |             )
           84 | 
           85 |     def get_lhs_str(self):
           86 |         if isinstance(self.lhs, ColPairs):
           87 |             return repr(self.lhs.field.name)
           88 |         else:

---

### FINDING 1
repository: pandas-dev/pandas   pull request #66717 (MERGED)
file: pandas/tests/indexes/multi/test_indexing.py
the model was shown this function: test_get_locs_list_like_not_a_list
claim_type: unhandled_case   model_confidence: high
cited line_a: 1092    cited line_b: 1103

CLAIM: The test creates a key from a set `lambda: {1, 2}`, whose iteration order is not guaranteed, but compares the result against a hardcoded array `np.array([0, 1])` that assumes a specific order, making the test non-deterministic.

CODE AROUND line_a (1092):
         1084 | 
         1085 | 
         1086 | @pytest.mark.parametrize(
         1087 |     "make_key",
         1088 |     [
         1089 |         lambda: range(1, 3),
         1090 |         lambda: (val for val in [1, 2]),
         1091 |         lambda: {1, 2},
    >>>  1092 |         lambda: {1: None, 2: None},
         1093 |     ],
         1094 | )
         1095 | def test_get_locs_list_like_not_a_list(make_key):
         1096 |     # GH#64807 - a level key that is list-like but neither a list nor an array
         1097 |     #  (range/generator/set/dict) must select the same rows as the equivalent
         1098 |     #  list. Ordering is a separate matter: reordering an unordered container
         1099 |     #  raises here, both before and after GH#64807.
         1100 |     idx = MultiIndex.from_product([["a", "b"], [1, 2, 3]])

CODE AROUND line_b (1103):
         1095 | def test_get_locs_list_like_not_a_list(make_key):
         1096 |     # GH#64807 - a level key that is list-like but neither a list nor an array
         1097 |     #  (range/generator/set/dict) must select the same rows as the equivalent
         1098 |     #  list. Ordering is a separate matter: reordering an unordered container
         1099 |     #  raises here, both before and after GH#64807.
         1100 |     idx = MultiIndex.from_product([["a", "b"], [1, 2, 3]])
         1101 |     result = idx.get_locs((["a"], make_key()))
         1102 |     expected = np.array([0, 1], dtype=np.intp)
    >>>  1103 |     tm.assert_numpy_array_equal(result, expected)
         1104 | 
         1105 | 
         1106 | def test_get_locs_list_like_not_a_list_with_na():
         1107 |     # GH#64807 - the NA inside a non-list list-like has to survive into the code
         1108 |     #  bookkeeping; isna() on the container itself is a scalar, not elementwise
         1109 |     idx = MultiIndex.from_arrays([["a", "a", "a"], [1.0, np.nan, 3.0]])
         1110 |     result = idx.get_locs((slice(None), {1.0: 0, np.nan: 0}))
         1111 |     tm.assert_numpy_array_equal(result, np.array([0, 1], dtype=np.intp))

---

### FINDING 2
repository: celery/celery   pull request #10459 (MERGED)
file: t/unit/backends/test_rpc.py
the model was shown this function: test_final_state_cached_when_cache_enabled
claim_type: resource_leak   model_confidence: high
cited line_a: 359    cited line_b: 361

CLAIM: Creating an `RPCBackend` instance at line 361 starts a consumer thread, but this instance is local to the `try` block and there is no corresponding `b.close()` or `b.stop()` call to terminate the thread before the function returns.

CODE AROUND line_a (359):
          351 |         assert meta['result'] == 42
          352 |         message.ack.assert_called_once_with()
          353 |         message.requeue.assert_not_called()
          354 | 
          355 |     def test_final_state_cached_when_cache_enabled(self):
          356 |         # the test app sets result_cache_max=-1 (cache disabled),
          357 |         # with caching on the final meta is served from the cache.
          358 |         old_cache_max = self.app.conf.result_cache_max
    >>>   359 |         self.app.conf.result_cache_max = 100
          360 |         try:
          361 |             b = RPCBackend(app=self.app)
          362 |             message = self.make_message('tid1', states.SUCCESS, 42)
          363 |             with patch.object(b, '_slurp_from_queue',
          364 |                               return_value=iter([message])):
          365 |                 b.get_task_meta('tid1')
          366 |             assert b._cache['tid1']['status'] == states.SUCCESS
          367 |             with patch.object(b, '_slurp_from_queue',

CODE AROUND line_b (361):
          353 |         message.requeue.assert_not_called()
          354 | 
          355 |     def test_final_state_cached_when_cache_enabled(self):
          356 |         # the test app sets result_cache_max=-1 (cache disabled),
          357 |         # with caching on the final meta is served from the cache.
          358 |         old_cache_max = self.app.conf.result_cache_max
          359 |         self.app.conf.result_cache_max = 100
          360 |         try:
    >>>   361 |             b = RPCBackend(app=self.app)
          362 |             message = self.make_message('tid1', states.SUCCESS, 42)
          363 |             with patch.object(b, '_slurp_from_queue',
          364 |                               return_value=iter([message])):
          365 |                 b.get_task_meta('tid1')
          366 |             assert b._cache['tid1']['status'] == states.SUCCESS
          367 |             with patch.object(b, '_slurp_from_queue',
          368 |                               return_value=iter([])):
          369 |                 assert b.get_task_meta('tid1')['result'] == 42

---

### FINDING 3
repository: pandas-dev/pandas   pull request #65195 (MERGED)
file: pandas/core/tools/datetimes.py
the model was shown this function: _assemble_from_unit_mappings
claim_type: missing_guard   model_confidence: high
cited line_a: 1396    cited line_b: 1439

CLAIM: The `coerce` call at line 1404 converts boolean columns to integer type, so the check `is_bool_dtype(vals.dtype)` at line 1439 is always false, causing boolean values in 'year', 'month', or 'day' columns to be incorrectly treated as numeric components instead of raising an error or being converted to NaT.

CODE AROUND line_a (1396):
         1388 |         arr = np.asarray(vals)
         1389 | 
         1390 |         if field in ("h", "m", "s"):
         1391 |             # the npy_datetimestruct time fields are int32
         1392 |             if is_integer_dtype(arr.dtype):
         1393 |                 fits_struct = len(arr) == 0 or (
         1394 |                     arr.min() >= i32info.min and arr.max() <= i32info.max
         1395 |                 )
    >>>  1396 |             elif is_float_dtype(arr.dtype):
         1397 |                 fits_struct = bool(
         1398 |                     (
         1399 |                         (arr == np.floor(arr))
         1400 |                         & (arr >= i32info.min)
         1401 |                         & (arr <= i32info.max)
         1402 |                     ).all()
         1403 |                 )
         1404 |             else:

CODE AROUND line_b (1439):
         1431 |             )
         1432 |         # +/-inf and values beyond int64 range cannot be cast meaningfully
         1433 |         out_of_range = (arr >= 2**63) | (arr < -(2**63))
         1434 |         if out_of_range.any() and errors == "raise":
         1435 |             raise ValueError(
         1436 |                 f"cannot assemble the datetimes: column {col_name!r} "
         1437 |                 f"contains out-of-bounds values"
         1438 |             )
    >>>  1439 |         bad = isnan | fractional | out_of_range
         1440 |         if bad.any():
         1441 |             nan_mask[bad] = True
         1442 |             arr = np.where(bad, default, arr)
         1443 |         field_arrs.append(arr.astype(np.int64))
         1444 | 
         1445 |     # Construct datetime64[us] directly from fields, avoiding the
         1446 |     # object-dtype round-trip through format="%Y%m%d" string parsing.
         1447 |     # Rows with NaN in a year/month/day column get valid placeholders in

---

### FINDING 4
repository: celery/celery   pull request #10298 (MERGED)
file: celery/backends/redis.py
the model was shown this function: _reconnect_pubsub
claim_type: unhandled_case   model_confidence: high
cited line_a: 111    cited line_b: 111

CLAIM: When reconnecting with no active subscriptions, the connection acquired at line 114 is not configured with an `on_connect` callback, which prevents the client from automatically re-subscribing to channels if they are added later and the connection subsequently drops.

CODE AROUND line_a (111):
          103 |             metas = self.backend.client.mget(self.subscribed_to)
          104 |             metas = [meta for meta in metas if meta]
          105 |             for meta in metas:
          106 |                 self.on_state_change(self._decode_result(meta), None)
          107 |         self._pubsub = self.backend.client.pubsub(
          108 |             ignore_subscribe_messages=True,
          109 |         )
          110 |         # subscribed_to maybe empty after on_state_change
    >>>   111 |         if self.subscribed_to:
          112 |             self._pubsub.subscribe(*self.subscribed_to)
          113 |         else:
          114 |             # redis-py < 5.3.0 requires ``command_name`` as a positional
          115 |             # argument to ``ConnectionPool.get_connection``. The argument was
          116 |             # made optional (and ignored) in 5.3.0+, so passing it stays
          117 |             # compatible across both ranges (#10294).
          118 |             try:
          119 |                 self._pubsub.connection = (

CODE AROUND line_b (111):
          103 |             metas = self.backend.client.mget(self.subscribed_to)
          104 |             metas = [meta for meta in metas if meta]
          105 |             for meta in metas:
          106 |                 self.on_state_change(self._decode_result(meta), None)
          107 |         self._pubsub = self.backend.client.pubsub(
          108 |             ignore_subscribe_messages=True,
          109 |         )
          110 |         # subscribed_to maybe empty after on_state_change
    >>>   111 |         if self.subscribed_to:
          112 |             self._pubsub.subscribe(*self.subscribed_to)
          113 |         else:
          114 |             # redis-py < 5.3.0 requires ``command_name`` as a positional
          115 |             # argument to ``ConnectionPool.get_connection``. The argument was
          116 |             # made optional (and ignored) in 5.3.0+, so passing it stays
          117 |             # compatible across both ranges (#10294).
          118 |             try:
          119 |                 self._pubsub.connection = (

---

### FINDING 5
repository: scrapy/scrapy   pull request #7946 (MERGED)
file: scrapy/core/spidermw.py
the model was shown this function: process_start
claim_type: contract_violation   model_confidence: high
cited line_a: 247    cited line_b: 247

CLAIM: Calling `close()` on a newly-created coroutine object `start` that has not been started raises a `TypeError`.

CODE AROUND line_a (247):
          239 |             else:
          240 |                 msg = (
          241 |                     "Passing a spider argument to SpiderMiddlewareManager.process_start() is deprecated,"
          242 |                     " SpiderMiddlewareManager should be instantiated with a Crawler instance instead."
          243 |                 )
          244 |             warn(msg, category=ScrapyDeprecationWarning, stacklevel=2)
          245 |             self._set_compat_spider(spider)
          246 |         start = self._spider.start()
    >>>   247 |         if not hasattr(start, "__aiter__"):
          248 |             if iscoroutine(start):
          249 |                 start.close()
          250 |             start = self._reject_start(start)
          251 |         return await self._process_chain("process_start", start)
          252 | 
          253 |     async def _reject_start(self, start: Any) -> AsyncIterator[Any]:
          254 |         raise TypeError(
          255 |             f"{global_object_name(type(self._spider))}.start() must be an"

CODE AROUND line_b (247):
          239 |             else:
          240 |                 msg = (
          241 |                     "Passing a spider argument to SpiderMiddlewareManager.process_start() is deprecated,"
          242 |                     " SpiderMiddlewareManager should be instantiated with a Crawler instance instead."
          243 |                 )
          244 |             warn(msg, category=ScrapyDeprecationWarning, stacklevel=2)
          245 |             self._set_compat_spider(spider)
          246 |         start = self._spider.start()
    >>>   247 |         if not hasattr(start, "__aiter__"):
          248 |             if iscoroutine(start):
          249 |                 start.close()
          250 |             start = self._reject_start(start)
          251 |         return await self._process_chain("process_start", start)
          252 | 
          253 |     async def _reject_start(self, start: Any) -> AsyncIterator[Any]:
          254 |         raise TypeError(
          255 |             f"{global_object_name(type(self._spider))}.start() must be an"

---

### FINDING 6
repository: pandas-dev/pandas   pull request #65195 (MERGED)
file: pandas/tests/tools/test_to_datetime.py
the model was shown this function: test_dataframe_time_field_outside_int32_valid
claim_type: contract_violation   model_confidence: high
cited line_a: 2521    cited line_b: 2522

CLAIM: The expected `Series` is created with `datetime64[us]` dtype, but `to_datetime` with a DataFrame argument returns a `Series` with `datetime64[ns]` dtype, causing `tm.assert_series_equal` to fail due to a dtype mismatch.

CODE AROUND line_a (2521):
         2513 |     )
         2514 |     def test_dataframe_time_field_outside_int32_valid(
         2515 |         self, year, field, value, exp_str
         2516 |     ):
         2517 |         # values outside int32 range that still produce an in-bounds
         2518 |         #  datetime go through the to_timedelta fallback
         2519 |         df = DataFrame({"year": [year], "month": [1], "day": [1], field: [value]})
         2520 |         result = to_datetime(df)
    >>>  2521 |         expected = Series(np.array([exp_str], dtype="datetime64[us]"))
         2522 |         tm.assert_series_equal(result, expected)
         2523 | 
         2524 |     def test_dataframe_infinite_float(self):
         2525 |         # +/-inf cannot be cast to int64; previously produced garbage values
         2526 |         df = DataFrame({"year": [2000.0, np.inf], "month": [1, 1], "day": [1, 1]})
         2527 |         msg = "cannot assemble the datetimes: column 'year' contains out-of-bounds"
         2528 |         with pytest.raises(ValueError, match=msg):
         2529 |             with tm.assert_produces_warning(None):

CODE AROUND line_b (2522):
         2514 |     def test_dataframe_time_field_outside_int32_valid(
         2515 |         self, year, field, value, exp_str
         2516 |     ):
         2517 |         # values outside int32 range that still produce an in-bounds
         2518 |         #  datetime go through the to_timedelta fallback
         2519 |         df = DataFrame({"year": [year], "month": [1], "day": [1], field: [value]})
         2520 |         result = to_datetime(df)
         2521 |         expected = Series(np.array([exp_str], dtype="datetime64[us]"))
    >>>  2522 |         tm.assert_series_equal(result, expected)
         2523 | 
         2524 |     def test_dataframe_infinite_float(self):
         2525 |         # +/-inf cannot be cast to int64; previously produced garbage values
         2526 |         df = DataFrame({"year": [2000.0, np.inf], "month": [1, 1], "day": [1, 1]})
         2527 |         msg = "cannot assemble the datetimes: column 'year' contains out-of-bounds"
         2528 |         with pytest.raises(ValueError, match=msg):
         2529 |             with tm.assert_produces_warning(None):
         2530 |                 to_datetime(df)

---

### FINDING 7
repository: scrapy/scrapy   pull request #7985 (MERGED)
file: tests/utils/bases/download_handlers_http.py
the model was shown this function: test_download_with_spider
claim_type: missing_guard   model_confidence: high
cited line_a: 1573    cited line_b: 1575

CLAIM: If the crawl fails due to a timeout or other error, `crawler.spider` is not assigned, causing line 1575 to raise an AttributeError when accessing `crawler.spider.meta`.

CODE AROUND line_a (1573):
         1565 |     async def test_download_with_spider(self) -> None:
         1566 |         crawler = get_crawler(
         1567 |             SingleRequestSpider, {**REAL_WEBSITE_SETTINGS, **(self.settings_dict or {})}
         1568 |         )
         1569 |         await maybe_deferred_to_future(
         1570 |             crawler.crawl(seed=Request("https://books.toscrape.com/"))
         1571 |         )
         1572 |         assert isinstance(crawler.spider, SingleRequestSpider)
    >>>  1573 |         failure = crawler.spider.meta.get("failure")
         1574 |         assert failure is None
         1575 |         reason = crawler.spider.meta["close_reason"]
         1576 |         assert reason == "finished"
         1577 | 
         1578 |     @coroutine_test
         1579 |     async def test_verify_certs(self) -> None:
         1580 |         if not self.platform_cert_store_works:
         1581 |             pytest.skip("Cannot verify certificates")

CODE AROUND line_b (1575):
         1567 |             SingleRequestSpider, {**REAL_WEBSITE_SETTINGS, **(self.settings_dict or {})}
         1568 |         )
         1569 |         await maybe_deferred_to_future(
         1570 |             crawler.crawl(seed=Request("https://books.toscrape.com/"))
         1571 |         )
         1572 |         assert isinstance(crawler.spider, SingleRequestSpider)
         1573 |         failure = crawler.spider.meta.get("failure")
         1574 |         assert failure is None
    >>>  1575 |         reason = crawler.spider.meta["close_reason"]
         1576 |         assert reason == "finished"
         1577 | 
         1578 |     @coroutine_test
         1579 |     async def test_verify_certs(self) -> None:
         1580 |         if not self.platform_cert_store_works:
         1581 |             pytest.skip("Cannot verify certificates")
         1582 |         request = Request("https://books.toscrape.com/")
         1583 |         async with self.get_dh(

---

### FINDING 8
repository: scikit-learn/scikit-learn   pull request #34741 (MERGED)
file: sklearn/datasets/_arff_parser.py
the model was shown this function: _liac_arff_parser
claim_type: wrong_order   model_confidence: high
cited line_a: 272    cited line_b: 262

CLAIM: The assignment at line 272 swaps the row and column indices because it uses `arff_data[1]` (which is `(rows, cols)`) instead of `arff_data[1][0]` (which is `rows`), causing line 273 to use the wrong indices when creating the sparse array.

CODE AROUND line_a (272):
          264 |             num_obs = max(arff_data[1]) + 1
          265 |             X_shape = (num_obs, len(feature_indices_to_select))
          266 |             X = sp.sparse.coo_array(
          267 |                 (arff_data_X[0], (arff_data_X[1], arff_data_X[2])),
          268 |                 shape=X_shape,
          269 |                 dtype=np.float64,
          270 |             )
          271 |             X = _align_api_if_sparse(X.tocsr())
    >>>   272 |             y = _sparse_data_to_array(arff_data, target_indices_to_select)
          273 |         else:
          274 |             # This should never happen
          275 |             raise ValueError(
          276 |                 f"Unexpected type for data obtained from arff: {type(arff_data)}"
          277 |             )
          278 | 
          279 |         is_classification = {
          280 |             col_name in categories for col_name in target_names_to_select

CODE AROUND line_b (262):
          254 |             data = np.fromiter(
          255 |                 itertools.chain.from_iterable(arff_data),
          256 |                 dtype="float64",
          257 |                 count=count,
          258 |             )
          259 |             data = data.reshape(*shape)
          260 |             X = data[:, feature_indices_to_select]
          261 |             y = data[:, target_indices_to_select]
    >>>   262 |         elif isinstance(arff_data, tuple):
          263 |             arff_data_X = _split_sparse_columns(arff_data, feature_indices_to_select)
          264 |             num_obs = max(arff_data[1]) + 1
          265 |             X_shape = (num_obs, len(feature_indices_to_select))
          266 |             X = sp.sparse.coo_array(
          267 |                 (arff_data_X[0], (arff_data_X[1], arff_data_X[2])),
          268 |                 shape=X_shape,
          269 |                 dtype=np.float64,
          270 |             )

---

### FINDING 9
repository: django/django   pull request #21724 (MERGED)
file: django/db/models/base.py
the model was shown this function: _perform_unique_checks
claim_type: unhandled_case   model_confidence: high
cited line_a: 1556    cited line_b: 1587

CLAIM: The condition at line 1559 fails to account for field values of type `DatabaseDefault`, causing such values to be passed to `model_class._default_manager.filter()` at line 1587, which in turn raises an unhandled `NotSupportedError` because `DatabaseDefault` expressions cannot be used in queries.

CODE AROUND line_a (1556):
         1548 |                     date_checks.append((model_class, "year", name, f.unique_for_year))
         1549 |                 if f.unique_for_month and f.unique_for_month not in exclude:
         1550 |                     date_checks.append((model_class, "month", name, f.unique_for_month))
         1551 |         return unique_checks, date_checks
         1552 | 
         1553 |     def _perform_unique_checks(self, unique_checks):
         1554 |         errors = {}
         1555 | 
    >>>  1556 |         for model_class, unique_check in unique_checks:
         1557 |             # Try to look up an existing object with the same values as this
         1558 |             # object's values for all the unique field.
         1559 | 
         1560 |             lookup_kwargs = {}
         1561 |             for field_name in unique_check:
         1562 |                 f = self._meta.get_field(field_name)
         1563 |                 lookup_value = getattr(self, f.attname)
         1564 |                 # TODO: Handle multiple backends with different feature flags.

CODE AROUND line_b (1587):
         1579 |                     # no need to check for unique primary key when editing
         1580 |                     continue
         1581 |                 lookup_kwargs[str(field_name)] = lookup_value
         1582 | 
         1583 |             # some fields were skipped, no reason to do the check
         1584 |             if len(unique_check) != len(lookup_kwargs):
         1585 |                 continue
         1586 | 
    >>>  1587 |             qs = model_class._default_manager.filter(**lookup_kwargs)
         1588 | 
         1589 |             # Exclude the current object from the query if we are editing an
         1590 |             # instance (as opposed to creating a new one)
         1591 |             # Note that we need to use the pk as defined by model_class, not
         1592 |             # self.pk. These can be different fields because model inheritance
         1593 |             # allows single model to have effectively multiple primary keys.
         1594 |             # Refs #17615.
         1595 |             model_class_pk = self._get_pk_val(model_class._meta)
