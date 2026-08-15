# Findings to adjudicate — chunk 1

There are 11 findings below, numbered by their global index.

### FINDING 11
repository: huggingface/transformers   pull request #47944 (MERGED)
file: src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py
the model was shown this function: _init_weights
claim_type: contract_violation   model_confidence: high
cited line_a: 416    cited line_b: 902

CLAIM: The `dt_bias` parameter is initialized to ones when its containing module is constructed at line 416, but this initialization is redundant because the parameter is always re-initialized to ones by `_init_weights` at line 902.

CODE AROUND line_a (416):
          408 |             groups=self.conv_dim,
          409 |             padding=self.conv_kernel_size - 1,
          410 |         )
          411 | 
          412 |         # time step projection (discretization)
          413 |         # instantiate once and copy inv_dt in init_weights of PretrainedModel
          414 |         self.dt_bias = nn.Parameter(torch.ones(self.num_v_heads))
          415 | 
    >>>   416 |         # Lower bound kept away from 0 so log(A) never becomes -inf
          417 |         A = torch.empty(self.num_v_heads).uniform_(0.01, 16)
          418 |         self.A_log = nn.Parameter(torch.log(A))
          419 | 
          420 |         self.norm = Qwen3_5MoeRMSNormGated(self.head_v_dim, eps=self.layer_norm_epsilon)
          421 |         self.out_proj = nn.Linear(self.value_dim, self.hidden_size, bias=False)
          422 | 
          423 |         self.layer_type = config.layer_types[layer_idx]
          424 | 

CODE AROUND line_b (902):
          894 |     }
          895 |     _is_stateful = True
          896 |     _can_compile_fullgraph = True
          897 | 
          898 |     @torch.no_grad()
          899 |     def _init_weights(self, module):
          900 |         super()._init_weights(module)
          901 |         if isinstance(module, Qwen3_5MoeGatedDeltaNet):
    >>>   902 |             init.ones_(module.dt_bias)
          903 |             # Lower bound kept away from 0 so log(A) never becomes -inf
          904 |             init.copy_(
          905 |                 module.A_log,
          906 |                 torch.empty(module.num_v_heads, device=module.A_log.device).uniform_(0.01, 16).log_(),
          907 |             )
          908 |         # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
          909 |         elif isinstance(module, Qwen3_5MoeRMSNorm):
          910 |             init.zeros_(module.weight)

---

### FINDING 12
repository: apache/airflow   pull request #61702 (MERGED)
file: airflow-core/tests/unit/models/test_serialized_dag.py
the model was shown this function: test_deadline_interval_change_triggers_new_serdag
claim_type: resource_leak   model_confidence: high
cited line_a: 798    cited line_b: 806

CLAIM: The database transaction is committed at line 798, but then another transaction is started and committed at line 806 without rolling back or cleaning up the first, potentially leaving orphaned data in the database if the test fails in between.

CODE AROUND line_a (798):
          790 |         session.commit()
          791 |         orig_serdag = session.scalar(select(SDM).where(SDM.dag_id == dag_id).order_by(SDM.created_at.desc()))
          792 | 
          793 |         # Modify the Dag's deadline interval.
          794 |         dag.deadline = DeadlineAlert(
          795 |             reference=DeadlineReference.DAGRUN_QUEUED_AT,
          796 |             interval=timedelta(minutes=10),
          797 |             callback=AsyncCallback(empty_callback_for_deadline),
    >>>   798 |         )
          799 | 
          800 |         SDM.write_dag(LazyDeserializedDAG.from_dag(dag), bundle_name="testing", session=session)
          801 |         session.commit()
          802 | 
          803 |         new_serdag_count = session.scalar(select(func.count()).select_from(SDM).where(SDM.dag_id == dag_id))
          804 |         new_serdag = session.scalar(select(SDM).where(SDM.dag_id == dag_id).order_by(SDM.created_at.desc()))
          805 |         new_alert = session.scalar(select(DAM).where(DAM.serialized_dag_id == new_serdag.id))
          806 | 

