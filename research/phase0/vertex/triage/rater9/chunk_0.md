# Findings to adjudicate — chunk 0

There are 7 findings below, numbered by their global index. Judge the CLAIM against the function shown.

### FINDING 0
repository: scrapy/scrapy   pull request #7988 (MERGED)
file: tests/test_http2_client_protocol.py
claim_type: wrong_order
symbols named: client.transport.loseConnection -> client.transport.abortConnection

CLAIM: Calling `abortConnection` immediately after `loseConnection` is redundant and negates the purpose of a graceful shutdown initiated by `loseConnection`.

THE FUNCTION UNDER REVIEW (client, lines 244-271):
   244 |     @async_yield_fixture  # type: ignore[untyped-decorator]
   245 |     async def client(
   246 |         self,
   247 |         server_port: int,
   248 |         client_certificate: PrivateCertificate,
   249 |         crawler: Crawler,
   250 |     ) -> AsyncGenerator[H2ClientProtocol]:
   251 |         from twisted.internet import reactor
   252 | 
   253 |         from scrapy.core._http2.protocol import H2ClientFactory  # noqa: PLC0415
   254 | 
   255 |         client_options = optionsForClientTLS(
   256 |             hostname=self.host,
   257 |             trustRoot=client_certificate,
   258 |             acceptableProtocols=[b"h2"],
   259 |         )
   260 |         uri = URI.fromBytes(bytes(self.get_url(server_port, "/"), "utf-8"))
   261 |         h2_client_factory = H2ClientFactory(uri, crawler, Deferred())
   262 |         client_endpoint = SSL4ClientEndpoint(
   263 |             reactor, self.host, server_port, client_options
   264 |         )
   265 |         client = await client_endpoint.connect(h2_client_factory)
   266 | 
   267 |         yield client
   268 | 
   269 |         if client.connected:
   270 |             client.transport.loseConnection()
   271 |             client.transport.abortConnection()

---

### FINDING 1
repository: celery/celery   pull request #10298 (MERGED)
file: celery/backends/redis.py
claim_type: contract_violation
symbols named: self._pubsub.connection_pool.get_connection() -> _reconnect_pubsub

CLAIM: The call to `get_connection()` without arguments violates the API contract of older redis-py versions which require a `command_name` argument, causing an unhandled `TypeError`.

THE FUNCTION UNDER REVIEW (_reconnect_pubsub, lines 97-128):
    97 |     def _reconnect_pubsub(self):
    98 |         self._pubsub = None
    99 |         self.backend.client.connection_pool.reset()
   100 |         # task state might have changed when the connection was down so we
   101 |         # retrieve meta for all subscribed tasks before going into pubsub mode
   102 |         if self.subscribed_to:
   103 |             metas = self.backend.client.mget(self.subscribed_to)
   104 |             metas = [meta for meta in metas if meta]
   105 |             for meta in metas:
   106 |                 self.on_state_change(self._decode_result(meta), None)
   107 |         self._pubsub = self.backend.client.pubsub(
   108 |             ignore_subscribe_messages=True,
   109 |         )
   110 |         # subscribed_to maybe empty after on_state_change
   111 |         if self.subscribed_to:
   112 |             self._pubsub.subscribe(*self.subscribed_to)
   113 |         else:
   114 |             # redis-py < 5.3.0 requires ``command_name`` as a positional
   115 |             # argument to ``ConnectionPool.get_connection``. The argument was
   116 |             # made optional (and ignored) in 5.3.0+, so passing it stays
   117 |             # compatible across both ranges (#10294).
   118 |             try:
   119 |                 self._pubsub.connection = (
   120 |                     self._pubsub.connection_pool.get_connection()
   121 |                 )
   122 |             except TypeError:
   123 |                 self._pubsub.connection = (
   124 |                     self._pubsub.connection_pool.get_connection('pubsub')
   125 |                 )
   126 |             # even if there is nothing to subscribe, we should not lose the callback after connecting.
   127 |             # The on_connect callback will re-subscribe to any channels we previously subscribed to.
   128 |             self._pubsub.connection.register_connect_callback(self._pubsub.on_connect)

