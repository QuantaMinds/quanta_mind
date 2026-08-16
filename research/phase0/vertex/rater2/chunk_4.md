# Findings to adjudicate — chunk 4

There are 11 findings below, numbered by their global index.

### FINDING 44
repository: huggingface/transformers   pull request #47948 (MERGED)
file: tests/models/emu3/test_modeling_emu3.py
the model was shown this function: test_model_generation_multi_image
claim_type: contract_violation   model_confidence: high
cited line_a: 425    cited line_b: 436

CLAIM: The image processor is unconditionally configured to produce `32*32` tokens per image, but the expected output for the `("xpu", 3)` case on line 436 is for `64*64` tokens per image.

CODE AROUND line_a (425):
          417 |     @require_bitsandbytes
          418 |     @require_torch_large_accelerator
          419 |     def test_model_generation_multi_image(self):
          420 |         model = Emu3ForConditionalGeneration.from_pretrained(
          421 |             "BAAI/Emu3-Chat-hf", quantization_config=BitsAndBytesConfig(load_in_4bit=True), attn_implementation="eager"
          422 |         )
          423 |         processor = Emu3Processor.from_pretrained("BAAI/Emu3-Chat-hf")
          424 |         # Force 32x32 tokens per image (256x256 pixels / spatial_factor 8) to avoid OOM on A10G
    >>>   425 |         processor.image_processor.min_pixels = 256 * 256
          426 |         processor.image_processor.max_pixels = 256 * 256
          427 |         processor.image_processor.size = {"min_pixels": 256 * 256, "max_pixels": 256 * 256}
          428 | 
          429 |         image = Image.open(requests.get("https://picsum.photos/id/237/200/200", stream=True).raw)
          430 |         image_2 = Image.open(requests.get("https://picsum.photos/id/247/200/200", stream=True).raw)
          431 |         prompt = "USER: <image><image>What do these two images have in common? ASSISTANT:"
          432 | 
          433 |         inputs = processor(images=[image, image_2], text=prompt, return_tensors="pt").to(model.device, torch.float16)

