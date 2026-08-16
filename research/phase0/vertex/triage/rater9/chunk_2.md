# Findings to adjudicate — chunk 2

There are 7 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 14
repository: scrapy/scrapy   pull request #7986 (MERGED)
file: tests/test_http2_client_protocol.py
claim_type: contract_violation
symbols named: client.transport.abortConnection() -> client

CLAIM: Calling `transport.abortConnection()` directly after `transport.loseConnection()` bypasses the protocol's graceful shutdown procedure, which should involve sending a GOAWAY frame.

THE FUNCTION UNDER REVIEW (client, lines 239-263):
   239 |     @async_yield_fixture  # type: ignore[untyped-decorator]
   240 |     async def client(
   241 |         self, server_port: int, client_certificate: PrivateCertificate
   242 |     ) -> AsyncGenerator[H2ClientProtocol]:
   243 |         from twisted.internet import reactor
   244 | 
   245 |         from scrapy.core._http2.protocol import H2ClientFactory  # noqa: PLC0415
   246 | 
   247 |         client_options = optionsForClientTLS(
   248 |             hostname=self.host,
   249 |             trustRoot=client_certificate,
   250 |             acceptableProtocols=[b"h2"],
   251 |         )
   252 |         uri = URI.fromBytes(bytes(self.get_url(server_port, "/"), "utf-8"))
   253 |         h2_client_factory = H2ClientFactory(uri, get_crawler(), Deferred())
   254 |         client_endpoint = SSL4ClientEndpoint(
   255 |             reactor, self.host, server_port, client_options
   256 |         )
   257 |         client = await client_endpoint.connect(h2_client_factory)
   258 | 
   259 |         yield client
   260 | 
   261 |         if client.connected:
   262 |             client.transport.loseConnection()
   263 |             client.transport.abortConnection()

---

### FINDING 15
repository: celery/celery   pull request #10298 (MERGED)
file: t/unit/backends/test_redis.py
claim_type: unhandled_case
symbols named: test__reconnect_pubsub_redis_py_below_5_3_compat -> test__reconnect_pubsub_redis_py_below_5_3_compat

CLAIM: The test mock setup is incorrect, causing it to call `get_connection` on the consumer's original connection pool instead of the mock pool, which makes the test unable to detect the regression it was designed to prevent.

THE FUNCTION UNDER REVIEW (test__reconnect_pubsub_redis_py_below_5_3_compat, lines 324-350):
   324 |     def test__reconnect_pubsub_redis_py_below_5_3_compat(self):
   325 |         """Regression test for celery#10294.
   326 | 
   327 |         On redis-py < 5.3.0, ConnectionPool.get_connection requires
   328 |         ``command_name`` as a positional argument. _reconnect_pubsub must
   329 |         remain compatible with that older signature when no tasks are
   330 |         subscribed.
   331 |         """
   332 |         consumer = self.get_consumer()
   333 |         consumer.start('initial')
   334 |         consumer.subscribed_to = set()
   335 | 
   336 |         def legacy_get_connection(command_name, *args, **kwargs):
   337 |             return Mock(name='legacy-connection')
   338 | 
   339 |         # Replace the auto-mocked get_connection with one that mirrors the
   340 |         # redis-py < 5.3.0 signature: command_name is required.
   341 |         consumer._pubsub = Mock(name='pubsub')
   342 |         consumer._pubsub.connection_pool = Mock(name='connection_pool')
   343 |         consumer._pubsub.connection_pool.get_connection.side_effect = (
   344 |             legacy_get_connection
   345 |         )
   346 |         consumer.backend.client = Mock(name='client')
   347 |         consumer.backend.client.pubsub.return_value = consumer._pubsub
   348 | 
   349 |         # Must not raise TypeError about a missing 'command_name' argument.
   350 |         consumer._reconnect_pubsub()

---

### FINDING 16
repository: scrapy/scrapy   pull request #7985 (MERGED)
file: conftest.py
claim_type: contract_violation
symbols named: item.add_marker -> item

CLAIM: Calling `item.add_marker` unconditionally adds a new `flaky` marker, which can override a more specific `flaky` marker already present on the test item, because the `pytest-rerunfailures` plugin typically uses the last-applied marker.

THE FUNCTION UNDER REVIEW (pytest_collection_modifyitems, lines 110-115):
   110 | def pytest_collection_modifyitems(items):
   111 |     for item in items:
   112 |         if item.get_closest_marker("requires_internet"):
   113 |             # Requests to real websites fail every now and then in CI for
   114 |             # reasons unrelated to the code under test.
   115 |             item.add_marker(pytest.mark.flaky(reruns=2, reruns_delay=5))

---

### FINDING 17
repository: django/django   pull request #21773 (MERGED)
file: django/db/models/fields/tuple_lookups.py
claim_type: unhandled_case
symbols named: check_rhs_is_supported_expression -> check_rhs_is_supported_expression

CLAIM: The function `check_rhs_is_supported_expression` failed to include `ColPairs` as a supported right-hand-side expression, causing it to incorrectly raise a `ValueError` when one was provided.

THE FUNCTION UNDER REVIEW (check_rhs_is_supported_expression, lines 76-83):
    76 |     def check_rhs_is_supported_expression(self):
    77 |         if not isinstance(self.rhs, (ColPairs, ResolvedOuterRef, Query)):
    78 |             lhs_str = self.get_lhs_str()
    79 |             rhs_cls = self.rhs.__class__.__name__
    80 |             raise ValueError(
    81 |                 f"{self.lookup_name!r} subquery lookup of {lhs_str} "
    82 |                 f"only supports OuterRef and QuerySet objects (received {rhs_cls!r})"
    83 |             )

---

