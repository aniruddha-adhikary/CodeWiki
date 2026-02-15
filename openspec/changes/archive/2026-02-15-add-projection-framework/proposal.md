# Change: Add Projection Framework for Multi-Audience Documentation Views

## Why

CodeWiki currently generates one fixed documentation view per codebase -- a developer-oriented view grouped by code structure. Real-world users need different views for different audiences: business analysts want to see business capabilities, product managers want domain concepts, and reimplementation engineers working on legacy modernization need code provenance context, framework conventions, and glossaries to translate transpiled identifiers into business terms.

Stress-testing the original plan against two legacy modernization scenarios (NATURAL-transpiled-to-Java, EJB student records) crossed with three personas (BA, PM, engineers) revealed 4 critical gaps (P0) that would cause projections to produce wrong or misleading output without:
1. **Code provenance + framework context** -- transpiled code and framework boilerplate need explicit context
2. **Supplementary file processing** -- XML configs (ejb-jar.xml, etc.) are invisible because `CODE_EXTENSIONS` excludes `.xml`
3. **Glossary / data dictionary** -- most-requested artifact for legacy modernization
4. **Parameterizable OBJECTIVES block** -- hardcoded objectives contradict non-developer projection goals

## What Changes

- **New `ProjectionConfig` data model** with built-in projections (developer, business, ejb-migration, natural-transpiled), JSON serialization, and resolver
- **Parameterizable prompt templates** -- replace hardcoded `<OBJECTIVES>` with `{objectives}` template variable; add `{code_context}`, `{framework_context}`, `{glossary}` slots
- **Fix sub-agent prompt bypass** -- `generate_sub_module_documentations.py:54,62` uses raw `.format()` instead of `format_system_prompt()`, breaking any new template variables (**BREAKING** for sub-agent prompt propagation)
- **Projection-aware clustering** -- `clustering_goal` directive injected into cluster prompt; saved grouping bypass skips LLM call
- **Supplementary file processing** -- collect XML/YAML configs matching projection patterns, inject into agent user prompts
- **Glossary generation** -- new pipeline stage extracting identifiers from `Node` objects, batching to LLM for business-term proposals, outputting `glossary.json` + `glossary.md`
- **Pipeline threading** -- `ProjectionConfig` flows through `DocumentationGenerator` -> `AgentOrchestrator` -> `CodeWikiDeps` -> sub-agents
- **CLI integration** -- `--projection`, `--load-grouping`, `--interactive-grouping`, `--generate-glossary`, `--load-glossary` options; projection-based output subdirectories
- **Interactive sessions** -- CLI-only grouping and glossary review/edit before doc generation

## Impact

- Affected specs: projection-model, prompt-parameterization, projection-clustering, supplementary-files, glossary-generation, projection-pipeline, projection-cli (all new)
- Affected code:
  - `codewiki/src/be/projection.py` (NEW)
  - `codewiki/src/be/glossary_generator.py` (NEW)
  - `codewiki/cli/interactive_grouping.py` (NEW)
  - `codewiki/cli/interactive_glossary.py` (NEW)
  - `codewiki/src/be/prompt_template.py` (MODIFY)
  - `codewiki/src/be/agent_orchestrator.py` (MODIFY)
  - `codewiki/src/be/agent_tools/deps.py` (MODIFY)
  - `codewiki/src/be/agent_tools/generate_sub_module_documentations.py` (MODIFY -- critical fix)
  - `codewiki/src/be/cluster_modules.py` (MODIFY)
  - `codewiki/src/be/documentation_generator.py` (MODIFY)
  - `codewiki/src/config.py` (MODIFY)
  - `codewiki/cli/commands/generate.py` (MODIFY)
  - `codewiki/cli/adapters/doc_generator.py` (MODIFY)
  - `codewiki/cli/models/config.py` (MODIFY)
- Backwards compatibility: Running without `--projection` produces identical output to current behavior
