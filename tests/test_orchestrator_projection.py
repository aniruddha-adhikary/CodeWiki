"""Tests for AgentOrchestrator projection integration."""

import pytest
from unittest.mock import patch, MagicMock, call

from codewiki.src.be.agent_orchestrator import AgentOrchestrator
from codewiki.src.be.projection import (
    get_business_projection,
    get_developer_projection,
    get_natural_transpiled_projection,
    compile_projection_instructions,
)
from codewiki.src.config import Config


def make_mock_config(prompt_addition=""):
    config = MagicMock(spec=Config)
    config.get_prompt_addition.return_value = prompt_addition
    config.main_model = "test-model"
    config.cluster_model = "test-model"
    config.fallback_model = "test-model"
    config.max_depth = 2
    config.max_token_per_leaf_module = 16000
    config.repo_path = "/tmp/test-repo"
    config.llm_base_url = "http://localhost"
    config.llm_api_key = "test-key"
    return config


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestInitWithBusinessProjection:
    def test_init_with_business_projection(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_business_projection()

        orch = AgentOrchestrator(config, projection=projection)

        assert orch.compiled is not None
        assert orch.compiled.objectives_override is not None
        assert "product managers" in orch.custom_instructions


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestInitWithoutProjection:
    def test_init_without_projection(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()

        orch = AgentOrchestrator(config, projection=None)

        assert orch.compiled is None
        assert orch.glossary_block == ""
        assert orch.supplementary_files == {}


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestInitMergesBaseAndProjectionInstructions:
    def test_init_merges_base_and_projection_instructions(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config(prompt_addition="Focus on APIs")
        projection = get_business_projection()

        orch = AgentOrchestrator(config, projection=projection)

        assert "Focus on APIs" in orch.custom_instructions
        assert "product managers" in orch.custom_instructions


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestCreateAgentWithProjection:
    def test_create_agent_with_projection(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()
        projection = get_natural_transpiled_projection()

        orch = AgentOrchestrator(config, projection=projection)

        # Use a single-file component so is_complex_module returns False (leaf path)
        mock_node = MagicMock()
        mock_node.file_path = "/tmp/test-repo/main.py"
        components = {"comp1": mock_node}
        core_ids = ["comp1"]

        with patch("codewiki.src.be.agent_orchestrator.Agent") as MockAgent:
            orch.create_agent("test-module", components, core_ids)
            # Agent was called once
            assert MockAgent.call_count == 1
            _, kwargs = MockAgent.call_args
            system_prompt = kwargs["system_prompt"]
            assert "NATURAL" in system_prompt
            assert "<CODE_CONTEXT>" in system_prompt


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestCreateAgentWithoutProjection:
    def test_create_agent_without_projection(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()

        orch = AgentOrchestrator(config, projection=None)

        mock_node = MagicMock()
        mock_node.file_path = "/tmp/test-repo/main.py"
        components = {"comp1": mock_node}
        core_ids = ["comp1"]

        with patch("codewiki.src.be.agent_orchestrator.Agent") as MockAgent:
            orch.create_agent("test-module", components, core_ids)
            assert MockAgent.call_count == 1
            _, kwargs = MockAgent.call_args
            system_prompt = kwargs["system_prompt"]
            assert "<CODE_CONTEXT>" not in system_prompt


@patch("codewiki.src.be.agent_orchestrator.create_fallback_models")
class TestGlossaryAndSupplementaryAttrs:
    def test_glossary_and_supplementary_attrs(self, mock_fallback):
        mock_fallback.return_value = MagicMock()
        config = make_mock_config()

        orch = AgentOrchestrator(config)

        # Set attributes
        orch.glossary_block = "<GLOSSARY>terms</GLOSSARY>"
        orch.supplementary_files = {"test.xml": "content"}

        assert orch.glossary_block == "<GLOSSARY>terms</GLOSSARY>"
        assert orch.supplementary_files == {"test.xml": "content"}
