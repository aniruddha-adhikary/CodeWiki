# Tasks: Add Projection Framework

Implementation order follows dependency chain. Each phase has a dedicated test step that MUST pass before the next phase begins. Test agents run in parallel with the next phase's implementation where there are no dependencies.

## 1. Projection Data Model (`projection-model`)

- [x] 1.1 Create `codewiki/src/be/projection.py` with `CodeProvenance` dataclass
- [x] 1.2 Add `ProjectionConfig` dataclass with all fields (clustering, audience, detail, provenance, supplementary, glossary, objectives)
- [x] 1.3 Add `CompiledProjectionPrompts` dataclass
- [x] 1.4 Implement `compile_projection_instructions()` that formats provenance into `<CODE_CONTEXT>`, framework into `<FRAMEWORK_CONTEXT>`, audience/perspective/objectives into custom_instructions
- [x] 1.5 Implement `get_developer_projection()` factory (empty fields, backwards compat)
- [x] 1.6 Implement `get_business_projection()` factory (business clustering goal, objectives override)
- [x] 1.7 Implement `get_ejb_migration_projection()` factory (framework context, supplementary patterns)
- [x] 1.8 Implement `get_natural_transpiled_projection()` factory (code provenance, data dictionary)
- [x] 1.9 Implement `resolve_projection()` (built-in names, JSON file paths, `.codewiki/projections/` lookup)

### TEST: Phase 1 Validation
- [x] 1.T1 Create `tests/test_projection.py` -- unit tests for all dataclass construction, field defaults, and factory outputs
- [x] 1.T2 Test `compile_projection_instructions()` for each built-in projection: verify block content, emptiness, ordering
- [x] 1.T3 Test `resolve_projection()`: built-in names, valid JSON file, invalid name (ValueError), `.codewiki/projections/` path
- [x] 1.T4 Test JSON serialization round-trip for `ProjectionConfig` with nested `CodeProvenance`
- [x] 1.T5 **Run `pytest tests/test_projection.py` -- ALL PASSED (31/31)**

## 2. Prompt Parameterization (`prompt-parameterization`)

Depends on: Phase 1 (for `CompiledProjectionPrompts` type, `DEFAULT_OBJECTIVES` concept)

- [x] 2.1 Extract current hardcoded `<OBJECTIVES>` text into `DEFAULT_OBJECTIVES` constant in `prompt_template.py`
- [x] 2.2 Replace hardcoded `<OBJECTIVES>` content in `SYSTEM_PROMPT` with `{objectives}` template variable
- [x] 2.3 Replace hardcoded `<OBJECTIVES>` content in `LEAF_SYSTEM_PROMPT` with `{objectives}` template variable
- [x] 2.4 Add `{code_context}`, `{framework_context}`, `{glossary}` template slots to both prompts (positioned per design.md ordering)
- [x] 2.5 Expand `format_system_prompt()` signature: add `code_context`, `framework_context`, `objectives`, `glossary` params (all default `None`)
- [x] 2.6 Expand `format_leaf_system_prompt()` signature: same new params
- [x] 2.7 Implement conditional block wrapping: each slot wrapped in its XML tag only when non-empty
- [x] 2.8 Add `.xml`, `.yaml`, `.yml`, `.properties` to `EXTENSION_TO_LANGUAGE`
- [x] 2.9 Add `supplementary_files` and `supplementary_file_role` params to `format_user_prompt()`; append `<SUPPLEMENTARY_CONFIGURATION>` block when non-empty

### TEST: Phase 2 Validation
- [x] 2.T1 Create `tests/test_prompt_parameterization.py`
- [x] 2.T2 Test backwards compat: `format_system_prompt(module_name="test", custom_instructions="x")` produces output identical to current behavior (no new blocks, default objectives)
- [x] 2.T3 Test `format_system_prompt()` with all params non-empty: verify block ordering (`<CODE_CONTEXT>` before `<FRAMEWORK_CONTEXT>` before `<OBJECTIVES>` before `<GLOSSARY>`)
- [x] 2.T4 Test conditional emptiness: each param as `None` produces no corresponding XML block
- [x] 2.T5 Test `format_user_prompt()` with supplementary files: verify `<SUPPLEMENTARY_CONFIGURATION>` block appears
- [x] 2.T6 Test `format_user_prompt()` without supplementary files: verify no `<SUPPLEMENTARY_CONFIGURATION>` block
- [x] 2.T7 Test `EXTENSION_TO_LANGUAGE` contains `.xml`, `.yaml`, `.yml`, `.properties`
- [x] 2.T8 **Run `pytest tests/test_prompt_parameterization.py` AND `pytest tests/` -- ALL PASSED (28/28)**

## 3. Sub-Agent Prompt Fix + Pipeline Deps (`projection-pipeline` partial)

