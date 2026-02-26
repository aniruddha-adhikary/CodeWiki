<h1 align="center">CodeWiki: Evaluating AI's Ability to Generate Holistic Documentation for Large-Scale Codebases</h1>

<p align="center">
  <strong>AI-Powered Repository Documentation Generation</strong> • <strong>Multi-Language Support</strong> • <strong>Architecture-Aware Analysis</strong>
</p>

<p align="center">
  Generate holistic, structured documentation for large-scale codebases • Cross-module interactions • Visual artifacts and diagrams
</p>

<p align="center">
  <a href="https://python.org/"><img alt="Python version" src="https://img.shields.io/badge/python-3.12+-blue?style=flat-square" /></a>
  <a href="./LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" /></a>
  <a href="https://github.com/aniruddha-adhikary/CodeWiki/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/aniruddha-adhikary/CodeWiki?style=flat-square" /></a>
  <a href="https://arxiv.org/abs/2510.24428"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2510.24428-b31b1b?style=flat-square" /></a>
</p>

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a> •
  <a href="#cli-commands"><strong>CLI Commands</strong></a> •
  <a href="#projection-framework"><strong>Projections</strong></a> •
  <a href="#documentation-output"><strong>Output Structure</strong></a> •
  <a href="https://arxiv.org/abs/2510.24428"><strong>Paper</strong></a>
</p>

<p align="center">
  <img src="./img/framework-overview.png" alt="CodeWiki Framework" width="600" style="border: 2px solid #e1e4e8; border-radius: 12px; padding: 20px;"/>
</p>

---

## Quick Start

### 1. Install CodeWiki

```bash
# Install from source
pip install git+https://github.com/aniruddha-adhikary/CodeWiki.git

# Verify installation
codewiki --version
```

### 2. Configure Your Environment

CodeWiki supports multiple models via an OpenAI-compatible SDK layer.

```bash
codewiki config set \
  --api-key YOUR_API_KEY \
  --base-url https://api.anthropic.com \
  --main-model claude-sonnet-4 \
  --cluster-model claude-sonnet-4 \
  --fallback-model glm-4p5
```

### 3. Generate Documentation

```bash
# Navigate to your project
cd /path/to/your/project

# Generate documentation
codewiki generate

# Generate with HTML viewer for GitHub Pages
codewiki generate --github-pages --create-branch
```

**That's it!** Your documentation will be generated in `./docs/` with comprehensive repository-level analysis.

### Usage Example

