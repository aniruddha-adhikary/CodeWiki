# Project Context

## Purpose

CodeWiki is an AI-powered documentation generation framework that transforms large codebases (86K–1.4M LOC) into comprehensive, architecture-aware documentation. It uses hierarchical decomposition with dynamic programming-inspired algorithms and recursive multi-agent processing to analyze code structure, dependencies, and relationships, then produces rich Markdown documentation with Mermaid diagrams.

## Tech Stack

- **Language:** Python 3.12+
- **CLI framework:** Click
- **AST parsing:** tree-sitter (with language-specific grammars for Python, Java, JavaScript, TypeScript, C, C++, C#, PHP)
- **Graph analysis:** NetworkX (dependency graphs, topological sorting, cycle resolution)
- **LLM integration:** LiteLLM (OpenAI-compatible SDK layer), pydantic-ai (agent orchestration)
- **Data validation:** Pydantic v2, pydantic-settings
- **Web frontend:** FastAPI
- **Templating:** Jinja2
- **Diagram validation:** mermaid-py, mermaid-parser-py (requires Node.js >=14)
- **Config/secrets:** keyring (system keychain), python-dotenv
- **Terminal output:** Rich
- **Git integration:** GitPython
- **Build system:** setuptools + wheel

## Project Conventions

### Code Style

- **Formatter:** Black with line length 100, target Python 3.12
- **Linter:** Ruff with line length 100, target Python 3.12
- **Type checker:** mypy (Python 3.12, `warn_return_any` and `warn_unused_configs` enabled; untyped defs currently allowed)
- **Entry point:** `codewiki.cli.main:cli`
- **Package layout:** Explicit package list in `pyproject.toml` under `[tool.setuptools]`

### Architecture Patterns

The system follows a three-layer architecture: **CLI → Backend → Frontend**.

1. **CLI Layer** (`codewiki/cli/`) — Click-based with `config` and `generate` command groups. The `AgentInstructions` dataclass flows from CLI options through the entire pipeline.
2. **Backend** (`codewiki/src/be/`) — Three-stage pipeline:
   - **Dependency Analyzer** — Tree-sitter AST parsing with per-language analyzers (each extends `BaseAnalyzer`), builds dependency graphs via NetworkX
   - **Module Clustering** — Hierarchical decomposition with configurable token thresholds and depth
   - **Agent Orchestrator** — Recursive bottom-up documentation agent via pydantic-ai with tool-based code reading, sub-module delegation, and doc editing
3. **Frontend** (`codewiki/src/fe/`) — FastAPI app for documentation viewing with GitHub integration, async background processing, and caching

**Key patterns:**
- Strategy pattern for language analyzers (one class per language, all extend `BaseAnalyzer`)
- Recursive agent delegation for complex modules
- Dataclass-driven configuration flowing through all layers
- LiteLLM abstraction for multi-provider LLM support with fallback models

### Testing Strategy

- **Framework:** pytest with pytest-asyncio for async tests
- **Coverage:** pytest-cov enabled by default in `pyproject.toml` (`addopts = "-v --cov=codewiki --cov-report=term-missing"`)
- **Test location:** `tests/` directory
- **Conventions:** Files named `test_*.py`, classes named `Test*`, functions named `test_*`

### Git Workflow

- **Main branch:** `main`
- **Branch naming:** Feature branches use `feat/<description>` prefix (e.g., `feat/config-maxtokens`, `feat/custom-instruction`)
- **Merge strategy:** Pull requests merged into `main`
- **Commit style:** Lowercase, imperative-ish descriptions (e.g., "make max depth configurable", "fix minor", "init custom instruction feature")
- **Hosting:** GitHub at `FSoft-AI4Code/CodeWiki`

## Domain Context

- **Token budgets** are central to the system — `max_tokens` (LLM context), `max_token_per_module`, and `max_token_per_leaf_module` control how code is partitioned for the LLM agents
- **Module tree** is the hierarchical decomposition of a repository; leaf modules are small enough for direct LLM processing, while complex modules are recursively delegated to sub-agents
- **Dependency graphs** are directed graphs where nodes are source files and edges represent import/include relationships; cycles are resolved before topological sorting
- Adding a new language requires: creating an analyzer extending `BaseAnalyzer`, registering it in `ast_parser.py`, adding file extensions, and adding tests

## Important Constraints

- Requires Python 3.12+
- Node.js >=14 is required at runtime for mermaid-py diagram validation
- API keys for LLM providers are stored in the system keychain via `keyring`
- MIT licensed
- Currently in Beta status (Development Status 4)

## External Dependencies

- **LLM providers:** Any OpenAI-compatible API via LiteLLM (OpenAI, Anthropic, local models, etc.)
- **GitHub API:** Used by the frontend for repository integration (`github_processor.py`)
- **System keychain:** API key storage via `keyring`
- **Tree-sitter grammars:** Pre-built language grammars for 8 supported languages