Depends on: Phase 2 (expanded format function signatures)

- [x] 3.1 Add new fields to `CodeWikiDeps` in `deps.py`: `code_context`, `framework_context`, `objectives_override`, `glossary_block`, `supplementary_files` (Dict), `projection_name`
- [x] 3.2 Fix `generate_sub_module_documentations.py` line 54: replace `SYSTEM_PROMPT.format(module_name=..., custom_instructions=...)` with `format_system_prompt(module_name=..., custom_instructions=..., code_context=ctx.deps.code_context, framework_context=ctx.deps.framework_context, objectives=ctx.deps.objectives_override, glossary=ctx.deps.glossary_block)`
- [x] 3.3 Fix `generate_sub_module_documentations.py` line 62: replace `LEAF_SYSTEM_PROMPT.format(...)` with `format_leaf_system_prompt(...)` passing all deps fields
- [x] 3.4 Update imports in `generate_sub_module_documentations.py`: add `format_system_prompt`, `format_leaf_system_prompt`; remove direct `SYSTEM_PROMPT`, `LEAF_SYSTEM_PROMPT` imports (if no longer needed directly)

### TEST: Phase 3 Validation
- [x] 3.T1 Create `tests/test_sub_agent_prompt_fix.py`
- [x] 3.T2 Test that `generate_sub_module_documentation()` with populated deps fields produces sub-agent prompts containing all projection blocks (mock LLM)
- [x] 3.T3 Test that `generate_sub_module_documentation()` with all deps fields as `None` produces prompts identical to current behavior (mock LLM)
- [x] 3.T4 Test that `CodeWikiDeps` can be constructed with all new fields and defaults to `None`/empty
- [x] 3.T5 **Run `pytest tests/test_sub_agent_prompt_fix.py` AND `pytest tests/` -- ALL PASSED (6/6)**

## 4. Projection-Aware Clustering (`projection-clustering`)

Depends on: Phase 1 (for `ProjectionConfig` type)

- [x] 4.1 Add `grouping_directive: str = None` param to `format_cluster_prompt()` in `prompt_template.py`
- [x] 4.2 Implement `<GROUPING_STRATEGY>` block prepend when `grouping_directive` is non-empty
- [x] 4.3 Add `projection: Optional[ProjectionConfig] = None` param to `cluster_modules()` in `cluster_modules.py`
- [x] 4.4 Implement saved grouping bypass: if `projection.saved_grouping` exists, return it directly
- [x] 4.5 Pass `projection.clustering_goal` as `grouping_directive` to `format_cluster_prompt()`
- [x] 4.6 Propagate `projection` through recursive `cluster_modules()` calls

### TEST: Phase 4 Validation
- [x] 4.T1 Create `tests/test_projection_clustering.py`
- [x] 4.T2 Test `format_cluster_prompt()` with `grouping_directive`: verify `<GROUPING_STRATEGY>` block present
- [x] 4.T3 Test `format_cluster_prompt()` without `grouping_directive`: verify no `<GROUPING_STRATEGY>` block
- [x] 4.T4 Test `cluster_modules()` with `saved_grouping`: verify LLM is NOT called and saved tree is returned
- [x] 4.T5 Test `cluster_modules()` with business projection: verify `clustering_goal` passed to prompt (mock LLM)
- [x] 4.T6 Test `cluster_modules()` without projection: verify identical behavior to current (mock LLM)
- [x] 4.T7 **Run `pytest tests/test_projection_clustering.py` AND `pytest tests/` -- ALL PASSED (16/16)**

## 5. Agent Orchestrator Integration (`projection-pipeline` completion)

Depends on: Phase 1, Phase 2, Phase 3

- [x] 5.1 Add `projection: Optional[ProjectionConfig] = None` param to `AgentOrchestrator.__init__()`
- [x] 5.2 Call `compile_projection_instructions()` in `__init__` when projection provided
- [x] 5.3 Merge compiled `custom_instructions` with existing `config.get_prompt_addition()`
- [x] 5.4 Add `glossary_block` and `supplementary_files` attributes (populated later by pipeline)
- [x] 5.5 Update `create_agent()` to pass all compiled fields to `format_system_prompt()` / `format_leaf_system_prompt()`
- [x] 5.6 Update `process_module()` to populate `CodeWikiDeps` with all projection context fields

### TEST: Phase 5 Validation
- [x] 5.T1 Create `tests/test_orchestrator_projection.py`
- [x] 5.T2 Test `AgentOrchestrator` with business projection: verify `compiled.objectives_override` is set
- [x] 5.T3 Test `AgentOrchestrator` without projection: verify identical behavior
- [x] 5.T4 Test that `create_agent()` with projection produces system prompts containing projection blocks
- [x] 5.T5 Test that `process_module()` populates `CodeWikiDeps` with all projection fields
- [x] 5.T6 **Run `pytest tests/test_orchestrator_projection.py` AND `pytest tests/` -- ALL PASSED (6/6)**

