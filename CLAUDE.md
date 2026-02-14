<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeWiki is an AI-powered documentation generation framework that transforms large codebases (86K-1.4M LOC) into comprehensive, architecture-aware documentation. It uses hierarchical decomposition with dynamic programming-inspired algorithms and recursive multi-agent processing. Supports Python, Java, JavaScript, TypeScript, C, C++, C#, and PHP.

## Build & Development Commands

```bash
# Install in development mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (includes coverage by default via pyproject.toml addopts)
pytest

# Run a single test file
pytest tests/test_dependency_analyzer.py

# Run with explicit coverage
pytest --cov=codewiki tests/

# Formatting
black --line-length 100 codewiki/

# Linting
ruff check codewiki/

# Type checking
mypy codewiki/
```

## Code Style

- Python 3.12+, line length 100 (Black + Ruff)
- Entry point: `codewiki.cli.main:cli` (Click CLI)

## Architecture

The system has three layers: **CLI**, **Backend (BE)**, and **Frontend (FE)**.

### CLI Layer (`codewiki/cli/`)

Click-based CLI with two command groups: `config` (API/agent settings) and `generate` (doc generation). Configuration persists to `~/.codewiki/config.json`; API keys stored in system keychain via `keyring`.

- `commands/config.py` — config set/show/validate/agent subcommands
- `commands/generate.py` — generation with include/exclude/focus/doc-type/instructions options
- `models/config.py` — `AgentInstructions` dataclass that flows through the entire system
- `adapters/doc_generator.py` — bridges CLI to backend `DocumentationGenerator`

### Backend (`codewiki/src/be/`)

Three-stage pipeline: **Dependency Analysis → Module Clustering → Agent Processing**.

1. **Dependency Analyzer** (`dependency_analyzer/`) — Tree-sitter AST parsing with per-language analyzers in `analyzers/` (one file per language, all extend `BaseAnalyzer`). Builds dependency graphs via `networkx`, performs topological sorting with cycle resolution.

2. **Module Clustering** (`cluster_modules.py`) — Hierarchical decomposition partitions the repo into a module tree. Token thresholds (`max_token_per_module`, `max_token_per_leaf_module`) and `max_depth` control granularity.

3. **Agent Orchestrator** (`agent_orchestrator.py`) — Recursive documentation agent built on `pydantic-ai`. Processes modules bottom-up; delegates complex modules to sub-agents. Agent tools in `agent_tools/` provide code reading, sub-module doc generation, dependency traversal, and doc editing.

- `llm_services.py` — OpenAI-compatible SDK layer via `litellm` with fallback model support
- `prompt_template.py` — System prompts with custom instruction injection; different prompts for leaf vs. complex modules
- `documentation_generator.py` — Orchestrates the full pipeline
- `config.py` — Backend `Config` class with all LLM/token/path settings

### Frontend (`codewiki/src/fe/`)

FastAPI web application for documentation viewing. `github_processor.py` handles GitHub integration, `visualise_docs.py` renders docs, `background_worker.py` manages async processing, `cache_manager.py` handles caching.

### Data Flow for AgentInstructions

CLI options → `AgentInstructions` dataclass → backend `Config.agent_instructions` dict → dependency analyzer (file filtering via `include_patterns`/`exclude_patterns`) + agent orchestrator (prompt injection via `custom_instructions`).

## Adding a New Language

1. Create analyzer in `codewiki/src/be/dependency_analyzer/analyzers/` extending `BaseAnalyzer`
2. Register it in `dependency_analyzer/ast_parser.py` `LANGUAGE_ANALYZERS` dict
3. Add file extensions in configuration
4. Add tests

## Key Configuration Defaults

| Setting | Default |
|---------|---------|
| `max_tokens` | 32768 |
| `max_token_per_module` | 36369 |
| `max_token_per_leaf_module` | 16000 |
| `max_depth` | 2 |

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must start with a type prefix:

- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — maintenance, config, tooling, dependencies
- `refactor:` — code restructuring with no behavior change
- `docs:` — documentation only
- `test:` — adding or updating tests
- `ci:` — CI/CD changes
- `style:` — formatting, whitespace (no logic change)
- `perf:` — performance improvement

Use an optional scope in parentheses: `feat(cli): add --verbose flag`. Keep the subject line under 72 characters, lowercase, imperative mood, no trailing period.
