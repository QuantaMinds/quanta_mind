# Findings to adjudicate — chunk 5

There are 11 findings below, numbered by their global index.

### FINDING 55
repository: Skyvern-AI/skyvern   pull request #8211 (MERGED)
file: tests/unit/test_copilot_request_policy_signin_intent_absent.py
the model was shown this function: test_trust_floor_trace_data_carries_no_signin_intent_key
claim_type: contract_violation   model_confidence: high
cited line_a: 30    cited line_b: 33

CLAIM: The mock handler passed at line 30 unconditionally reports a 'clean' state, which ignores the explicit 'Sign in' intent from the user message at line 25, causing the assertion at line 33 to pass without actually testing the system's behavior for sign-in requests.

CODE AROUND line_a (30):
           22 | @pytest.mark.asyncio
           23 | async def test_trust_floor_trace_data_carries_no_signin_intent_key() -> None:
           24 |     policy = await build_request_policy_trust_floor(
           25 |         user_message="Sign in to the reporting portal and download last week's report.",
           26 |         workflow_yaml="",
           27 |         chat_history=[],
           28 |         global_llm_context="",
           29 |         organization_id="org-replay",
    >>>    30 |         handler=_clean_safety_handler,
           31 |     )
           32 | 
           33 |     assert SIGNIN_TRACE_KEYS.isdisjoint(policy.to_trace_data())
           34 | 
           35 | 
           36 | def test_dynamic_system_prompt_never_mentions_a_sign_in_address() -> None:
           37 |     instructions = agent_module._build_dynamic_system_prompt(tool_usage_guide="", config=agent_module.CopilotConfig())
           38 | 

CODE AROUND line_b (33):
           25 |         user_message="Sign in to the reporting portal and download last week's report.",
           26 |         workflow_yaml="",
           27 |         chat_history=[],
           28 |         global_llm_context="",
           29 |         organization_id="org-replay",
           30 |         handler=_clean_safety_handler,
           31 |     )
           32 | 
    >>>    33 |     assert SIGNIN_TRACE_KEYS.isdisjoint(policy.to_trace_data())
           34 | 
           35 | 
           36 | def test_dynamic_system_prompt_never_mentions_a_sign_in_address() -> None:
           37 |     instructions = agent_module._build_dynamic_system_prompt(tool_usage_guide="", config=agent_module.CopilotConfig())
           38 | 
           39 |     ctx = make_copilot_ctx(request_policy=RequestPolicy())
           40 | 
           41 |     prompt = instructions(SimpleNamespace(context=ctx), None)

---

### FINDING 56
repository: huggingface/transformers   pull request #47896 (MERGED)
file: src/transformers/models/gemma4_unified/modular_gemma4_unified.py
the model was shown this function: get_video_features
claim_type: missing_guard   model_confidence: high
cited line_a: 962    cited line_b: 971

CLAIM: The function's signature at line 962 allows `video_position_ids` to be `None`, but it is dereferenced without a check at line 971, which will raise an `AttributeError`.

CODE AROUND line_a (962):
          954 |             pooler_output=torch.split(vision_outputs, split_sizes),
          955 |         )
          956 | 
          957 |     @can_return_tuple
          958 |     @auto_docstring(custom_intro="Projects video frames into language model space via the unified pipeline.")
          959 |     def get_video_features(
          960 |         self,
          961 |         pixel_values_videos: torch.FloatTensor,
    >>>   962 |         video_position_ids: torch.LongTensor | None = None,
          963 |         **kwargs,
          964 |     ) -> Gemma4UnifiedVisionModelOutput:
          965 |         r"""
          966 |         video_position_ids (`torch.LongTensor` of shape `(num_videos, num_frames, max_patches, 2)`, *optional*):
          967 |             2D patch position coordinates from the video processor, with `(-1, -1)` indicating padding.
          968 |         """
          969 |         vision_outputs = self.embed_vision(pixel_values_videos.flatten(0, 1), video_position_ids.flatten(0, 1))
          970 | 