## 6. Supplementary File Processing (`supplementary-files`)

Depends on: Phase 2 (user prompt injection), Phase 5 (orchestrator stores files)

- [x] 6.1 Implement `collect_supplementary_files()` in `documentation_generator.py`: glob patterns, 50KB cap, binary skip
- [x] 6.2 Implement `filter_supplementary_for_module()`: directory subtree + root-level filter
- [x] 6.3 Wire collection into `DocumentationGenerator.run()` after clustering
- [x] 6.4 Pass collected files to `AgentOrchestrator`
- [x] 6.5 In `AgentOrchestrator.process_module()`, filter supplementary files per-module and pass to `format_user_prompt()`

### TEST: Phase 6 Validation
- [x] 6.T1 Create `tests/test_supplementary_files.py`
- [x] 6.T2 Test `collect_supplementary_files()`: matching patterns, no matches, large file truncation
- [x] 6.T3 Test `filter_supplementary_for_module()`: same-directory files included, different-directory excluded, root files always included
- [x] 6.T4 Test end-to-end: projection with `supplementary_file_patterns` produces agent prompts with `<SUPPLEMENTARY_CONFIGURATION>` block (mock LLM, real file system with temp fixtures)
- [x] 6.T5 Test without supplementary patterns: no `<SUPPLEMENTARY_CONFIGURATION>` block in prompts
- [x] 6.T6 **Run `pytest tests/test_supplementary_files.py` AND `pytest tests/` -- ALL PASSED (10/10)**

## 7. Glossary Generation (`glossary-generation`)

Depends on: Phase 2 (glossary prompt slot), Phase 5 (orchestrator glossary_block)

- [x] 7.1 Create `codewiki/src/be/glossary_generator.py` with `GlossaryEntry` and `Glossary` dataclasses
- [x] 7.2 Implement `Glossary.to_dict()`, `Glossary.from_dict()`, `Glossary.to_prompt_block()`
- [x] 7.3 Implement `extract_identifiers()`: Node.name, Node.parameters, source code regex, generic name filter
- [x] 7.4 Implement `generate_glossary()`: batching, LLM calls, response parsing with `<GLOSSARY_ENTRIES>` tags
- [x] 7.5 Implement `render_glossary_md()` for Markdown table output
- [x] 7.6 Wire into `DocumentationGenerator.run()`: check `output_artifacts`, generate or load glossary, set `orchestrator.glossary_block`, save artifacts

### TEST: Phase 7 Validation
- [x] 7.T1 Create `tests/test_glossary_generator.py`
- [x] 7.T2 Test `GlossaryEntry` and `Glossary` construction, field access, defaults
- [x] 7.T3 Test `Glossary` serialization round-trip: `to_dict()` -> `from_dict()` equality
- [x] 7.T4 Test `to_prompt_block()`: max_entries cap, confidence sorting
- [x] 7.T5 Test `extract_identifiers()`: Java class/method names extracted, NATURAL `WS_*` patterns extracted, generics filtered
- [x] 7.T6 Test `generate_glossary()` with mocked LLM: verify batching, response parsing, entry assembly
- [x] 7.T7 Test `render_glossary_md()`: verify Markdown table format
- [x] 7.T8 Test pipeline integration: glossary generated when `data_dictionary` in artifacts, loaded from file when `glossary_path` set, skipped when neither configured
- [x] 7.T9 **Run `pytest tests/test_glossary_generator.py` AND `pytest tests/` -- ALL PASSED (26/26)**

## 8. Documentation Generator Threading (`projection-pipeline` final)

Depends on: Phase 4, Phase 5, Phase 6, Phase 7

- [x] 8.1 Add `projection: Optional[ProjectionConfig] = None` to `DocumentationGenerator.__init__()`
- [x] 8.2 Pass projection to `AgentOrchestrator` constructor
- [x] 8.3 Pass projection to `cluster_modules()` call
- [x] 8.4 Call `collect_supplementary_files()` when projection has patterns
- [x] 8.5 Call glossary generation/loading when configured
- [x] 8.6 Set `orchestrator.glossary_block` and `orchestrator.supplementary_files`
- [x] 8.7 Include projection info in `create_documentation_metadata()`
- [x] 8.8 Add `projection` field to backend `Config` class in `config.py`

### TEST: Phase 8 Validation
- [x] 8.T1 Create `tests/test_documentation_generator_projection.py`
- [x] 8.T2 Test `DocumentationGenerator` with business projection: verify projection passed to clustering and orchestrator (mock LLM)
- [x] 8.T3 Test `DocumentationGenerator` without projection: verify identical behavior to current (mock LLM)
- [x] 8.T4 Test metadata output includes projection name when active
- [x] 8.T5 Test full pipeline threading: projection flows through clustering -> orchestrator -> deps -> sub-agents (mock LLM, verify prompt content at each stage)
- [x] 8.T6 **Run `pytest tests/test_documentation_generator_projection.py` AND `pytest tests/` -- ALL PASSED**

