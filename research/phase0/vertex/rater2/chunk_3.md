# Findings to adjudicate — chunk 3

There are 11 findings below, numbered by their global index.

### FINDING 33
repository: vllm-project/vllm   pull request #50597 (MERGED)
file: vllm/model_executor/layers/quantization/mxfp4.py
the model was shown this function: _setup_kernel
claim_type: wrong_order   model_confidence: high
cited line_a: 716    cited line_b: 707

CLAIM: The check for whether bias assertions should be performed is moved inside the surrounding if block at line 716, but the assertions themselves are outside this block, meaning they are now unconditionally executed whereas the original intent was to skip them for SITU activation.

CODE AROUND line_a (716):
          708 |                     and w13_bias.shape[0] == num_experts
          709 |                     and w13_bias.shape[1] == intermediate_size * self.moe.w13_num_shards
          710 |                 )
          711 |             if w2_bias is not None:
          712 |                 assert (
          713 |                     w2_bias.dim() == 2
          714 |                     and w2_bias.shape[0] == num_experts
          715 |                     and w2_bias.shape[1] == hidden_size
    >>>   716 |                 )
          717 | 
          718 |         # Convert weights to kernel format
          719 |         w13, w2, w13_scale, w2_scale, w13_bias, w2_bias = (
          720 |             convert_weight_to_mxfp4_moe_kernel_format(
          721 |                 mxfp4_backend=self.mxfp4_backend,
          722 |                 layer=layer,
          723 |                 w13_weight=w13,
          724 |                 w2_weight=w2,

CODE AROUND line_b (707):
          699 |             )
          700 |             assert (
          701 |                 w2_scale.dim() == 3
          702 |                 and w2_scale.shape[1] == hidden_size
          703 |                 and w2_scale.shape[2] == intermediate_size // sf_block_size
          704 |             )
          705 |             if w13_bias is not None:
          706 |                 assert (
    >>>   707 |                     w13_bias.dim() == 2
          708 |                     and w13_bias.shape[0] == num_experts
          709 |                     and w13_bias.shape[1] == intermediate_size * self.moe.w13_num_shards
          710 |                 )
          711 |             if w2_bias is not None:
          712 |                 assert (
          713 |                     w2_bias.dim() == 2
          714 |                     and w2_bias.shape[0] == num_experts
          715 |                     and w2_bias.shape[1] == hidden_size

---

### FINDING 34
repository: Skyvern-AI/skyvern   pull request #8214 (MERGED)
file: tests/unit/test_copilot_agent_helpers.py
the model was shown this function: test_turn_start_snapshot_does_not_follow_the_workflow_through_the_turn
claim_type: wrong_order   model_confidence: high
cited line_a: 3174    cited line_b: 3176

CLAIM: The `extra_parameter` variable containing YAML is defined with a trailing newline, which causes a syntax error when it is formatted into `workflow_yaml` at line 3176 because it pushes `  blocks:` to a new line, breaking the YAML structure.

CODE AROUND line_a (3174):
         3166 |         - login_credential
         3167 | """
         3168 |         policy = RequestPolicy(
         3169 |             resolved_credentials=[],
         3170 |             persisted_workflow_credential_ids=sorted(workflow_credential_ids(workflow_yaml.format(extra_parameter=""))),
         3171 |         )
         3172 | 
         3173 |         this_turn_ids = sorted(
    >>>  3174 |             workflow_credential_ids(
         3175 |                 workflow_yaml.format(
         3176 |                     extra_parameter="""    - parameter_type: workflow
         3177 |       workflow_parameter_type: credential_id
         3178 |       key: added_credential
         3179 |       default_value: cred_added_this_turn
         3180 | """
         3181 |                 )
         3182 |             )

CODE AROUND line_b (3176):
         3168 |         policy = RequestPolicy(
         3169 |             resolved_credentials=[],
         3170 |             persisted_workflow_credential_ids=sorted(workflow_credential_ids(workflow_yaml.format(extra_parameter=""))),
         3171 |         )
         3172 | 
         3173 |         this_turn_ids = sorted(
         3174 |             workflow_credential_ids(
         3175 |                 workflow_yaml.format(
    >>>  3176 |                     extra_parameter="""    - parameter_type: workflow
         3177 |       workflow_parameter_type: credential_id
         3178 |       key: added_credential
         3179 |       default_value: cred_added_this_turn
         3180 | """
         3181 |                 )
         3182 |             )
         3183 |         )
         3184 |         assert this_turn_ids == ["cred_added_this_turn", "cred_bound"]

---

### FINDING 35
repository: vllm-project/vllm   pull request #51216 (MERGED)
file: tests/v1/worker/test_gpu_model_runner.py
the model was shown this function: test_reasoning_config_without_custom_logitsprocs_does_not_need_output_token_ids
claim_type: contract_violation   model_confidence: high
cited line_a: 319    cited line_b: 328

CLAIM: The `runner` object created within the `set_current_vllm_config` context is accessed at line_b after the context has been exited at line_a, which is unsafe as the object's properties may depend on the context being active.

CODE AROUND line_a (319):
          311 |     vllm_config = get_vllm_config()
          312 |     assert vllm_config.model_config.logits_processors is None
          313 |     reasoning_config = ReasoningConfig(
          314 |         reasoning_start_str="<think>", reasoning_end_str="</think>"
          315 |     )
          316 |     reasoning_config._reasoning_start_token_ids = [1]
          317 |     reasoning_config._reasoning_end_token_ids = [2]
          318 |     vllm_config.reasoning_config = reasoning_config
    >>>   319 | 
          320 |     with set_current_vllm_config(vllm_config):
          321 |         model_config = vllm_config.model_config
          322 |         num_heads = model_config.get_num_kv_heads(vllm_config.parallel_config)
          323 |         head_size = model_config.get_head_size()
          324 |         vllm_config.compilation_config.static_forward_context["layer.0"] = Attention(
          325 |             num_heads, head_size, 0.1
          326 |         )
          327 |         runner = GPUModelRunner(vllm_config, torch.device("cpu"))

CODE AROUND line_b (328):
          320 |     with set_current_vllm_config(vllm_config):
          321 |         model_config = vllm_config.model_config
          322 |         num_heads = model_config.get_num_kv_heads(vllm_config.parallel_config)
          323 |         head_size = model_config.get_head_size()
          324 |         vllm_config.compilation_config.static_forward_context["layer.0"] = Attention(
          325 |             num_heads, head_size, 0.1
          326 |         )
          327 |         runner = GPUModelRunner(vllm_config, torch.device("cpu"))
    >>>   328 | 
          329 |     assert runner.input_batch.thinking_budget_state_holder is not None
          330 |     assert runner.input_batch.logitsprocs_need_output_token_ids is False
          331 | 
          332 | 
          333 | @pytest.mark.skip_global_cleanup
          334 | @pytest.mark.parametrize(
          335 |     ("world_size", "is_last_rank", "expected_calls"),
          336 |     [(1, True, 0), (2, True, 0), (2, False, 1)],

---

### FINDING 36
repository: cartography-cncf/cartography   pull request #3145 (MERGED)
file: tests/unit/cartography/intel/wiz/test_transforms.py
the model was shown this function: test_transform_findings_extracts_configuration_metadata
claim_type: contract_violation   model_confidence: high
cited line_a: 36    cited line_b: 54

CLAIM: The assertion at line 36 states that a vulnerability with a CVE is not a security issue, which contradicts the assertion at line 54 that a vulnerability without a CVE is a security issue, creating semantically confusing and inconsistent logic.

CODE AROUND line_a (36):
           28 | def test_transform_findings_extracts_vulnerability_cve_and_resource_metadata():
           29 |     findings = transform_findings(VULNERABILITY_FINDINGS, TENANT_ID)
           30 | 
           31 |     assert findings[0]["id"] == "wiz-vuln-1"
           32 |     assert findings[0]["finding_type"] == "VULNERABILITY"
           33 |     assert findings[0]["cve_id"] == CVE_ID_1
           34 |     assert findings[0]["has_cve"] == "true"
           35 |     assert findings[0]["is_security_issue"] == "false"
    >>>    36 |     assert findings[0]["resource_id"] == RESOURCE_ID_1
           37 |     assert findings[0]["resource_external_id"] == (
           38 |         "arn:aws:ec2:us-east-1:123456789012:instance/i-123"
           39 |     )
           40 | 
           41 | 
           42 | def test_transform_findings_labels_non_cve_vulnerabilities_as_security_issues():
           43 |     finding = {
           44 |         **VULNERABILITY_FINDINGS[0],

CODE AROUND line_b (54):
           46 |         "detailedName": "openssl",
           47 |         "description": "Package is vulnerable",
           48 |         "link": None,
           49 |     }
           50 | 
           51 |     transformed = transform_findings([finding], TENANT_ID)
           52 | 
           53 |     assert transformed[0]["has_cve"] == "false"
    >>>    54 |     assert transformed[0]["is_security_issue"] == "true"
           55 | 
           56 | 
           57 | def test_transform_findings_extracts_configuration_metadata():
           58 |     findings = transform_findings(CONFIGURATION_FINDINGS, TENANT_ID)
           59 | 
           60 |     assert findings[0]["id"] == CONFIGURATION_FINDING_ID_1
           61 |     assert findings[0]["finding_type"] == "CONFIGURATION"
           62 |     assert findings[0]["result"] == "FAIL"

---

### FINDING 37
repository: cartography-cncf/cartography   pull request #3111 (MERGED)
file: cartography/graph/job.py
the model was shown this function: from_matchlink
claim_type: missing_guard   model_confidence: high
cited line_a: 434    cited line_b: 451

CLAIM: The docstring at line 434 states that `rel_schema` must define `_sub_resource_label` and `_sub_resource_id` properties, but the code at line 451 uses `rel_schema` without verifying this precondition, which could lead to a `KeyError`.

CODE AROUND line_a (434):
          426 |         Returns:
          427 |             GraphJob: A new GraphJob instance configured for matchlink cleanup.
          428 | 
          429 |         Note:
          430 |             - This method is specifically designed for matchlink cleanup operations.
          431 |             - Required relationship properties ``_sub_resource_label`` and ``_sub_resource_id``
          432 |               must be defined in the rel_schema.
          433 |             - For a given rel_schema, the fields used in the rel_schema.properties._sub_resource_label.name and
    >>>   434 |               rel_schema.properties._sub_resource_id.name must be provided as keys and values in the params dict.
          435 |             - The rel_schema must have a source_node_matcher and target_node_matcher.
          436 | 
          437 |         """
          438 |         cleanup_link_query = build_cleanup_query_for_matchlink(rel_schema)
          439 |         logger.debug("Cleanup query: %s", cleanup_link_query)
          440 | 
          441 |         parameters = {
          442 |             "UPDATE_TAG": update_tag,

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

### FINDING 38
repository: langchain-ai/langchain   pull request #39635 (MERGED)
file: libs/partners/openai/tests/integration_tests/chat_models/test_responses_api.py
the model was shown this function: test_stream_encrypted_reasoning
claim_type: contract_violation   model_confidence: high
cited line_a: 790    cited line_b: 810

CLAIM: The `ChatOpenAI` instance is configured with `store=False` on line 790, but line 810 attempts to continue a conversation by passing back the previous AI response, which is not a valid operation because the backend has not stored the required reasoning state.

CODE AROUND line_a (790):
          782 |     assert isinstance(response_2, AIMessage)
          783 | 
          784 | 
          785 | @pytest.mark.vcr
          786 | def test_stream_encrypted_reasoning() -> None:
          787 |     llm = ChatOpenAI(
          788 |         model="gpt-5.6-luna",
          789 |         use_responses_api=True,
    >>>   790 |         reasoning_effort="medium",
          791 |         store=False,
          792 |         include=["reasoning.encrypted_content"],
          793 |     )
          794 |     message_1 = {
          795 |         "role": "user",
          796 |         "content": "What was the third tallest buliding in the year 2000?",
          797 |     }
          798 |     response_1 = llm.stream_events([message_1], version="v3").output

CODE AROUND line_b (810):
          802 |             total_reasoning_blocks += 1
          803 |             assert isinstance(block.get("id"), str)
          804 |             assert block.get("id", "").startswith("rs_")
          805 |             assert isinstance(block["extras"].get("encrypted_content"), str)
          806 |             assert isinstance(block.get("index"), str)
          807 | 
          808 |     # Check we can pass back summaries
          809 |     message_2 = {"role": "user", "content": "Thank you."}
    >>>   810 |     response_2 = llm.invoke([message_1, response_1, message_2])
          811 |     assert isinstance(response_2, AIMessage)
          812 | 
          813 | 
          814 | @pytest.mark.default_cassette("test_code_interpreter.yaml.gz")
          815 | @pytest.mark.vcr
          816 | @pytest.mark.parametrize(
          817 |     ("output_version", "use_v2_stream"),
          818 |     [

---

### FINDING 39
repository: Skyvern-AI/skyvern   pull request #8211 (MERGED)
file: tests/unit/test_copilot_request_policy_signin_intent_absent.py
the model was shown this function: test_dynamic_system_prompt_never_mentions_a_sign_in_address
claim_type: contract_violation   model_confidence: high
cited line_a: 39    cited line_b: 43

CLAIM: The test creates a default `RequestPolicy` with no sign-in information at line 39, which makes the assertion at line 43 succeed trivially without verifying the function's behavior in the more critical case where sign-in data is present.

CODE AROUND line_a (39):
           31 |     )
           32 | 
           33 |     assert SIGNIN_TRACE_KEYS.isdisjoint(policy.to_trace_data())
           34 | 
           35 | 
           36 | def test_dynamic_system_prompt_never_mentions_a_sign_in_address() -> None:
           37 |     instructions = agent_module._build_dynamic_system_prompt(tool_usage_guide="", config=agent_module.CopilotConfig())
           38 | 
    >>>    39 |     ctx = make_copilot_ctx(request_policy=RequestPolicy())
           40 | 
           41 |     prompt = instructions(SimpleNamespace(context=ctx), None)
           42 | 
           43 |     assert "signin" not in prompt.lower()
           44 | 
           45 | 
           46 | def test_stored_context_carrying_a_signin_email_still_loads() -> None:
           47 |     stored = json.dumps(

CODE AROUND line_b (43):
           35 | 
           36 | def test_dynamic_system_prompt_never_mentions_a_sign_in_address() -> None:
           37 |     instructions = agent_module._build_dynamic_system_prompt(tool_usage_guide="", config=agent_module.CopilotConfig())
           38 | 
           39 |     ctx = make_copilot_ctx(request_policy=RequestPolicy())
           40 | 
           41 |     prompt = instructions(SimpleNamespace(context=ctx), None)
           42 | 
    >>>    43 |     assert "signin" not in prompt.lower()
           44 | 
           45 | 
           46 | def test_stored_context_carrying_a_signin_email_still_loads() -> None:
           47 |     stored = json.dumps(
           48 |         {"user_goal": "sign in", "signin_email": "user@example.com", "signin_email_host": "example.com"}
           49 |     )
           50 | 
           51 |     structured = StructuredContext.from_json_str(stored)

---

### FINDING 40
repository: huggingface/transformers   pull request #47948 (MERGED)
file: src/transformers/models/emu3/modeling_emu3.py
the model was shown this function: forward
claim_type: unhandled_case   model_confidence: high
cited line_a: 1604    cited line_b: 1608

CLAIM: When `logits_to_keep` is used to slice `hidden_states` at line 1604, the `labels` tensor is not correspondingly sliced before being used for loss calculation at line 1608, which will cause a shape mismatch error if `labels` are provided.

CODE AROUND line_a (1604):
         1596 | 
         1597 |         hidden_states = outputs[0]
         1598 |         # Only compute necessary logits, and do not upcast them to float if we are not computing the loss
         1599 |         slice_indices = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep
         1600 |         logits = self.lm_head(hidden_states[:, slice_indices, :])
         1601 | 
         1602 |         loss = None
         1603 |         if labels is not None:
    >>>  1604 |             loss = self.loss_function(
         1605 |                 logits=logits, labels=labels, vocab_size=self.config.text_config.vocab_size, **kwargs
         1606 |             )
         1607 | 
         1608 |         return CausalLMOutputWithPast(
         1609 |             loss=loss,
         1610 |             logits=logits,
         1611 |             past_key_values=outputs.past_key_values,
         1612 |             hidden_states=outputs.hidden_states,

CODE AROUND line_b (1608):
         1600 |         logits = self.lm_head(hidden_states[:, slice_indices, :])
         1601 | 
         1602 |         loss = None
         1603 |         if labels is not None:
         1604 |             loss = self.loss_function(
         1605 |                 logits=logits, labels=labels, vocab_size=self.config.text_config.vocab_size, **kwargs
         1606 |             )
         1607 | 
    >>>  1608 |         return CausalLMOutputWithPast(
         1609 |             loss=loss,
         1610 |             logits=logits,
         1611 |             past_key_values=outputs.past_key_values,
         1612 |             hidden_states=outputs.hidden_states,
         1613 |             attentions=outputs.attentions,
         1614 |         )
         1615 | 
         1616 | 

---

### FINDING 41
repository: langchain-ai/langchain   pull request #39651 (MERGED)
file: libs/partners/openai/tests/integration_tests/chat_models/test_base.py
the model was shown this function: _gateway_or_provider_key
claim_type: missing_guard   model_confidence: high
cited line_a: 53    cited line_b: 54

CLAIM: The check for `_GATEWAY_ENABLED` on line 53 does not ensure that the `LANGSMITH_GATEWAY_API_KEY` environment variable is also set, which can cause a `KeyError` on line 54.

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

CODE AROUND line_b (54):
           46 | 
           47 | def _gateway_or_provider_key() -> str:
           48 |     """Return an API key valid for the endpoint the base URL resolves to.
           49 | 
           50 |     When the LangSmith gateway is enabled, requests route through it and must
           51 |     authenticate with the gateway key rather than the provider key.
           52 |     """
           53 |     if _GATEWAY_ENABLED:
    >>>    54 |         return os.environ["LANGSMITH_GATEWAY_API_KEY"]
           55 |     return os.environ["OPENAI_API_KEY"]
           56 | 
           57 | 
           58 | @pytest.mark.scheduled
           59 | def test_chat_openai() -> None:
           60 |     """Test ChatOpenAI wrapper."""
           61 |     chat = ChatOpenAI(
           62 |         temperature=0.7,

---

### FINDING 42
repository: huggingface/transformers   pull request #47152 (MERGED)
file: src/transformers/utils/quantization_config.py
the model was shown this function: is_quantization_compressed
claim_type: wrong_order   model_confidence: high
cited line_a: 1234    cited line_b: 1236

CLAIM: The access to `self.quantization_config` on line 1234 will raise an `AttributeError` if the model is not quantized and lacks this attribute, but the check `self.is_quantized` on line 1236, which safely verifies the attribute's existence, is performed too late.

CODE AROUND line_a (1234):
         1226 |         return {"run_compressed": self.run_compressed}
         1227 | 
         1228 |     @property
         1229 |     def is_quantized(self):
         1230 |         return bool(self.quantization_config) and bool(self.quantization_config.config_groups)
         1231 | 
         1232 |     @property
         1233 |     def is_quantization_compressed(self):
    >>>  1234 |         qc = self.quantization_config
         1235 |         return (
         1236 |             self.is_quantized
         1237 |             and qc is not None
         1238 |             and qc.quant_method == QuantizationMethod.COMPRESSED_TENSORS
         1239 |             and qc.format != "dense"
         1240 |         )
         1241 | 
         1242 | 

CODE AROUND line_b (1236):
         1228 |     @property
         1229 |     def is_quantized(self):
         1230 |         return bool(self.quantization_config) and bool(self.quantization_config.config_groups)
         1231 | 
         1232 |     @property
         1233 |     def is_quantization_compressed(self):
         1234 |         qc = self.quantization_config
         1235 |         return (
    >>>  1236 |             self.is_quantized
         1237 |             and qc is not None
         1238 |             and qc.quant_method == QuantizationMethod.COMPRESSED_TENSORS
         1239 |             and qc.format != "dense"
         1240 |         )
         1241 | 
         1242 | 
         1243 | @dataclass
         1244 | class FbgemmFp8Config(QuantizationConfigMixin):

---

### FINDING 43
repository: Skyvern-AI/skyvern   pull request #8210 (MERGED)
file: skyvern/forge/sdk/copilot/tools/__init__.py
the model was shown this function: inspect_page_for_composition_tool
claim_type: unhandled_case   model_confidence: high
cited line_a: 979    cited line_b: 976

CLAIM: The check on line 979 for whether `data` is a dictionary does not handle the case where it is not, causing the results from `_verify_requested_output_reads` to be silently discarded if the inspection result on line 976 is 'ok' but lacks a dictionary under the 'data' key.

CODE AROUND line_a (979):
          971 |     if authority_error:
          972 |         return _diagnosis_repair_tool_error(ctx.context, "inspect_page_for_composition", authority_error)
          973 |     result = await _inspect_page_for_composition_impl(ctx.context, target_url)
          974 |     if requested_output_reads and result.get("ok"):
          975 |         verified, unverified = await _verify_requested_output_reads(ctx.context, requested_output_reads)
          976 |         data = result.get("data")
          977 |         if isinstance(data, dict):
          978 |             data["requested_output_designations"] = verified
    >>>   979 |             if unverified:
          980 |                 data["unverified_output_designations"] = unverified
          981 |     return json.dumps(scrub_secrets_from_structure(ctx.context, result))
          982 | 
          983 | 
          984 | @function_tool(name_override="fill_credential_field", strict_mode=False)
          985 | async def fill_credential_field_tool(
          986 |     ctx: RunContextWrapper,
          987 |     selector: str,

CODE AROUND line_b (976):
          968 |     remain responsible for choosing a selector and authoring the workflow read.
          969 |     """
          970 |     authority_error = _authority_tool_error(ctx.context, "inspect_page_for_composition")
          971 |     if authority_error:
          972 |         return _diagnosis_repair_tool_error(ctx.context, "inspect_page_for_composition", authority_error)
          973 |     result = await _inspect_page_for_composition_impl(ctx.context, target_url)
          974 |     if requested_output_reads and result.get("ok"):
          975 |         verified, unverified = await _verify_requested_output_reads(ctx.context, requested_output_reads)
    >>>   976 |         data = result.get("data")
          977 |         if isinstance(data, dict):
          978 |             data["requested_output_designations"] = verified
          979 |             if unverified:
          980 |                 data["unverified_output_designations"] = unverified
          981 |     return json.dumps(scrub_secrets_from_structure(ctx.context, result))
          982 | 
          983 | 
          984 | @function_tool(name_override="fill_credential_field", strict_mode=False)
