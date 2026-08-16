# Findings to adjudicate — chunk 3

There are 9 findings below, numbered by their global index.

### FINDING 30
repository: scrapy/scrapy   pull request #7946 (MERGED)
file: tests/test_engine_loop.py
the model was shown this function: test_start_not_an_async_generator
claim_type: contract_violation   model_confidence: high
cited line_a: 188    cited line_b: 188

CLAIM: The assertion on line 191 fails because the f-string on line 189 uses the spider's class name (`spider_cls.__name__`) to construct the expected error message, but the Scrapy engine logs the spider's `name` attribute ("test").

CODE AROUND line_a (188):
          180 |         caplog: pytest.LogCaptureFixture,
          181 |     ) -> None:
          182 |         crawler = get_crawler(spider_cls)
          183 | 
          184 |         caplog.clear()
          185 |         with caplog.at_level(ERROR):
          186 |             await crawler.crawl_async()
          187 | 
    >>>   188 |         assert (
          189 |             f"{spider_cls.__name__}.start() must be an asynchronous generator,"
          190 |             f" i.e. an async def method with yield statements, got {expected_type}"
          191 |         ) in caplog.text
          192 |         assert crawler.stats
          193 |         assert crawler.stats.get_value("finish_reason") == "start_error"
          194 | 
          195 |     @coroutine_test
          196 |     async def test_start_error(self, caplog: pytest.LogCaptureFixture) -> None:

CODE AROUND line_b (188):
          180 |         caplog: pytest.LogCaptureFixture,
          181 |     ) -> None:
          182 |         crawler = get_crawler(spider_cls)
          183 | 
          184 |         caplog.clear()
          185 |         with caplog.at_level(ERROR):
          186 |             await crawler.crawl_async()
          187 | 
    >>>   188 |         assert (
          189 |             f"{spider_cls.__name__}.start() must be an asynchronous generator,"
          190 |             f" i.e. an async def method with yield statements, got {expected_type}"
          191 |         ) in caplog.text
          192 |         assert crawler.stats
          193 |         assert crawler.stats.get_value("finish_reason") == "start_error"
          194 | 
          195 |     @coroutine_test
          196 |     async def test_start_error(self, caplog: pytest.LogCaptureFixture) -> None:

---

### FINDING 31
repository: celery/celery   pull request #10420 (MERGED)
file: t/unit/app/test_schedules.py
the model was shown this function: test_aware_last_run_at_in_different_timezone_without_utc
claim_type: contract_violation   model_confidence: high
cited line_a: 576    cited line_b: 586

CLAIM: Setting `self.app.conf.enable_utc = False` on line 576 creates a test of local time processing, but the assertion on line 586 incorrectly compares the result to a UTC-aware datetime, which will fail if the system's local timezone is not UTC.

CODE AROUND line_a (576):
          568 |         # The next run is at 08:40 UTC on the same day, not a day later.
          569 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))
          570 | 
          571 |     def test_aware_last_run_at_in_different_timezone_without_utc(self):
          572 |         # Same as above with enable_utc off, which is a common
          573 |         # django-celery-beat setup.  The returned datetimes must stay in the
          574 |         # frame the delta was computed in (#9715).
          575 |         self.app.conf.enable_utc = False
    >>>   576 |         self.app.conf.timezone = "UTC"
          577 |         vilnius = ZoneInfo("Europe/Vilnius")
          578 |         crontab = self.crontab(minute=40, hour=8)
          579 | 
          580 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
          581 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
          582 |         crontab.nowfun = lambda: now
          583 | 
          584 |         next = now + crontab.remaining_estimate(last_run_at)

CODE AROUND line_b (586):
          578 |         crontab = self.crontab(minute=40, hour=8)
          579 | 
          580 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
          581 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
          582 |         crontab.nowfun = lambda: now
          583 | 
          584 |         next = now + crontab.remaining_estimate(last_run_at)
          585 | 
    >>>   586 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))
          587 | 
          588 | 
          589 | class test_crontab_is_due:
          590 | 
          591 |     def setup_method(self):
          592 |         self.now = self.app.now()
          593 |         self.next_minute = 60 - self.now.second - 1e-6 * self.now.microsecond
          594 |         self.every_minute = self.crontab()

---

### FINDING 32
repository: pandas-dev/pandas   pull request #66696 (MERGED)
file: pandas/tests/util/test_assert_almost_equal.py
the model was shown this function: test_assert_almost_equal_large_integers_within_atol
claim_type: wrong_order   model_confidence: high
cited line_a: 150    cited line_b: 151

