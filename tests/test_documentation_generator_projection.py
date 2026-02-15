"""Tests for DocumentationGenerator projection integration."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from codewiki.src.be.documentation_generator import (
    DocumentationGenerator,
    collect_supplementary_files,
)
from codewiki.src.be.projection import (
    get_business_projection,
    get_natural_transpiled_projection,
    get_developer_projection,
    ProjectionConfig,
)
from codewiki.src.config import Config


def make_mock_config():
    config = MagicMock(spec=Config)
    config.get_prompt_addition.return_value = ""
    config.main_model = "test-model"
    config.cluster_model = "test-model"
    config.fallback_model = "test-model"
    config.max_depth = 2
    config.max_tokens = 32768
    config.max_token_per_module = 36369
    config.max_token_per_leaf_module = 16000
    config.repo_path = "/tmp/test-repo"
    config.docs_dir = "/tmp/test-docs"
    config.llm_base_url = "http://localhost"
    config.llm_api_key = "test-key"
    config.agent_instructions = None
    return config


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
class TestInitWithProjection:
    def test_projection_stored_and_forwarded(self, mock_graph_builder, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_business_projection()

        gen = DocumentationGenerator(config, projection=projection)

        assert gen.projection is projection
        assert gen.agent_orchestrator.projection is projection


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
class TestInitWithoutProjection:
    def test_projection_is_none(self, mock_graph_builder, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()

        gen = DocumentationGenerator(config)

        assert gen.projection is None


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
@patch("codewiki.src.be.documentation_generator.file_manager")
class TestMetadataIncludesProjection:
    def test_metadata_includes_projection_name(
        self, mock_fm, mock_graph_builder, mock_fallback, tmp_path
    ):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_business_projection()

        gen = DocumentationGenerator(config, projection=projection)

        working_dir = str(tmp_path)
        components = {"c1": MagicMock()}

        # Capture what save_json is called with
        saved = {}

        def capture_save_json(data, path):
            saved["data"] = data
            saved["path"] = path

        mock_fm.save_json.side_effect = capture_save_json

        gen.create_documentation_metadata(working_dir, components, 1)

        assert saved["data"]["projection"] == "business"

    def test_metadata_no_projection(
        self, mock_fm, mock_graph_builder, mock_fallback, tmp_path
    ):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()

        gen = DocumentationGenerator(config)

        working_dir = str(tmp_path)
        components = {"c1": MagicMock()}

        saved = {}

        def capture_save_json(data, path):
            saved["data"] = data
            saved["path"] = path

        mock_fm.save_json.side_effect = capture_save_json

        gen.create_documentation_metadata(working_dir, components, 1)

        assert saved["data"]["projection"] is None


@pytest.mark.asyncio
@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.file_manager")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
@patch("codewiki.src.be.documentation_generator.cluster_modules")
class TestClusterModulesReceivesProjection:
    async def test_cluster_called_with_projection(
        self, mock_cluster, mock_graph_builder, mock_fm, mock_fallback
    ):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_business_projection()

        mock_components = {"c1": MagicMock()}
        mock_graph_builder.return_value.build_dependency_graph.return_value = (
            mock_components,
            ["c1"],
        )
        mock_cluster.return_value = {}
        mock_fm.load_json.return_value = {}
        mock_fm.ensure_directory.return_value = None

        gen = DocumentationGenerator(config, projection=projection)
        gen.generate_module_documentation = AsyncMock(return_value="/tmp/test-docs")
        gen.create_documentation_metadata = MagicMock()

        # Make os.path.exists return False so clustering happens
        with patch("os.path.exists", return_value=False):
            await gen.run()

        mock_cluster.assert_called_once()
        _, kwargs = mock_cluster.call_args
        assert kwargs["projection"] is projection


@pytest.mark.asyncio
@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.generate_glossary")
@patch("codewiki.src.be.documentation_generator.render_glossary_md")
@patch("codewiki.src.be.documentation_generator.file_manager")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
@patch("codewiki.src.be.documentation_generator.cluster_modules")
class TestGlossaryGenerationTriggered:
    async def test_glossary_triggered_with_data_dictionary(
        self,
        mock_cluster,
        mock_graph_builder,
        mock_fm,
        mock_render,
        mock_gen_glossary,
        mock_fallback,
    ):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_natural_transpiled_projection()
        assert "data_dictionary" in projection.output_artifacts

        mock_components = {"c1": MagicMock()}
        mock_graph_builder.return_value.build_dependency_graph.return_value = (
            mock_components,
            ["c1"],
        )
        mock_cluster.return_value = {}
        mock_fm.load_json.return_value = {}
        mock_fm.ensure_directory.return_value = None

        mock_glossary = MagicMock()
        mock_glossary.entries = {"test": MagicMock()}
        mock_glossary.to_prompt_block.return_value = "<GLOSSARY>test</GLOSSARY>"
        mock_glossary.to_dict.return_value = {"entries": {}}
        mock_gen_glossary.return_value = mock_glossary
        mock_render.return_value = "# Glossary"

        gen = DocumentationGenerator(config, projection=projection)
        gen.generate_module_documentation = AsyncMock(return_value="/tmp/test-docs")
        gen.create_documentation_metadata = MagicMock()

        with patch("os.path.exists", return_value=False):
            await gen.run()

        mock_gen_glossary.assert_called_once()
        assert gen.agent_orchestrator.glossary_block == "<GLOSSARY>test</GLOSSARY>"


@pytest.mark.asyncio
@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
@patch("codewiki.src.be.documentation_generator.generate_glossary")
@patch("codewiki.src.be.documentation_generator.file_manager")
@patch("codewiki.src.be.documentation_generator.DependencyGraphBuilder")
@patch("codewiki.src.be.documentation_generator.cluster_modules")
class TestGlossaryNotTriggeredWithoutDataDictionary:
    async def test_glossary_not_triggered_without_data_dictionary(
        self,
        mock_cluster,
        mock_graph_builder,
        mock_fm,
        mock_gen_glossary,
        mock_fallback,
    ):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_business_projection()
        assert "data_dictionary" not in projection.output_artifacts

        mock_components = {"c1": MagicMock()}
        mock_graph_builder.return_value.build_dependency_graph.return_value = (
            mock_components,
            ["c1"],
        )
        mock_cluster.return_value = {}
        mock_fm.load_json.return_value = {}
        mock_fm.ensure_directory.return_value = None

        gen = DocumentationGenerator(config, projection=projection)
        gen.generate_module_documentation = AsyncMock(return_value="/tmp/test-docs")
        gen.create_documentation_metadata = MagicMock()

        with patch("os.path.exists", return_value=False):
            await gen.run()

        mock_gen_glossary.assert_not_called()


class TestConfigHasProjectionField:
    def test_config_accepts_projection_field(self):
        config = Config(
            repo_path="/tmp/test",
            output_dir="/tmp/out",
            dependency_graph_dir="/tmp/dep",
            docs_dir="/tmp/docs",
            max_depth=2,
            llm_base_url="http://localhost",
            llm_api_key="test-key",
            main_model="test-model",
            cluster_model="test-model",
            projection="business",
        )
        assert config.projection == "business"

    def test_config_projection_default_none(self):
        config = Config(
            repo_path="/tmp/test",
            output_dir="/tmp/out",
            dependency_graph_dir="/tmp/dep",
            docs_dir="/tmp/docs",
            max_depth=2,
            llm_base_url="http://localhost",
            llm_api_key="test-key",
            main_model="test-model",
            cluster_model="test-model",
        )
        assert config.projection is None