CODE AROUND line_b (971):
          963 |         **kwargs,
          964 |     ) -> Gemma4UnifiedVisionModelOutput:
          965 |         r"""
          966 |         video_position_ids (`torch.LongTensor` of shape `(num_videos, num_frames, max_patches, 2)`, *optional*):
          967 |             2D patch position coordinates from the video processor, with `(-1, -1)` indicating padding.
          968 |         """
          969 |         vision_outputs = self.embed_vision(pixel_values_videos.flatten(0, 1), video_position_ids.flatten(0, 1))
          970 | 
    >>>   971 |         # Strip padding patches before scattering into text sequence.
          972 |         non_pad_mask = (video_position_ids != -1).all(dim=-1).to(vision_outputs.device)
          973 | 
          974 |         # Flatten valid patches: keep only non-padding patches across all frames
          975 |         vision_outputs = vision_outputs[non_pad_mask.flatten(0, 1)]  # (total_valid_patches, text_hidden_size)
          976 | 
          977 |         split_sizes = non_pad_mask.sum(dim=(-2, -1)).tolist()
          978 |         return Gemma4UnifiedVisionModelOutput(
          979 |             pooler_output=torch.split(vision_outputs, split_sizes),

---

### FINDING 57
repository: vllm-project/vllm   pull request #50597 (MERGED)
file: vllm/model_executor/layers/fused_moe/oracle/mxfp4.py
the model was shown this function: convert_weight_to_mxfp4_moe_kernel_format
claim_type: contract_violation   model_confidence: high
cited line_a: 1287    cited line_b: 1500

CLAIM: The function `convert_weight_to_mxfp4_moe_kernel_format` is passed `activation=None` by its only caller but its internal logic for the `AITER_MXFP4_BF16` backend requires a non-None `activation` value to correctly dispatch to the SiTU-specific path.

CODE AROUND line_a (1287):
         1279 |     _cache_permute_indices: dict[torch.Size, torch.Tensor] | None = None,
         1280 |     activation: MoEActivation | None = None,
         1281 | ) -> tuple[
         1282 |     torch.Tensor,
         1283 |     torch.Tensor,
         1284 |     Union[torch.Tensor, "PrecisionConfig"],
         1285 |     Union[torch.Tensor, "PrecisionConfig"],
         1286 |     torch.Tensor | None,
    >>>  1287 |     torch.Tensor | None,
         1288 | ]:
         1289 |     """Convert loaded weights into backend-specific kernel format.
         1290 | 
         1291 |     Supports DeepGEMM, FlashInfer, TRTLLM MXFP8, Triton and Marlin backends.
         1292 |     """
         1293 |     is_gfx1250 = False
         1294 |     if current_platform.is_rocm():
         1295 |         from vllm.platforms.rocm import on_gfx1250

CODE AROUND line_b (1500):
         1492 |             # default a16w4 keeps the separated layout.
         1493 |             guinterleave = rocm_aiter_ops.is_fused_moe_situv2_a8w4_enabled()
         1494 |             w13 = rocm_aiter_ops.shuffle_weight_a16w4(
         1495 |                 w13_weight.data.view(fp4_dtype), 16, guinterleave
         1496 |             )
         1497 |             w2 = rocm_aiter_ops.shuffle_weight_a16w4(
         1498 |                 w2_weight.data.view(fp4_dtype), 16, False
         1499 |             )
    >>>  1500 |             w13_scale_raw = w13_weight_scale.data.view(e8m0_dtype)
         1501 |             w2_scale_raw = w2_weight_scale.data.view(e8m0_dtype)
         1502 |             w13_scale = rocm_aiter_ops.shuffle_scale_a16w4(
         1503 |                 w13_scale_raw.view(-1, w13_scale_raw.shape[-1]),
         1504 |                 num_experts,
         1505 |                 guinterleave,
         1506 |             )
         1507 |             w2_scale = e8m0_shuffle(w2_scale_raw.view(-1, w2_scale_raw.shape[-1]))
         1508 |             w13.is_shuffled = True

---

### FINDING 58
repository: vllm-project/vllm   pull request #51316 (MERGED)
file: vllm/v1/worker/gpu_worker.py
the model was shown this function: supports_draft_weight_updates
claim_type: missing_guard   model_confidence: low
cited line_a: 879    cited line_b: 880

CLAIM: The check for `callable(get_draft_model)` on line 879 is insufficient to prevent a `TypeError` on line 880 if `get_draft_model` resolves to a non-`None`, non-callable object.

CODE AROUND line_a (879):
          871 | 
          872 |     def supports_draft_weight_updates(self) -> bool:
          873 |         engine = self.weight_transfer_engine
          874 |         speculative_config = self.speculative_config
          875 |         get_draft_model = getattr(self.model_runner, "get_draft_model", None)
          876 |         return (
          877 |             engine is not None
          878 |             and engine.supports_draft_weight_update
    >>>   879 |             and callable(get_draft_model)
          880 |             and get_draft_model() is not None
          881 |             and speculative_config is not None
          882 |             and speculative_config.draft_model_config is not None
          883 |         )
          884 | 
          885 |     def _set_draft_weight_update_target(self) -> None:
          886 |         assert self.weight_transfer_engine is not None
          887 | 

