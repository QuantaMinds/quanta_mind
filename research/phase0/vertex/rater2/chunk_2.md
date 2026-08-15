# Findings to adjudicate — chunk 2

There are 11 findings below, numbered by their global index.

### FINDING 22
repository: vllm-project/vllm   pull request #51316 (MERGED)
file: vllm/v1/engine/core.py
the model was shown this function: _make_ready_response
claim_type: missing_guard   model_confidence: high
cited line_a: 1645    cited line_b: 1645

CLAIM: The code at line 1645 calls a method on `self.model_executor` without checking if it is `None`, which will cause an `AttributeError` if the engine is initialized in a state where the model executor is not created (e.g. with `skip_model_init=True`).

CODE AROUND line_a (1645):
         1637 |             kv_events_config=self.scheduler.get_kv_event_publisher_config(),
         1638 |             weight_transfer_backend=(
         1639 |                 self.vllm_config.weight_transfer_config.backend
         1640 |                 if self.vllm_config.weight_transfer_config is not None
         1641 |                 else None
         1642 |             ),
         1643 |             enable_sleep_mode=self.vllm_config.model_config.enable_sleep_mode,
         1644 |             supports_draft_weight_updates=(
    >>>  1645 |                 self.model_executor.supports_draft_weight_updates()
         1646 |             ),
         1647 |         )
         1648 | 
         1649 |     def process_input_sockets(
         1650 |         self,
         1651 |         input_addresses: list[str],
         1652 |         coord_input_address: str | None,
         1653 |         identity: bytes,

CODE AROUND line_b (1645):
         1637 |             kv_events_config=self.scheduler.get_kv_event_publisher_config(),
         1638 |             weight_transfer_backend=(
         1639 |                 self.vllm_config.weight_transfer_config.backend
         1640 |                 if self.vllm_config.weight_transfer_config is not None
         1641 |                 else None
         1642 |             ),
         1643 |             enable_sleep_mode=self.vllm_config.model_config.enable_sleep_mode,
         1644 |             supports_draft_weight_updates=(
    >>>  1645 |                 self.model_executor.supports_draft_weight_updates()
         1646 |             ),
         1647 |         )
         1648 | 
         1649 |     def process_input_sockets(
         1650 |         self,
         1651 |         input_addresses: list[str],
         1652 |         coord_input_address: str | None,
         1653 |         identity: bytes,

---

### FINDING 23
repository: Skyvern-AI/skyvern   pull request #8211 (MERGED)
file: tests/unit/test_copilot_request_policy_signin_intent_absent.py
the model was shown this function: test_stored_context_carrying_a_signin_email_still_loads
claim_type: missing_guard   model_confidence: high
cited line_a: 48    cited line_b: 53

CLAIM: Line 48 creates a serialized context with a `signin_email` field, but the assertion at line 53 only confirms that `user_goal` is loaded and fails to check that the sensitive `signin_email` field was sanitized or ignored during deserialization.

CODE AROUND line_a (48):
           40 | 
           41 |     prompt = instructions(SimpleNamespace(context=ctx), None)
           42 | 
           43 |     assert "signin" not in prompt.lower()
           44 | 
           45 | 
           46 | def test_stored_context_carrying_a_signin_email_still_loads() -> None:
           47 |     stored = json.dumps(
    >>>    48 |         {"user_goal": "sign in", "signin_email": "user@example.com", "signin_email_host": "example.com"}
           49 |     )
           50 | 
           51 |     structured = StructuredContext.from_json_str(stored)
           52 | 
           53 |     assert structured.user_goal == "sign in"
           54 | 

CODE AROUND line_b (53):
           45 | 
           46 | def test_stored_context_carrying_a_signin_email_still_loads() -> None:
           47 |     stored = json.dumps(
           48 |         {"user_goal": "sign in", "signin_email": "user@example.com", "signin_email_host": "example.com"}
           49 |     )
           50 | 
           51 |     structured = StructuredContext.from_json_str(stored)
           52 | 
    >>>    53 |     assert structured.user_goal == "sign in"
           54 | 

---

### FINDING 24
repository: cartography-cncf/cartography   pull request #3111 (MERGED)
file: cartography/graph/job.py
the model was shown this function: from_matchlink
claim_type: contract_violation   model_confidence: high
cited line_a: 436    cited line_b: 455

CLAIM: The docstring starting at line 436 requires using parameter names from the `rel_schema` object for the query parameters, but the code at line 455 uses a hardcoded string `"_sub_resource_label"` as a parameter key.

CODE AROUND line_a (436):
          428 | 
          429 |         Note:
          430 |             - This method is specifically designed for matchlink cleanup operations.
          431 |             - Required relationship properties ``_sub_resource_label`` and ``_sub_resource_id``
          432 |               must be defined in the rel_schema.
          433 |             - For a given rel_schema, the fields used in the rel_schema.properties._sub_resource_label.name and
          434 |               rel_schema.properties._sub_resource_id.name must be provided as keys and values in the params dict.
          435 |             - The rel_schema must have a source_node_matcher and target_node_matcher.
    >>>   436 | 
          437 |         """
          438 |         cleanup_link_query = build_cleanup_query_for_matchlink(rel_schema)
          439 |         logger.debug("Cleanup query: %s", cleanup_link_query)
          440 | 
          441 |         parameters = {
          442 |             "UPDATE_TAG": update_tag,
          443 |             "_sub_resource_label": sub_resource_label,
          444 |             "_sub_resource_id": sub_resource_id,

CODE AROUND line_b (455):
          447 |         statement = GraphStatement(
          448 |             cleanup_link_query,
          449 |             parameters=parameters,
          450 |             iterative=True,
          451 |             iterationsize=iterationsize,
          452 |             parent_job_name=rel_schema.rel_label,
          453 |         )
          454 | 
    >>>   455 |         return cls(
          456 |             f"Cleanup {rel_schema.rel_label} between {rel_schema.source_node_label} and {rel_schema.target_node_label}",
          457 |             [statement],
          458 |             rel_schema.rel_label,
          459 |         )
          460 | 
          461 |     @classmethod
          462 |     def from_json_file(cls, file_path: Union[str, Path]) -> "GraphJob":
          463 |         """

---

### FINDING 25
repository: Skyvern-AI/skyvern   pull request #8213 (MERGED)
file: skyvern/forge/sdk/forge_log.py
the model was shown this function: render_bounded_json
claim_type: contract_violation   model_confidence: high
cited line_a: 256    cited line_b: 276

CLAIM: The `minimal` dictionary at line 276 is created by truncating values from the `bounded` dictionary, but `bounded`'s values from line 256 may already be truncated strings, leading to doubly-truncated results.

CODE AROUND line_a (256):
          248 |     # length is also the emitted UTF-8 byte length without allocating another copy.
          249 |     original_size_bytes = len(rendered)
          250 |     if original_size_bytes <= MAX_JSON_LOG_BYTES:
          251 |         return rendered
          252 | 
          253 |     bounded = {
          254 |         key: _truncate_log_value(
          255 |             event_dict[key],
    >>>   256 |             _OVERSIZED_LOG_VALUE_CHARS if key in {"msg", "exception"} else _OVERSIZED_LOG_METADATA_CHARS,
          257 |         )
          258 |         for key in _OVERSIZED_LOG_FIELDS
          259 |         if key in event_dict
          260 |     }
          261 |     omitted_fields = sorted(str(key)[:128] for key in event_dict if key not in bounded)
          262 |     bounded.update(
          263 |         {
          264 |             "log_truncated": True,

CODE AROUND line_b (276):
          268 |         }
          269 |     )
          270 |     rendered = _JSON_RENDERER(logger, method_name, bounded)
          271 |     if len(rendered) <= MAX_JSON_LOG_BYTES:
          272 |         return rendered
          273 | 
          274 |     # Unusual escaped/control-heavy metadata can expand during JSON encoding. Keep a
          275 |     # minimal correlated record rather than emitting another line the collector splits.
    >>>   276 |     minimal = {
          277 |         key: _truncate_log_value(bounded[key], 256 if key == "msg" else 128)
          278 |         for key in _OVERSIZED_LOG_FIELDS
          279 |         if key in bounded and key != "exception"
          280 |     }
          281 |     minimal.update(
          282 |         {
          283 |             "log_truncated": True,
          284 |             "original_size_bytes": original_size_bytes,

---

### FINDING 26
repository: vllm-project/vllm   pull request #51216 (MERGED)
file: tests/v1/worker/test_gpu_model_runner.py
the model was shown this function: test_select_common_block_size_accepts_rocm_sparse_block_size_16
claim_type: missing_guard   model_confidence: high
cited line_a: 41    cited line_b: 298

CLAIM: The unconditional import of `ROCMAiterMLASparseBackend` starting on line 41, a ROCm-specific module, will cause test collection to fail on non-ROCm systems, preventing any tests in the file including the one at line 298 from running.

CODE AROUND line_a (41):
           33 | from vllm.sampling_params import SamplingParams
           34 | from vllm.utils.mem_constants import GiB_bytes
           35 | from vllm.utils.system_utils import update_environment_variables
           36 | from vllm.utils.torch_utils import set_random_seed
           37 | from vllm.v1.attention.backend import MultipleOf
           38 | from vllm.v1.attention.backends.mla.indexer import DeepseekV32IndexerBackend
           39 | from vllm.v1.attention.backends.mla.rocm_aiter_mla_sparse import (
           40 |     ROCMAiterMLASparseBackend,
    >>>    41 | )
           42 | from vllm.v1.attention.backends.registry import AttentionBackendEnum
           43 | from vllm.v1.core.kv_cache_utils import estimate_max_model_len, get_kv_cache_configs
           44 | from vllm.v1.core.sched.output import CachedRequestData, NewRequestData, SchedulerOutput
           45 | from vllm.v1.kv_cache_interface import (
           46 |     FullAttentionSpec,
           47 |     KVCacheConfig,
           48 |     KVCacheGroupSpec,
           49 |     KVCacheTensor,

CODE AROUND line_b (298):
          290 | def test_select_common_block_size_uses_largest_shared_int():
          291 |     backend_a = _make_mock_backend_for_kernel_block_size([128, 64])
          292 |     backend_b = _make_mock_backend_for_kernel_block_size([64, 32])
          293 | 
          294 |     selected_size = select_common_block_size(256, [backend_a, backend_b])
          295 |     assert selected_size == 64
          296 | 
          297 | 
    >>>   298 | def test_select_common_block_size_accepts_rocm_sparse_block_size_16(monkeypatch):
          299 |     monkeypatch.setattr(current_platform, "is_rocm", lambda: True)
          300 | 
          301 |     selected_size = select_common_block_size(
          302 |         16,
          303 |         [DeepseekV32IndexerBackend, ROCMAiterMLASparseBackend],
          304 |     )
          305 |     assert selected_size == 16
          306 | 

---

### FINDING 27
repository: vllm-project/vllm   pull request #51216 (MERGED)
file: vllm/v1/attention/backends/mla/indexer.py
the model was shown this function: get_supported_kernel_block_sizes
claim_type: contract_violation   model_confidence: high
cited line_a: 144    cited line_b: 144

CLAIM: The function returns `MultipleOf(16)` for ROCm, which makes an unbounded claim that the kernel supports any block size that is a multiple of 16, but kernels typically have an upper block size limit, making this claim likely incorrect and capable of causing runtime failures.

CODE AROUND line_a (144):
          136 |         return _supports_varlen_paged_mqa_logits()
          137 | 
          138 |     @staticmethod
          139 |     def get_name() -> str:
          140 |         return "DEEPSEEK_V32_INDEXER"
          141 | 
          142 |     @staticmethod
          143 |     def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:
    >>>   144 |         return [1, MultipleOf(16)] if current_platform.is_rocm() else [64]
          145 | 
          146 |     @classmethod
          147 |     def get_supported_head_sizes(cls) -> list[int]:
          148 |         return [32, 64, 128]
          149 | 
          150 |     @staticmethod
          151 |     def get_builder_cls() -> type["DeepseekV32IndexerMetadataBuilder"]:
          152 |         return DeepseekV32IndexerMetadataBuilder

CODE AROUND line_b (144):
          136 |         return _supports_varlen_paged_mqa_logits()
          137 | 
          138 |     @staticmethod
          139 |     def get_name() -> str:
          140 |         return "DEEPSEEK_V32_INDEXER"
          141 | 
          142 |     @staticmethod
          143 |     def get_supported_kernel_block_sizes() -> list[int | MultipleOf]:
    >>>   144 |         return [1, MultipleOf(16)] if current_platform.is_rocm() else [64]
          145 | 
          146 |     @classmethod
          147 |     def get_supported_head_sizes(cls) -> list[int]:
          148 |         return [32, 64, 128]
          149 | 
          150 |     @staticmethod
          151 |     def get_builder_cls() -> type["DeepseekV32IndexerMetadataBuilder"]:
          152 |         return DeepseekV32IndexerMetadataBuilder

---

### FINDING 28
repository: Skyvern-AI/skyvern   pull request #8210 (MERGED)
file: tests/unit/test_copilot_challenge_evidence_is_not_a_verdict.py
the model was shown this function: test_challenge_state_is_never_the_condition_for_abandoning_a_run
claim_type: missing_guard   model_confidence: high
cited line_a: 46    cited line_b: 49

CLAIM: The check at line 46 processes each line in isolation, causing the assertion at line 49 to miss forbidden instructions that are conditioned on 'gates_submit_controls' across multiple lines.

CODE AROUND line_a (46):
           38 |     assert not found, f"{source.name} still tells the model to stop on challenge evidence: {found}"
           39 | 
           40 | 
           41 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           42 | def test_challenge_state_is_never_the_condition_for_abandoning_a_run(source: Path) -> None:
           43 |     # Reading challenge_state is fine and expected; conditioning a retreat on it is not.
           44 |     for line_number, line in enumerate(source.read_text().splitlines(), start=1):
           45 |         if "gates_submit_controls" not in line:
    >>>    46 |             continue
           47 |         lowered = line.lower()
           48 |         assert "stop and report" not in lowered, f"{source.name}:{line_number} conditions a stop on challenge state"
           49 |         assert "rather than retrying" not in lowered, (
           50 |             f"{source.name}:{line_number} conditions a retreat on challenge state"
           51 |         )
           52 | 

CODE AROUND line_b (49):
           41 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           42 | def test_challenge_state_is_never_the_condition_for_abandoning_a_run(source: Path) -> None:
           43 |     # Reading challenge_state is fine and expected; conditioning a retreat on it is not.
           44 |     for line_number, line in enumerate(source.read_text().splitlines(), start=1):
           45 |         if "gates_submit_controls" not in line:
           46 |             continue
           47 |         lowered = line.lower()
           48 |         assert "stop and report" not in lowered, f"{source.name}:{line_number} conditions a stop on challenge state"
    >>>    49 |         assert "rather than retrying" not in lowered, (
           50 |             f"{source.name}:{line_number} conditions a retreat on challenge state"
           51 |         )
           52 | 

---

### FINDING 29
repository: Skyvern-AI/skyvern   pull request #8210 (MERGED)
file: tests/unit/test_copilot_challenge_evidence_is_not_a_verdict.py
the model was shown this function: test_no_model_facing_surface_orders_a_stop_from_challenge_evidence
claim_type: unhandled_case   model_confidence: high
cited line_a: 37    cited line_b: 38

CLAIM: The case-sensitive search on line 37 may fail to find forbidden phrases that use different capitalization, causing the assertion on line 38 to incorrectly pass and miss a violation.

CODE AROUND line_a (37):
           29 |     "report the observed anti-bot blocker rather than retrying",
           30 |     "treat challenge resolution",
           31 | )
           32 | 
           33 | 
           34 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           35 | def test_no_model_facing_surface_orders_a_stop_from_challenge_evidence(source: Path) -> None:
           36 |     text = source.read_text()
    >>>    37 |     found = [phrase for phrase in STOP_PHRASES if phrase in text]
           38 |     assert not found, f"{source.name} still tells the model to stop on challenge evidence: {found}"
           39 | 
           40 | 
           41 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           42 | def test_challenge_state_is_never_the_condition_for_abandoning_a_run(source: Path) -> None:
           43 |     # Reading challenge_state is fine and expected; conditioning a retreat on it is not.
           44 |     for line_number, line in enumerate(source.read_text().splitlines(), start=1):
           45 |         if "gates_submit_controls" not in line:

CODE AROUND line_b (38):
           30 |     "treat challenge resolution",
           31 | )
           32 | 
           33 | 
           34 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           35 | def test_no_model_facing_surface_orders_a_stop_from_challenge_evidence(source: Path) -> None:
           36 |     text = source.read_text()
           37 |     found = [phrase for phrase in STOP_PHRASES if phrase in text]
    >>>    38 |     assert not found, f"{source.name} still tells the model to stop on challenge evidence: {found}"
           39 | 
           40 | 
           41 | @pytest.mark.parametrize("source", MODEL_FACING_SOURCES, ids=lambda p: p.name)
           42 | def test_challenge_state_is_never_the_condition_for_abandoning_a_run(source: Path) -> None:
           43 |     # Reading challenge_state is fine and expected; conditioning a retreat on it is not.
           44 |     for line_number, line in enumerate(source.read_text().splitlines(), start=1):
           45 |         if "gates_submit_controls" not in line:
           46 |             continue

---

### FINDING 30
repository: langchain-ai/langchain   pull request #39367 (MERGED)
file: libs/core/langchain_core/utils/aiter.py
the model was shown this function: abatch_iterate
claim_type: contract_violation   model_confidence: high
cited line_a: 357    cited line_b: 357

CLAIM: After a batch is yielded on line 357, the `batch` list is not cleared, causing subsequent yields to contain elements from prior batches instead of yielding distinct, non-overlapping batches.

CODE AROUND line_a (357):
          349 |         raise ValueError(msg)
          350 |     batch: list[T] = []
          351 |     async for element in iterable:
          352 |         batch.append(element)
          353 |         if len(batch) >= size:
          354 |             yield batch
          355 |             batch = []
          356 |     if batch:
    >>>   357 |         yield batch
          358 | 

CODE AROUND line_b (357):
          349 |         raise ValueError(msg)
          350 |     batch: list[T] = []
          351 |     async for element in iterable:
          352 |         batch.append(element)
          353 |         if len(batch) >= size:
          354 |             yield batch
          355 |             batch = []
          356 |     if batch:
    >>>   357 |         yield batch
          358 | 

---

### FINDING 31
repository: langchain-ai/langchain   pull request #39651 (MERGED)
file: libs/partners/openai/tests/integration_tests/chat_models/test_base.py
the model was shown this function: _test_stream
claim_type: unhandled_case   model_confidence: high
cited line_a: 391    cited line_b: 394

CLAIM: The `elif` at line 391 causes the execution to fall through when `expect_usage` is false and `_GATEWAY_ENABLED` is true, so the function completes at line 394 without verifying that usage metadata is present, contrary to the documented behavior (line 389) that the gateway should always provide it.

CODE AROUND line_a (391):
          383 |                 )
          384 |                 raise AssertionError(msg)
          385 |             assert full.usage_metadata is not None
          386 |             assert full.usage_metadata["input_tokens"] > 0
          387 |             assert full.usage_metadata["output_tokens"] > 0
          388 |             assert full.usage_metadata["total_tokens"] > 0
          389 |         # The LangSmith gateway always emits a usage chunk regardless of
          390 |         # `stream_options.include_usage`, so the opt-out assertions below only
    >>>   391 |         # hold when not routing through it.
          392 |         elif not _GATEWAY_ENABLED:
          393 |             assert chunks_with_token_counts == 0
          394 |             assert full.usage_metadata is None
          395 | 
          396 |     llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, max_tokens=MAX_TOKEN_COUNT)  # type: ignore[call-arg]
          397 |     await _test_stream(llm.astream("Hello", stream_usage=False), expect_usage=False)
          398 |     await _test_stream(
          399 |         llm.astream("Hello", stream_options={"include_usage": True}), expect_usage=True

CODE AROUND line_b (394):
          386 |             assert full.usage_metadata["input_tokens"] > 0
          387 |             assert full.usage_metadata["output_tokens"] > 0
          388 |             assert full.usage_metadata["total_tokens"] > 0
          389 |         # The LangSmith gateway always emits a usage chunk regardless of
          390 |         # `stream_options.include_usage`, so the opt-out assertions below only
          391 |         # hold when not routing through it.
          392 |         elif not _GATEWAY_ENABLED:
          393 |             assert chunks_with_token_counts == 0
    >>>   394 |             assert full.usage_metadata is None
          395 | 
          396 |     llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, max_tokens=MAX_TOKEN_COUNT)  # type: ignore[call-arg]
          397 |     await _test_stream(llm.astream("Hello", stream_usage=False), expect_usage=False)
          398 |     await _test_stream(
          399 |         llm.astream("Hello", stream_options={"include_usage": True}), expect_usage=True
          400 |     )
          401 |     await _test_stream(llm.astream("Hello", stream_usage=True), expect_usage=True)
          402 |     llm = ChatOpenAI(

---

### FINDING 32
repository: cartography-cncf/cartography   pull request #3145 (MERGED)
file: tests/unit/cartography/intel/wiz/test_transforms.py
the model was shown this function: test_transform_findings_labels_non_cve_vulnerabilities_as_security_issues
claim_type: contract_violation   model_confidence: high
cited line_a: 44    cited line_b: 53

CLAIM: Line 44 copies all fields from a finding that has a CVE, but the following lines only overwrite top-level keys, likely leaving nested CVE data untouched, which could cause the assertion for a non-CVE finding on line 53 to fail.

CODE AROUND line_a (44):
           36 |     assert findings[0]["resource_id"] == RESOURCE_ID_1
           37 |     assert findings[0]["resource_external_id"] == (
           38 |         "arn:aws:ec2:us-east-1:123456789012:instance/i-123"
           39 |     )
           40 | 
           41 | 
           42 | def test_transform_findings_labels_non_cve_vulnerabilities_as_security_issues():
           43 |     finding = {
    >>>    44 |         **VULNERABILITY_FINDINGS[0],
           45 |         "name": "openssl vulnerability",
           46 |         "detailedName": "openssl",
           47 |         "description": "Package is vulnerable",
           48 |         "link": None,
           49 |     }
           50 | 
           51 |     transformed = transform_findings([finding], TENANT_ID)
           52 | 

CODE AROUND line_b (53):
           45 |         "name": "openssl vulnerability",
           46 |         "detailedName": "openssl",
           47 |         "description": "Package is vulnerable",
           48 |         "link": None,
           49 |     }
           50 | 
           51 |     transformed = transform_findings([finding], TENANT_ID)
           52 | 
    >>>    53 |     assert transformed[0]["has_cve"] == "false"
           54 |     assert transformed[0]["is_security_issue"] == "true"
           55 | 
           56 | 
           57 | def test_transform_findings_extracts_configuration_metadata():
           58 |     findings = transform_findings(CONFIGURATION_FINDINGS, TENANT_ID)
           59 | 
           60 |     assert findings[0]["id"] == CONFIGURATION_FINDING_ID_1
           61 |     assert findings[0]["finding_type"] == "CONFIGURATION"
