## ADDED Requirements

### Requirement: Projection-Aware Agent Orchestrator
The system SHALL accept an optional `projection: ProjectionConfig` parameter in `AgentOrchestrator.__init__()`. When provided, the orchestrator SHALL:
1. Call `compile_projection_instructions(projection)` to produce `CompiledProjectionPrompts`
2. Merge compiled `custom_instructions` with existing `config.get_prompt_addition()`
3. Store `glossary_block` and `supplementary_files` attributes (set later by pipeline)
4. Pass all compiled fields to `format_system_prompt()` / `format_leaf_system_prompt()` in `create_agent()`

Cross-reference: `projection-model` provides `ProjectionConfig` and `compile_projection_instructions()`; `prompt-parameterization` provides expanded format function signatures.

#### Scenario: Orchestrator with business projection
- **WHEN** `AgentOrchestrator(config, projection=get_business_projection())` is created
- **THEN** `self.compiled.objectives_override` is non-empty and `self.compiled.custom_instructions` contains "product managers"

#### Scenario: Orchestrator without projection
- **WHEN** `AgentOrchestrator(config)` is created (no projection)
- **THEN** behavior is identical to current: `custom_instructions` comes from `config.get_prompt_addition()` only

### Requirement: Extended CodeWikiDeps
The system SHALL add the following fields to `CodeWikiDeps` (`codewiki/src/be/agent_tools/deps.py`):
- `code_context: str = None`
- `framework_context: str = None`
- `objectives_override: str = None`
- `glossary_block: str = None`
- `supplementary_files: Dict[str, str] = field(default_factory=dict)`
- `projection_name: str = None`

These fields SHALL be populated by `AgentOrchestrator.process_module()` and read by `generate_sub_module_documentations.py` for sub-agent propagation.

#### Scenario: Deps populated with projection context
- **WHEN** `process_module()` is called with a NATURAL projection active
- **THEN** the `CodeWikiDeps` instance has `code_context` containing NATURAL provenance, `objectives_override` with reimplementation focus, and `projection_name="natural-transpiled"`

#### Scenario: Deps without projection
- **WHEN** `process_module()` is called without a projection
- **THEN** all new fields are `None` / empty (backwards compatible)

### Requirement: Projection-Aware Documentation Generator
The system SHALL accept an optional `projection: ProjectionConfig` parameter in `DocumentationGenerator.__init__()`. The generator SHALL:
1. Pass projection to `AgentOrchestrator`
2. Pass projection to `cluster_modules()`
3. Collect supplementary files when `projection.supplementary_file_patterns` is set
4. Run glossary generation when `"data_dictionary"` in `projection.output_artifacts`
5. Include projection info in `create_documentation_metadata()`

Cross-reference: `projection-clustering`, `supplementary-files`, `glossary-generation` for the respective features.

#### Scenario: Full pipeline with EJB projection
- **WHEN** `DocumentationGenerator(config, projection=get_ejb_migration_projection())` runs
- **THEN** clustering receives the projection, supplementary XML files are collected, and agent prompts contain framework context

#### Scenario: Pipeline without projection
- **WHEN** `DocumentationGenerator(config)` runs (no projection)
- **THEN** behavior is identical to current: no supplementary files, no glossary, default clustering

### Requirement: Backend Config Projection Field
The system SHALL add `projection: Optional[Dict[str, Any]] = None` to the backend `Config` class (`codewiki/src/config.py`) and a `from_cli()` constructor path for CLI integration.

#### Scenario: Config with projection
- **WHEN** `Config` is created with `projection=get_business_projection().__dict__`
- **THEN** the projection data is accessible and can be deserialized back to `ProjectionConfig`

#### Scenario: Config without projection
- **WHEN** `Config` is created without `projection` field
- **THEN** `config.projection` is `None` (backwards compatible)