### FINDING 18
repository: celery/celery   pull request #10459 (MERGED)
file: celery/backends/rpc.py
claim_type: resource_leak
symbols named: get_task_meta -> on_out_of_band_result

CLAIM: `get_task_meta` calls `on_out_of_band_result` for out-of-band messages, which unconditionally acks the message, causing non-final state messages to be permanently removed from the queue instead of being requeued.

THE FUNCTION UNDER REVIEW (get_task_meta, lines 325-369):
   325 |     def get_task_meta(self, task_id, backlog_limit=1000):
   326 |         buffered = self._out_of_band.pop(task_id, None)
   327 |         if buffered:
   328 |             return self._set_cache_by_message(task_id, buffered)
   329 | 
   330 |         # Polling and using basic_get
   331 |         latest_by_id = {}
   332 |         prev = None
   333 |         for acc in self._slurp_from_queue(task_id, self.accept, backlog_limit):
   334 |             tid = self._get_message_task_id(acc)
   335 |             prev, latest_by_id[tid] = latest_by_id.get(tid), acc
   336 |             if prev:
   337 |                 # backends aren't expected to keep history,
   338 |                 # so we delete everything except the most recent state.
   339 |                 prev.ack()
   340 |                 prev = None
   341 | 
   342 |         latest = latest_by_id.pop(task_id, None)
   343 |         for tid, msg in latest_by_id.items():
   344 |             self.on_out_of_band_result(tid, msg)
   345 | 
   346 |         if latest:
   347 |             meta = self._set_cache_by_message(task_id, latest)
   348 |             if meta['status'] in states.READY_STATES:
   349 |                 # final state: resolve any pending waiter from the cache
   350 |                 # and ack, requeueing would keep the message circulating
   351 |                 # between the queue and _out_of_band forever.
   352 |                 self.result_consumer.on_out_of_band_result(latest)
   353 |                 latest.ack()
   354 |             else:
   355 |                 latest.requeue()
   356 |             return meta
   357 |         else:
   358 |             # no new state, use previous
   359 |             try:
   360 |                 return self._cache[task_id]
   361 |             except KeyError:
   362 |                 pass
   363 |             # a final state consumed by an earlier poll is kept in the
   364 |             # pending buffer for late waiters, peek without consuming.
   365 |             buf = self._pending_messages.get(task_id)
   366 |             if buf:
   367 |                 return self.meta_from_decoded(dict(buf[-1]))
   368 |             # result probably pending.
   369 |             return {'status': states.PENDING, 'result': None}

---

### FINDING 19
repository: scrapy/scrapy   pull request #7986 (MERGED)
file: tests/test_http2_client_protocol.py
claim_type: contract_violation
symbols named: client.setTimeout(1) -> f"Connection was IDLE for more than {H2ClientProtocol.IDLE_TIMEOUT}s"

CLAIM: The test sets a connection timeout of 1 second but the assertion incorrectly checks if the timeout error message contains the default idle timeout of 20 seconds.

THE FUNCTION UNDER REVIEW (test_connection_timeout, lines 727-749):
   727 |     @inlineCallbacks
   728 |     def test_connection_timeout(
   729 |         self, server_port: int, client: H2ClientProtocol
   730 |     ) -> Generator[Deferred[Any], Any, None]:
   731 |         request = Request(self.get_url(server_port, "/timeout"))
   732 | 
   733 |         # Update the timer to 1s to test connection timeout
   734 |         client.setTimeout(1)  # type: ignore[no-untyped-call]
   735 | 
   736 |         with pytest.raises(ResponseFailed) as exc_info:
   737 |             yield make_request_dfd(client, request)
   738 | 
   739 |         for err in exc_info.value.reasons:
   740 |             from scrapy.core._http2.protocol import H2ClientProtocol  # noqa: PLC0415
   741 | 
   742 |             if isinstance(err, DownloadTimeoutError):
   743 |                 assert (
   744 |                     f"Connection was IDLE for more than {H2ClientProtocol.IDLE_TIMEOUT}s"
   745 |                     in str(err)
   746 |                 )
   747 |                 break
   748 |         else:
   749 |             pytest.fail("No TimeoutError raised.")

---

### FINDING 20
repository: celery/celery   pull request #10420 (MERGED)
file: t/unit/app/test_schedules.py
claim_type: wrong_order
symbols named: crontab.remaining_estimate -> next

CLAIM: The `crontab.remaining_estimate` method returns a `timedelta` calculated in a specific timezone (UTC in this case), but adding this delta to `now`, which is in a different timezone (Vilnius), produces a `next` datetime in the `now` object's timezone, not the one expected by the test's assertion.

THE FUNCTION UNDER REVIEW (test_aware_last_run_at_in_different_timezone_without_utc, lines 571-586):
   571 |     def test_aware_last_run_at_in_different_timezone_without_utc(self):
   572 |         # Same as above with enable_utc off, which is a common
   573 |         # django-celery-beat setup.  The returned datetimes must stay in the
   574 |         # frame the delta was computed in (#9715).
   575 |         self.app.conf.enable_utc = False
   576 |         self.app.conf.timezone = "UTC"
   577 |         vilnius = ZoneInfo("Europe/Vilnius")
   578 |         crontab = self.crontab(minute=40, hour=8)
   579 | 
   580 |         last_run_at = datetime(2025, 5, 20, 9, 25, 8, tzinfo=vilnius)
   581 |         now = datetime(2025, 5, 20, 9, 26, 8, tzinfo=vilnius)
   582 |         crontab.nowfun = lambda: now
   583 | 
   584 |         next = now + crontab.remaining_estimate(last_run_at)
   585 | 
   586 |         assert next == datetime(2025, 5, 20, 8, 40, tzinfo=ZoneInfo("UTC"))
