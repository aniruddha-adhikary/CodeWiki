## ADDED Requirements

### Requirement: Supplementary File Collection
The system SHALL provide a `collect_supplementary_files(repo_path: str, patterns: List[str]) -> Dict[str, str]` function in `DocumentationGenerator` that:
1. Globs `projection.supplementary_file_patterns` against the repository root
2. Returns a `Dict[str, str]` mapping relative file paths to file contents
3. Caps individual files at 50KB (truncates with `... [truncated]` marker)
4. Skips binary files

Cross-reference: `projection-model` provides the `supplementary_file_patterns` field; `prompt-parameterization` handles injection into prompts.

#### Scenario: Collect EJB XML configs
- **WHEN** `collect_supplementary_files()` is called with patterns `["**/ejb-jar.xml", "**/web.xml"]` on a repo containing both files
- **THEN** the returned dict contains both file paths as keys with their XML content as values

#### Scenario: Large file truncation
- **WHEN** a matching file exceeds 50KB
- **THEN** its content is truncated to 50KB with `... [truncated]` appended

#### Scenario: No matching files
- **WHEN** patterns match no files in the repository
- **THEN** an empty dict is returned

#### Scenario: No supplementary patterns configured
- **WHEN** `projection.supplementary_file_patterns` is `None` or empty
- **THEN** supplementary file collection is skipped entirely

### Requirement: Module-Scoped Supplementary File Filtering
The system SHALL provide a `filter_supplementary_for_module(all_files: Dict[str, str], module_component_paths: List[str]) -> Dict[str, str]` function that filters supplementary files to:
1. Files in the same directory subtree as the module's code files
2. Top-level configuration files (files in the repository root)

#### Scenario: Module-specific XML
- **WHEN** a module contains code in `src/student/` AND supplementary files include `src/student/ejb-jar.xml` and `src/payment/ejb-jar.xml`
- **THEN** only `src/student/ejb-jar.xml` (and any root-level configs) are returned for that module

#### Scenario: Root-level config always included
- **WHEN** supplementary files include `persistence.xml` at the repository root
- **THEN** it is included for every module regardless of the module's directory

### Requirement: Supplementary Files in Pipeline
The system SHALL collect supplementary files in `DocumentationGenerator.run()` after clustering and before documentation generation. The collected files SHALL be passed to `AgentOrchestrator` which stores them for per-module filtering and injection into `format_user_prompt()`.

#### Scenario: End-to-end supplementary file flow
- **WHEN** a projection with `supplementary_file_patterns=["**/ejb-jar.xml"]` is used for generation
- **THEN** matching XML files appear in the `<SUPPLEMENTARY_CONFIGURATION>` block of relevant agent user prompts