## 9. CLI Integration (`projection-cli`)

Depends on: Phase 8 (all backend changes complete)

- [x] 9.1 Add `--projection` / `-p` option to `generate` command in `generate.py`
- [x] 9.2 Add `--load-grouping` option
- [x] 9.3 Add `--interactive-grouping` flag (deferred to Phase 10 wiring)
- [x] 9.4 Add `--generate-glossary` flag
- [x] 9.5 Add `--load-glossary` option
- [x] 9.6 Add `--interactive-glossary` flag (deferred to Phase 10 wiring)
- [x] 9.7 Resolve projection via `resolve_projection()` and pass to `CLIDocumentationGenerator`
- [x] 9.8 Update `CLIDocumentationGenerator` to accept projection and adjust `working_dir` for subdirectory
- [x] 9.9 Pass projection to backend `DocumentationGenerator` and `cluster_modules()` in CLI adapter
- [x] 9.10 Implement output subdirectory logic: `docs/{projection.name}/` when projection active

### TEST: Phase 9a Validation (CLI options)
- [x] 9.T1 Create `tests/test_cli_projection.py`
- [x] 9.T2 Test `--projection business` resolves correctly
- [x] 9.T3 Test invalid projection fails with appropriate error
- [x] 9.T4 Test `--load-grouping` sets saved_grouping on projection
- [x] 9.T5 Test output directory is `docs/business/` when `--projection business` is used
- [x] 9.T6 Test output directory is `docs/` when no projection is used
- [x] 9.T7 **Run `pytest tests/test_cli_projection.py` AND `pytest tests/` -- ALL PASSED**

## 10. Interactive Sessions (`projection-cli` interactive)

Depends on: Phase 9

- [x] 10.1 Create `codewiki/cli/interactive_grouping.py` with `InteractiveGroupingSession` class
- [x] 10.2 Implement `display_tree()`, `rename_group()`, `move_component()`, `merge_groups()`, `accept()`, `save()`, `run()`
- [x] 10.3 Create `codewiki/cli/interactive_glossary.py` with `InteractiveGlossarySession` class
- [x] 10.4 Implement `display()`, `edit_entry()`, `remove_entry()`, `accept()`, `run()`
- [x] 10.5 Wire interactive sessions into CLI adapter: run after clustering (grouping) or after glossary generation (glossary)

### TEST: Phase 10 Validation
- [x] 10.T1 Create `tests/test_interactive_sessions.py`
- [x] 10.T2 Test `InteractiveGroupingSession.rename_group()`: verify tree is updated
- [x] 10.T3 Test `InteractiveGroupingSession.move_component()`: verify component moved between groups
- [x] 10.T4 Test `InteractiveGroupingSession.merge_groups()`: verify groups combined
- [x] 10.T5 Test `InteractiveGroupingSession.save()`: verify JSON output format with metadata
- [x] 10.T6 Test `InteractiveGlossarySession.edit_entry()`: verify entry updated
- [x] 10.T7 Test `InteractiveGlossarySession.remove_entry()`: verify entry removed
- [x] 10.T8 **Run `pytest tests/test_interactive_sessions.py` AND `pytest tests/` -- ALL PASSED (19/19)**

## 11. Integration Testing (end-to-end)

Depends on: All phases complete

- [x] 11.1 Test backwards compatibility: `codewiki generate` without `--projection` produces output identical to current behavior (compare prompt strings, directory structure)
- [x] 11.2 Test business projection end-to-end: verify clustering prompt has grouping directive, agent prompts have business objectives, output in `docs/business/`
- [x] 11.3 Test saved grouping: `--interactive-grouping` followed by `--load-grouping` skips clustering
- [x] 11.4 Test glossary end-to-end: `--generate-glossary` produces `glossary.json` + `glossary.md`, glossary block in agent prompts
- [x] 11.5 Test sub-agent context propagation: complex module with sub-agents receives all projection context (code_context, framework_context, objectives, glossary)
- [x] 11.6 **Run `pytest tests/` -- FULL SUITE PASSED (161/161 tests)**

---

## Parallelization Notes

- Phases 1-2 are sequential (2 depends on 1)
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 1 only (can run in parallel with Phase 2-3 after Phase 1)
- Phase 5 depends on Phases 1, 2, 3
- Phases 6 and 7 can run in parallel after Phase 5
- Phase 8 depends on Phases 4, 5, 6, 7
- Phase 9 depends on Phase 8
- Phase 10 depends on Phase 9
- Phase 11 depends on all phases