CLAIM: The subtraction to calculate the difference of 76 in the comment at line 151 is performed on values `a` (line 150) and `b` (line 151) that do not match the values used in the test.

CODE AROUND line_a (150):
          142 | def test_assert_not_almost_equal_numbers_rtol(a, b):
          143 |     _assert_not_almost_equal_both(a, b, rtol=0.05)
          144 | 
          145 | 
          146 | @pytest.mark.parametrize("dtype", [int, np.int64, np.uint64])
          147 | def test_assert_almost_equal_large_integers_within_atol(dtype):
          148 |     # GH#66400 these land on float64s 256 apart, so the comparison used to
          149 |     #  report a difference that is not there
    >>>   150 |     a = 1450804465901089690
          151 |     b = 1450804465901089614  # 76 apart
          152 | 
          153 |     _assert_almost_equal_both(dtype(a), dtype(b), rtol=0, atol=100)
          154 | 
          155 | 
          156 | @pytest.mark.parametrize("dtype", [int, np.int64, np.uint64])
          157 | def test_assert_not_almost_equal_large_integers_outside_atol(dtype):
          158 |     # GH#66400 these land on the same float64, so the comparison used to pass

CODE AROUND line_b (151):
          143 |     _assert_not_almost_equal_both(a, b, rtol=0.05)
          144 | 
          145 | 
          146 | @pytest.mark.parametrize("dtype", [int, np.int64, np.uint64])
          147 | def test_assert_almost_equal_large_integers_within_atol(dtype):
          148 |     # GH#66400 these land on float64s 256 apart, so the comparison used to
          149 |     #  report a difference that is not there
          150 |     a = 1450804465901089690
    >>>   151 |     b = 1450804465901089614  # 76 apart
          152 | 
          153 |     _assert_almost_equal_both(dtype(a), dtype(b), rtol=0, atol=100)
          154 | 
          155 | 
          156 | @pytest.mark.parametrize("dtype", [int, np.int64, np.uint64])
          157 | def test_assert_not_almost_equal_large_integers_outside_atol(dtype):
          158 |     # GH#66400 these land on the same float64, so the comparison used to pass
          159 |     a = 1450804465901089690

---

### FINDING 33
repository: ansible/ansible   pull request #87250 (MERGED)
file: lib/ansible/module_utils/_internal/_logging.py
the model was shown this function: log_to_system
claim_type: unhandled_case   model_confidence: high
cited line_a: 85    cited line_b: 56

CLAIM: The `except OSError` block at line 85 assumes the `_log_to_syslog` fallback at line 86 will succeed, but if `HAS_SYSLOG` is false, `_log_to_syslog` does nothing, causing the log message to be silently dropped.

CODE AROUND line_a (85):
           77 |                 journal.send(
           78 |                     MESSAGE="%s %s" % (module, msg),
           79 |                     SYSLOG_FACILITY=facility,
           80 |                     **dict(journal_args),
           81 |                 )
           82 |             else:
           83 |                 journal.send(MESSAGE="%s %s" % (module, msg), **dict(journal_args))
           84 |         except OSError:
    >>>    85 |             _log_to_syslog(msg, module_name, syslog_facility)
           86 |     else:
           87 |         _log_to_syslog(msg, module_name, syslog_facility)
           88 | 

CODE AROUND line_b (56):
           48 |     if log_args is None:
           49 |         log_args = {}
           50 | 
           51 |     module = "ansible-%s" % module_name
           52 | 
           53 |     if target_log_info:
           54 |         msg = " ".join([target_log_info, msg])
           55 | 
    >>>    56 |     if has_journal:
           57 |         journal_args = [("MODULE", module_name)]
           58 |         for arg in log_args:
           59 |             name, value = (arg.upper(), str(log_args[arg]))
           60 |             if name in (
           61 |                 "PRIORITY",
           62 |                 "MESSAGE",
           63 |                 "MESSAGE_ID",
           64 |                 "CODE_FILE",

---

### FINDING 34
repository: scrapy/scrapy   pull request #7986 (MERGED)
file: tests/test_http2_client_protocol.py
the model was shown this function: client
claim_type: resource_leak   model_confidence: high
cited line_a: 262    cited line_b: 263

CLAIM: The call to `loseConnection` on line 262 for a graceful connection teardown is immediately subverted by the call to `abortConnection` on line 263, which forcefully terminates the connection without allowing the graceful shutdown to complete.

CODE AROUND line_a (262):
          254 |         client_endpoint = SSL4ClientEndpoint(
          255 |             reactor, self.host, server_port, client_options
          256 |         )
          257 |         client = await client_endpoint.connect(h2_client_factory)
          258 | 
          259 |         yield client
          260 | 
          261 |         if client.connected:
    >>>   262 |             client.transport.loseConnection()
          263 |             client.transport.abortConnection()
          264 | 
          265 |     def get_url(self, portno: int, path: str) -> str:
          266 |         """
          267 |         :param path: Should have / at the starting compulsorily if not empty
          268 |         :return: Complete url
          269 |         """
          270 |         assert len(path) > 0

CODE AROUND line_b (263):
          255 |             reactor, self.host, server_port, client_options
          256 |         )
          257 |         client = await client_endpoint.connect(h2_client_factory)
          258 | 
          259 |         yield client
          260 | 
          261 |         if client.connected:
          262 |             client.transport.loseConnection()
    >>>   263 |             client.transport.abortConnection()
          264 | 
          265 |     def get_url(self, portno: int, path: str) -> str:
          266 |         """
          267 |         :param path: Should have / at the starting compulsorily if not empty
          268 |         :return: Complete url
          269 |         """
          270 |         assert len(path) > 0
          271 |         assert path[0] == "/" or path[0] == "&"