---

### FINDING 2
repository: django/django   pull request #21750 (MERGED)
file: tests/schema/tests.py
claim_type: wrong_order
symbols named: test_fk_alter_on_delete_python_level_noop -> alter_field

CLAIM: The test incorrectly assumes that changing a ForeignKey's `on_delete` from `CASCADE` to `PROTECT` is a database no-op, but Django's schema editor treats `CASCADE` as a special case that creates a database-level `ON DELETE CASCADE` clause, so altering it to `PROTECT` (which has no database-level equivalent) requires dropping and recreating the foreign key constraint.

THE FUNCTION UNDER REVIEW (test_fk_alter_on_delete_python_level_noop, lines 643-656):
   643 |     @skipUnlessDBFeature("supports_foreign_keys", "can_introspect_foreign_keys")
   644 |     def test_fk_alter_on_delete_python_level_noop(self):
   645 |         with connection.schema_editor() as editor:
   646 |             editor.create_model(Author)
   647 |             editor.create_model(Book)
   648 |         old_field = Book._meta.get_field("author")
   649 |         new_field = ForeignKey(Author, PROTECT)
   650 |         new_field.set_attributes_from_name("author")
   651 |         # Changing between Python-level on_delete options doesn't require
   652 |         # database changes.
   653 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
   654 |             editor.alter_field(Book, old_field, new_field, strict=True)
   655 |         with connection.schema_editor() as editor, self.assertNumQueries(0):
   656 |             editor.alter_field(Book, new_field, old_field, strict=True)

---

### FINDING 3
repository: scrapy/scrapy   pull request #7988 (MERGED)
file: scrapy/core/_http2/protocol.py
claim_type: wrong_order
symbols named: self.conn.initiate_connection() -> self.conn.update_settings({SettingCodes.MAX_FRAME_SIZE: max_frame_size})

CLAIM: `initiate_connection` is called before the custom `MAX_FRAME_SIZE` is configured, causing an initial SETTINGS frame with default values to be queued, immediately followed by another SETTINGS frame from `update_settings` with the desired value.

THE FUNCTION UNDER REVIEW (connectionMade, lines 252-268):
   252 |     def connectionMade(self) -> None:
   253 |         """Called by Twisted when the connection is established. We can start
   254 |         sending some data now: we should open with the connection preamble.
   255 |         """
   256 |         # Initialize the timeout
   257 |         self.setTimeout(self.IDLE_TIMEOUT)  # type: ignore[no-untyped-call]
   258 | 
   259 |         assert self.transport is not None  # typing
   260 |         destination = self.transport.getPeer()
   261 |         self.metadata["ip_address"] = ipaddress.ip_address(destination.host)
   262 | 
   263 |         # Initiate H2 Connection
   264 |         self.conn.initiate_connection()
   265 |         max_frame_size = self._crawler.settings.getint("HTTP2_MAX_FRAME_SIZE")
   266 |         if max_frame_size != self.conn.local_settings.max_frame_size:
   267 |             self.conn.update_settings({SettingCodes.MAX_FRAME_SIZE: max_frame_size})
   268 |         self._write_to_transport()

---

### FINDING 4
repository: django/django   pull request #21752 (MERGED)
file: tests/forms_tests/tests/test_media.py
claim_type: unhandled_case
symbols named: Media._get_js -> Media.render

CLAIM: When processing assets, the deduplication logic in `Media._get_js` (and `_get_css`) treats a path to a resource (e.g., 'path/to/script.js') and a pre-rendered, `mark_safe` HTML tag for the same resource (e.g., '<script src="path/to/script.js"></script>') as distinct items, causing `Media.render` to output duplicate assets.