CODE AROUND line_b (880):
          872 |     def supports_draft_weight_updates(self) -> bool:
          873 |         engine = self.weight_transfer_engine
          874 |         speculative_config = self.speculative_config
          875 |         get_draft_model = getattr(self.model_runner, "get_draft_model", None)
          876 |         return (
          877 |             engine is not None
          878 |             and engine.supports_draft_weight_update
          879 |             and callable(get_draft_model)
    >>>   880 |             and get_draft_model() is not None
          881 |             and speculative_config is not None
          882 |             and speculative_config.draft_model_config is not None
          883 |         )
          884 | 
          885 |     def _set_draft_weight_update_target(self) -> None:
          886 |         assert self.weight_transfer_engine is not None
          887 | 
          888 |         draft_model = self.get_draft_model()

---

### FINDING 59
repository: Skyvern-AI/skyvern   pull request #8214 (MERGED)
file: tests/unit/test_workflow_copilot_route_helpers.py
the model was shown this function: _credential_bound_workflow
claim_type: contract_violation   model_confidence: low
cited line_a: 544    cited line_b: 557

CLAIM: The function's return type hint `Any` at line 544 is too permissive, as the function is implemented to always return an instance of `Workflow` at line 557.

CODE AROUND line_a (544):
          536 |     legacy = _non_error_narrative_payload() | {"mode": "build"}
          537 | 
          538 |     message = _persisted_message(legacy)
          539 | 
          540 |     assert message.narrative_payload is not None
          541 |     assert "mode" not in message.narrative_payload
          542 | 
          543 | 
    >>>   544 | def _credential_bound_workflow(credential_id: str) -> Any:
          545 |     """A saved workflow row whose login block binds ``credential_id``."""
          546 |     parameter = WorkflowParameter(
          547 |         parameter_type="workflow",
          548 |         workflow_parameter_type=WorkflowParameterType.CREDENTIAL_ID,
          549 |         key="login_credential",
          550 |         workflow_parameter_id="wp_1",
          551 |         workflow_id="w_1",
          552 |         default_value=credential_id,

CODE AROUND line_b (557):
          549 |         key="login_credential",
          550 |         workflow_parameter_id="wp_1",
          551 |         workflow_id="w_1",
          552 |         default_value=credential_id,
          553 |         created_at=datetime.now(timezone.utc),
          554 |         modified_at=datetime.now(timezone.utc),
          555 |     )
          556 |     return Workflow(
    >>>   557 |         workflow_id="w_1",
          558 |         organization_id="o_1",
          559 |         title="saved",
          560 |         workflow_permanent_id="wpid_1",
          561 |         version=1,
          562 |         proxy_location=ProxyLocation.NONE,
          563 |         is_saved_task=False,
          564 |         workflow_definition=WorkflowDefinition(
          565 |             parameters=[parameter],

---

### FINDING 60
repository: apache/airflow   pull request #61702 (MERGED)
file: airflow-core/src/airflow/models/serialized_dag.py
the model was shown this function: write_dag
claim_type: unhandled_case   model_confidence: high
cited line_a: 528    cited line_b: 632

CLAIM: When a DAG's deadlines are removed, `deadline_uuid_mapping` is set to an empty dict at line 528, which causes the check at line 632 to be false, thus failing to clear the stale `deadline_alerts` from the updated serialized DAG.

CODE AROUND line_a (528):
          520 |         If the record already exists, it checks if the Serialized DAG changed or not. If it is
          521 |         changed, it updates the record, ignores otherwise.
          522 | 
          523 |         :param dag: a DAG to be written into database
          524 |         :param bundle_name: bundle name of the DAG
          525 |         :param bundle_version: bundle version of the DAG
          526 |         :param min_update_interval: minimal interval in seconds to update serialized DAG
          527 |         :param session: ORM Session
    >>>   528 | 
          529 |         :returns: Boolean indicating if the DAG was written to the DB
          530 |         """
          531 |         # Checks if (Current Time - Time when the DAG was written to DB) < min_update_interval
          532 |         # If Yes, does nothing
          533 |         # If No or the DAG does not exists, updates / writes Serialized DAG to DB
          534 |         if min_update_interval is not None:
          535 |             if session.scalar(
          536 |                 select(literal(True))

CODE AROUND line_b (632):
          624 |                 # No rows updated - serialized DAG doesn't exist
          625 |                 return False
          626 | 
          627 |             if deadline_uuid_mapping:
          628 |                 updated_serialized_dag = session.scalar(
          629 |                     select(cls).where(cls.dag_version_id == dag_version.id)
          630 |                 )
          631 |                 if updated_serialized_dag:
    >>>   632 |                     updated_serialized_dag.deadline_alerts.clear()
          633 |                     cls._create_deadline_alert_records(updated_serialized_dag, deadline_uuid_mapping)
          634 | 
          635 |             # The dag_version and dag_code may not have changed, still we should
          636 |             # do the below actions:
          637 |             # Update the latest dag version
          638 |             dag_version.bundle_name = bundle_name
          639 |             dag_version.bundle_version = bundle_version
          640 |             session.merge(dag_version)

---

### FINDING 61
repository: vllm-project/vllm   pull request #52374 (MERGED)
file: tests/v1/e2e/general/test_mamba_prefix_cache.py
the model was shown this function: _run_mamba_prefix_cache_mrv1
claim_type: resource_leak   model_confidence: high
cited line_a: 878    cited line_b: 935

CLAIM: The call to `envs.disable_envs_cache()` at line 878 makes a global state change that is not reverted before the function exits at line 935, which can cause subsequent tests to fail or behave incorrectly.

CODE AROUND line_a (878):
          870 |     return tests
          871 | 
          872 | 
          873 | def _run_mamba_prefix_cache_mrv1(
          874 |     monkeypatch: pytest.MonkeyPatch, async_scheduling: bool
          875 | ):
          876 |     # This test patches the V1 model runner, so pin V1 explicitly: MoE/hybrid
          877 |     # models like Qwen3-Next now default to the V2 runner.
    >>>   878 |     monkeypatch.setenv("VLLM_USE_V2_MODEL_RUNNER", "0")
          879 |     envs.disable_envs_cache()
          880 |     global async_scheduling_mode
          881 |     async_scheduling_mode = async_scheduling
          882 |     run_ref_mamba_state_in_subprocess()
          883 |     apply_patch(monkeypatch)
          884 |     prompt_dataset = datasets.load_dataset("heheda/a_long_article")
          885 |     full_prompt = prompt_dataset["train"][0]["text"]
          886 |     tests = get_mamba_prefix_cache_step_configs(async_scheduling)

CODE AROUND line_b (935):
          927 |             for action in test_config.step_actions
          928 |             if action.postprocess_copy_idx and action.postprocess_copy_idx[0] != -1
          929 |         ]
          930 |         mamba_state_ref = torch.load("mamba_kv_cache_dict_ref.pth")
          931 |         check_mamba_state_equal(mamba_state_ref, mamba_kv_cache_dict, keys_to_check)
          932 |         mamba_kv_cache_dict.clear()
          933 |     del engine
          934 |     torch.accelerator.empty_cache()
    >>>   935 |     cleanup_dist_env_and_memory()
          936 | 
          937 | 
          938 | @create_new_process_for_each_test()
          939 | def test_mamba_prefix_cache_mrv1(monkeypatch: pytest.MonkeyPatch):
          940 |     _run_mamba_prefix_cache_mrv1(monkeypatch, async_scheduling=False)
          941 | 
          942 | 
          943 | @create_new_process_for_each_test()

---

### FINDING 62
repository: apache/airflow   pull request #71640 (MERGED)
file: dev/breeze/tests/test_kubernetes_lang_sdk_commands.py
the model was shown this function: test_checkout_with_both_sdks_builds_from_them
claim_type: contract_violation   model_confidence: high
cited line_a: 409    cited line_b: 412

CLAIM: The test creates mock SDK directories inside `repo_root` at line 409, but the function under test uses `tmp_path` to resolve paths at line 412, so the assertion at line 413 fails.

CODE AROUND line_a (409):
          401 |     def test_checkout_with_both_sdks_builds_from_them(
          402 |         self, mock_fetch, env, repo_root, tmp_path, monkeypatch
          403 |     ):
          404 |         monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
          405 |         monkeypatch.delenv("DEFAULT_BRANCH", raising=False)
          406 |         for key, value in env.items():
          407 |             monkeypatch.setenv(key, value)
          408 |         (repo_root / "go-sdk").mkdir()
    >>>   409 |         (repo_root / "java-sdk").mkdir()
          410 | 
          411 |         go_sdk, java_sdk = _lang_sdk_resolve_sdk_sources(tmp_path, None)
          412 | 
          413 |         assert (go_sdk, java_sdk) == (repo_root / "go-sdk", repo_root / "java-sdk")
          414 |         mock_fetch.assert_not_called()
          415 | 
          416 |     @pytest.mark.parametrize(
          417 |         "present",

CODE AROUND line_b (412):
          404 |         monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
          405 |         monkeypatch.delenv("DEFAULT_BRANCH", raising=False)
          406 |         for key, value in env.items():
          407 |             monkeypatch.setenv(key, value)
          408 |         (repo_root / "go-sdk").mkdir()
          409 |         (repo_root / "java-sdk").mkdir()
          410 | 
          411 |         go_sdk, java_sdk = _lang_sdk_resolve_sdk_sources(tmp_path, None)
    >>>   412 | 
          413 |         assert (go_sdk, java_sdk) == (repo_root / "go-sdk", repo_root / "java-sdk")
          414 |         mock_fetch.assert_not_called()
          415 | 
          416 |     @pytest.mark.parametrize(
          417 |         "present",
          418 |         [
          419 |             pytest.param((), id="neither-sdk"),
          420 |             pytest.param(("go-sdk",), id="only-go-sdk"),

---

### FINDING 63
repository: apache/airflow   pull request #68734 (MERGED)
file: airflow-core/tests/unit/models/test_serialized_dag.py
the model was shown this function: test_non_deadline_edit_creates_deadline_alert_for_new_serdag
claim_type: wrong_order   model_confidence: low
cited line_a: 1060    cited line_b: 1065

CLAIM: Calling `sync_dag_to_db` at line 1060 before `create_dagrun` at line 1065 is not sufficient to create task instances for the serialized DAG, which might cause `SDM.write_dag` to take the UPDATE path instead of the intended INSERT path.

CODE AROUND line_a (1060):
         1052 |             deadline=DeadlineAlert(
         1053 |                 reference=DeadlineReference.DAGRUN_QUEUED_AT,
         1054 |                 interval=timedelta(minutes=5),
         1055 |                 callback=AsyncCallback(empty_callback_for_deadline),
         1056 |             ),
         1057 |         )
         1058 |         EmptyOperator(task_id="task1", dag=dag)
         1059 |         scheduler_dag = sync_dag_to_db(dag, session=session)
    >>>  1060 | 
         1061 |         # Create a dagrun so the existing dag_version has task instances,
         1062 |         # forcing write_dag into the INSERT branch (new serialized_dag row).
         1063 |         scheduler_dag.create_dagrun(
         1064 |             run_id="test1",
         1065 |             run_after=DEFAULT_DATE,
         1066 |             state=DagRunState.QUEUED,
         1067 |             logical_date=DEFAULT_DATE,
         1068 |             data_interval=(DEFAULT_DATE, DEFAULT_DATE),

CODE AROUND line_b (1065):
         1057 |         )
         1058 |         EmptyOperator(task_id="task1", dag=dag)
         1059 |         scheduler_dag = sync_dag_to_db(dag, session=session)
         1060 | 
         1061 |         # Create a dagrun so the existing dag_version has task instances,
         1062 |         # forcing write_dag into the INSERT branch (new serialized_dag row).
         1063 |         scheduler_dag.create_dagrun(
         1064 |             run_id="test1",
    >>>  1065 |             run_after=DEFAULT_DATE,
         1066 |             state=DagRunState.QUEUED,
         1067 |             logical_date=DEFAULT_DATE,
         1068 |             data_interval=(DEFAULT_DATE, DEFAULT_DATE),
         1069 |             triggered_by=DagRunTriggeredByType.TEST,
         1070 |             run_type=DagRunType.MANUAL,
         1071 |         )
         1072 |         session.commit()
         1073 | 

---

### FINDING 64
repository: huggingface/transformers   pull request #47896 (MERGED)
file: src/transformers/models/gemma4_unified/modeling_gemma4_unified.py
the model was shown this function: get_image_features
claim_type: wrong_order   model_confidence: high
cited line_a: 1187    cited line_b: 1184

CLAIM: The tensor `vision_outputs` is indexed at line 1187 before being moved to the same device as `non_pad_mask`, which was moved to `vision_outputs.device` at line 1184, potentially causing a runtime error if the tensors are on different devices.

CODE AROUND line_a (1187):
         1179 |         vision_outputs = self.embed_vision(pixel_values_videos.flatten(0, 1), video_position_ids.flatten(0, 1))
         1180 | 
         1181 |         # Strip padding patches before scattering into text sequence.
         1182 |         non_pad_mask = (video_position_ids != -1).all(dim=-1).to(vision_outputs.device)
         1183 | 
         1184 |         # Flatten valid patches: keep only non-padding patches across all frames
         1185 |         vision_outputs = vision_outputs[non_pad_mask.flatten(0, 1)]  # (total_valid_patches, text_hidden_size)
         1186 | 
    >>>  1187 |         split_sizes = non_pad_mask.sum(dim=(-2, -1)).tolist()
         1188 |         return Gemma4UnifiedVisionModelOutput(
         1189 |             pooler_output=torch.split(vision_outputs, split_sizes),
         1190 |         )
         1191 | 
         1192 | 
         1193 | def create_masks_for_vision_model(
         1194 |     config: PreTrainedConfig,
         1195 |     inputs_embeds: torch.Tensor,

CODE AROUND line_b (1184):
         1176 |         video_position_ids (`torch.LongTensor` of shape `(num_videos, num_frames, max_patches, 2)`, *optional*):
         1177 |             2D patch position coordinates from the video processor, with `(-1, -1)` indicating padding.
         1178 |         """
         1179 |         vision_outputs = self.embed_vision(pixel_values_videos.flatten(0, 1), video_position_ids.flatten(0, 1))
         1180 | 
         1181 |         # Strip padding patches before scattering into text sequence.
         1182 |         non_pad_mask = (video_position_ids != -1).all(dim=-1).to(vision_outputs.device)
         1183 | 
    >>>  1184 |         # Flatten valid patches: keep only non-padding patches across all frames
         1185 |         vision_outputs = vision_outputs[non_pad_mask.flatten(0, 1)]  # (total_valid_patches, text_hidden_size)
         1186 | 
         1187 |         split_sizes = non_pad_mask.sum(dim=(-2, -1)).tolist()
         1188 |         return Gemma4UnifiedVisionModelOutput(
         1189 |             pooler_output=torch.split(vision_outputs, split_sizes),
         1190 |         )
         1191 | 
         1192 | 

---

### FINDING 65
repository: vllm-project/vllm   pull request #51316 (MERGED)
file: vllm/v1/executor/abstract.py
the model was shown this function: supports_draft_weight_updates
claim_type: unhandled_case   model_confidence: high
cited line_a: 293    cited line_b: 296

CLAIM: If `collective_rpc` on line 293 returns an empty list (e.g., if there are no workers), `all(worker_support)` on line 296 will incorrectly return `True`.

CODE AROUND line_a (293):
          285 | 
          286 |     @cached_property  # Avoid unnecessary RPC calls
          287 |     def supported_tasks(self) -> tuple[SupportedTask, ...]:
          288 |         output: list[tuple[SupportedTask, ...]]
          289 |         output = self.collective_rpc("get_supported_tasks")
          290 |         return output[0]
          291 | 
          292 |     def supports_draft_weight_updates(self) -> bool:
    >>>   293 |         worker_support: list[bool] = self.collective_rpc(
          294 |             "supports_draft_weight_updates"
          295 |         )
          296 |         return all(worker_support)
          297 | 
          298 |     def add_lora(self, lora_request: LoRARequest) -> bool:
          299 |         assert lora_request.lora_int_id > 0, "lora_id must be greater than 0."
          300 |         return all(self.collective_rpc("add_lora", args=(lora_request,)))
          301 | 

CODE AROUND line_b (296):
          288 |         output: list[tuple[SupportedTask, ...]]
          289 |         output = self.collective_rpc("get_supported_tasks")
          290 |         return output[0]
          291 | 
          292 |     def supports_draft_weight_updates(self) -> bool:
          293 |         worker_support: list[bool] = self.collective_rpc(
          294 |             "supports_draft_weight_updates"
          295 |         )
    >>>   296 |         return all(worker_support)
          297 | 
          298 |     def add_lora(self, lora_request: LoRARequest) -> bool:
          299 |         assert lora_request.lora_int_id > 0, "lora_id must be greater than 0."
          300 |         return all(self.collective_rpc("add_lora", args=(lora_request,)))
          301 | 
          302 |     def remove_lora(self, lora_id: int) -> bool:
          303 |         assert lora_id > 0, "lora_id must be greater than 0."
          304 |         return all(self.collective_rpc("remove_lora", args=(lora_id,)))