---

### FINDING 35
repository: celery/celery   pull request #10459 (MERGED)
file: celery/backends/rpc.py
the model was shown this function: get_task_meta
claim_type: resource_leak   model_confidence: high
cited line_a: 325    cited line_b: 336

CLAIM: In the loop that processes messages from the queue, if a message for a given task ID is not the last one, the `ack()` is called at line 341, but this does not prevent the message reference from being stored in `latest_by_id` at line 337, leading to it being processed again after the loop.

CODE AROUND line_a (325):
          317 |             # no need to buffer the message itself.
          318 |             self._set_cache_by_message(task_id, message)
          319 |         else:
          320 |             self._out_of_band[task_id] = message
          321 |         # the payload is buffered/cached in memory now, so complete the
          322 |         # delivery instead of leaving it unacked on the channel.
          323 |         message.ack()
          324 | 
    >>>   325 |     def get_task_meta(self, task_id, backlog_limit=1000):
          326 |         buffered = self._out_of_band.pop(task_id, None)
          327 |         if buffered:
          328 |             return self._set_cache_by_message(task_id, buffered)
          329 | 
          330 |         # Polling and using basic_get
          331 |         latest_by_id = {}
          332 |         prev = None
          333 |         for acc in self._slurp_from_queue(task_id, self.accept, backlog_limit):

CODE AROUND line_b (336):
          328 |             return self._set_cache_by_message(task_id, buffered)
          329 | 
          330 |         # Polling and using basic_get
          331 |         latest_by_id = {}
          332 |         prev = None
          333 |         for acc in self._slurp_from_queue(task_id, self.accept, backlog_limit):
          334 |             tid = self._get_message_task_id(acc)
          335 |             prev, latest_by_id[tid] = latest_by_id.get(tid), acc
    >>>   336 |             if prev:
          337 |                 # backends aren't expected to keep history,
          338 |                 # so we delete everything except the most recent state.
          339 |                 prev.ack()
          340 |                 prev = None
          341 | 
          342 |         latest = latest_by_id.pop(task_id, None)
          343 |         for tid, msg in latest_by_id.items():
          344 |             self.on_out_of_band_result(tid, msg)

---

### FINDING 36
repository: celery/celery   pull request #10470 (MERGED)
file: t/unit/app/test_schedules.py
the model was shown this function: test_raises_improperly_configured_when_ephem_is_missing
claim_type: contract_violation   model_confidence: high
cited line_a: 102    cited line_b: 108

CLAIM: The test class `test_solar_without_ephem` does not have a `setup_method` to initialize the `self.app` attribute, causing an `AttributeError` when it is accessed on line 108.

CODE AROUND line_a (102):
           94 |             s.is_center = s._use_center_l[ev]
           95 |             try:
           96 |                 s.remaining_estimate(datetime.now(timezone.utc))
           97 |             except TypeError:
           98 |                 pytest.fail(
           99 |                     f"{s.method} was called with 'use_center' which is not a "
          100 |                     "valid keyword for the function.")
          101 | 
    >>>   102 | 
          103 | class test_solar_without_ephem:
          104 | 
          105 |     def test_raises_improperly_configured_when_ephem_is_missing(
          106 |             self, monkeypatch):
          107 |         monkeypatch.setitem(sys.modules, 'ephem', None)
          108 |         with pytest.raises(ImproperlyConfigured, match=r'celery\[solar\]'):
          109 |             solar('sunrise', 60, 30, app=self.app)
          110 | 

