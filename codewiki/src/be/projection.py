"""Projection data model for configurable documentation views.

Projections define how documentation is generated: audience, perspective,
objectives, code provenance context, and framework-specific instructions.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECTIONS_DIR = Path(__file__).parent / "projections"

# ---------------------------------------------------------------------------
# Validation constants & error
# ---------------------------------------------------------------------------

VALID_DETAIL_LEVELS: frozenset = frozenset({"standard", "detailed", "concise"})
VALID_OUTPUT_ARTIFACTS: frozenset = frozenset({"documentation", "data_dictionary"})


class ProjectionValidationError(ValueError):
    """Raised when a projection JSON file has an invalid structure or values."""


def _validate_code_provenance(cp: Any, errors: List[str]) -> None:
    """Append validation errors for a code_provenance object."""
    if not isinstance(cp, dict):
        errors.append("'code_provenance' must be a JSON object or null")
        return
    for field_name in ("source_language", "transpilation_tool"):
        val = cp.get(field_name)
        if val is not None and not isinstance(val, str):
            errors.append(f"'code_provenance.{field_name}' must be a string or null")
    naming = cp.get("naming_conventions", {})
    if not isinstance(naming, dict):
        errors.append("'code_provenance.naming_conventions' must be a JSON object")
    else:
        for k, v in naming.items():
            if not isinstance(k, str) or not isinstance(v, str):
                errors.append("'code_provenance.naming_conventions' must map strings to strings")
                break
    for list_field in ("runtime_library_packages", "known_boilerplate_patterns"):
        val = cp.get(list_field, [])
        if not isinstance(val, list):
            errors.append(f"'code_provenance.{list_field}' must be a list")
        else:
            for i, item in enumerate(val):
                if not isinstance(item, str):
                    errors.append(f"'code_provenance.{list_field}[{i}]' must be a string")


def validate_projection_dict(data: Any, source: str = "<unknown>") -> None:
    """Validate a dict deserialised from a projection JSON file.

    Raises ProjectionValidationError with a descriptive message listing all
    problems found.  Callers should catch this and surface it to the user.
    """
    if not isinstance(data, dict):
        raise ProjectionValidationError(
            f"Projection '{source}': expected a JSON object at the top level, "
            f"got {type(data).__name__}"
        )

    errors: List[str] = []

    # name — must be present and non-empty
    name = data.get("name", "")
    if not isinstance(name, str) or not name.strip():
        errors.append("'name' must be a non-empty string")

    # plain string fields (optional, but must be strings when present)
    for f in ("description", "clustering_goal", "clustering_examples", "audience", "perspective",
              "objectives_override", "framework_context", "supplementary_file_role", "glossary_path"):
        val = data.get(f)
        if val is not None and not isinstance(val, str):
            errors.append(f"'{f}' must be a string or null, got {type(val).__name__}")

    # detail_level
    dl = data.get("detail_level", "standard")
    if not isinstance(dl, str):
        errors.append(f"'detail_level' must be a string, got {type(dl).__name__}")
    elif dl not in VALID_DETAIL_LEVELS:
        errors.append(f"'detail_level' must be one of {sorted(VALID_DETAIL_LEVELS)}, got '{dl}'")

    # max_depth_override
    mdep = data.get("max_depth_override")
    if mdep is not None and (not isinstance(mdep, int) or isinstance(mdep, bool) or mdep < 1):
        errors.append("'max_depth_override' must be a positive integer or null")

    # list-of-strings fields
    for f in ("doc_objectives", "doc_anti_objectives", "supplementary_file_patterns"):
        val = data.get(f)
        if val is None:
            continue
        if not isinstance(val, list):
            errors.append(f"'{f}' must be a list or null, got {type(val).__name__}")
        else:
            for i, item in enumerate(val):
                if not isinstance(item, str):
                    errors.append(f"'{f}[{i}]' must be a string, got {type(item).__name__}")

    # output_artifacts
    oa = data.get("output_artifacts", ["documentation"])
    if not isinstance(oa, list):
        errors.append("'output_artifacts' must be a list")
    else:
        for i, item in enumerate(oa):
            if not isinstance(item, str):
                errors.append(f"'output_artifacts[{i}]' must be a string")
            elif item not in VALID_OUTPUT_ARTIFACTS:
                errors.append(
                    f"'output_artifacts[{i}]': unknown artifact '{item}'; "
                    f"valid values: {sorted(VALID_OUTPUT_ARTIFACTS)}"
                )

    # saved_grouping
    sg = data.get("saved_grouping")
    if sg is not None and not isinstance(sg, dict):
        errors.append("'saved_grouping' must be a JSON object or null")

    # code_provenance
    cp = data.get("code_provenance")
    if cp is not None:
        _validate_code_provenance(cp, errors)

    if errors:
        bullet_list = "\n  • ".join(errors)
        raise ProjectionValidationError(
            f"Invalid projection '{source}':\n  • {bullet_list}"
        )


@dataclass
class CodeProvenance:
    """Origin metadata for non-standard (e.g., transpiled) source code."""

    source_language: Optional[str] = None
    transpilation_tool: Optional[str] = None
    naming_conventions: Dict[str, str] = field(default_factory=dict)
    runtime_library_packages: List[str] = field(default_factory=list)
    known_boilerplate_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_language": self.source_language,
            "transpilation_tool": self.transpilation_tool,
            "naming_conventions": self.naming_conventions,
            "runtime_library_packages": self.runtime_library_packages,
            "known_boilerplate_patterns": self.known_boilerplate_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeProvenance":
        return cls(
            source_language=data.get("source_language"),
            transpilation_tool=data.get("transpilation_tool"),
            naming_conventions=data.get("naming_conventions", {}),
            runtime_library_packages=data.get("runtime_library_packages", []),
            known_boilerplate_patterns=data.get("known_boilerplate_patterns", []),
        )


@dataclass
class ProjectionConfig:
    """Configuration for a documentation projection."""

    name: str = ""
    description: str = ""
    clustering_goal: str = ""
    clustering_examples: str = ""
    audience: str = ""
    perspective: str = ""
    doc_objectives: List[str] = field(default_factory=list)
    doc_anti_objectives: List[str] = field(default_factory=list)
    detail_level: str = "standard"
    max_depth_override: Optional[int] = None
    saved_grouping: Optional[Dict] = None
    objectives_override: Optional[str] = None
    code_provenance: Optional[CodeProvenance] = None
    framework_context: Optional[str] = None
    supplementary_file_patterns: Optional[List[str]] = None
    supplementary_file_role: Optional[str] = None
    output_artifacts: List[str] = field(default_factory=lambda: ["documentation"])
    glossary_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "clustering_goal": self.clustering_goal,
            "clustering_examples": self.clustering_examples,
            "audience": self.audience,
            "perspective": self.perspective,
            "doc_objectives": self.doc_objectives,
            "doc_anti_objectives": self.doc_anti_objectives,
            "detail_level": self.detail_level,
            "max_depth_override": self.max_depth_override,
            "saved_grouping": self.saved_grouping,
            "objectives_override": self.objectives_override,
            "code_provenance": self.code_provenance.to_dict() if self.code_provenance else None,
            "framework_context": self.framework_context,
            "supplementary_file_patterns": self.supplementary_file_patterns,
            "supplementary_file_role": self.supplementary_file_role,
            "output_artifacts": self.output_artifacts,
            "glossary_path": self.glossary_path,
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectionConfig":
        provenance_data = data.get("code_provenance")
        code_provenance = (
            CodeProvenance.from_dict(provenance_data)
            if provenance_data is not None
            else None
        )
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            clustering_goal=data.get("clustering_goal", ""),
            clustering_examples=data.get("clustering_examples", ""),
            audience=data.get("audience", ""),
            perspective=data.get("perspective", ""),
            doc_objectives=data.get("doc_objectives", []),
            doc_anti_objectives=data.get("doc_anti_objectives", []),
            detail_level=data.get("detail_level", "standard"),
            max_depth_override=data.get("max_depth_override"),
            saved_grouping=data.get("saved_grouping"),
            objectives_override=data.get("objectives_override"),
            code_provenance=code_provenance,
            framework_context=data.get("framework_context"),
            supplementary_file_patterns=data.get("supplementary_file_patterns"),
            supplementary_file_role=data.get("supplementary_file_role"),
            output_artifacts=data.get("output_artifacts", ["documentation"]),
            glossary_path=data.get("glossary_path"),
        )


@dataclass
class CompiledProjectionPrompts:
    """Intermediate representation of projection-derived prompt blocks."""

    code_context_block: str = ""
    framework_context_block: str = ""
    objectives_override: Optional[str] = None
    custom_instructions: str = ""
    glossary_block: str = ""


def compile_projection_instructions(
    projection: ProjectionConfig,
) -> CompiledProjectionPrompts:
    """Compile a ProjectionConfig into prompt blocks for the agent pipeline."""
    result = CompiledProjectionPrompts()

    # Code context block from provenance
    if projection.code_provenance:
        prov = projection.code_provenance
        lines = ["<CODE_CONTEXT>"]
        if prov.source_language:
            lines.append(
                f"This codebase was originally written in {prov.source_language}."
            )
        if prov.transpilation_tool:
            lines.append(
                f"It was transpiled using {prov.transpilation_tool}."
            )
        if prov.naming_conventions:
            lines.append("")
            lines.append("Naming conventions from the original language:")
            for pattern, meaning in prov.naming_conventions.items():
                lines.append(f"  - {pattern}: {meaning}")
        if prov.runtime_library_packages:
            lines.append("")
            lines.append(
                "Runtime library packages (downweight in documentation): "
                + ", ".join(prov.runtime_library_packages)
            )
        if prov.known_boilerplate_patterns:
            lines.append("")
            lines.append("Known boilerplate patterns to de-emphasize:")
            for pattern in prov.known_boilerplate_patterns:
                lines.append(f"  - {pattern}")
        lines.append("</CODE_CONTEXT>")
        result.code_context_block = "\n".join(lines)

    # Framework context block
    if projection.framework_context:
        result.framework_context_block = (
            f"<FRAMEWORK_CONTEXT>\n{projection.framework_context}\n</FRAMEWORK_CONTEXT>"
        )

    # Objectives override
    result.objectives_override = projection.objectives_override

    # Custom instructions from audience, perspective, objectives, detail_level
    instructions = []
    if projection.audience:
        instructions.append(f"Target audience: {projection.audience}.")
    if projection.perspective:
        instructions.append(f"Documentation perspective: {projection.perspective}.")
    if projection.detail_level and projection.detail_level != "standard":
        instructions.append(f"Detail level: {projection.detail_level}.")
    if projection.doc_objectives:
        instructions.append("Documentation objectives:")
        for obj in projection.doc_objectives:
            instructions.append(f"  - {obj}")
    if projection.doc_anti_objectives:
        instructions.append("Do NOT include:")
        for anti in projection.doc_anti_objectives:
            instructions.append(f"  - {anti}")
    result.custom_instructions = "\n".join(instructions)

    return result


# ---------------------------------------------------------------------------
# Built-in projection loader
# ---------------------------------------------------------------------------

_BUILTIN_PROJECTIONS: set[str] = {"developer", "business", "ejb-migration", "natural-transpiled"}


def _load_builtin(name: str) -> ProjectionConfig:
    """Load a built-in projection from its bundled JSON file."""
    json_path = _PROJECTIONS_DIR / f"{name}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate_projection_dict(data, source=name)
    return ProjectionConfig.from_dict(data)


def get_developer_projection() -> ProjectionConfig:
    """Backwards-compatible developer documentation projection."""
    return _load_builtin("developer")


def get_business_projection() -> ProjectionConfig:
    """Business-oriented documentation projection for non-technical stakeholders."""
    return _load_builtin("business")


def get_ejb_migration_projection() -> ProjectionConfig:
    """EJB migration projection for engineers planning reimplementation."""
    return _load_builtin("ejb-migration")


def get_natural_transpiled_projection() -> ProjectionConfig:
    """Projection for NATURAL-transpiled codebases."""
    return _load_builtin("natural-transpiled")


# ---------------------------------------------------------------------------
# Projection resolver
# ---------------------------------------------------------------------------


def resolve_projection(name_or_path: str) -> ProjectionConfig:
    """Resolve a projection by built-in name, JSON file path, or project-local name.

    Resolution order:
    1. Built-in names: "developer", "business", "ejb-migration", "natural-transpiled"
    2. File paths ending in .json: load and deserialize
    3. Project-local: .codewiki/projections/{name}.json
    4. Raise ValueError with available options
    """
    # 1. Built-in name
    if name_or_path in _BUILTIN_PROJECTIONS:
        return _load_builtin(name_or_path)

    # 2. JSON file path
    if name_or_path.endswith(".json"):
        if not os.path.isfile(name_or_path):
            raise FileNotFoundError(f"Projection file not found: {name_or_path}")
        with open(name_or_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError(
                    f"Projection file '{name_or_path}' is not valid JSON: {exc.msg}",
                    exc.doc,
                    exc.pos,
                ) from exc
        validate_projection_dict(data, source=name_or_path)
        return ProjectionConfig.from_dict(data)

    # 3. Project-local .codewiki/projections/{name}.json
    local_path = os.path.join(".codewiki", "projections", f"{name_or_path}.json")
    if os.path.isfile(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as exc:
                raise json.JSONDecodeError(
                    f"Projection file '{local_path}' is not valid JSON: {exc.msg}",
                    exc.doc,
                    exc.pos,
                ) from exc
        validate_projection_dict(data, source=local_path)
        return ProjectionConfig.from_dict(data)

    # 4. Unknown
    available = ", ".join(sorted(_BUILTIN_PROJECTIONS))
    raise ValueError(
        f"Unknown projection '{name_or_path}'. "
        f"Available built-in projections: {available}. "
        f"Or provide a path to a .json file."
    )
