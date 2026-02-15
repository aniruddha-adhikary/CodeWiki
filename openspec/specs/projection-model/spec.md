# projection-model Specification

## Purpose
TBD - created by archiving change add-projection-framework. Update Purpose after archive.
## Requirements
### Requirement: Projection Configuration Data Model
The system SHALL provide a `ProjectionConfig` dataclass in `codewiki/src/be/projection.py` that defines a documentation projection with the following fields:
- `name: str` -- projection identifier (e.g., "developer", "business")
- `description: str` -- human-readable description
- `clustering_goal: str` -- injected into clustering prompt (empty = use defaults)
- `clustering_examples: str` -- example groupings to guide LLM
- `audience: str` -- target audience (e.g., "product managers", "developers")
- `perspective: str` -- documentation perspective (e.g., "business capabilities", "code structure")
- `doc_objectives: List[str]` -- what to focus on
- `doc_anti_objectives: List[str]` -- what to skip
- `detail_level: str` -- "minimal" | "standard" | "detailed"
- `max_depth_override: Optional[int]` -- overrides config max_depth
- `saved_grouping: Optional[Dict]` -- pre-approved module_tree (skips clustering)
- `objectives_override: Optional[str]` -- replaces default `<OBJECTIVES>` block
- `code_provenance: Optional[CodeProvenance]` -- origin of non-standard source code
- `framework_context: Optional[str]` -- multi-paragraph framework description
- `supplementary_file_patterns: Optional[List[str]]` -- glob patterns for config files
- `supplementary_file_role: Optional[str]` -- describes the role of supplementary files
- `output_artifacts: List[str]` -- defaults to `["documentation"]`; may include `"data_dictionary"`
- `glossary_path: Optional[str]` -- path to load pre-existing glossary JSON

#### Scenario: Create a business projection config
- **WHEN** `get_business_projection()` is called
- **THEN** a `ProjectionConfig` is returned with `audience="product managers and business analysts"`, `perspective="business capabilities"`, non-empty `clustering_goal` and `objectives_override`, and `detail_level="standard"`

#### Scenario: Create a developer projection config
- **WHEN** `get_developer_projection()` is called
- **THEN** a `ProjectionConfig` is returned with empty `clustering_goal`, empty `objectives_override` (uses default), `audience="developers"`, and `perspective="code structure"`

### Requirement: Code Provenance Data Model
The system SHALL provide a `CodeProvenance` dataclass with:
- `source_language: Optional[str]` -- original language (e.g., "NATURAL", "COBOL")
- `transpilation_tool: Optional[str]` -- tool used for transpilation
- `naming_conventions: Dict[str, str]` -- maps code patterns to their meaning (e.g., `{"PRFM_NNNN()": "PERFORM paragraph -- subroutine call"}`)
- `runtime_library_packages: List[str]` -- packages to downweight in docs
- `known_boilerplate_patterns: List[str]` -- patterns to identify boilerplate

#### Scenario: NATURAL-transpiled code provenance
- **WHEN** a `CodeProvenance` is created with `source_language="NATURAL"` and `naming_conventions={"WS_*": "Working Storage variable", "MOVE_TO(a,b)": "Assignment"}`
- **THEN** the provenance is valid and `naming_conventions` contains both entries

### Requirement: Built-in Projection Factories
The system SHALL provide factory functions for at least 4 built-in projections:
- `get_developer_projection()` -- backwards-compatible defaults
- `get_business_projection()` -- business capability grouping, non-technical audience
- `get_ejb_migration_projection()` -- EJB framework context, supplementary XML patterns, migration-focused objectives
- `get_natural_transpiled_projection()` -- NATURAL code provenance, data dictionary output artifact

#### Scenario: EJB migration projection includes supplementary patterns
- **WHEN** `get_ejb_migration_projection()` is called
- **THEN** the returned config has `supplementary_file_patterns` containing `"**/ejb-jar.xml"` and `framework_context` containing EJB convention descriptions

#### Scenario: NATURAL projection enables data dictionary
- **WHEN** `get_natural_transpiled_projection()` is called
- **THEN** the returned config has `"data_dictionary"` in `output_artifacts` and `code_provenance.source_language == "NATURAL"`

### Requirement: Projection Resolver
The system SHALL provide `resolve_projection(name_or_path: str) -> ProjectionConfig` that resolves:
1. Built-in names ("developer", "business", "ejb-migration", "natural-transpiled") to factory functions
2. File paths ending in `.json` to deserialized `ProjectionConfig` from JSON
3. Paths matching `.codewiki/projections/{name}.json` for project-local custom projections

#### Scenario: Resolve built-in name
- **WHEN** `resolve_projection("business")` is called
- **THEN** the result equals `get_business_projection()`

#### Scenario: Resolve JSON file path
- **WHEN** `resolve_projection("/path/to/custom.json")` is called with a valid JSON file containing `ProjectionConfig` fields
- **THEN** a `ProjectionConfig` is returned with fields matching the JSON content

#### Scenario: Unknown name without JSON extension
- **WHEN** `resolve_projection("nonexistent")` is called
- **THEN** a `ValueError` is raised with a message listing available built-in projections

### Requirement: Projection Serialization
The system SHALL support JSON serialization and deserialization of `ProjectionConfig` including nested `CodeProvenance`.

#### Scenario: Round-trip serialization
- **WHEN** a `ProjectionConfig` with `code_provenance` is serialized to JSON and deserialized back
- **THEN** the deserialized config equals the original

### Requirement: Compiled Projection Prompts
The system SHALL provide `compile_projection_instructions(projection: ProjectionConfig) -> CompiledProjectionPrompts` that produces a `CompiledProjectionPrompts` dataclass with:
- `code_context_block: str` -- formatted `<CODE_CONTEXT>` block from provenance (empty if no provenance)
- `framework_context_block: str` -- formatted `<FRAMEWORK_CONTEXT>` block (empty if no framework_context)
- `objectives_override: Optional[str]` -- replaces `<OBJECTIVES>` content if set
- `custom_instructions: str` -- audience/perspective/doc_objectives formatted for `{custom_instructions}` slot
- `glossary_block: str` -- initially empty, set later by pipeline

#### Scenario: Compile business projection
- **WHEN** `compile_projection_instructions(get_business_projection())` is called
- **THEN** the result has non-empty `objectives_override`, non-empty `custom_instructions` containing "product managers", and empty `code_context_block`

#### Scenario: Compile NATURAL projection with provenance
- **WHEN** `compile_projection_instructions(get_natural_transpiled_projection())` is called
- **THEN** the result has non-empty `code_context_block` containing "NATURAL" and "Working Storage"

