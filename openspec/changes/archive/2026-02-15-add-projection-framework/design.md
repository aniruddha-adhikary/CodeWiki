## Context

CodeWiki's pipeline is: Dependency Analysis -> Module Clustering -> Agent Documentation (leaf-first, bottom-up). Custom instructions currently flow through a single `{custom_instructions}` slot at the end of system prompts. Projections need to inject structured context (provenance, framework, objectives, glossary) at specific positions in the prompt hierarchy, and optionally add a glossary generation stage to the pipeline.

### Stakeholders
- Business analysts needing domain-concept documentation from legacy systems
- Product managers planning modernization of EJB / NATURAL / COBOL-transpiled systems
- Reimplementation engineers needing code provenance, glossaries, and framework context

### Constraints
- Must not break existing `codewiki generate` (no `--projection` = identical behavior)
- Must work with all existing LLM providers via LiteLLM
- Sub-agents must inherit all projection context (currently broken: `generate_sub_module_documentations.py` bypasses `format_system_prompt()`)

## Goals / Non-Goals

- **Goals:**
  - Configurable documentation views via `ProjectionConfig` data model
  - Prompt parameterization with separate slots for code context, framework context, objectives, and glossary
  - Glossary/data dictionary as a pipeline stage with structured JSON output
  - Supplementary file (XML, YAML) injection into agent prompts
  - CLI integration with built-in and custom projections
  - Interactive grouping and glossary refinement sessions

- **Non-Goals:**
  - Web frontend projection UI (CLI-only for v1)
  - Automatic projection detection (user must specify `--projection`)
  - Multi-projection generation in a single run
  - Streaming/incremental glossary updates

## Decisions

### 1. Separate prompt slots instead of overloading `{custom_instructions}`

**Decision:** Add `{code_context}`, `{framework_context}`, `{objectives}`, `{glossary}` as distinct template variables in `SYSTEM_PROMPT` and `LEAF_SYSTEM_PROMPT`.

**Why:** Each block has a different position in the prompt hierarchy. Provenance/framework context must come before objectives so the LLM understands *what the code is* before *what to do with it*. Mixing everything into `{custom_instructions}` loses this ordering control.

**Alternatives considered:**
- Single `{custom_instructions}` injection: Simpler but loses prompt ordering; projection-specific blocks would compete with user's own custom instructions.
- Separate system prompt templates per projection: Too much duplication; hard to maintain.

### 2. Prompt ordering: context before directives

**Decision:** `<CODE_CONTEXT>` -> `<FRAMEWORK_CONTEXT>` -> `<OBJECTIVES>` -> `<GLOSSARY>` -> `<DOCUMENTATION_STRUCTURE>` -> `<WORKFLOW>` -> `<AVAILABLE_TOOLS>` -> `<CUSTOM_INSTRUCTIONS>`

**Why:** LLMs benefit from receiving background context before task instructions. This mirrors how a human would brief someone: "Here's what you're looking at" before "Here's what I need you to do."

### 3. Supplementary files in user prompt, not system prompt

**Decision:** XML/YAML configs are injected via `format_user_prompt()` in a `<SUPPLEMENTARY_CONFIGURATION>` block, not in the system prompt.

**Why:** Supplementary files are per-module content (different files relevant to different modules), not global instructions. They belong alongside code in the user prompt.

### 4. Glossary as a pipeline stage, not a prompt hack

**Decision:** Glossary generation runs between clustering and documentation as a separate LLM-powered stage. It produces structured JSON that feeds back into all agent prompts as a `<GLOSSARY>` block.

**Why:** The glossary needs to see all identifiers across the codebase before any documentation is generated. Running it inline per-module would miss cross-cutting terms and produce inconsistent naming.

### 5. `CompiledProjectionPrompts` as intermediate representation

**Decision:** `compile_projection_instructions(projection) -> CompiledProjectionPrompts` produces a structured object with separate string fields for each prompt slot, rather than a single string.

**Why:** Different consumers need different fields. The orchestrator passes all fields to `format_system_prompt()`, while `format_user_prompt()` only needs supplementary files. A single string would require re-parsing.

### 6. Saved grouping = complete module_tree dict

**Decision:** When a user saves an interactive grouping session, the entire `module_tree` dict is persisted as JSON. On re-run with `--load-grouping`, the clustering LLM call is skipped entirely.

**Why:** Deterministic and fast. No need to re-interpret partial edits against a potentially different set of components.

### 7. Sub-agent fix is a prerequisite

**Decision:** Fix `generate_sub_module_documentations.py` lines 54 and 62 to use `format_system_prompt()` / `format_leaf_system_prompt()` instead of raw `.format()` BEFORE adding any new template variables.

**Why:** Without this fix, any new template variable (`{objectives}`, `{code_context}`, etc.) would cause a `KeyError` in sub-agents. This is a critical correctness issue, not an enhancement.

## Risks / Trade-offs

- **Prompt length:** Adding `<CODE_CONTEXT>`, `<FRAMEWORK_CONTEXT>`, `<GLOSSARY>` blocks increases system prompt size. Mitigation: each block is only included when non-empty; glossary is capped at 200 entries via `to_prompt_block(max_entries=200)`.
- **Glossary accuracy:** LLM-generated business terms may be wrong. Mitigation: confidence scores, interactive review session, `--load-glossary` for curated glossaries.
- **Supplementary file size:** XML configs can be large. Mitigation: 50KB per-file cap with truncation; filtered to same directory subtree as module.

## Migration Plan

No migration needed. Feature is additive:
- Without `--projection`: identical behavior (DEFAULT_OBJECTIVES used, no extra blocks, flat output dir)
- With `--projection`: new behavior in subdirectory

## Open Questions

None remaining after stress test. All P0 items are fully designed.