CODE AROUND line_b (436):
          428 | 
          429 |         image = Image.open(requests.get("https://picsum.photos/id/237/200/200", stream=True).raw)
          430 |         image_2 = Image.open(requests.get("https://picsum.photos/id/247/200/200", stream=True).raw)
          431 |         prompt = "USER: <image><image>What do these two images have in common? ASSISTANT:"
          432 | 
          433 |         inputs = processor(images=[image, image_2], text=prompt, return_tensors="pt").to(model.device, torch.float16)
          434 | 
          435 |         # greedy generation outputs
    >>>   436 |         EXPECTED_TEXT_COMPLETIONS = Expectations(
          437 |                 {
          438 |                     ("xpu", 3): ['USER: 64*6464*64What do these two images have in common? ASSISTANT: The two images bot
          439 |                     (None, None): ["USER: 64*6464*64What do these two images have in common? ASSISTANT: Both images feat
          440 |                     ("cuda", 8): ["USER: 32*3232*32What do these two images have in common? ASSISTANT: The two images sh
          441 |                 }
          442 |             )  # fmt: skip
          443 |         EXPECTED_TEXT_COMPLETION = EXPECTED_TEXT_COMPLETIONS.get_expectation()
          444 |         generated_ids = model.generate(**inputs, max_new_tokens=40, do_sample=False)

---

### FINDING 45
repository: langchain-ai/langchain   pull request #39635 (MERGED)
file: libs/partners/openai/tests/unit_tests/chat_models/test_responses_stream.py
the model was shown this function: test_responses_stream_encrypted_reasoning_replays_with_store_false
claim_type: contract_violation   model_confidence: high
cited line_a: 819    cited line_b: 801

CLAIM: The test `test_responses_reasoning_done_without_encrypted_content_emits_no_chunk` at line 819 asserts that a reasoning `done` event without `encrypted_content` produces no message chunk, but for the test at line 774 to pass, the final aggregated chunk at line 801 must contain the reasoning item from such an event in order to test its exclusion during replay.

CODE AROUND line_a (819):
          811 | def test_responses_reasoning_done_without_encrypted_content_emits_no_chunk() -> None:
          812 |     """A reasoning `done` event with no encrypted content yields no chunk at all.
          813 | 
          814 |     The event carries nothing the `added` event has not already surfaced, so
          815 |     emitting a chunk for it would mean an extra empty `on_llm_new_token` callback
          816 |     for every reasoning item -- the common case, since encrypted content is only
          817 |     populated when the caller opts into it.
          818 |     """
    >>>   819 |     for encrypted_content in (None, ""):
          820 |         event = ResponseOutputItemDoneEvent(
          821 |             item=ResponseReasoningItem(
          822 |                 id="rs_123",
          823 |                 summary=[Summary(text="reasoning", type="summary_text")],
          824 |                 type="reasoning",
          825 |                 encrypted_content=encrypted_content,
          826 |                 status=None,
          827 |             ),

CODE AROUND line_b (801):
          793 |     mock_client.responses.create = mock_create
          794 | 
          795 |     full: BaseMessageChunk | None = None
          796 |     with patch.object(llm, "root_client", mock_client):
          797 |         for chunk in llm.stream("test"):
          798 |             full = chunk if full is None else full + chunk
          799 |     assert isinstance(full, AIMessageChunk)
          800 | 
    >>>   801 |     payload = llm._get_request_payload([full], store=False)
          802 |     reasoning_items = [
          803 |         item for item in payload["input"] if item.get("type") == "reasoning"
          804 |     ]
          805 | 
          806 |     # `rs_123` carried no encrypted content and is dropped; `rs_234` is replayed.
          807 |     assert [item["id"] for item in reasoning_items] == ["rs_234"]
          808 |     assert reasoning_items[0]["encrypted_content"] == "encrypted-content"
          809 | 

---

### FINDING 46
repository: huggingface/transformers   pull request #47896 (MERGED)
file: src/transformers/models/gemma4_unified/modeling_gemma4_unified.py
the model was shown this function: get_video_features
claim_type: contract_violation   model_confidence: high
cited line_a: 1184    cited line_b: 1187

CLAIM: The calculation of `split_sizes` at line 1187 by summing `non_pad_mask` over dimensions -2 and -1 is incorrect because `non_pad_mask` at line 1184 is a 4D tensor, resulting in summing over `num_frames` and `max_patches` instead of just `max_patches` per video frame.

CODE AROUND line_a (1184):
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

CODE AROUND line_b (1187):
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

---

### FINDING 47
repository: langchain-ai/langchain   pull request #39651 (MERGED)
file: libs/partners/openai/tests/integration_tests/chat_models/test_base.py
the model was shown this function: test_astream
claim_type: unhandled_case   model_confidence: high
cited line_a: 386    cited line_b: 397

CLAIM: The conditional logic starting at line 386, which checks `expect_usage`, combined with the `elif` at line 397, fails to handle the case where `expect_usage` is `False` but `_GATEWAY_ENABLED` is `True`, resulting in the test failing to assert that the gateway correctly provides usage data.

CODE AROUND line_a (386):
          378 |             if chunks_with_token_counts != 1:
          379 |                 msg = (
          380 |                     "Expected exactly one chunk with token counts. "
          381 |                     "AIMessageChunk aggregation adds counts. Check that "
          382 |                     "this is behaving properly."
          383 |                 )
          384 |                 raise AssertionError(msg)
          385 |             assert full.usage_metadata is not None
    >>>   386 |             assert full.usage_metadata["input_tokens"] > 0
          387 |             assert full.usage_metadata["output_tokens"] > 0
          388 |             assert full.usage_metadata["total_tokens"] > 0
          389 |         # The LangSmith gateway always emits a usage chunk regardless of
          390 |         # `stream_options.include_usage`, so the opt-out assertions below only
          391 |         # hold when not routing through it.
          392 |         elif not _GATEWAY_ENABLED:
          393 |             assert chunks_with_token_counts == 0
          394 |             assert full.usage_metadata is None

CODE AROUND line_b (397):
          389 |         # The LangSmith gateway always emits a usage chunk regardless of
          390 |         # `stream_options.include_usage`, so the opt-out assertions below only
          391 |         # hold when not routing through it.
          392 |         elif not _GATEWAY_ENABLED:
          393 |             assert chunks_with_token_counts == 0
          394 |             assert full.usage_metadata is None
          395 | 
          396 |     llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0, max_tokens=MAX_TOKEN_COUNT)  # type: ignore[call-arg]
    >>>   397 |     await _test_stream(llm.astream("Hello", stream_usage=False), expect_usage=False)
          398 |     await _test_stream(
          399 |         llm.astream("Hello", stream_options={"include_usage": True}), expect_usage=True
          400 |     )
          401 |     await _test_stream(llm.astream("Hello", stream_usage=True), expect_usage=True)
          402 |     llm = ChatOpenAI(
          403 |         model="gpt-4.1-mini",
          404 |         temperature=0,
          405 |         max_tokens=MAX_TOKEN_COUNT,  # type: ignore[call-arg]

---

### FINDING 48
repository: huggingface/transformers   pull request #47948 (MERGED)
file: tests/models/emu3/test_modeling_emu3.py
the model was shown this function: test_model_generation_multi_image
claim_type: contract_violation   model_confidence: high
cited line_a: 425    cited line_b: 437

CLAIM: The image processor is unconditionally configured to produce `32*32` tokens per image, but the expected output for the `(None, None)` case on line 437 is for `64*64` tokens per image.

CODE AROUND line_a (425):
          417 |     @require_bitsandbytes
          418 |     @require_torch_large_accelerator
          419 |     def test_model_generation_multi_image(self):
          420 |         model = Emu3ForConditionalGeneration.from_pretrained(
          421 |             "BAAI/Emu3-Chat-hf", quantization_config=BitsAndBytesConfig(load_in_4bit=True), attn_implementation="eager"
          422 |         )
          423 |         processor = Emu3Processor.from_pretrained("BAAI/Emu3-Chat-hf")
          424 |         # Force 32x32 tokens per image (256x256 pixels / spatial_factor 8) to avoid OOM on A10G
    >>>   425 |         processor.image_processor.min_pixels = 256 * 256
          426 |         processor.image_processor.max_pixels = 256 * 256
          427 |         processor.image_processor.size = {"min_pixels": 256 * 256, "max_pixels": 256 * 256}
          428 | 
          429 |         image = Image.open(requests.get("https://picsum.photos/id/237/200/200", stream=True).raw)
          430 |         image_2 = Image.open(requests.get("https://picsum.photos/id/247/200/200", stream=True).raw)
          431 |         prompt = "USER: <image><image>What do these two images have in common? ASSISTANT:"
          432 | 
          433 |         inputs = processor(images=[image, image_2], text=prompt, return_tensors="pt").to(model.device, torch.float16)

CODE AROUND line_b (437):
          429 |         image = Image.open(requests.get("https://picsum.photos/id/237/200/200", stream=True).raw)
          430 |         image_2 = Image.open(requests.get("https://picsum.photos/id/247/200/200", stream=True).raw)
          431 |         prompt = "USER: <image><image>What do these two images have in common? ASSISTANT:"
          432 | 
          433 |         inputs = processor(images=[image, image_2], text=prompt, return_tensors="pt").to(model.device, torch.float16)
          434 | 
          435 |         # greedy generation outputs
          436 |         EXPECTED_TEXT_COMPLETIONS = Expectations(
    >>>   437 |                 {
          438 |                     ("xpu", 3): ['USER: 64*6464*64What do these two images have in common? ASSISTANT: The two images bot
          439 |                     (None, None): ["USER: 64*6464*64What do these two images have in common? ASSISTANT: Both images feat
          440 |                     ("cuda", 8): ["USER: 32*3232*32What do these two images have in common? ASSISTANT: The two images sh
          441 |                 }
          442 |             )  # fmt: skip
          443 |         EXPECTED_TEXT_COMPLETION = EXPECTED_TEXT_COMPLETIONS.get_expectation()
          444 |         generated_ids = model.generate(**inputs, max_new_tokens=40, do_sample=False)
          445 |         text = processor.batch_decode(generated_ids, skip_special_tokens=True)

---

### FINDING 49
repository: huggingface/transformers   pull request #47944 (MERGED)
file: src/transformers/models/qwen3_5_moe/modeling_qwen3_5_moe.py
the model was shown this function: _init_weights
claim_type: contract_violation   model_confidence: high
cited line_a: 420    cited line_b: 904

CLAIM: The `A_log` parameter is initialized with specific random values when its containing module is constructed at line 420, but this initialization is redundant because the parameter is always re-initialized by `_init_weights` at line 904.

CODE AROUND line_a (420):
          412 |         # time step projection (discretization)
          413 |         # instantiate once and copy inv_dt in init_weights of PretrainedModel
          414 |         self.dt_bias = nn.Parameter(torch.ones(self.num_v_heads))
          415 | 
          416 |         # Lower bound kept away from 0 so log(A) never becomes -inf
          417 |         A = torch.empty(self.num_v_heads).uniform_(0.01, 16)
          418 |         self.A_log = nn.Parameter(torch.log(A))
          419 | 
    >>>   420 |         self.norm = Qwen3_5MoeRMSNormGated(self.head_v_dim, eps=self.layer_norm_epsilon)
          421 |         self.out_proj = nn.Linear(self.value_dim, self.hidden_size, bias=False)
          422 | 
          423 |         self.layer_type = config.layer_types[layer_idx]
          424 | 
          425 |         self.in_proj_qkv = nn.Linear(self.hidden_size, self.key_dim * 2 + self.value_dim, bias=False)
          426 |         self.in_proj_z = nn.Linear(self.hidden_size, self.value_dim, bias=False)
          427 |         self.in_proj_b = nn.Linear(self.hidden_size, self.num_v_heads, bias=False)
          428 |         self.in_proj_a = nn.Linear(self.hidden_size, self.num_v_heads, bias=False)

CODE AROUND line_b (904):
          896 |     _can_compile_fullgraph = True
          897 | 
          898 |     @torch.no_grad()
          899 |     def _init_weights(self, module):
          900 |         super()._init_weights(module)
          901 |         if isinstance(module, Qwen3_5MoeGatedDeltaNet):
          902 |             init.ones_(module.dt_bias)
          903 |             # Lower bound kept away from 0 so log(A) never becomes -inf
    >>>   904 |             init.copy_(
          905 |                 module.A_log,
          906 |                 torch.empty(module.num_v_heads, device=module.A_log.device).uniform_(0.01, 16).log_(),
          907 |             )
          908 |         # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
          909 |         elif isinstance(module, Qwen3_5MoeRMSNorm):
          910 |             init.zeros_(module.weight)
          911 |         elif isinstance(module, Qwen3_5MoeExperts):
          912 |             init.normal_(module.gate_up_proj, mean=0.0, std=self.config.initializer_range)

---

### FINDING 50
repository: huggingface/transformers   pull request #47944 (MERGED)
file: src/transformers/models/qwen3_5_moe/modular_qwen3_5_moe.py
the model was shown this function: _init_weights
claim_type: contract_violation   model_confidence: low
cited line_a: 219    cited line_b: 218

CLAIM: The tensor created on line 219 is explicitly 1-dimensional, which will cause the `copy_` operation on line 218 to fail with a shape mismatch error if `module.A_log` has the same number of elements but a different shape, such as `(num_v_heads, 1)`.

CODE AROUND line_a (219):
          211 | 
          212 |     def _init_weights(self, module):
          213 |         PreTrainedModel._init_weights(self, module)
          214 |         if isinstance(module, Qwen3_5MoeGatedDeltaNet):
          215 |             init.ones_(module.dt_bias)
          216 |             # Lower bound kept away from 0 so log(A) never becomes -inf
          217 |             init.copy_(
          218 |                 module.A_log,
    >>>   219 |                 torch.empty(module.num_v_heads, device=module.A_log.device).uniform_(0.01, 16).log_(),
          220 |             )
          221 |         # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
          222 |         elif isinstance(module, Qwen3_5MoeRMSNorm):
          223 |             init.zeros_(module.weight)
          224 |         elif isinstance(module, Qwen3_5MoeExperts):
          225 |             init.normal_(module.gate_up_proj, mean=0.0, std=self.config.initializer_range)
          226 |             init.normal_(module.down_proj, mean=0.0, std=self.config.initializer_range)
          227 |         elif isinstance(module, Qwen3_5MoeSparseMoeBlock):

CODE AROUND line_b (218):
          210 |     _no_split_modules = ["Qwen3_5MoeDecoderLayer", "Qwen3_5MoeVisionBlock"]
          211 | 
          212 |     def _init_weights(self, module):
          213 |         PreTrainedModel._init_weights(self, module)
          214 |         if isinstance(module, Qwen3_5MoeGatedDeltaNet):
          215 |             init.ones_(module.dt_bias)
          216 |             # Lower bound kept away from 0 so log(A) never becomes -inf
          217 |             init.copy_(
    >>>   218 |                 module.A_log,
          219 |                 torch.empty(module.num_v_heads, device=module.A_log.device).uniform_(0.01, 16).log_(),
          220 |             )
          221 |         # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
          222 |         elif isinstance(module, Qwen3_5MoeRMSNorm):
          223 |             init.zeros_(module.weight)
          224 |         elif isinstance(module, Qwen3_5MoeExperts):
          225 |             init.normal_(module.gate_up_proj, mean=0.0, std=self.config.initializer_range)
          226 |             init.normal_(module.down_proj, mean=0.0, std=self.config.initializer_range)

---

### FINDING 51
repository: vllm-project/vllm   pull request #52374 (MERGED)
file: vllm/v1/worker/gpu/model_runner.py
the model was shown this function: load_model
claim_type: unhandled_case   model_confidence: high
cited line_a: 345    cited line_b: 360

CLAIM: When a model is reloaded, `load_model` does not reset `self.cudagraph_manager`, causing the new model assigned at line 360 to be used with potentially stale CUDA graphs from a previous model.

CODE AROUND line_a (345):
          337 |             tasks.extend(self.model_state.get_supported_generation_tasks())
          338 |         if self.is_pooling_model:
          339 |             # Do not rely on pooling_runner here, since this information is needed
          340 |             # on the first PP rank, while pooling_runner is only initialized
          341 |             # on the last PP rank.
          342 |             tasks.extend(PoolingRunner.get_supported_tasks(self.model))
          343 |         return tuple(tasks)
          344 | 
    >>>   345 |     def load_model(self, load_dummy_weights: bool = False, *args, **kwargs) -> None:
          346 |         time_before_load = time.perf_counter()
          347 |         if load_dummy_weights:
          348 |             self.load_config.load_format = "dummy"
          349 |         self.eplb.prepare_load()
          350 |         eplb_models_added = False
          351 |         with DeviceMemoryProfiler() as m:
          352 |             model_loader = get_model_loader(self.vllm_config.load_config)
          353 |             logger.info_once("Loading model from scratch...")

CODE AROUND line_b (360):
          352 |             model_loader = get_model_loader(self.vllm_config.load_config)
          353 |             logger.info_once("Loading model from scratch...")
          354 | 
          355 |             self.model = model_loader.load_model(
          356 |                 vllm_config=self.vllm_config, model_config=self.vllm_config.model_config
          357 |             )
          358 |             if self.lora_config:
          359 |                 self.model = self.load_lora_model(
    >>>   360 |                     self.model, self.vllm_config, self.device
          361 |                 )
          362 | 
          363 |             if self.use_aux_hidden_state_outputs:
          364 |                 assert self.speculative_config is not None
          365 |                 set_eagle3_aux_hidden_state_layers(self.model, self.speculative_config)
          366 |             if isinstance(self.speculator, DraftModelSpeculator):
          367 |                 self.speculator.load_model(self.model)
          368 |                 eplb_models_added = self.eplb.maybe_register_speculator(

---

### FINDING 52
repository: apache/airflow   pull request #70152 (MERGED)
file: providers/amazon/tests/unit/amazon/aws/operators/test_datasync.py
the model was shown this function: test_no_task_identified_or_created
claim_type: unhandled_case   model_confidence: low
cited line_a: 349    cited line_b: 362

CLAIM: The call to `self.client.list_tasks()` at line 349 does not handle pagination, so if more than 100 tasks exist, some will not be deleted, which could cause the `execute` method to find a task and not raise the expected `DataSyncTaskNotFoundError` at line 362.

CODE AROUND line_a (349):
          341 |         mock_get_conn.assert_called()
          342 | 
          343 |     def test_no_task_identified_or_created(self, mock_get_conn):
          344 |         # ### Set up mocks:
          345 |         mock_get_conn.return_value = self.client
          346 |         # ### Begin tests:
          347 | 
          348 |         # Delete all tasks so none can be matched.
    >>>   349 |         tasks = self.client.list_tasks()
          350 |         for task in tasks["Tasks"]:
          351 |             self.client.delete_task(TaskArn=task["TaskArn"])
          352 | 
          353 |         # Without create_task_kwargs there is nothing to run or create.
          354 |         self.datasync = DataSyncOperator(
          355 |             task_id="datasync_no_task",
          356 |             dag=self.dag,
          357 |             source_location_uri=SOURCE_LOCATION_URI,

CODE AROUND line_b (362):
          354 |         self.datasync = DataSyncOperator(
          355 |             task_id="datasync_no_task",
          356 |             dag=self.dag,
          357 |             source_location_uri=SOURCE_LOCATION_URI,
          358 |             destination_location_uri=DESTINATION_LOCATION_URI,
          359 |             wait_interval_seconds=0,
          360 |         )
          361 |         with pytest.raises(DataSyncTaskNotFoundError):
    >>>   362 |             self.datasync.execute(None)
          363 |         # ### Check mocks:
          364 |         mock_get_conn.assert_called()
          365 | 
          366 |     def test_create_task_no_source_location(self, mock_get_conn):
          367 |         # ### Set up mocks:
          368 |         mock_get_conn.return_value = self.client
          369 |         # ### Begin tests:
          370 | 

---

### FINDING 53
repository: cartography-cncf/cartography   pull request #3130 (MERGED)
file: tests/unit/rules/test_malicious_npm_dependencies_shai_hulud.py
the model was shown this function: test_aug_2026_facts_cover_the_same_packages
claim_type: contract_violation   model_confidence: high
cited line_a: 65    cited line_b: 72

CLAIM: The function's docstring beginning at line 65 states an intent to ensure that the two Facts do not drift apart, but the check at line 72 is incomplete as it only compares their `cypher_query` attributes while omitting a comparison of their `cypher_visual_query` attributes.

CODE AROUND line_a (65):
           57 | def test_aug_2026_fact_covers_keyv_scoped_family() -> None:
           58 |     """The worm republished the whole @keyv/* scope at 6.0.0, not just `keyv`."""
           59 |     names = _package_names(_fact(_AUG_2026_FACT_ID).cypher_query)
           60 |     scoped = {name for name in names if name.startswith("@keyv/")}
           61 |     assert len(scoped) >= 14
           62 | 
           63 | 
           64 | def test_aug_2026_facts_cover_the_same_packages() -> None:
    >>>    65 |     """
           66 |     The pinned and at-risk Facts must not drift apart: a package added to one
           67 |     without the other would silently lose either exact-version or
           68 |     floating-range coverage.
           69 |     """
           70 |     pinned = _package_names(_fact(_AUG_2026_FACT_ID).cypher_query)
           71 |     at_risk = _package_names(_fact(_AUG_2026_AT_RISK_FACT_ID).cypher_query)
           72 |     assert pinned == at_risk
           73 | 

CODE AROUND line_b (72):
           64 | def test_aug_2026_facts_cover_the_same_packages() -> None:
           65 |     """
           66 |     The pinned and at-risk Facts must not drift apart: a package added to one
           67 |     without the other would silently lose either exact-version or
           68 |     floating-range coverage.
           69 |     """
           70 |     pinned = _package_names(_fact(_AUG_2026_FACT_ID).cypher_query)
           71 |     at_risk = _package_names(_fact(_AUG_2026_AT_RISK_FACT_ID).cypher_query)
    >>>    72 |     assert pinned == at_risk
           73 | 
           74 | 
           75 | def test_aug_2026_queries_and_visual_queries_agree() -> None:
           76 |     """
           77 |     cypher_visual_query duplicates the IOC list for the web UI; nothing
           78 |     generic diffs it against cypher_query, so it can silently drift.
           79 |     """
           80 |     for fact_id in (_AUG_2026_FACT_ID, _AUG_2026_AT_RISK_FACT_ID):

---

### FINDING 54
repository: vllm-project/vllm   pull request #50597 (MERGED)
file: vllm/model_executor/layers/fused_moe/oracle/mxfp4.py
the model was shown this function: mxfp4_round_up_hidden_size_and_intermediate_size
claim_type: wrong_order   model_confidence: high
cited line_a: 1506    cited line_b: 1521

CLAIM: The import of `_shuf_s` and `_shuf_w` at line 1521 should occur before line 1506, as the `if` block for `SITU` activation can return early, leaving these modules un-imported for other activation functions like `SILU` that fall through and require them.

CODE AROUND line_a (1506):
         1498 |                 w2_weight.data.view(fp4_dtype), 16, False
         1499 |             )
         1500 |             w13_scale_raw = w13_weight_scale.data.view(e8m0_dtype)
         1501 |             w2_scale_raw = w2_weight_scale.data.view(e8m0_dtype)
         1502 |             w13_scale = rocm_aiter_ops.shuffle_scale_a16w4(
         1503 |                 w13_scale_raw.view(-1, w13_scale_raw.shape[-1]),
         1504 |                 num_experts,
         1505 |                 guinterleave,
    >>>  1506 |             )
         1507 |             w2_scale = e8m0_shuffle(w2_scale_raw.view(-1, w2_scale_raw.shape[-1]))
         1508 |             w13.is_shuffled = True
         1509 |             w2.is_shuffled = True
         1510 |             return (w13, w2, w13_scale, w2_scale, w13_bias, w2_bias)
         1511 | 
         1512 |         from aiter.ops.shuffle import shuffle_scale as _shuf_s
         1513 |         from aiter.ops.shuffle import shuffle_weight as _shuf_w
         1514 | 

CODE AROUND line_b (1521):
         1513 |         from aiter.ops.shuffle import shuffle_weight as _shuf_w
         1514 | 
         1515 |         w13_weight = torch.nn.Parameter(
         1516 |             _shuf_w(
         1517 |                 w13_weight.data.view(torch.float4_e2m1fn_x2),
         1518 |                 is_guinterleave=True,
         1519 |                 gate_up=True,
         1520 |             ),
    >>>  1521 |             requires_grad=False,
         1522 |         )
         1523 |         shuffled_w13_scale = _shuf_s(
         1524 |             w13_weight_scale.reshape(-1, w13_weight_scale.shape[-1]),
         1525 |             num_experts,
         1526 |             True,
         1527 |             True,
         1528 |         )
         1529 | 