CODE AROUND line_b (108):
          100 |                     "valid keyword for the function.")
          101 | 
          102 | 
          103 | class test_solar_without_ephem:
          104 | 
          105 |     def test_raises_improperly_configured_when_ephem_is_missing(
          106 |             self, monkeypatch):
          107 |         monkeypatch.setitem(sys.modules, 'ephem', None)
    >>>   108 |         with pytest.raises(ImproperlyConfigured, match=r'celery\[solar\]'):
          109 |             solar('sunrise', 60, 30, app=self.app)
          110 | 
          111 | 
          112 | class test_schedule:
          113 | 
          114 |     def test_ne(self):
          115 |         s1 = schedule(10, app=self.app)
          116 |         s2 = schedule(12, app=self.app)

---

### FINDING 37
repository: scikit-learn/scikit-learn   pull request #34741 (MERGED)
file: sklearn/mixture/_gaussian_mixture.py
the model was shown this function: _estimate_gaussian_covariances_spherical
claim_type: contract_violation   model_confidence: high
cited line_a: 255    cited line_b: 276

CLAIM: The function signature at line 255 accepts an `xp` parameter, but its value is unconditionally overwritten at line 276, meaning any value passed by the caller for `xp` is ignored.

CODE AROUND line_a (255):
          247 |         The covariance vector of the current components.
          248 |     """
          249 |     xp, _ = get_namespace(X, xp=xp)
          250 |     avg_X2 = (resp.T @ (X * X)) / nk[:, xp.newaxis]
          251 |     avg_means2 = means**2
          252 |     return avg_X2 - avg_means2 + reg_covar
          253 | 
          254 | 
    >>>   255 | def _estimate_gaussian_covariances_spherical(resp, X, nk, means, reg_covar, xp=None):
          256 |     """Estimate the spherical variance values.
          257 | 
          258 |     Parameters
          259 |     ----------
          260 |     resp : array-like of shape (n_samples, n_components)
          261 | 
          262 |     X : array-like of shape (n_samples, n_features)
          263 | 

CODE AROUND line_b (276):
          268 |     reg_covar : float
          269 | 
          270 |     Returns
          271 |     -------
          272 |     variances : array, shape (n_components,)
          273 |         The variance values of each components.
          274 |     """
          275 |     xp, _ = get_namespace(X)
    >>>   276 |     return xp.mean(
          277 |         _estimate_gaussian_covariances_diag(resp, X, nk, means, reg_covar, xp=xp),
          278 |         axis=1,
          279 |     )
          280 | 
          281 | 
          282 | def _estimate_gaussian_parameters(X, resp, reg_covar, covariance_type, xp=None):
          283 |     """Estimate the Gaussian distribution parameters.
          284 | 

---

### FINDING 38
repository: pandas-dev/pandas   pull request #66717 (MERGED)
file: pandas/core/indexes/multi.py
the model was shown this function: get_locs
claim_type: contract_violation   model_confidence: high
cited line_a: 4357    cited line_b: 4319

CLAIM: The assignment to `vec_indexer` at line 4357 does not account for the possibility that `k_codes` can contain duplicate values, but `wanted` is created from unique values, which causes `wanted[level_codes]` to incorrectly select only the first occurrence of a duplicated code from the level's codes, leading to missing results at line 4359.

CODE AROUND line_a (4357):
         4349 |                         if na_count and not lib.has_sentinel(level_codes, -1):
         4350 |                             raise KeyError(k) from None
         4351 |                         # GH#64807 Every missing non-NA label has raised by now,
         4352 |                         #  so the only -1 codes left stand for NA labels. Those
         4353 |                         #  are resolved by the (level_codes == -1) union below,
         4354 |                         #  never by a code: get_indexer may have matched one to
         4355 |                         #  an NA entry of the level, but the scalar path always
         4356 |                         #  resolves NA to -1, so drop them to agree with it.
    >>>  4357 |                         k_codes = k_codes[~k_isna]
         4358 |                         # GH#64807 A label can be present in the level but unused
         4359 |                         #  by any code, in which case it is still a missing key.
         4360 |                         # Codes are small non-negative ints, so tables indexed by
         4361 |                         #  code beat hashing -- but only while the level is no
         4362 |                         #  bigger than the codes. Slicing a MultiIndex leaves its
         4363 |                         #  levels untrimmed, so a short one can carry a huge level.
         4364 |                         if len(level_index) <= len(level_codes):
         4365 |                             # The extra trailing slot absorbs the -1 code for NaN,

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