![CLI Usage Example](https://github.com/FSoft-AI4Code/CodeWiki/releases/download/assets/cli-usage-example.gif)

---

## What is CodeWiki?

CodeWiki is an open-source framework for **automated repository-level documentation** across seven programming languages. It generates holistic, architecture-aware documentation that captures not only individual functions but also their cross-file, cross-module, and system-level interactions.

### Key Innovations

| Innovation | Description | Impact |
|------------|-------------|--------|
| **Hierarchical Decomposition** | Dynamic programming-inspired strategy that preserves architectural context | Handles codebases of arbitrary size (86K-1.4M LOC tested) |
| **Recursive Agentic System** | Adaptive multi-agent processing with dynamic delegation capabilities | Maintains quality while scaling to repository-level scope |
| **Multi-Modal Synthesis** | Generates textual documentation, architecture diagrams, data flows, and sequence diagrams | Comprehensive understanding from multiple perspectives |

### Supported Languages

**🐍 Python** • **☕ Java** • **🟨 JavaScript** • **🔷 TypeScript** • **⚙️ C** • **🔧 C++** • **🪟 C#**

---

## CLI Commands

### Configuration Management

```bash
# Set up your API configuration
codewiki config set \
  --api-key <your-api-key> \
  --base-url <provider-url> \
  --main-model <model-name> \
  --cluster-model <model-name> \
  --fallback-model <model-name>

# Configure max token settings
codewiki config set --max-tokens 32768 --max-token-per-module 36369 --max-token-per-leaf-module 16000

# Configure max depth for hierarchical decomposition
codewiki config set --max-depth 3

# Show current configuration
codewiki config show

# Validate your configuration
codewiki config validate
```

### Documentation Generation

```bash
# Basic generation
codewiki generate

# Custom output directory
codewiki generate --output ./documentation

# Create git branch for documentation
codewiki generate --create-branch

# Generate HTML viewer for GitHub Pages
codewiki generate --github-pages

# Enable verbose logging
codewiki generate --verbose

# Full-featured generation
codewiki generate --create-branch --github-pages --verbose
```

### Customization Options

CodeWiki supports customization for language-specific projects and documentation styles:

```bash
# C# project: only analyze .cs files, exclude test directories
codewiki generate --include "*.cs" --exclude "Tests,Specs,*.test.cs"

# Focus on specific modules with architecture-style docs
codewiki generate --focus "src/core,src/api" --doc-type architecture

# Add custom instructions for the AI agent
codewiki generate --instructions "Focus on public APIs and include usage examples"
```

### Projection Framework

Projections let you generate different documentation views for different audiences from the same codebase. A projection is a JSON file that controls how modules are grouped, what the documentation focuses on, and what level of technical detail is included — without changing the underlying dependency graph or analysis pipeline.

```bash
codewiki generate --projection ./my-projection.json
```

The JSON is validated before generation starts. If the file is missing, malformed, or has invalid field types, you get a specific error message immediately.

When a projection is used, output goes into a subdirectory named after the projection (e.g. `docs/business/`), so you can generate multiple views side by side from the same codebase.

#### How Projections Affect the Pipeline

Projections steer three stages of the generation pipeline:

```
Projection JSON
  │
  ├─ Clustering ──── clustering_goal → injected into the LLM clustering prompt
  │                  saved_grouping  → bypasses the clustering LLM call entirely
  │
  ├─ Agent Prompts ─ audience, perspective, detail_level, doc_objectives,
  │                  doc_anti_objectives → compiled into <CUSTOM_INSTRUCTIONS>
  │                  objectives_override → replaces the default <OBJECTIVES> block
  │                  framework_context   → injected as <FRAMEWORK_CONTEXT>
  │                  code_provenance     → injected as <CODE_CONTEXT>
  │                  glossary            → injected as glossary block
  │
  └─ File Collection  supplementary_file_patterns → config/XML files read and
                      supplementary_file_role       passed alongside source code
```

Everything else — dependency graph construction, AST parsing, topological sorting, the documentation structure template, the agent workflow, and the repo/module overview prompts — remains unchanged regardless of the projection.

#### Projection JSON Format

Only `name` is required. All other fields are optional and fall back to sensible defaults.

```json
{
  "name": "my-projection",
  "description": "Custom projection for my team",
  "audience": "senior engineers",
  "perspective": "system design",
  "detail_level": "detailed",
  "clustering_goal": "Group by domain bounded context",
  "doc_objectives": [
    "Explain architectural decisions",
    "Document cross-service dependencies"
  ],
  "doc_anti_objectives": [
    "Low-level implementation details"
  ],
  "output_artifacts": ["documentation"]
}
```

#### Field Reference

##### Identity

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (**required**) | Identifier for the projection. Also used as the output subdirectory name under `docs/`. |
| `description` | string | Human-readable description. Not injected into prompts — for your own reference. |

##### Audience and Perspective

These fields are compiled into a `<CUSTOM_INSTRUCTIONS>` block appended to every agent's system prompt.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `audience` | string | _(none)_ | Who the documentation is for. Injected as `"Target audience: {value}."` |
| `perspective` | string | _(none)_ | The lens through which to write. Injected as `"Documentation perspective: {value}."` |
| `detail_level` | string | `"standard"` | One of `standard`, `detailed`, or `concise`. Only injected when not `standard`. |

**Example effect:** Setting `"audience": "product managers"` and `"perspective": "business capabilities"` causes every agent to receive:

```
<CUSTOM_INSTRUCTIONS>
Target audience: product managers.
Documentation perspective: business capabilities.
</CUSTOM_INSTRUCTIONS>
```

##### Documentation Objectives

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `doc_objectives` | list of strings | _(none)_ | What the documentation should cover. Each item becomes a bullet in `<CUSTOM_INSTRUCTIONS>`. |
| `doc_anti_objectives` | list of strings | _(none)_ | What to explicitly omit. Each item becomes a "Do NOT include" bullet. |
| `objectives_override` | string | _(none)_ | **Fully replaces** the default `<OBJECTIVES>` block in the agent system prompt. When set, the default objectives ("help developers understand the module's purpose, architecture, and system fit") are discarded entirely. |

`doc_objectives` and `doc_anti_objectives` are appended as custom instructions _alongside_ the default objectives. Use `objectives_override` when you need to rewrite the objectives from scratch — for example, to make the agent focus on migration planning instead of general documentation.

##### Module Clustering

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `clustering_goal` | string | _(none)_ | Injected as a `<GROUPING_STRATEGY>` block into the LLM clustering prompt. Steers how components are grouped into modules. |
| `clustering_examples` | string | _(none)_ | Example groupings to further steer the LLM. |
| `saved_grouping` | object | _(none)_ | A pre-built module tree dict. When set, **skips the clustering LLM call entirely** and uses this grouping as-is. Useful for locking down a known-good grouping. |
| `max_depth_override` | integer (≥ 1) | _(none)_ | Override the hierarchical decomposition depth for this projection. |

**Tip:** Run a generation once, inspect the resulting `module_tree.json`, edit it to your liking, then pass it back via `--load-grouping` on subsequent runs to skip the clustering step.

##### Framework and Code Context

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `framework_context` | string | _(none)_ | Free-form text injected as a `<FRAMEWORK_CONTEXT>` block in the agent system prompt. Use this to explain framework conventions the LLM might not know (e.g. EJB patterns, Spring conventions, Django signals). |
| `code_provenance` | object | _(none)_ | Origin metadata for non-standard codebases (transpiled, generated, legacy). Compiled into a `<CODE_CONTEXT>` block. See [Code Provenance](#code-provenance) below. |

##### Supplementary Files

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `supplementary_file_patterns` | list of strings | _(none)_ | Glob patterns for non-code files to include alongside source code (e.g. `**/ejb-jar.xml`, `**/web.xml`, `**/*.properties`). Matched files are read and passed to agents as `<SUPPLEMENTARY_CONFIGURATION>`. |
| `supplementary_file_role` | string | `"Configuration files relevant to this module:"` | Describes what the supplementary files are, shown as a heading in the supplementary block. |

Supplementary files are automatically filtered per module — each agent only sees files whose paths are near the module's source files.

##### Output Control

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output_artifacts` | list of strings | `["documentation"]` | What to generate. Valid values: `"documentation"`, `"data_dictionary"`. Include `"data_dictionary"` to trigger glossary generation. |
| `glossary_path` | string | _(none)_ | Path to a pre-existing glossary JSON file to load instead of generating one. |

#### Code Provenance

The `code_provenance` sub-object is designed for transpiled, generated, or legacy codebases where the source code doesn't look like idiomatic code in its language. It compiles into a `<CODE_CONTEXT>` block.

```json
{
  "code_provenance": {
    "source_language": "COBOL",
    "transpilation_tool": "Micro Focus Enterprise Developer",
    "naming_conventions": {
      "WS-*": "Working Storage variable",
      "PERFORM-*": "PERFORM paragraph (subroutine call)",
      "88-level": "Condition name (boolean flag)"
    },
    "runtime_library_packages": [
      "com.microfocus.cobol.runtime"
    ],
    "known_boilerplate_patterns": [
      "CobolProgram.initialize()",
      "CobolProgram.terminate()"
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source_language` | string | The original language before transpilation (e.g. `"NATURAL"`, `"COBOL"`, `"RPG"`). |
| `transpilation_tool` | string | The tool used to produce the target code (e.g. `"Natural One"`, `"Micro Focus"`). |
| `naming_conventions` | object | Map of identifier patterns to their meanings. Helps the agent decode cryptic names. |
| `runtime_library_packages` | list of strings | Packages that are part of the transpiler runtime. The agent is told to down-weight these in documentation. |
| `known_boilerplate_patterns` | list of strings | Code patterns that are transpiler scaffolding. The agent is told to de-emphasise these. |

The compiled output looks like:

```
<CODE_CONTEXT>
This codebase was originally written in COBOL.
It was transpiled using Micro Focus Enterprise Developer.

Naming conventions from the original language:
  - WS-*: Working Storage variable
  - PERFORM-*: PERFORM paragraph (subroutine call)

Runtime library packages (downweight in documentation): com.microfocus.cobol.runtime

Known boilerplate patterns to de-emphasize:
  - CobolProgram.initialize()
  - CobolProgram.terminate()
</CODE_CONTEXT>
```

#### What Projections Cannot Change

The following are hardcoded in the prompt templates and not configurable via projections:

- **Agent role** — The agent is always introduced as "an AI documentation assistant" generating "comprehensive system documentation."
- **Output structure** — Documentation always follows the pattern: main module `.md` file with overview and architecture, sub-module `.md` files, and Mermaid diagrams. You cannot change the output format to, say, plain-text or HTML.
- **Agent workflow** — The sequence of steps (analyse components → create main file → delegate sub-modules → cross-reference) is fixed.
- **Repo and module overview prompts** — The final overview generation has no projection awareness. Overviews are always written from a generic developer perspective.
- **Folder filtering prompt** — The prompt that decides which folders contain "core functionality" is fixed and always filters out test/documentation files.
- **Clustering output format** — The JSON structure of grouped components is fixed. `clustering_goal` steers the grouping strategy but not the output schema.

#### Starter Projections

The package ships four ready-made projection files you can copy and customise. Find them in `codewiki/src/be/projections/` inside the repository, or locate the installed package with:

```bash
python -c "import codewiki.src.be.projection as m; from pathlib import Path; print(Path(m.__file__).parent / 'projections')"
```

| File | Audience | Focus | Key fields demonstrated |
|------|----------|-------|------------------------|
| `developer.json` | Developers & maintainers | Code structure (default behaviour) | `audience`, `perspective` only — minimal projection |
| `business.json` | Product managers & analysts | Business capabilities, no code details | `clustering_goal`, `doc_objectives`, `doc_anti_objectives`, `objectives_override` |
| `ejb-migration.json` | Migration engineers | EJB conventions, deployment descriptors | `framework_context`, `supplementary_file_patterns`, `supplementary_file_role` |
| `natural-transpiled.json` | Reimplementation engineers | Recovers original NATURAL logic from transpiled Java | `code_provenance`, `output_artifacts` with `data_dictionary` |

```bash
# Copy a starter and customise it
cp "$(python -c "import codewiki.src.be.projection as m; from pathlib import Path; print(Path(m.__file__).parent / 'projections/business.json')")" ./my-projection.json
# Edit my-projection.json to taste...
codewiki generate --projection ./my-projection.json
```

#### Creating a Custom Projection

**Step 1: Start with a minimal JSON file.**

```json
{
  "name": "security-review",
  "audience": "security engineers",
  "perspective": "attack surface and trust boundaries"
}
```

This is enough to shift the tone of every generated document toward security concerns while keeping everything else at defaults.

**Step 2: Add objectives to sharpen focus.**

```json
{
  "name": "security-review",
  "audience": "security engineers",
  "perspective": "attack surface and trust boundaries",
  "doc_objectives": [
    "Identify authentication and authorization boundaries",
    "Document input validation and sanitization points",
    "Map data flows that cross trust boundaries"
  ],
  "doc_anti_objectives": [
    "UI layout and styling details",
    "Build and deployment configuration"
  ]
}
```

**Step 3: Steer clustering if the default grouping doesn't suit your needs.**

```json
{
  "name": "security-review",
  "clustering_goal": "Group components by trust boundary: external-facing, internal services, data access layer, and shared utilities."
}
```

**Step 4: Add framework context if the codebase uses patterns the LLM might not infer.**

```json
{
  "framework_context": "This is a Spring Boot application using Spring Security with JWT tokens. @PreAuthorize annotations control method-level access. SecurityFilterChain beans define the HTTP security pipeline."
}
```

**Step 5: Run it.**

```bash
codewiki generate --projection ./security-review.json --verbose
```

Output lands in `docs/security-review/`.

#### Glossary / Data Dictionary

The glossary feature uses an LLM to map code identifiers to business-friendly names and definitions. This is especially useful for transpiled or legacy codebases where variable names are cryptic.

```bash
# Generate a glossary alongside documentation
codewiki generate --projection ./my-projection.json --generate-glossary

# Reuse a previously generated glossary on subsequent runs
codewiki generate --projection ./my-projection.json --load-glossary ./docs/my-projection/glossary.json
```

You can also enable glossary generation inside the projection JSON itself:

```json
{
  "output_artifacts": ["documentation", "data_dictionary"]
}
```

Output files: `glossary.json` (structured, reusable) and `glossary.md` (human-readable table).

#### Saved Groupings

After a generation run, the clustering result is saved as `module_tree.json` in the output directory. You can edit this file and pass it back to skip the clustering LLM call on future runs:

```bash
# First run — generates module_tree.json
codewiki generate --projection ./my-projection.json

# Edit docs/my-projection/module_tree.json to your liking...

# Subsequent runs — reuse the grouping
codewiki generate --projection ./my-projection.json \
  --load-grouping ./docs/my-projection/module_tree.json
```

This is useful when you've found a good module grouping and want to iterate on other projection fields without re-clustering.

#### Projection CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--projection`, `-p` | Path to a projection JSON file | `./my-projection.json` |
| `--generate-glossary` | Generate a glossary / data dictionary | Flag |
| `--load-glossary` | Load a pre-existing glossary JSON | `./glossary.json` |
| `--load-grouping` | Load saved module grouping (requires `--projection`) | `./grouping.json` |

These options combine with the standard generation flags (`--include`, `--exclude`, `--focus`, `--instructions`, `--max-depth`, etc.) — projections and CLI flags are additive.

#### Pattern Behavior (Important!)

- **`--include`**: When specified, **ONLY** these patterns are used (replaces defaults completely)
  - Example: `--include "*.cs"` will analyze ONLY `.cs` files
  - If omitted, all supported file types are analyzed
  - Supports glob patterns: `*.py`, `src/**/*.ts`, `*.{js,jsx}`

- **`--exclude`**: When specified, patterns are **MERGED** with default ignore patterns
  - Example: `--exclude "Tests,Specs"` will exclude these directories AND still exclude `.git`, `__pycache__`, `node_modules`, etc.
  - Default patterns include: `.git`, `node_modules`, `__pycache__`, `*.pyc`, `bin/`, `dist/`, and many more
  - Supports multiple formats:
    - Exact names: `Tests`, `.env`, `config.local`
    - Glob patterns: `*.test.js`, `*_test.py`, `*.min.*`
    - Directory patterns: `build/`, `dist/`, `coverage/`

#### Setting Persistent Defaults

Save your preferred settings as defaults:

```bash
# Set include patterns for C# projects
codewiki config agent --include "*.cs"

# Exclude test projects by default (merged with default excludes)
codewiki config agent --exclude "Tests,Specs,*.test.cs"

# Set focus modules
codewiki config agent --focus "src/core,src/api"

# Set default documentation type
codewiki config agent --doc-type architecture

# View current agent settings
codewiki config agent

# Clear all agent settings
codewiki config agent --clear
```

| Option | Description | Behavior | Example |
|--------|-------------|----------|---------|
| `--include` | File patterns to include | **Replaces** defaults | `*.cs`, `*.py`, `src/**/*.ts` |
| `--exclude` | Patterns to exclude | **Merges** with defaults | `Tests,Specs`, `*.test.js`, `build/` |
| `--focus` | Modules to document in detail | Standalone option | `src/core,src/api` |
| `--doc-type` | Documentation style | Standalone option | `api`, `architecture`, `user-guide`, `developer` |
| `--instructions` | Custom agent instructions | Standalone option | Free-form text |

### Token Settings

CodeWiki allows you to configure maximum token limits for LLM calls. This is useful for:
- Adapting to different model context windows
- Controlling costs by limiting response sizes
- Optimizing for faster response times

```bash
# Set max tokens for LLM responses (default: 32768)
codewiki config set --max-tokens 16384

# Set max tokens for module clustering (default: 36369)
codewiki config set --max-token-per-module 40000

# Set max tokens for leaf modules (default: 16000)
codewiki config set --max-token-per-leaf-module 20000

# Set max depth for hierarchical decomposition (default: 2)
codewiki config set --max-depth 3

# Override at runtime for a single generation
codewiki generate --max-tokens 16384 --max-token-per-module 40000 --max-depth 3
```

| Option | Description | Default |
|--------|-------------|---------|
| `--max-tokens` | Maximum output tokens for LLM response | 32768 |
| `--max-token-per-module` | Input tokens threshold for module clustering | 36369 |
| `--max-token-per-leaf-module` | Input tokens threshold for leaf modules | 16000 |
| `--max-depth` | Maximum depth for hierarchical decomposition | 2 |

### Configuration Storage

- **API keys**: Securely stored in system keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- **Settings & Agent Instructions**: `~/.codewiki/config.json`

---

## Documentation Output

Generated documentation includes both **textual descriptions** and **visual artifacts** for comprehensive understanding.

### Textual Documentation
- Repository overview with architecture guide
- Module-level documentation with API references
- Usage examples and implementation patterns
- Cross-module interaction analysis

### Visual Artifacts
- System architecture diagrams (Mermaid)
- Data flow visualizations
- Dependency graphs and module relationships
- Sequence diagrams for complex interactions

### Output Structure

```
./docs/
├── overview.md              # Repository overview (start here!)
├── module1.md               # Module documentation
├── module2.md               # Additional modules...
├── module_tree.json         # Hierarchical module structure
├── first_module_tree.json   # Initial clustering result
├── metadata.json            # Generation metadata
└── index.html               # Interactive viewer (with --github-pages)
```

When using a projection, output goes into a subdirectory named after the projection:

```
./docs/
└── business/                # Projection subdirectory
    ├── overview.md
    ├── *.md
    ├── module_tree.json
    ├── metadata.json
    ├── glossary.json        # If --generate-glossary was used
    └── glossary.md          # Human-readable glossary
```

---

## Experimental Results

CodeWiki has been evaluated on **CodeWikiBench**, the first benchmark specifically designed for repository-level documentation quality assessment.

### Performance by Language Category

| Language Category | CodeWiki (Sonnet-4) | DeepWiki | Improvement |
|-------------------|---------------------|----------|-------------|
| High-Level (Python, JS, TS) | **79.14%** | 68.67% | **+10.47%** |
| Managed (C#, Java) | **68.84%** | 64.80% | **+4.04%** |
| Systems (C, C++) | 53.24% | 56.39% | -3.15% |
| **Overall Average** | **68.79%** | **64.06%** | **+4.73%** |

### Results on Representative Repositories

| Repository | Language | LOC | CodeWiki-Sonnet-4 | DeepWiki | Improvement |
|------------|----------|-----|-------------------|----------|-------------|
| All-Hands-AI--OpenHands | Python | 229K | **82.45%** | 73.04% | **+9.41%** |
| puppeteer--puppeteer | TypeScript | 136K | **83.00%** | 64.46% | **+18.54%** |
| sveltejs--svelte | JavaScript | 125K | **71.96%** | 68.51% | **+3.45%** |
| Unity-Technologies--ml-agents | C# | 86K | **79.78%** | 74.80% | **+4.98%** |
| elastic--logstash | Java | 117K | **57.90%** | 54.80% | **+3.10%** |

**View comprehensive results:** See [paper](https://arxiv.org/abs/2510.24428) for complete evaluation on 21 repositories spanning all supported languages.

---

## How It Works

### Architecture Overview

CodeWiki employs a three-stage process for comprehensive documentation generation:

1. **Hierarchical Decomposition**: Uses dynamic programming-inspired algorithms to partition repositories into coherent modules while preserving architectural context across multiple granularity levels.

2. **Recursive Multi-Agent Processing**: Implements adaptive multi-agent processing with dynamic task delegation, allowing the system to handle complex modules at scale while maintaining quality.

3. **Multi-Modal Synthesis**: Integrates textual descriptions with visual artifacts including architecture diagrams, data-flow representations, and sequence diagrams for comprehensive understanding.

### Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Codebase      │───▶│  Hierarchical    │───▶│  Multi-Agent    │
│   Analysis      │    │  Decomposition   │    │  Processing     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Visual        │◀───│  Multi-Modal     │◀───│  Structured     │
│   Artifacts     │    │  Synthesis       │    │  Content        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## Requirements

- **Python 3.12+**
- **Node.js** (for Mermaid diagram validation)
- **LLM API access** (Anthropic Claude, OpenAI, etc.)
- **Git** (for branch creation features)

---

## Additional Resources

### Documentation & Guides
- **[Docker Deployment](docker/DOCKER_README.md)** - Containerized deployment instructions
- **[Development Guide](DEVELOPMENT.md)** - Project structure, architecture, and contributing guidelines
- **[CodeWikiBench](https://github.com/FSoft-AI4Code/CodeWikiBench)** - Repository-level documentation benchmark
- **[Live Demo](https://fsoft-ai4code.github.io/codewiki-demo/)** - Interactive demo and examples

### Academic Resources
- **[Paper](https://arxiv.org/abs/2510.24428)** - Full research paper with detailed methodology and results
- **[Citation](#citation)** - How to cite CodeWiki in your research

---

## Citation

This project is a fork of the [original CodeWiki repository](https://github.com/FSoft-AI4Code/CodeWiki) by FSoft-AI4Code. If you use the original research in your work, please cite:

```bibtex
@misc{hoang2025codewikievaluatingaisability,
      title={CodeWiki: Evaluating AI's Ability to Generate Holistic Documentation for Large-Scale Codebases},
      author={Anh Nguyen Hoang and Minh Le-Anh and Bach Le and Nghi D. Q. Bui},
      year={2025},
      eprint={2510.24428},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2510.24428},
}
```

To reference this fork (which adds the projection framework, glossary generation, and multi-audience documentation support):

```bibtex
@software{adhikary2026codewikiprojections,
      title={CodeWiki Projections: Multi-Audience Documentation Generation for Large-Scale Codebases},
      author={Aniruddha Adhikary},
      year={2026},
      url={https://github.com/aniruddha-adhikary/CodeWiki},
      note={Fork of CodeWiki with projection framework, glossary generation, and multi-audience documentation support},
}
```

---

## Star History

<p align="center">
  <a href="https://star-history.com/#aniruddha-adhikary/CodeWiki&Date">
   <picture>
     <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=aniruddha-adhikary/CodeWiki&type=Date&theme=dark" />
     <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=aniruddha-adhikary/CodeWiki&type=Date" />
     <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=aniruddha-adhikary/CodeWiki&type=Date" />
   </picture>
  </a>
</p>

---

## License

This project is licensed under the MIT License.
