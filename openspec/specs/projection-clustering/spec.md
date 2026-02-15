# projection-clustering Specification

## Purpose
TBD - created by archiving change add-projection-framework. Update Purpose after archive.
## Requirements
### Requirement: Projection-Aware Clustering
The system SHALL accept an optional `projection: ProjectionConfig` parameter in `cluster_modules()` (`codewiki/src/be/cluster_modules.py`). When provided, the projection's `clustering_goal` SHALL be passed as a `grouping_directive` to `format_cluster_prompt()`.

Cross-reference: `projection-model` provides the `ProjectionConfig` data model.

#### Scenario: Business projection clustering
- **WHEN** `cluster_modules()` is called with a business projection (non-empty `clustering_goal`)
- **THEN** the LLM clustering prompt includes a `<GROUPING_STRATEGY>` block instructing the LLM to group by business capabilities

#### Scenario: Developer projection clustering (default)
- **WHEN** `cluster_modules()` is called with a developer projection (empty `clustering_goal`) or no projection
- **THEN** the clustering prompt is identical to the current behavior with no `<GROUPING_STRATEGY>` block

### Requirement: Grouping Directive in Cluster Prompt
The system SHALL add a `grouping_directive: str = None` parameter to `format_cluster_prompt()` in `prompt_template.py`. When non-empty, a `<GROUPING_STRATEGY>` block SHALL be prepended before the component list in the clustering prompt.

#### Scenario: Grouping directive present
- **WHEN** `format_cluster_prompt(grouping_directive="Group components by business capabilities, not code structure")` is called
- **THEN** the prompt contains `<GROUPING_STRATEGY>Group components by business capabilities...</GROUPING_STRATEGY>` before the component list

#### Scenario: No grouping directive
- **WHEN** `format_cluster_prompt()` is called without `grouping_directive`
- **THEN** the prompt has no `<GROUPING_STRATEGY>` block (backwards compatible)

### Requirement: Saved Grouping Bypass
The system SHALL check `projection.saved_grouping` at the top of `cluster_modules()`. When a saved grouping exists, the function SHALL return it directly without calling the LLM.

#### Scenario: Saved grouping used
- **WHEN** `cluster_modules()` is called with a projection whose `saved_grouping` contains a valid module_tree dict
- **THEN** the function returns the saved module_tree without any LLM call

#### Scenario: No saved grouping
- **WHEN** `cluster_modules()` is called with a projection whose `saved_grouping` is `None`
- **THEN** the function proceeds with normal LLM-based clustering

### Requirement: Projection Propagation Through Recursive Clustering
The system SHALL propagate the `projection` parameter through recursive calls to `cluster_modules()` for sub-module clustering.

#### Scenario: Deep module tree with projection
- **WHEN** a repository requires multi-level clustering AND a business projection is active
- **THEN** all recursive clustering calls receive the same `clustering_goal` directive

