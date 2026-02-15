"""Projection data model for configurable documentation views.

Projections define how documentation is generated: audience, perspective,
objectives, code provenance context, and framework-specific instructions.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
# Built-in projection factories
# ---------------------------------------------------------------------------


def get_developer_projection() -> ProjectionConfig:
    """Backwards-compatible developer documentation projection."""
    return ProjectionConfig(
        name="developer",
        description="Standard developer documentation with code structure focus.",
        audience="developers and maintainers",
        perspective="code structure",
    )


def get_business_projection() -> ProjectionConfig:
    """Business-oriented documentation projection for non-technical stakeholders."""
    return ProjectionConfig(
        name="business",
        description="Business capability documentation for non-technical stakeholders.",
        clustering_goal=(
            "Group components by business domain and capability rather than "
            "technical structure. Identify bounded contexts, business workflows, "
            "and domain concepts. Prefer names that reflect what the system does "
            "for the business over how it is implemented."
        ),
        audience="product managers and business analysts",
        perspective="business capabilities",
        doc_objectives=[
            "Explain what each component does in business terms",
            "Identify business workflows and processes",
            "Map technical components to business capabilities",
        ],
        doc_anti_objectives=[
            "Implementation details and code-level specifics",
            "Internal data structures and algorithms",
            "Developer-oriented API documentation",
        ],
        objectives_override=(
            "Write documentation for a non-technical audience. Focus on business "
            "capabilities, workflows, and domain concepts. Avoid code snippets, "
            "class names, and implementation details unless they directly explain "
            "a business concept."
        ),
        detail_level="standard",
    )


def get_ejb_migration_projection() -> ProjectionConfig:
    """EJB migration projection for engineers planning reimplementation."""
    return ProjectionConfig(
        name="ejb-migration",
        description="EJB application documentation for migration planning.",
        audience="software engineers planning reimplementation",
        perspective="migration planning",
        framework_context=(
            "This is a Java EE / EJB application. Key conventions:\n"
            "- Entity Beans: persistent data objects mapped to database tables, "
            "managed by the EJB container.\n"
            "- Session Beans (Stateless/Stateful): business logic components. "
            "Stateless beans handle single request/response; Stateful beans "
            "maintain conversational state.\n"
            "- JNDI lookups: the standard way EJB clients locate beans "
            "(e.g., java:comp/env/ejb/MyBean).\n"
            "- Deployment descriptors (ejb-jar.xml, web.xml): XML files that "
            "configure bean properties, security roles, transaction attributes, "
            "and resource references.\n"
            "- Container-Managed Transactions (CMT): the EJB container "
            "automatically manages transaction boundaries."
        ),
        supplementary_file_patterns=[
            "**/ejb-jar.xml",
            "**/web.xml",
            "**/persistence.xml",
            "**/jboss*.xml",
        ],
        supplementary_file_role="EJB deployment descriptors and configuration files",
        doc_objectives=[
            "Identify all EJB components and their roles",
            "Map entity relationships and data model",
            "Document business logic in session beans",
            "Capture transaction and security configuration",
        ],
        doc_anti_objectives=[
            "Container internals and classloading details",
            "IDE-specific project configuration",
        ],
        objectives_override=(
            "Document this EJB application for engineers planning a "
            "reimplementation in a modern framework. For each module, identify: "
            "(1) Entity beans and their database mappings, (2) Session beans and "
            "the business operations they expose, (3) JNDI lookup patterns and "
            "inter-bean dependencies, (4) Transaction and security configuration "
            "from deployment descriptors. Highlight aspects that will need "
            "architectural changes during migration."
        ),
    )


def get_natural_transpiled_projection() -> ProjectionConfig:
    """Projection for NATURAL-transpiled codebases."""
    return ProjectionConfig(
        name="natural-transpiled",
        description="Documentation for NATURAL-transpiled code targeting reimplementation.",
        audience="software engineers reimplementing NATURAL-transpiled code",
        perspective="original NATURAL logic and data structures",
        code_provenance=CodeProvenance(
            source_language="NATURAL",
            naming_conventions={
                "WS_*": "Working Storage variable (from NATURAL DEFINE DATA LOCAL/GLOBAL)",
                "PERFORM_*": "PERFORM paragraph — subroutine call",
                "PRFM_*": "PERFORM paragraph — subroutine call (alternate prefix)",
                "MOVE_TO(a, b)": "Assignment: move value of a into b",
                "IF_*": "Conditional block from NATURAL IF/DECIDE",
                "LOOP_*": "Loop construct from NATURAL REPEAT/FOR/READ",
            },
            runtime_library_packages=[
                "com.softwareag.natural.runtime",
                "com.softwareag.natural.io",
            ],
            known_boilerplate_patterns=[
                "NaturalProgram.initialize()",
                "NaturalProgram.terminate()",
                "WorkingStorage field declarations",
            ],
        ),
        output_artifacts=["documentation", "data_dictionary"],
        doc_objectives=[
            "Recover original NATURAL program logic from transpiled code",
            "Identify Working Storage data structures and their business meaning",
            "Map PERFORM paragraphs to logical subroutines",
            "Document ADABAS database access patterns",
        ],
        doc_anti_objectives=[
            "Transpiler-generated scaffolding and boilerplate",
            "Runtime library internals",
            "Java-specific implementation artifacts",
        ],
        objectives_override=(
            "This code was mechanically transpiled from Software AG NATURAL to "
            "Java. Your goal is to document the ORIGINAL business logic, not the "
            "Java translation artifacts. For each module: (1) Identify the "
            "original NATURAL program structure (Working Storage, main logic, "
            "PERFORMs), (2) Document data structures with their business meaning, "
            "(3) Explain the business workflow in terms of the original NATURAL "
            "constructs, (4) Flag ADABAS database access patterns (READ, FIND, "
            "GET, STORE, UPDATE, DELETE)."
        ),
    )


# ---------------------------------------------------------------------------
# Projection resolver
# ---------------------------------------------------------------------------

_BUILTIN_PROJECTIONS = {
    "developer": get_developer_projection,
    "business": get_business_projection,
    "ejb-migration": get_ejb_migration_projection,
    "natural-transpiled": get_natural_transpiled_projection,
}


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
        return _BUILTIN_PROJECTIONS[name_or_path]()

    # 2. JSON file path
    if name_or_path.endswith(".json"):
        if not os.path.isfile(name_or_path):
            raise ValueError(f"Projection file not found: {name_or_path}")
        with open(name_or_path, "r") as f:
            data = json.load(f)
        return ProjectionConfig.from_dict(data)

    # 3. Project-local .codewiki/projections/{name}.json
    local_path = os.path.join(".codewiki", "projections", f"{name_or_path}.json")
    if os.path.isfile(local_path):
        with open(local_path, "r") as f:
            data = json.load(f)
        return ProjectionConfig.from_dict(data)

    # 4. Unknown
    available = ", ".join(sorted(_BUILTIN_PROJECTIONS.keys()))
    raise ValueError(
        f"Unknown projection '{name_or_path}'. "
        f"Available built-in projections: {available}. "
        f"Or provide a path to a .json file."
    )