THE FUNCTION UNDER REVIEW (test_html_safe_string_deduplication, lines 880-895):
   880 |     def test_html_safe_string_deduplication(self):
   881 |         js_tag = mark_safe('<script defer src="https://example.org/asset.js"></script>')
   882 |         css_tag = mark_safe(
   883 |             '<link href="https://example.org/asset.css" rel="stylesheet">'
   884 |         )
   885 |         media = Media(
   886 |             css={"all": [css_tag, css_tag, "/path/to/css1"]},
   887 |             js=[js_tag, js_tag, Script("/path/to/js1")],
   888 |         )
   889 |         self.assertHTMLEqual(
   890 |             str(media),
   891 |             '<link href="https://example.org/asset.css" rel="stylesheet">\n'
   892 |             '<link href="/path/to/css1" media="all" rel="stylesheet">\n'
   893 |             '<script defer src="https://example.org/asset.js"></script>\n'
   894 |             '<script src="/path/to/js1"></script>',
   895 |         )

---

### FINDING 5
repository: ansible/ansible   pull request #87250 (MERGED)
file: lib/ansible/module_utils/basic.py
claim_type: missing_guard
symbols named: log -> _logging.log_to_system

CLAIM: The `log` method no longer ensures `log_args` is a dictionary (by replacing `None` with `{}`), causing a `TypeError` when `log_args` is `None` and the internal `_logging.log_to_system` function attempts to iterate over it.

THE FUNCTION UNDER REVIEW (log, lines 1243-1270):
  1243 |     def log(self, msg, log_args=None):
  1244 | 
  1245 |         if self.no_log:
  1246 |             return
  1247 | 
  1248 |         if not isinstance(msg, (bytes, str)):
  1249 |             raise TypeError("msg should be a string (got %s)" % type(msg))
  1250 | 
  1251 |         if isinstance(msg, bytes):
  1252 |             msg = msg.decode('utf-8', 'replace')
  1253 | 
  1254 |         msg = remove_values(msg, self.no_log_values)
  1255 | 
  1256 |         try:
  1257 |             _logging.log_to_system(
  1258 |                 msg,
  1259 |                 module_name=self._name,
  1260 |                 log_args=log_args,
  1261 |                 syslog_facility=self._syslog_facility,
  1262 |                 target_log_info=self._target_log_info,
  1263 |             )
  1264 |         except (TypeError, ValueError) as e:
  1265 |             self.fail_json(
  1266 |                 msg='Failed to log to syslog (%s). To proceed anyway, '
  1267 |                     'disable syslog logging by setting no_target_syslog '
  1268 |                     'to True in your Ansible config.' % to_native(e),
  1269 |                 msg_to_log=msg,
  1270 |             )

---

### FINDING 6
repository: celery/celery   pull request #10459 (MERGED)
file: t/unit/backends/test_rpc.py
claim_type: contract_violation
symbols named: test_final_state_cached_when_cache_enabled -> RPCBackend

CLAIM: The test `test_final_state_cached_when_cache_enabled` instantiates a local `RPCBackend` instance `b` which is distinct from the `self.b` instance used by helper methods and other tests in the same test class, violating the test class's implicit contract of operating on the instance created in `setup_method`.

THE FUNCTION UNDER REVIEW (test_final_state_cached_when_cache_enabled, lines 355-371):
   355 |     def test_final_state_cached_when_cache_enabled(self):
   356 |         # the test app sets result_cache_max=-1 (cache disabled),
   357 |         # with caching on the final meta is served from the cache.
   358 |         old_cache_max = self.app.conf.result_cache_max
   359 |         self.app.conf.result_cache_max = 100
   360 |         try:
   361 |             b = RPCBackend(app=self.app)
   362 |             message = self.make_message('tid1', states.SUCCESS, 42)
   363 |             with patch.object(b, '_slurp_from_queue',
   364 |                               return_value=iter([message])):
   365 |                 b.get_task_meta('tid1')
   366 |             assert b._cache['tid1']['status'] == states.SUCCESS
   367 |             with patch.object(b, '_slurp_from_queue',
   368 |                               return_value=iter([])):
   369 |                 assert b.get_task_meta('tid1')['result'] == 42
   370 |         finally:
   371 |             self.app.conf.result_cache_max = old_cache_max