CODE AROUND line_b (806):
          798 |         )
          799 | 
          800 |         SDM.write_dag(LazyDeserializedDAG.from_dag(dag), bundle_name="testing", session=session)
          801 |         session.commit()
          802 | 
          803 |         new_serdag_count = session.scalar(select(func.count()).select_from(SDM).where(SDM.dag_id == dag_id))
          804 |         new_serdag = session.scalar(select(SDM).where(SDM.dag_id == dag_id).order_by(SDM.created_at.desc()))
          805 |         new_alert = session.scalar(select(DAM).where(DAM.serialized_dag_id == new_serdag.id))
    >>>   806 | 
          807 |         # There should be a second serdag with a new hash and the new interval.
          808 |         assert new_serdag_count == 2
          809 |         assert new_serdag.dag_hash != orig_serdag.dag_hash
          810 |         assert new_alert.interval == 600.0
          811 | 

---

### FINDING 13
repository: apache/airflow   pull request #61702 (MERGED)
file: airflow-core/src/airflow/models/serialized_dag.py
the model was shown this function: _try_reuse_deadline_uuids
claim_type: wrong_order   model_confidence: high
cited line_a: 453    cited line_b: 464

CLAIM: The query at line 453 fetches `existing_alerts` from the database without a guaranteed order, but the loop starting at line 464 iterates through `new_deadline_data` and performs a greedy match, which can fail to find a valid mapping if there are identical deadline definitions and the non-deterministic order of `existing_alerts` is unfavorable.

CODE AROUND line_a (453):
          445 | 
          446 |         if len(existing_deadline_uuids) != len(new_deadline_data):
          447 |             return None
          448 | 
          449 |         existing_deadline_uuids_as_uuid = [UUID(uid) for uid in existing_deadline_uuids]
          450 |         existing_alerts = session.scalars(
          451 |             select(DeadlineAlertModel).where(DeadlineAlertModel.id.in_(existing_deadline_uuids_as_uuid))
          452 |         ).all()
    >>>   453 | 
          454 |         if len(existing_alerts) != len(existing_deadline_uuids):
          455 |             return None
          456 | 
          457 |         matched_uuids: set[UUID] = set()
          458 |         uuid_mapping: dict[str, dict] = {}
          459 | 
          460 |         for deadline_alert in new_deadline_data:
          461 |             deadline_data = deadline_alert.get(Encoding.VAR, deadline_alert)

CODE AROUND line_b (464):
          456 | 
          457 |         matched_uuids: set[UUID] = set()
          458 |         uuid_mapping: dict[str, dict] = {}
          459 | 
          460 |         for deadline_alert in new_deadline_data:
          461 |             deadline_data = deadline_alert.get(Encoding.VAR, deadline_alert)
          462 | 
          463 |             found_match = False
    >>>   464 |             for existing_alert in existing_alerts:
          465 |                 if existing_alert.id in matched_uuids:
          466 |                     continue  # Already matched to another new deadline
          467 | 
          468 |                 if _definitions_match(deadline_data, existing_alert):
          469 |                     # Found a match, reuse this UUID
          470 |                     uuid_mapping[str(existing_alert.id)] = deadline_data
          471 |                     matched_uuids.add(existing_alert.id)
          472 |                     found_match = True

---

### FINDING 14
repository: langchain-ai/langchain   pull request #39651 (MERGED)
file: libs/partners/openai/tests/integration_tests/chat_models/test_base.py
the model was shown this function: _gateway_or_provider_key
claim_type: missing_guard   model_confidence: high
cited line_a: 53    cited line_b: 55

CLAIM: When the condition on line 53 is false, the code accesses the `OPENAI_API_KEY` environment variable on line 55 without a prior check for its existence, which can cause a `KeyError`.

