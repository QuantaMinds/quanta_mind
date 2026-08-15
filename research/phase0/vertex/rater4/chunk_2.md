# Findings to adjudicate — chunk 2

There are 10 findings below, numbered by their global index.

### FINDING 20
repository: scikit-learn/scikit-learn   pull request #34740 (MERGED)
file: sklearn/datasets/_base.py
the model was shown this function: load_digits
claim_type: contract_violation   model_confidence: high
cited line_a: 1006    cited line_b: 1031

CLAIM: The assignment `images = flat_data.view()` on line 1006 (in the original code) creates a view, causing `images` and `flat_data` to share the same underlying memory, and when both are returned in the Bunch object on line 1033, modifying one array unexpectedly modifies the other.

CODE AROUND line_a (1006):
          998 |     """
          999 | 
         1000 |     data, fdescr = load_gzip_compressed_csv_data(
         1001 |         data_file_name="digits.csv.gz", descr_file_name="digits.rst", delimiter=","
         1002 |     )
         1003 | 
         1004 |     target = data[:, -1].astype(int, copy=False)
         1005 |     flat_data = data[:, :-1]
    >>>  1006 |     images = flat_data.reshape(-1, 8, 8)
         1007 | 
         1008 |     if n_class < 10:
         1009 |         idx = target < n_class
         1010 |         flat_data, target = flat_data[idx], target[idx]
         1011 |         images = images[idx]
         1012 | 
         1013 |     feature_names = [
         1014 |         "pixel_{}_{}".format(row_idx, col_idx)

CODE AROUND line_b (1031):
         1023 |     if as_frame:
         1024 |         frame, flat_data, target = _convert_data_dataframe(
         1025 |             "load_digits", flat_data, target, feature_names, target_columns
         1026 |         )
         1027 | 
         1028 |     if return_X_y:
         1029 |         return flat_data, target
         1030 | 
    >>>  1031 |     return Bunch(
         1032 |         data=flat_data,
         1033 |         target=target,
         1034 |         frame=frame,
         1035 |         feature_names=feature_names,
         1036 |         target_names=np.arange(10),
         1037 |         images=images,
         1038 |         DESCR=fdescr,
         1039 |     )

---

### FINDING 21
repository: celery/celery   pull request #10459 (MERGED)
file: t/smoke/tests/test_rpc_backend.py
the model was shown this function: test_repeated_final_polls_do_not_recirculate
claim_type: unhandled_case   model_confidence: high
cited line_a: 145    cited line_b: 146

CLAIM: The first loop from lines 136-138, via `poll_until_ready`, caches task results upon completion, so the subsequent polls in the loop at line 145 will always hit the cache at line 146 and never interact with the broker, failing to test the bug's core behavior of requeueing on repeated polls.

CODE AROUND line_a (145):
          137 |         # message on every call.
          138 |         for i, res in enumerate(results):
          139 |             meta = poll_until_ready(res.id)
          140 |             assert meta["status"] == states.SUCCESS
          141 |             assert meta["result"] == i + i
          142 | 
          143 |         # further polls are served from the cache without putting the
          144 |         # final result message back on the reply queue.
    >>>   145 |         for res in results:
          146 |             for _ in range(5):
          147 |                 meta = app.backend.get_task_meta(res.id)
          148 |                 assert meta["status"] == states.SUCCESS, meta
          149 | 
          150 |         broker = celery_setup.broker
          151 | 
          152 |         @retry(
          153 |             stop=stop_after_attempt(30),

CODE AROUND line_b (146):
          138 |         for i, res in enumerate(results):
          139 |             meta = poll_until_ready(res.id)
          140 |             assert meta["status"] == states.SUCCESS
          141 |             assert meta["result"] == i + i
          142 | 
          143 |         # further polls are served from the cache without putting the
          144 |         # final result message back on the reply queue.
          145 |         for res in results:
    >>>   146 |             for _ in range(5):
          147 |                 meta = app.backend.get_task_meta(res.id)
          148 |                 assert meta["status"] == states.SUCCESS, meta
          149 | 
          150 |         broker = celery_setup.broker
          151 | 
          152 |         @retry(
          153 |             stop=stop_after_attempt(30),
          154 |             wait=wait_fixed(0.2),

---

### FINDING 22
repository: scrapy/scrapy   pull request #7988 (MERGED)
file: scrapy/core/_http2/protocol.py
the model was shown this function: connectionMade
claim_type: wrong_order   model_confidence: high
cited line_a: 252    cited line_b: 265

CLAIM: Calling `self.conn.initiate_connection()` before `self.conn.update_settings()` causes an unnecessary default SETTINGS frame to be sent before the intended custom settings, which is inefficient and delays the application of the custom settings.

CODE AROUND line_a (252):
          244 |         # Add the stream to the request pool
          245 |         self._pending_request_stream_pool.append(stream)
          246 | 
          247 |         # If we receive a request when connection is idle
          248 |         # We need to initiate pending requests
          249 |         self._send_pending_requests()
          250 |         return d
          251 | 
    >>>   252 |     def connectionMade(self) -> None:
          253 |         """Called by Twisted when the connection is established. We can start
          254 |         sending some data now: we should open with the connection preamble.
          255 |         """
          256 |         # Initialize the timeout
          257 |         self.setTimeout(self.IDLE_TIMEOUT)  # type: ignore[no-untyped-call]
          258 | 
          259 |         assert self.transport is not None  # typing
          260 |         destination = self.transport.getPeer()

CODE AROUND line_b (265):
          257 |         self.setTimeout(self.IDLE_TIMEOUT)  # type: ignore[no-untyped-call]
          258 | 
          259 |         assert self.transport is not None  # typing
          260 |         destination = self.transport.getPeer()
          261 |         self.metadata["ip_address"] = ipaddress.ip_address(destination.host)
          262 | 
          263 |         # Initiate H2 Connection
          264 |         self.conn.initiate_connection()
    >>>   265 |         max_frame_size = self._crawler.settings.getint("HTTP2_MAX_FRAME_SIZE")
          266 |         if max_frame_size != self.conn.local_settings.max_frame_size:
          267 |             self.conn.update_settings({SettingCodes.MAX_FRAME_SIZE: max_frame_size})
          268 |         self._write_to_transport()
          269 | 
          270 |     def _lose_connection_with_error(self, errors: list[BaseException]) -> None:
          271 |         """Helper function to lose the connection with the error sent as a
          272 |         reason"""
          273 |         self._conn_lost_errors.extend(errors)

---

### FINDING 23
repository: celery/celery   pull request #10298 (MERGED)
file: celery/backends/redis.py
the model was shown this function: _reconnect_pubsub
claim_type: contract_violation   model_confidence: high
cited line_a: 111    cited line_b: 111

CLAIM: The call to `get_connection()` without arguments violates the API contract for redis-py versions older than 5.3.0, which require a `command_name` argument, causing a `TypeError`.

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

### FINDING 24
repository: celery/celery   pull request #10420 (MERGED)
file: t/unit/app/test_schedules.py
the model was shown this function: test_aware_last_run_at_in_different_timezone
claim_type: wrong_order   model_confidence: low
cited line_a: 566    cited line_b: 569

CLAIM: The timedelta returned by `remaining_estimate` is added to `now` (a datetime in the Vilnius timezone) at line 566, but the result is compared to a datetime in the UTC timezone at line 569, which is only valid if `ZoneInfo` is not affected by daylight saving time transitions.

CODE AROUND line_a (566):
          558 |         vilnius = ZoneInfo("Europe/Vilnius")
          559 |         crontab = self.crontab(minute=40, hour=8)
          560 | 
          561 |         # 09:25:08 in Vilnius == 06:25:08 UTC
          562 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
          563 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
          564 |         crontab.nowfun = lambda: now
          565 | 
    >>>   566 |         next = now + crontab.remaining_estimate(last_run_at)
          567 | 
          568 |         # The next run is at 08:40 UTC on the same day, not a day later.
          569 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))
          570 | 
          571 |     def test_aware_last_run_at_in_different_timezone_without_utc(self):
          572 |         # Same as above with enable_utc off, which is a common
          573 |         # django-celery-beat setup.  The returned datetimes must stay in the
          574 |         # frame the delta was computed in (#9715).

CODE AROUND line_b (569):
          561 |         # 09:25:08 in Vilnius == 06:25:08 UTC
          562 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
          563 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
          564 |         crontab.nowfun = lambda: now
          565 | 
          566 |         next = now + crontab.remaining_estimate(last_run_at)
          567 | 
          568 |         # The next run is at 08:40 UTC on the same day, not a day later.
    >>>   569 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))
          570 | 
          571 |     def test_aware_last_run_at_in_different_timezone_without_utc(self):
          572 |         # Same as above with enable_utc off, which is a common
          573 |         # django-celery-beat setup.  The returned datetimes must stay in the
          574 |         # frame the delta was computed in (#9715).
          575 |         self.app.conf.enable_utc = False
          576 |         self.app.conf.timezone = "UTC"
          577 |         vilnius = ZoneInfo("Europe/Vilnius")

---

### FINDING 25
repository: django/django   pull request #21752 (MERGED)
file: tests/forms_tests/tests/test_media.py
the model was shown this function: test_html_safe_string_css
claim_type: contract_violation   model_confidence: high
cited line_a: 877    cited line_b: 878

CLAIM: The Media object initialized on line 877 with a SafeString asset under the 'all' media type ignores this media type during rendering, and the test on line 878 incorrectly asserts this behavior is correct by comparing the output to the original tag which lacks a `media="all"` attribute.

CODE AROUND line_a (877):
          869 | 
          870 |     def test_html_safe_string_js(self):
          871 |         tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
          872 |         media = Media(js=[tag])
          873 |         self.assertEqual(str(media), tag)
          874 | 
          875 |     def test_html_safe_string_css(self):
          876 |         tag = mark_safe('<link href="https://example.org/asset.css" rel="stylesheet">')
    >>>   877 |         media = Media(css={"all": [tag]})
          878 |         self.assertEqual(str(media), tag)
          879 | 
          880 |     def test_html_safe_string_deduplication(self):
          881 |         js_tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
          882 |         css_tag = mark_safe(
          883 |             '<link href="https://example.org/asset.css" rel="stylesheet">'
          884 |         )
          885 |         media = Media(

CODE AROUND line_b (878):
          870 |     def test_html_safe_string_js(self):
          871 |         tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
          872 |         media = Media(js=[tag])
          873 |         self.assertEqual(str(media), tag)
          874 | 
          875 |     def test_html_safe_string_css(self):
          876 |         tag = mark_safe('<link href="https://example.org/asset.css" rel="stylesheet">')
          877 |         media = Media(css={"all": [tag]})
    >>>   878 |         self.assertEqual(str(media), tag)
          879 | 
          880 |     def test_html_safe_string_deduplication(self):
          881 |         js_tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
          882 |         css_tag = mark_safe(
          883 |             '<link href="https://example.org/asset.css" rel="stylesheet">'
          884 |         )
          885 |         media = Media(
          886 |             css={"all": [css_tag, css_tag, "/path/to/css1"]},

---

### FINDING 26
repository: pandas-dev/pandas   pull request #66762 (MERGED)
file: pandas/tests/io/json/test_pandas.py
the model was shown this function: test_blocks_compat_GH9037
claim_type: wrong_order   model_confidence: high
cited line_a: 635    cited line_b: 635

CLAIM: The serialization of `df_mixed` at line 637 uses the original nanosecond-precision index, while the modification of `df_mixed` at line 639 to have a millisecond-precision index happens after the serialization, which is the wrong order for a true round-trip test.

CODE AROUND line_a (635):
          627 |         df_mixed.columns = df_mixed.columns.astype(
          628 |             np.str_ if not using_infer_string else "str"
          629 |         )
          630 |         msg = "The default formatting of datetime/timedelta values will change"
          631 |         with tm.assert_produces_warning(Pandas4Warning, match=msg):
          632 |             data = StringIO(df_mixed.to_json(orient="split"))
          633 |         df_roundtrip = read_json(data, orient="split")
          634 |         df_mixed.index = df_mixed.index.as_unit("ms")
    >>>   635 |         tm.assert_frame_equal(
          636 |             df_mixed,
          637 |             df_roundtrip,
          638 |             check_index_type=True,
          639 |             check_column_type=True,
          640 |         )
          641 | 
          642 |     def test_frame_nonprintable_bytes(self):
          643 |         # GH14256: failing column caused segfaults, if it is not the last one

CODE AROUND line_b (635):
          627 |         df_mixed.columns = df_mixed.columns.astype(
          628 |             np.str_ if not using_infer_string else "str"
          629 |         )
          630 |         msg = "The default formatting of datetime/timedelta values will change"
          631 |         with tm.assert_produces_warning(Pandas4Warning, match=msg):
          632 |             data = StringIO(df_mixed.to_json(orient="split"))
          633 |         df_roundtrip = read_json(data, orient="split")
          634 |         df_mixed.index = df_mixed.index.as_unit("ms")
    >>>   635 |         tm.assert_frame_equal(
          636 |             df_mixed,
          637 |             df_roundtrip,
          638 |             check_index_type=True,
          639 |             check_column_type=True,
          640 |         )
          641 | 
          642 |     def test_frame_nonprintable_bytes(self):
          643 |         # GH14256: failing column caused segfaults, if it is not the last one

---

### FINDING 27
repository: ansible/ansible   pull request #87250 (MERGED)
file: lib/ansible/module_utils/basic.py
the model was shown this function: log
claim_type: wrong_order   model_confidence: high
cited line_a: 1254    cited line_b: 1257

CLAIM: The sanitization via `remove_values` on line 1254 now runs before the message is combined with `self._target_log_info`, causing the latter to be passed unsanitized on line 1262 and potentially leak secrets into system logs.

CODE AROUND line_a (1254):
         1246 |             return
         1247 | 
         1248 |         if not isinstance(msg, (bytes, str)):
         1249 |             raise TypeError("msg should be a string (got %s)" % type(msg))
         1250 | 
         1251 |         if isinstance(msg, bytes):
         1252 |             msg = msg.decode('utf-8', 'replace')
         1253 | 
    >>>  1254 |         msg = remove_values(msg, self.no_log_values)
         1255 | 
         1256 |         try:
         1257 |             _logging.log_to_system(
         1258 |                 msg,
         1259 |                 module_name=self._name,
         1260 |                 log_args=log_args,
         1261 |                 syslog_facility=self._syslog_facility,
         1262 |                 target_log_info=self._target_log_info,

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

### FINDING 28
repository: scrapy/scrapy   pull request #7985 (MERGED)
file: tests/utils/bases/download_handlers_http.py
the model was shown this function: get_dh
claim_type: resource_leak   model_confidence: low
cited line_a: 1549    cited line_b: 1554

CLAIM: A spider instance is created on line 1549 and assigned to the crawler, but it is never closed, causing a potential resource leak if a spider subclass allocates resources during initialization.

CODE AROUND line_a (1549):
         1541 | 
         1542 |     @asynccontextmanager
         1543 |     async def get_dh(
         1544 |         self, settings_dict: dict[str, Any] | None = None
         1545 |     ) -> AsyncGenerator[DownloadHandlerProtocol]:
         1546 |         crawler = get_crawler(
         1547 |             DefaultSpider, {**REAL_WEBSITE_SETTINGS, **(settings_dict or {})}
         1548 |         )
    >>>  1549 |         crawler.spider = crawler._create_spider()
         1550 |         dh = build_from_crawler(self.download_handler_cls, crawler)
         1551 |         try:
         1552 |             yield dh
         1553 |         finally:
         1554 |             await dh.close()
         1555 | 
         1556 |     @coroutine_test
         1557 |     async def test_download(self) -> None:

CODE AROUND line_b (1554):
         1546 |         crawler = get_crawler(
         1547 |             DefaultSpider, {**REAL_WEBSITE_SETTINGS, **(settings_dict or {})}
         1548 |         )
         1549 |         crawler.spider = crawler._create_spider()
         1550 |         dh = build_from_crawler(self.download_handler_cls, crawler)
         1551 |         try:
         1552 |             yield dh
         1553 |         finally:
    >>>  1554 |             await dh.close()
         1555 | 
         1556 |     @coroutine_test
         1557 |     async def test_download(self) -> None:
         1558 |         request = Request("https://books.toscrape.com/")
         1559 |         async with self.get_dh() as download_handler:
         1560 |             response = await download_handler.download_request(request)
         1561 |         assert response.status == 200
         1562 |         assert "All products | Books to Scrape - Sandbox" in response.text

---

### FINDING 29
repository: scrapy/scrapy   pull request #7988 (MERGED)
file: tests/test_http2_client_protocol.py
the model was shown this function: test_GET_large_frames
claim_type: contract_violation   model_confidence: high
cited line_a: 194    cited line_b: 327

CLAIM: The `@pytest.mark.parametrize` decorator on line 324 targets the `crawler` parameter, but the test function signature on line 327 does not include a parameter named `crawler`, which violates the pytest contract and will cause the test to fail at runtime.

CODE AROUND line_a (194):
          186 | def make_request_dfd(client: H2ClientProtocol, request: Request) -> Deferred[Response]:
          187 |     return client.request(request, DummySpider())
          188 | 
          189 | 
          190 | async def make_request(client: H2ClientProtocol, request: Request) -> Response:
          191 |     return await maybe_deferred_to_future(make_request_dfd(client, request))
          192 | 
          193 | 
    >>>   194 | class TestHttps2ClientProtocol:
          195 |     scheme = "https"
          196 |     host = "localhost"
          197 |     key_file = Path(__file__).parent / "keys" / "localhost.key"
          198 |     certificate_file = Path(__file__).parent / "keys" / "localhost.crt"
          199 | 
          200 |     @pytest.fixture
          201 |     def site(self, tmp_path):
          202 |         r = File(str(tmp_path))

CODE AROUND line_b (327):
          319 |     ) -> None:
          320 |         request = Request(self.get_url(server_port, "/get-data-html-large"))
          321 |         await self._check_GET(client, request, Data.HTML_LARGE, 200)
          322 | 
          323 |     @pytest.mark.parametrize(
          324 |         "crawler", [{"HTTP2_MAX_FRAME_SIZE": 1024**2}], indirect=True
          325 |     )
          326 |     @deferred_f_from_coro_f
    >>>   327 |     async def test_GET_large_frames(
          328 |         self, server_port: int, client: H2ClientProtocol
          329 |     ) -> None:
          330 |         request = Request(self.get_url(server_port, "/get-data-html-large"))
          331 |         await self._check_GET(client, request, Data.HTML_LARGE, 200)
          332 |         assert client.conn.local_settings.max_frame_size == 1024**2
          333 | 
          334 |     async def _check_GET_x10(
          335 |         self,
