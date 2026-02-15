"""Glossary / data dictionary generation for projection framework.

Extracts meaningful identifiers from code components and uses LLM to
produce business-friendly names and definitions.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Data models                                                         #
# ------------------------------------------------------------------ #

@dataclass
class GlossaryEntry:
    identifier: str
    business_name: str
    definition: str
    category: str  # "entity", "operation", "field", "constant"
    confidence: float  # 0.0 - 1.0
    source_files: List[str] = field(default_factory=list)
    component_ids: List[str] = field(default_factory=list)


@dataclass
class Glossary:
    entries: Dict[str, GlossaryEntry] = field(default_factory=dict)

    # -- serialization --------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": {
                k: {
                    "identifier": v.identifier,
                    "business_name": v.business_name,
                    "definition": v.definition,
                    "category": v.category,
                    "confidence": v.confidence,
                    "source_files": v.source_files,
                    "component_ids": v.component_ids,
                }
                for k, v in self.entries.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Glossary":
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = GlossaryEntry(
                identifier=v["identifier"],
                business_name=v["business_name"],
                definition=v["definition"],
                category=v["category"],
                confidence=v["confidence"],
                source_files=v.get("source_files", []),
                component_ids=v.get("component_ids", []),
            )
        return cls(entries=entries)

    # -- prompt rendering -----------------------------------------------

    def to_prompt_block(self, max_entries: int = 200) -> str:
        if not self.entries:
            return ""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.confidence,
            reverse=True,
        )[:max_entries]
        lines = ["<GLOSSARY>", "Code identifier -> Business meaning:"]
        for entry in sorted_entries:
            lines.append(
                f"  - {entry.identifier} -> {entry.business_name}: {entry.definition}"
            )
        lines.append("</GLOSSARY>")
        return "\n".join(lines)


# ------------------------------------------------------------------ #
# Generic-name filter                                                 #
# ------------------------------------------------------------------ #

GENERIC_NAMES = frozenset(
    {
        "i", "j", "k", "n", "x", "y", "e", "f", "s", "t", "v",
        "get", "set", "put", "add", "run", "init", "main", "test",
        "toString", "hashCode", "equals", "clone", "close",
        "__init__", "__str__", "__repr__", "__eq__", "__hash__",
        "self", "cls", "args", "kwargs", "this",
    }
)


# ------------------------------------------------------------------ #
# Identifier extraction                                               #
# ------------------------------------------------------------------ #

def extract_identifiers(
    components: Dict[str, Any],
    leaf_nodes: List[str],
) -> Dict[str, List[str]]:
    """Extract meaningful identifiers mapped to component IDs.

    Returns a dict of ``{identifier: [component_id, ...]}`` excluding
    generic names and identifiers shorter than 3 characters.
    """
    identifiers: Dict[str, List[str]] = {}

    for node_id in leaf_nodes:
        if node_id not in components:
            continue
        node = components[node_id]

        # Node name (class, function, method)
        if node.name and node.name not in GENERIC_NAMES and len(node.name) > 2:
            identifiers.setdefault(node.name, []).append(node_id)

        # Parameters
        if node.parameters:
            for param in node.parameters:
                param_name = param.split(":")[0].split("=")[0].strip()
                if (
                    param_name
                    and param_name not in GENERIC_NAMES
                    and len(param_name) > 2
                ):
                    identifiers.setdefault(param_name, []).append(node_id)

        # Source code regex for fields
        if node.source_code:
            # Java fields: private/public/protected Type fieldName
            for match in re.finditer(
                r"(?:private|public|protected)\s+\w+\s+(\w+)\s*[;=]",
                node.source_code,
            ):
                name = match.group(1)
                if name not in GENERIC_NAMES and len(name) > 2:
                    identifiers.setdefault(name, []).append(node_id)
            # NATURAL WS_* variables
            for match in re.finditer(r"\b(WS_\w+)\b", node.source_code):
                identifiers.setdefault(match.group(1), []).append(node_id)

    return identifiers


# ------------------------------------------------------------------ #
# LLM-based glossary generation                                       #
# ------------------------------------------------------------------ #

GLOSSARY_PROMPT = """\
You are analyzing code identifiers to create a business glossary.
{context}