CODE AROUND line_a (53):
           45 | 
           46 | 
           47 | def _gateway_or_provider_key() -> str:
           48 |     """Return an API key valid for the endpoint the base URL resolves to.
           49 | 
           50 |     When the LangSmith gateway is enabled, requests route through it and must
           51 |     authenticate with the gateway key rather than the provider key.
           52 |     """
    >>>    53 |     if _GATEWAY_ENABLED:
           54 |         return os.environ["LANGSMITH_GATEWAY_API_KEY"]
           55 |     return os.environ["OPENAI_API_KEY"]
           56 | 
           57 | 
           58 | @pytest.mark.scheduled
           59 | def test_chat_openai() -> None:
           60 |     """Test ChatOpenAI wrapper."""
           61 |     chat = ChatOpenAI(

CODE AROUND line_b (55):
           47 | def _gateway_or_provider_key() -> str:
           48 |     """Return an API key valid for the endpoint the base URL resolves to.
           49 | 
           50 |     When the LangSmith gateway is enabled, requests route through it and must
           51 |     authenticate with the gateway key rather than the provider key.
           52 |     """
           53 |     if _GATEWAY_ENABLED:
           54 |         return os.environ["LANGSMITH_GATEWAY_API_KEY"]
    >>>    55 |     return os.environ["OPENAI_API_KEY"]
           56 | 
           57 | 
           58 | @pytest.mark.scheduled
           59 | def test_chat_openai() -> None:
           60 |     """Test ChatOpenAI wrapper."""
           61 |     chat = ChatOpenAI(
           62 |         temperature=0.7,
           63 |         base_url=None,

---

### FINDING 15
repository: huggingface/transformers   pull request #47152 (MERGED)
file: tests/quantization/compressed_tensors_integration/test_compressed_tensors.py
the model was shown this function: test_frozen_fp8_dequantized_on_load
claim_type: resource_leak   model_confidence: high
cited line_a: 62    cited line_b: 75

CLAIM: The model loaded at line 62 allocates significant GPU memory but is not explicitly deallocated before the function returns at line 75, which can lead to out-of-memory errors in other tests.

CODE AROUND line_a (62):
           54 |     def test_tinyllama_fp8(self):
           55 |         self._test_quantized_model(self.tinyllama_fp8, 20.0)
           56 | 
           57 |     def test_tinyllama_w8a16(self):
           58 |         self._test_quantized_model(self.tinyllama_w8a16, 20.0)
           59 | 
           60 |     def test_frozen_fp8_dequantized_on_load(self):
           61 |         quantization_config = CompressedTensorsConfig(run_compressed=False)
    >>>    62 |         model = AutoModelForCausalLM.from_pretrained(
           63 |             self.llama3_fp8_frozen,
           64 |             device_map=torch_device,
           65 |             torch_dtype=torch.float32,
           66 |             quantization_config=quantization_config,
           67 |         )
           68 |         weight = model.model.layers[0].self_attn.q_proj.weight
           69 |         # Dequantized max is small (~0.68); raw fp8 max would be 448.0
           70 |         self.assertLess(weight.abs().max().item(), 5.0)

CODE AROUND line_b (75):
           67 |         )
           68 |         weight = model.model.layers[0].self_attn.q_proj.weight
           69 |         # Dequantized max is small (~0.68); raw fp8 max would be 448.0
           70 |         self.assertLess(weight.abs().max().item(), 5.0)
           71 | 
           72 |         tokenizer = AutoTokenizer.from_pretrained(self.llama3_fp8_frozen)
           73 |         inputs = tokenizer(self.prompt, return_tensors="pt").to(torch_device)
           74 |         output_ids = model.generate(**inputs, max_new_tokens=8, do_sample=False)
    >>>    75 |         self.assertGreater(output_ids.shape[1], inputs["input_ids"].shape[1])
           76 | 
           77 |     def _test_quantized_model(self, model_name: str, expected_perplexity: float):
           78 |         # load model
           79 |         quantized_model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
           80 |         tokenizer = AutoTokenizer.from_pretrained(model_name)
           81 |         device = quantized_model.device
           82 | 
           83 |         # check config

---

### FINDING 16
repository: cartography-cncf/cartography   pull request #3111 (MERGED)
file: cartography/graph/job.py
the model was shown this function: from_matchlink
claim_type: missing_guard   model_confidence: high
cited line_a: 439    cited line_b: 451

CLAIM: The docstring at line 439 states that `rel_schema` must have a `source_node_matcher` and `target_node_matcher`, but the code at line 451 uses `rel_schema` without verifying this precondition, which could lead to an `AttributeError`.

CODE AROUND line_a (439):
          431 |             - Required relationship properties ``_sub_resource_label`` and ``_sub_resource_id``
          432 |               must be defined in the rel_schema.
          433 |             - For a given rel_schema, the fields used in the rel_schema.properties._sub_resource_label.name and
          434 |               rel_schema.properties._sub_resource_id.name must be provided as keys and values in the params dict.
          435 |             - The rel_schema must have a source_node_matcher and target_node_matcher.
          436 | 
          437 |         """
          438 |         cleanup_link_query = build_cleanup_query_for_matchlink(rel_schema)
    >>>   439 |         logger.debug("Cleanup query: %s", cleanup_link_query)
          440 | 
          441 |         parameters = {
          442 |             "UPDATE_TAG": update_tag,
          443 |             "_sub_resource_label": sub_resource_label,
          444 |             "_sub_resource_id": sub_resource_id,
          445 |         }
          446 | 
          447 |         statement = GraphStatement(

CODE AROUND line_b (451):
          443 |             "_sub_resource_label": sub_resource_label,
          444 |             "_sub_resource_id": sub_resource_id,
          445 |         }
          446 | 
          447 |         statement = GraphStatement(
          448 |             cleanup_link_query,
          449 |             parameters=parameters,
          450 |             iterative=True,
    >>>   451 |             iterationsize=iterationsize,
          452 |             parent_job_name=rel_schema.rel_label,
          453 |         )
          454 | 
          455 |         return cls(
          456 |             f"Cleanup {rel_schema.rel_label} between {rel_schema.source_node_label} and {rel_schema.target_node_label}",
          457 |             [statement],
          458 |             rel_schema.rel_label,
          459 |         )

---

### FINDING 17
repository: langchain-ai/langchain   pull request #39367 (MERGED)
file: libs/core/tests/unit_tests/utils/test_aiter.py
the model was shown this function: test_abatch_iterate_invalid_size
claim_type: contract_violation   model_confidence: high
cited line_a: 21    cited line_b: 13

CLAIM: The function `test_abatch_iterate` is type-hinted to accept an `input_iterable` of `list[str]` on line 21, but the parameterized test case on line 13 provides a `list[int]`.

CODE AROUND line_a (21):
           13 |         (1, [100, 200, 300], [[100], [200], [300]]),
           14 |         (4, [], []),
           15 |         (None, [1, 2, 3], [[1, 2, 3]]),
           16 |         (None, [], []),
           17 |     ],
           18 | )
           19 | async def test_abatch_iterate(
           20 |     input_size: int | None,
    >>>    21 |     input_iterable: list[str],
           22 |     expected_output: list[list[str]],
           23 | ) -> None:
           24 |     """Test batching function."""
           25 | 
           26 |     async def _to_async_iterable(iterable: list[str]) -> AsyncIterator[str]:
           27 |         for item in iterable:
           28 |             yield item
           29 | 

CODE AROUND line_b (13):
            5 | from langchain_core.utils.aiter import abatch_iterate
            6 | 
            7 | 
            8 | @pytest.mark.parametrize(
            9 |     ("input_size", "input_iterable", "expected_output"),
           10 |     [
           11 |         (2, [1, 2, 3, 4, 5], [[1, 2], [3, 4], [5]]),
           12 |         (3, [10, 20, 30, 40, 50], [[10, 20, 30], [40, 50]]),
    >>>    13 |         (1, [100, 200, 300], [[100], [200], [300]]),
           14 |         (4, [], []),
           15 |         (None, [1, 2, 3], [[1, 2, 3]]),
           16 |         (None, [], []),
           17 |     ],
           18 | )
           19 | async def test_abatch_iterate(
           20 |     input_size: int | None,
           21 |     input_iterable: list[str],

---

### FINDING 18
repository: cartography-cncf/cartography   pull request #3111 (MERGED)
file: cartography/util.py
the model was shown this function: aws_handle_regions
claim_type: contract_violation   model_confidence: high
cited line_a: 757    cited line_b: 731

CLAIM: Re-raising a generic ClientError at line 757 causes it to be caught by the `@backoff.on_exception` decorator at line 731, which will retry even non-transient errors for up to 10 minutes, violating the documented behavior to only retry transient errors.

CODE AROUND line_a (757):
          749 |                 "Encountered an EndpointConnectionError. This means that the AWS "
          750 |                 "resource is not available in this region. Skipping.",
          751 |             )
          752 |             return []
          753 |         except (ConnectTimeoutError, ReadTimeoutError):
          754 |             logger.warning(
          755 |                 "Encountered a timeout while calling a regional AWS endpoint. "
          756 |                 "Skipping this region.",
    >>>   757 |             )
          758 |             return []
          759 | 
          760 |     return cast(AWSGetFunc, inner_function)
          761 | 
          762 | 
          763 | def retries_with_backoff(
          764 |     func: Callable,
          765 |     exception_type: Type[Exception],

CODE AROUND line_b (731):
          723 |                 raise RuntimeError(
          724 |                     "AWS returned an InvalidToken error. Configure regional STS endpoints by "
          725 |                     "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
          726 |                     "'sts_regional_endpoints = regional' to your AWS config file."
          727 |                 ) from e
          728 |             # The account is not authorized to use this service in this region
          729 |             # or the service is unavailable in the region, so we can continue
          730 |             # without raising an exception.
    >>>   731 |             if is_aws_region_skippable_client_error(e):
          732 |                 if is_service_control_policy_explicit_deny(e):
          733 |                     logger.warning(
          734 |                         "Service control policy denied access while calling %s: %s",
          735 |                         func.__name__,
          736 |                         error_message,
          737 |                     )
          738 |                 else:
          739 |                     logger.warning(

---

### FINDING 19
repository: langchain-ai/langchain   pull request #39367 (MERGED)
file: libs/core/tests/unit_tests/utils/test_aiter.py
the model was shown this function: test_abatch_iterate_invalid_size
claim_type: contract_violation   model_confidence: high
cited line_a: 22    cited line_b: 13

CLAIM: The function `test_abatch_iterate` is type-hinted to accept an `expected_output` of `list[list[str]]` on line 22, but the parameterized test case on line 13 provides a `list[list[int]]`.

CODE AROUND line_a (22):
           14 |         (4, [], []),
           15 |         (None, [1, 2, 3], [[1, 2, 3]]),
           16 |         (None, [], []),
           17 |     ],
           18 | )
           19 | async def test_abatch_iterate(
           20 |     input_size: int | None,
           21 |     input_iterable: list[str],
    >>>    22 |     expected_output: list[list[str]],
           23 | ) -> None:
           24 |     """Test batching function."""
           25 | 
           26 |     async def _to_async_iterable(iterable: list[str]) -> AsyncIterator[str]:
           27 |         for item in iterable:
           28 |             yield item
           29 | 
           30 |     iterator_ = abatch_iterate(input_size, _to_async_iterable(input_iterable))

CODE AROUND line_b (13):
            5 | from langchain_core.utils.aiter import abatch_iterate
            6 | 
            7 | 
            8 | @pytest.mark.parametrize(
            9 |     ("input_size", "input_iterable", "expected_output"),
           10 |     [
           11 |         (2, [1, 2, 3, 4, 5], [[1, 2], [3, 4], [5]]),
           12 |         (3, [10, 20, 30, 40, 50], [[10, 20, 30], [40, 50]]),
    >>>    13 |         (1, [100, 200, 300], [[100], [200], [300]]),
           14 |         (4, [], []),
           15 |         (None, [1, 2, 3], [[1, 2, 3]]),
           16 |         (None, [], []),
           17 |     ],
           18 | )
           19 | async def test_abatch_iterate(
           20 |     input_size: int | None,
           21 |     input_iterable: list[str],

---

### FINDING 20
repository: vllm-project/vllm   pull request #52374 (MERGED)
file: vllm/v1/worker/gpu/model_states/__init__.py
the model was shown this function: init_model_state
claim_type: wrong_order   model_confidence: high
cited line_a: 37    cited line_b: 23

CLAIM: The check for hybrid models on line 37 is performed after the check for cross-attention models on line 23, which would cause a hybrid model containing cross-attention layers to be incorrectly handled by `EncoderDecoderModelState` instead of the more specific `MambaHybridModelState`.

CODE AROUND line_a (37):
           29 | 
           30 |     # Encoder-only models (BERT/RoBERTa): non-causal self-attention, no KV cache.
           31 |     if any(isinstance(m, EncoderOnlyAttention) for m in model.modules()):
           32 |         from vllm.v1.worker.gpu.model_states.encoder_only import EncoderOnlyModelState
           33 | 
           34 |         return EncoderOnlyModelState(vllm_config, model, encoder_cache, device)
           35 | 
           36 |     if vllm_config.model_config.is_hybrid or vllm_config.model_config.is_attention_free:
    >>>    37 |         from vllm.v1.worker.gpu.model_states.mamba_hybrid import MambaHybridModelState
           38 | 
           39 |         return MambaHybridModelState(vllm_config, model, encoder_cache, device)
           40 | 
           41 |     from vllm.v1.worker.gpu.model_states.default import DefaultModelState
           42 | 
           43 |     return DefaultModelState(vllm_config, model, encoder_cache, device)
           44 | 

CODE AROUND line_b (23):
           15 |     device: torch.device,
           16 | ):
           17 |     # Let the model provide its own ModelState if it defines one.
           18 |     if hasattr(model, "get_model_state_cls"):
           19 |         cls = model.get_model_state_cls()
           20 |         return cls(vllm_config, model, encoder_cache, device)
           21 | 
           22 |     # Cross-attention encoder-decoder models (Whisper, CohereASR, NemotronParse, ...)
    >>>    23 |     if any(isinstance(m, CrossAttention) for m in model.modules()):
           24 |         from vllm.v1.worker.gpu.model_states.encoder_decoder import (
           25 |             EncoderDecoderModelState,
           26 |         )
           27 | 
           28 |         return EncoderDecoderModelState(vllm_config, model, encoder_cache, device)
           29 | 
           30 |     # Encoder-only models (BERT/RoBERTa): non-causal self-attention, no KV cache.
           31 |     if any(isinstance(m, EncoderOnlyAttention) for m in model.modules()):

---

### FINDING 21
repository: cartography-cncf/cartography   pull request #3152 (MERGED)
file: tests/unit/cartography/intel/cve_metadata/test_init.py
the model was shown this function: test_load_cve_metadata_bounds_batch_size
claim_type: wrong_order   model_confidence: low
cited line_a: 37    cited line_b: 35

CLAIM: The check for the constant's value on line 37 should occur before it is used in the assertion on line 35 to provide a more direct failure message if the constant itself is invalid.

CODE AROUND line_a (37):
           29 | def test_load_cve_metadata_bounds_batch_size(mock_load):
           30 |     """Each row fans out to every :CVE-labelled node, so transactions must stay small."""
           31 |     cve_metadata.load_cve_metadata(MagicMock(), [{"id": "CVE-2024-0001"}], 123)
           32 | 
           33 |     assert (
           34 |         mock_load.call_args.kwargs["batch_size"] == cve_metadata.CVE_METADATA_BATCH_SIZE
           35 |     )
           36 |     # Guard against someone raising this back toward the 10000-row load() default.
    >>>    37 |     assert cve_metadata.CVE_METADATA_BATCH_SIZE <= 500
           38 | 
           39 | 
           40 | @patch.object(cve_metadata, "merge_module_sync_metadata")
           41 | @patch.object(GraphJob, "from_node_schema")
           42 | @patch.object(cve_metadata, "run_analysis_job")
           43 | @patch.object(cve_metadata, "load_cve_metadata_feed")
           44 | @patch.object(cve_metadata, "load_cve_metadata")
           45 | @patch.object(cve_metadata.epss, "merge_epss_into_cves")

CODE AROUND line_b (35):
           27 | 
           28 | @patch.object(cve_metadata, "load")
           29 | def test_load_cve_metadata_bounds_batch_size(mock_load):
           30 |     """Each row fans out to every :CVE-labelled node, so transactions must stay small."""
           31 |     cve_metadata.load_cve_metadata(MagicMock(), [{"id": "CVE-2024-0001"}], 123)
           32 | 
           33 |     assert (
           34 |         mock_load.call_args.kwargs["batch_size"] == cve_metadata.CVE_METADATA_BATCH_SIZE
    >>>    35 |     )
           36 |     # Guard against someone raising this back toward the 10000-row load() default.
           37 |     assert cve_metadata.CVE_METADATA_BATCH_SIZE <= 500
           38 | 
           39 | 
           40 | @patch.object(cve_metadata, "merge_module_sync_metadata")
           41 | @patch.object(GraphJob, "from_node_schema")
           42 | @patch.object(cve_metadata, "run_analysis_job")
           43 | @patch.object(cve_metadata, "load_cve_metadata_feed")
