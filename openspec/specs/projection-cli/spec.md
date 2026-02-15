# projection-cli Specification

## Purpose
TBD - created by archiving change add-projection-framework. Update Purpose after archive.
## Requirements
### Requirement: Projection CLI Option
The `generate` command SHALL accept a `--projection` / `-p` option that takes a string argument. Valid values:
- Built-in names: "developer", "business", "ejb-migration", "natural-transpiled"
- Path to a JSON file containing a custom `ProjectionConfig`

Cross-reference: `projection-model` provides `resolve_projection()`.

#### Scenario: Built-in projection
- **WHEN** `codewiki generate --projection business` is run
- **THEN** the business projection is resolved and passed through the pipeline

#### Scenario: Custom JSON projection
- **WHEN** `codewiki generate --projection /path/to/custom.json` is run with a valid JSON file
- **THEN** the custom projection is loaded and passed through the pipeline

#### Scenario: Invalid projection name
- **WHEN** `codewiki generate --projection nonexistent` is run
- **THEN** the command fails with an error listing available built-in projections

### Requirement: Load Grouping CLI Option
The `generate` command SHALL accept a `--load-grouping` option that takes a path to a saved grouping JSON file. The loaded grouping is set as `projection.saved_grouping`, causing clustering to be skipped.

#### Scenario: Load saved grouping
- **WHEN** `codewiki generate --projection business --load-grouping ./grouping.json` is run with a valid grouping file
- **THEN** the clustering LLM call is skipped and the saved module tree is used

#### Scenario: Load grouping without projection
- **WHEN** `codewiki generate --load-grouping ./grouping.json` is run without `--projection`
- **THEN** the command fails with an error indicating `--projection` is required

### Requirement: Interactive Grouping CLI Option
The `generate` command SHALL accept an `--interactive-grouping` flag. When set:
1. Clustering runs normally to produce a proposed module tree
2. An interactive session displays the tree and allows rename, move, merge, and accept operations
3. The accepted grouping is saved to `.codewiki/projections/{name}-grouping.json`
4. The accepted grouping is used for documentation generation

Cross-reference: `projection-clustering` for saved grouping bypass on re-runs.

#### Scenario: Interactive grouping session
- **WHEN** `codewiki generate --projection business --interactive-grouping` is run
- **THEN** after clustering, the user sees the proposed groups and can modify them before doc generation proceeds

### Requirement: Glossary CLI Options
The `generate` command SHALL accept:
- `--generate-glossary` flag: enables glossary generation (adds `"data_dictionary"` to `output_artifacts`)
- `--load-glossary` option: path to a pre-existing `glossary.json` file
- `--interactive-glossary` flag: after generation, allows interactive review/edit

Cross-reference: `glossary-generation` for the glossary pipeline stage.

#### Scenario: Generate glossary
- **WHEN** `codewiki generate --projection natural-transpiled --generate-glossary` is run
- **THEN** glossary generation runs and produces `glossary.json` + `glossary.md` in the output directory

#### Scenario: Load and inject glossary
- **WHEN** `codewiki generate --projection business --load-glossary ./glossary.json` is run
- **THEN** the glossary is loaded from the file and injected into agent prompts without running glossary generation

### Requirement: Projection Output Subdirectory
When a projection is active, documentation output SHALL be placed in a subdirectory named after the projection:
```
docs/{projection_name}/
  overview.md
  module_tree.json
  glossary.json        (if data_dictionary enabled)
  glossary.md          (if data_dictionary enabled)
  *.md
```

When NO projection is specified, output SHALL remain in the flat structure for backwards compatibility:
```
docs/
  overview.md
  module_tree.json
  *.md
```

#### Scenario: Business projection output directory
- **WHEN** `codewiki generate --projection business` is run with default output dir
- **THEN** all output files are written to `docs/business/`

#### Scenario: No projection output directory
- **WHEN** `codewiki generate` is run without `--projection`
- **THEN** output files are written to `docs/` directly (backwards compatible)

### Requirement: CLI Adapter Projection Support
`CLIDocumentationGenerator` (`codewiki/cli/adapters/doc_generator.py`) SHALL accept a `projection` parameter and:
1. Pass it to backend `DocumentationGenerator`
2. Adjust `working_dir` to include projection subdirectory
3. Run interactive grouping/glossary sessions when respective flags are set

Cross-reference: `projection-pipeline` for backend `DocumentationGenerator` changes.

#### Scenario: Adapter with projection
- **WHEN** `CLIDocumentationGenerator` is created with a business projection
- **THEN** the backend generator receives the projection and output goes to the projection subdirectory

### Requirement: Interactive Grouping Session
The system SHALL provide an `InteractiveGroupingSession` class in `codewiki/cli/interactive_grouping.py` with:
- `display_tree()` -- pretty-print proposed groups with component counts
- `rename_group(old, new)` -- rename a group
- `move_component(id, from_group, to_group)` -- reassign a component
- `merge_groups(a, b, new_name)` -- combine two groups
- `accept()` -- finalize and return the modified module tree
- `save(path)` -- persist as JSON with metadata (projection name, timestamp)
- `run()` -- interactive loop reading user commands

#### Scenario: Rename a group
- **WHEN** the user enters `rename "Module A" "User Authentication"` in the interactive session
- **THEN** the group is renamed in the module tree and the display updates

#### Scenario: Accept and save
- **WHEN** the user enters `accept` in the interactive session
- **THEN** the modified module tree is saved to `.codewiki/projections/{name}-grouping.json` and returned for use

### Requirement: Interactive Glossary Session
The system SHALL provide an `InteractiveGlossarySession` class in `codewiki/cli/interactive_glossary.py` with:
- `display()` -- show entries grouped by confidence (high/medium/low)
- `edit_entry(identifier, field, value)` -- modify an entry's business_name or definition
- `remove_entry(identifier)` -- remove an entry
- `accept()` -- finalize and return the modified glossary
- `run()` -- interactive loop reading user commands

#### Scenario: Edit glossary entry
- **WHEN** the user enters `edit WS_CUST_NM business_name "Full Customer Name"` in the interactive session
- **THEN** the entry's `business_name` is updated to "Full Customer Name"

#### Scenario: Remove low-confidence entry
- **WHEN** the user enters `remove WS_TMP_1` in the interactive session
- **THEN** the entry is removed from the glossary