For each identifier below, propose a business-friendly name and definition.
Return your response as JSON inside <GLOSSARY_ENTRIES> tags.

Identifiers to analyze:
{identifiers}

<GLOSSARY_ENTRIES>
[
  {{"identifier": "...", "business_name": "...", "definition": "...", "category": "entity|operation|field|constant", "confidence": 0.0-1.0}}
]
</GLOSSARY_ENTRIES>
"""


def _parse_glossary_response(response: str) -> List[GlossaryEntry]:
    """Parse LLM response containing ``<GLOSSARY_ENTRIES>`` JSON block."""
    if "<GLOSSARY_ENTRIES>" not in response:
        return []
    content = (
        response.split("<GLOSSARY_ENTRIES>")[1]
        .split("</GLOSSARY_ENTRIES>")[0]
        .strip()
    )
    try:
        entries_data = json.loads(content)
        return [
            GlossaryEntry(
                identifier=e["identifier"],
                business_name=e["business_name"],
                definition=e["definition"],
                category=e.get("category", "field"),
                confidence=float(e.get("confidence", 0.5)),
            )
            for e in entries_data
        ]
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to parse glossary entries: %s", exc)
        return []


def generate_glossary(
    components: Dict[str, Any],
    leaf_nodes: List[str],
    config: "Config",
    context: str = "",
    batch_size: int = 80,
) -> Glossary:
    """Generate a business glossary from code identifiers via LLM.

    Parameters
    ----------
    components : dict of Node objects keyed by component ID.
    leaf_nodes : list of component IDs to scan.
    config : LLM configuration.
    context : optional provenance/context string for the LLM.
    batch_size : number of identifiers per LLM call.
    """
    from codewiki.src.be.llm_services import call_llm

    identifiers = extract_identifiers(components, leaf_nodes)
    if not identifiers:
        return Glossary()

    glossary = Glossary()
    id_list = list(identifiers.keys())

    for i in range(0, len(id_list), batch_size):
        batch = id_list[i : i + batch_size]
        batch_str = "\n".join(f"- {name}" for name in batch)

        context_str = f"\nContext: {context}" if context else ""
        prompt = GLOSSARY_PROMPT.format(context=context_str, identifiers=batch_str)

        try:
            response = call_llm(prompt, config)
            entries = _parse_glossary_response(response)
            for entry in entries:
                entry.component_ids = identifiers.get(entry.identifier, [])
                source_files: set[str] = set()
                for cid in entry.component_ids:
                    if cid in components:
                        source_files.add(components[cid].relative_path)
                entry.source_files = sorted(source_files)
                glossary.entries[entry.identifier] = entry
        except Exception as exc:
            logger.error(
                "Failed to process glossary batch %d-%d: %s",
                i,
                i + batch_size,
                exc,
            )
            continue

    return glossary


# ------------------------------------------------------------------ #
# Markdown rendering                                                  #
# ------------------------------------------------------------------ #

def render_glossary_md(glossary: Glossary) -> str:
    """Render a glossary as a human-readable Markdown table."""
    lines = [
        "# Glossary / Data Dictionary",
        "",
        "| Identifier | Business Name | Definition | Category | Confidence |",
        "|---|---|---|---|---|",
    ]
    sorted_entries = sorted(
        glossary.entries.values(),
        key=lambda e: (e.category, e.identifier),
    )
    for entry in sorted_entries:
        lines.append(
            f"| `{entry.identifier}` | {entry.business_name} | "
            f"{entry.definition} | {entry.category} | {entry.confidence:.1f} |"
        )
    return "\n".join(lines)
