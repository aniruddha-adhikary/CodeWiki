# prompt-parameterization Specification

## Purpose
TBD - created by archiving change add-projection-framework. Update Purpose after archive.
## Requirements
### Requirement: Parameterizable Objectives Block
The system SHALL replace the hardcoded `<OBJECTIVES>` content in both `SYSTEM_PROMPT` and `LEAF_SYSTEM_PROMPT` (`codewiki/src/be/prompt_template.py`) with a `{objectives}` template variable. A `DEFAULT_OBJECTIVES` constant SHALL preserve the current hardcoded text for backwards compatibility.

#### Scenario: Default objectives when no projection
- **WHEN** `format_system_prompt()` is called without an `objectives` parameter (or with `None`)
- **THEN** the rendered prompt contains the current hardcoded objectives text ("helps developers and maintainers understand")

#### Scenario: Custom objectives from projection
- **WHEN** `format_system_prompt(objectives="Help business stakeholders understand business capabilities")` is called
- **THEN** the rendered prompt's `<OBJECTIVES>` block contains "business stakeholders" instead of the default text

### Requirement: Code Context Prompt Slot
The system SHALL add a `{code_context}` template variable to `SYSTEM_PROMPT` and `LEAF_SYSTEM_PROMPT`, positioned after `<ROLE>` and before `<OBJECTIVES>`. When non-empty, it SHALL be wrapped in `<CODE_CONTEXT>...</CODE_CONTEXT>` tags.

#### Scenario: No code context
- **WHEN** `format_system_prompt(code_context=None)` is called
- **THEN** the rendered prompt contains no `<CODE_CONTEXT>` block

#### Scenario: NATURAL provenance code context
- **WHEN** `format_system_prompt(code_context="This code was transpiled from NATURAL...")` is called
- **THEN** the rendered prompt contains `<CODE_CONTEXT>This code was transpiled from NATURAL...</CODE_CONTEXT>` between `<ROLE>` and `<OBJECTIVES>`

### Requirement: Framework Context Prompt Slot
The system SHALL add a `{framework_context}` template variable to `SYSTEM_PROMPT` and `LEAF_SYSTEM_PROMPT`, positioned after `{code_context}` and before `<OBJECTIVES>`. When non-empty, it SHALL be wrapped in `<FRAMEWORK_CONTEXT>...</FRAMEWORK_CONTEXT>` tags.

#### Scenario: EJB framework context
- **WHEN** `format_system_prompt(framework_context="EJB Entity Beans represent...")` is called
- **THEN** the rendered prompt contains `<FRAMEWORK_CONTEXT>EJB Entity Beans represent...</FRAMEWORK_CONTEXT>`

### Requirement: Glossary Prompt Slot
The system SHALL add a `{glossary}` template variable to `SYSTEM_PROMPT` and `LEAF_SYSTEM_PROMPT`, positioned after `<OBJECTIVES>` and before `<DOCUMENTATION_STRUCTURE>`. When non-empty, it SHALL be wrapped in `<GLOSSARY>...</GLOSSARY>` tags.

#### Scenario: Glossary block injected
- **WHEN** `format_system_prompt(glossary="WS_CUST_NM -> Customer Name\nWS_ACCT_BAL -> Account Balance")` is called
- **THEN** the rendered prompt contains a `<GLOSSARY>` block with both mappings

### Requirement: Expanded Format Function Signatures
The system SHALL expand `format_system_prompt()` and `format_leaf_system_prompt()` to accept:
- `module_name: str`
- `custom_instructions: str = None`
- `code_context: str = None`
- `framework_context: str = None`
- `objectives: str = None`
- `glossary: str = None`

#### Scenario: All parameters provided
- **WHEN** `format_system_prompt()` is called with all parameters non-empty
- **THEN** the rendered prompt contains all blocks in order: `<ROLE>`, `<CODE_CONTEXT>`, `<FRAMEWORK_CONTEXT>`, `<OBJECTIVES>`, `<GLOSSARY>`, `<DOCUMENTATION_STRUCTURE>`, `<WORKFLOW>`, `<AVAILABLE_TOOLS>`, `<CUSTOM_INSTRUCTIONS>`

#### Scenario: Backwards compatible call
- **WHEN** `format_system_prompt(module_name="test", custom_instructions="focus on APIs")` is called (existing 2-arg pattern)
- **THEN** the rendered prompt is functionally identical to the current behavior with no new blocks

### Requirement: Sub-Agent Prompt Fix
The system SHALL replace raw `.format()` calls in `codewiki/src/be/agent_tools/generate_sub_module_documentations.py` (lines 54 and 62) with `format_system_prompt()` and `format_leaf_system_prompt()` respectively, passing all projection context fields from `ctx.deps`.

Cross-reference: Depends on `projection-pipeline` for `CodeWikiDeps` field additions.

#### Scenario: Sub-agent receives projection context
- **WHEN** a complex module delegates to a sub-agent AND a projection with `objectives_override` is active
- **THEN** the sub-agent's system prompt contains the custom objectives, not the default text

#### Scenario: Sub-agent without projection
- **WHEN** a complex module delegates to a sub-agent without any projection
- **THEN** the sub-agent's system prompt uses `DEFAULT_OBJECTIVES` and has no `<CODE_CONTEXT>` or `<FRAMEWORK_CONTEXT>` blocks

### Requirement: Supplementary File Prompt Injection
The system SHALL add `supplementary_files: Dict[str, str]` and `supplementary_file_role: str` parameters to `format_user_prompt()`. When `supplementary_files` is non-empty, a `<SUPPLEMENTARY_CONFIGURATION>` block SHALL be appended after `<CORE_COMPONENT_CODES>` in the user prompt.

Cross-reference: `supplementary-files` capability provides the data; this requirement handles prompt injection.

#### Scenario: EJB XML config in user prompt
- **WHEN** `format_user_prompt(supplementary_files={"ejb-jar.xml": "<ejb-jar>...</ejb-jar>"}, supplementary_file_role="EJB deployment descriptors")` is called
- **THEN** the user prompt contains a `<SUPPLEMENTARY_CONFIGURATION>` block with the XML content and role description

#### Scenario: No supplementary files
- **WHEN** `format_user_prompt()` is called without `supplementary_files` (or with empty dict)
- **THEN** the user prompt contains no `<SUPPLEMENTARY_CONFIGURATION>` block

### Requirement: Extended Language Mapping
The system SHALL add `.xml`, `.yaml`, `.yml`, and `.properties` to `EXTENSION_TO_LANGUAGE` in `prompt_template.py`.

#### Scenario: XML file language detection
- **WHEN** a file with `.xml` extension is processed by `format_user_prompt()`
- **THEN** it is recognized as language `"xml"` for code block formatting

