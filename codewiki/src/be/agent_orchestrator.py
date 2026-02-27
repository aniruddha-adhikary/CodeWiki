from pydantic_ai import Agent
# import logfire
import logging
import os
import traceback
from typing import Dict, List, Any

# Configure logging and monitoring

logger = logging.getLogger(__name__)

# try:
#     # Configure logfire with environment variables for Docker compatibility
#     logfire_token = os.getenv('LOGFIRE_TOKEN')
#     logfire_project = os.getenv('LOGFIRE_PROJECT_NAME', 'default')
#     logfire_service = os.getenv('LOGFIRE_SERVICE_NAME', 'default')
    
#     if logfire_token:
#         # Configure with explicit token (for Docker)
#         logfire.configure(
#             token=logfire_token,
#             project_name=logfire_project,
#             service_name=logfire_service,
#         )
#     else:
#         # Use default configuration (for local development with logfire auth)
#         logfire.configure(
#             project_name=logfire_project,
#             service_name=logfire_service,
#         )
    
#     logfire.instrument_pydantic_ai()
#     logger.debug(f"Logfire configured successfully for project: {logfire_project}")
    
# except Exception as e:
#     logger.warning(f"Failed to configure logfire: {e}")

# Local imports
from codewiki.src.be.agent_tools.deps import CodeWikiDeps
from codewiki.src.be.projection import ProjectionConfig, compile_projection_instructions
from codewiki.src.be.agent_tools.read_code_components import read_code_components_tool
from codewiki.src.be.agent_tools.str_replace_editor import str_replace_editor_tool
from codewiki.src.be.agent_tools.generate_sub_module_documentations import generate_sub_module_documentation_tool
from codewiki.src.be.utils import filter_supplementary_for_module
from codewiki.src.be.llm_services import create_fallback_models
from codewiki.src.be.prompt_template import (
    format_user_prompt,
    format_system_prompt,
    format_leaf_system_prompt,
)
from codewiki.src.be.utils import is_complex_module
from codewiki.src.config import (
    Config,
    MODULE_TREE_FILENAME,
    OVERVIEW_FILENAME,
)
from codewiki.src.utils import file_manager
from codewiki.src.be.dependency_analyzer.models.core import Node


class AgentOrchestrator:
    """Orchestrates the AI agents for documentation generation."""
    
    def __init__(self, config: Config, projection: ProjectionConfig = None):
        self.config = config
        self.projection = projection
        self.fallback_models = create_fallback_models(config)

        # Compile projection instructions
        base_instructions = config.get_prompt_addition() if config else ""
        if projection:
            self.compiled = compile_projection_instructions(projection)
            # Merge compiled custom_instructions with existing
            parts = [p for p in [base_instructions, self.compiled.custom_instructions] if p]
            self.custom_instructions = "\n".join(parts) if parts else None
        else:
            self.compiled = None
            self.custom_instructions = base_instructions or None

        # These will be set by the pipeline (DocumentationGenerator) later
        self.glossary_block = ""
        self.supplementary_files = {}
    
    def create_agent(self, module_name: str, components: Dict[str, Any],
                    core_component_ids: List[str]) -> Agent:
        """Create an appropriate agent based on module complexity."""

        # Get projection prompt fields
        code_context = self.compiled.code_context_block if self.compiled else None
        framework_context = self.compiled.framework_context_block if self.compiled else None
        objectives = self.compiled.objectives_override if self.compiled else None
        glossary = self.glossary_block or None

        if is_complex_module(components, core_component_ids):
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[
                    read_code_components_tool,
                    str_replace_editor_tool,
                    generate_sub_module_documentation_tool
                ],
                system_prompt=format_system_prompt(
                    module_name, self.custom_instructions,
                    code_context=code_context,
                    framework_context=framework_context,
                    objectives=objectives,
                    glossary=glossary,
                ),
            )
        else:
            return Agent(
                self.fallback_models,
                name=module_name,
                deps_type=CodeWikiDeps,
                tools=[read_code_components_tool, str_replace_editor_tool],
                system_prompt=format_leaf_system_prompt(
                    module_name, self.custom_instructions,
                    code_context=code_context,
                    framework_context=framework_context,
                    objectives=objectives,
                    glossary=glossary,
                ),
            )
    
    async def process_module(self, module_name: str, components: Dict[str, Node], 
                           core_component_ids: List[str], module_path: List[str], working_dir: str) -> Dict[str, Any]:
        """Process a single module and generate its documentation."""
        logger.info(f"Processing module: {module_name}")
        
        # Load or create module tree
        module_tree_path = os.path.join(working_dir, MODULE_TREE_FILENAME)
        module_tree = file_manager.load_json(module_tree_path)
        
        # Create agent
        agent = self.create_agent(module_name, components, core_component_ids)
        
        # Create dependencies
        deps = CodeWikiDeps(
            absolute_docs_path=working_dir,
            absolute_repo_path=str(os.path.abspath(self.config.repo_path)),
            registry={},
            components=components,
            path_to_current_module=module_path,
            current_module_name=module_name,
            module_tree=module_tree,
            max_depth=self.config.max_depth,
            current_depth=1,
            config=self.config,
            custom_instructions=self.custom_instructions,
            # Projection fields
            code_context=self.compiled.code_context_block if self.compiled else None,
            framework_context=self.compiled.framework_context_block if self.compiled else None,
            objectives_override=self.compiled.objectives_override if self.compiled else None,
            glossary_block=self.glossary_block or None,
            supplementary_files=self.supplementary_files,
            projection_name=self.projection.name if self.projection else None,
        )

        # check if overview docs already exists
        overview_docs_path = os.path.join(working_dir, OVERVIEW_FILENAME)
        if os.path.exists(overview_docs_path):
            logger.info(f"✓ Overview docs already exists at {overview_docs_path}")
            return module_tree

        # check if module docs already exists
        docs_path = os.path.join(working_dir, f"{module_name}.md")
        if os.path.exists(docs_path):
            logger.info(f"✓ Module docs already exists at {docs_path}")
            return module_tree
        
        # Filter supplementary files for this module
        module_component_paths = [
            components[cid].relative_path
            for cid in core_component_ids
            if cid in components
        ]
        filtered_supplementary = filter_supplementary_for_module(
            self.supplementary_files, module_component_paths
        )

        # Run agent
        try:
            result = await agent.run(
                format_user_prompt(
                    module_name=module_name,
                    core_component_ids=core_component_ids,
                    components=components,
                    module_tree=deps.module_tree,
                    supplementary_files=filtered_supplementary,
                    supplementary_file_role=(
                        self.projection.supplementary_file_role
                        if self.projection
                        else None
                    ),
                ),
                deps=deps
            )
            
            # Save updated module tree
            file_manager.save_json(deps.module_tree, module_tree_path)

            # Verify documentation file was created
            docs_path = os.path.join(working_dir, f"{module_name}.md")
            if not os.path.exists(docs_path):
                logger.warning(f"Agent completed but no documentation file created for {module_name} at {docs_path}")

            logger.debug(f"Successfully processed module: {module_name}")

            return deps.module_tree
            
        except Exception as e:
            logger.error(f"Error processing module {module_name}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise