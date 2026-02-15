## ADDED Requirements

### Requirement: Glossary Entry Data Model
The system SHALL provide a `GlossaryEntry` dataclass in `codewiki/src/be/glossary_generator.py` with fields:
- `identifier: str` -- the code identifier
- `business_name: str` -- proposed business-friendly name
- `definition: str` -- one-sentence definition
- `category: str` -- e.g., "entity", "operation", "field", "constant"
- `confidence: float` -- LLM confidence (0.0 - 1.0)
- `source_files: List[str]` -- files where the identifier appears
- `component_ids: List[str]` -- component IDs containing the identifier

#### Scenario: Create glossary entry
- **WHEN** a `GlossaryEntry` is created with `identifier="WS_CUST_NM"`, `business_name="Customer Name"`, `confidence=0.9`
- **THEN** the entry is valid with all fields accessible

### Requirement: Glossary Data Model
The system SHALL provide a `Glossary` dataclass with:
- `entries: Dict[str, GlossaryEntry]` -- keyed by identifier
- `to_dict() -> Dict` -- JSON-serializable dict
- `from_dict(data: Dict) -> Glossary` -- classmethod deserializer
- `to_prompt_block(max_entries: int = 200) -> str` -- renders entries as a prompt-injectable string, sorted by confidence descending, capped at `max_entries`

#### Scenario: Glossary serialization round-trip
- **WHEN** a `Glossary` with 3 entries is serialized via `to_dict()` and deserialized via `from_dict()`
- **THEN** the deserialized glossary has identical entries

#### Scenario: Prompt block generation with cap
- **WHEN** `to_prompt_block(max_entries=2)` is called on a glossary with 5 entries
- **THEN** the returned string contains exactly the 2 highest-confidence entries

### Requirement: Identifier Extraction
The system SHALL provide `extract_identifiers(components: Dict[str, Node], leaf_nodes: List[str]) -> Dict[str, List[str]]` that extracts meaningful identifiers from `Node` objects using:
1. `Node.name` (class, function, method names)
2. `Node.parameters` (parameter names)
3. Field declarations from `Node.source_code` via regex (Java fields, NATURAL `WS_*` variables)

The function SHALL filter out generic identifiers (e.g., `i`, `j`, `get`, `set`, `main`, `toString`, `__init__`).

#### Scenario: Extract Java class and method names
- **WHEN** `extract_identifiers()` is called with components containing Java classes and methods
- **THEN** the returned dict maps each identifier to the list of component IDs where it appears, excluding generic names

#### Scenario: Extract NATURAL-style variable names
- **WHEN** components contain source code with `WS_CUST_NM`, `WS_ACCT_BAL` patterns
- **THEN** these identifiers are extracted and mapped to their source components

#### Scenario: Generic names filtered
- **WHEN** components contain methods named `get`, `set`, `toString`, `main`
- **THEN** these identifiers are NOT included in the extracted results

### Requirement: Glossary Generation via LLM
The system SHALL provide `generate_glossary(components, leaf_nodes, config, context: str = "", batch_size: int = 80) -> Glossary` that:
1. Extracts identifiers via `extract_identifiers()`
2. Batches identifiers (default 80 per batch) for LLM calls
3. Sends each batch with a `GLOSSARY_PROMPT` template requesting structured JSON responses within `<GLOSSARY_ENTRIES>` tags
4. Parses responses and assembles a complete `Glossary`
5. Uses the provenance `context` string to help the LLM understand naming conventions

#### Scenario: Generate glossary for NATURAL-transpiled code
- **WHEN** `generate_glossary()` is called with components from a NATURAL-transpiled system and `context="Code transpiled from NATURAL. WS_* = Working Storage variables."`
- **THEN** a `Glossary` is returned with entries mapping NATURAL-style identifiers to business terms

#### Scenario: Empty component set
- **WHEN** `generate_glossary()` is called with no components
- **THEN** an empty `Glossary` is returned

### Requirement: Glossary Output Artifacts
The system SHALL save glossary output as:
1. `glossary.json` -- structured, machine-readable JSON via `Glossary.to_dict()`
2. `glossary.md` -- human-readable Markdown table with columns: Identifier, Business Name, Definition, Category, Confidence

#### Scenario: Glossary files generated
- **WHEN** glossary generation completes with at least one entry
- **THEN** both `glossary.json` and `glossary.md` are written to the output directory

#### Scenario: Glossary Markdown format
- **WHEN** `glossary.md` is generated
- **THEN** it contains a Markdown table sorted by category then identifier

### Requirement: Glossary Pipeline Integration
The system SHALL integrate glossary generation into `DocumentationGenerator.run()`:
1. After clustering, before documentation generation
2. Only when `"data_dictionary"` is in `projection.output_artifacts`
3. OR when `projection.glossary_path` is set (load pre-existing glossary)
4. The glossary prompt block is set on `AgentOrchestrator.glossary_block` for injection into all agent system prompts

Cross-reference: `prompt-parameterization` provides the `{glossary}` template slot; `projection-pipeline` provides the `glossary_block` field on deps.

#### Scenario: Glossary generation enabled
- **WHEN** a projection with `output_artifacts=["documentation", "data_dictionary"]` is used
- **THEN** glossary generation runs between clustering and doc generation, and the glossary block appears in agent system prompts

#### Scenario: Load pre-existing glossary
- **WHEN** a projection with `glossary_path="/path/to/glossary.json"` is used
- **THEN** the glossary is loaded from the file instead of generated, and still injected into agent prompts

#### Scenario: No glossary configured
- **WHEN** a projection without `"data_dictionary"` in `output_artifacts` and no `glossary_path` is used
- **THEN** no glossary generation or loading occurs, and the `{glossary}` prompt slot is empty
