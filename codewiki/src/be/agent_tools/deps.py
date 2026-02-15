from dataclasses import dataclass, field
from typing import Dict

from codewiki.src.be.dependency_analyzer.models.core import Node
from codewiki.src.config import Config

@dataclass
class CodeWikiDeps:
    absolute_docs_path: str
    absolute_repo_path: str
    registry: dict
    components: dict[str, Node]
    path_to_current_module: list[str]
    current_module_name: str
    module_tree: dict[str, any]
    max_depth: int
    current_depth: int
    config: Config  # LLM configuration
    custom_instructions: str = None
    code_context: str = None
    framework_context: str = None
    objectives_override: str = None
    glossary_block: str = None
    supplementary_files: Dict[str, str] = field(default_factory=dict)
    projection_name: str = None