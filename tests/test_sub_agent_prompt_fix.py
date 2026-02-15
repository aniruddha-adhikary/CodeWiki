"""Tests for Phase 3: Sub-agent prompt fix and CodeWikiDeps new fields.

Validates that generate_sub_module_documentation() correctly propagates
projection context (code_context, framework_context, objectives_override,
glossary_block) through to sub-agent system prompts.
"""

import pytest
from dataclasses import fields as dataclass_fields
from unittest.mock import AsyncMock, MagicMock, patch

from codewiki.src.be.agent_tools.deps import CodeWikiDeps
from codewiki.src.be.prompt_template import DEFAULT_OBJECTIVES


# ---------------------------------------------------------------------------
# CodeWikiDeps new fields
# ---------------------------------------------------------------------------


class TestCodeWikiDepsNewFields:
    """CodeWikiDeps must accept all new projection fields with safe defaults."""

    @staticmethod
    def _make_deps(**overrides):
        """Build a CodeWikiDeps with minimal required fields + overrides."""
        defaults = dict(
            absolute_docs_path="/tmp/docs",
            absolute_repo_path="/tmp/repo",
            registry={},
            components={},
            path_to_current_module=[],
            current_module_name="root",
            module_tree={},
            max_depth=2,
            current_depth=0,
            config=MagicMock(),
        )
        defaults.update(overrides)
        return CodeWikiDeps(**defaults)

    def test_defaults_are_none_or_empty(self):
        deps = self._make_deps()
        assert deps.custom_instructions is None
        assert deps.code_context is None
        assert deps.framework_context is None
        assert deps.objectives_override is None
        assert deps.glossary_block is None
        assert deps.supplementary_files == {}
        assert deps.projection_name is None

    def test_all_fields_populated(self):
        deps = self._make_deps(
            custom_instructions="focus on APIs",
            code_context="<CODE_CONTEXT>Java 8</CODE_CONTEXT>",
            framework_context="<FRAMEWORK_CONTEXT>EJB 2.1</FRAMEWORK_CONTEXT>",
            objectives_override="Help business stakeholders",
            glossary_block="<GLOSSARY>terms</GLOSSARY>",
            supplementary_files={"ejb-jar.xml": "<ejb>content</ejb>"},
            projection_name="ejb-migration",
        )
        assert deps.code_context == "<CODE_CONTEXT>Java 8</CODE_CONTEXT>"
        assert deps.framework_context == "<FRAMEWORK_CONTEXT>EJB 2.1</FRAMEWORK_CONTEXT>"
        assert deps.objectives_override == "Help business stakeholders"
        assert deps.glossary_block == "<GLOSSARY>terms</GLOSSARY>"
        assert deps.supplementary_files == {"ejb-jar.xml": "<ejb>content</ejb>"}
        assert deps.projection_name == "ejb-migration"

    def test_field_names_exist(self):
        """All expected field names must be present on the dataclass."""
        field_names = {f.name for f in dataclass_fields(CodeWikiDeps)}
        expected = {
            "code_context",
            "framework_context",
            "objectives_override",
            "glossary_block",
            "supplementary_files",
            "projection_name",
        }
        assert expected.issubset(field_names)


# ---------------------------------------------------------------------------
# Sub-agent prompt propagation
# ---------------------------------------------------------------------------


class TestSubAgentPromptPropagation:
    """generate_sub_module_documentation() must pass deps projection
    fields through to format_system_prompt / format_leaf_system_prompt."""

    @staticmethod
    def _make_fake_component(name: str):
        comp = MagicMock()
        comp.relative_path = f"{name}.java"
        comp.file_path = f"/tmp/repo/{name}.java"
        return comp

    @staticmethod
    def _make_deps_with_projection():
        config = MagicMock()
        config.max_token_per_leaf_module = 16000
        config.max_depth = 2
        return CodeWikiDeps(
            absolute_docs_path="/tmp/docs",
            absolute_repo_path="/tmp/repo",
            registry={},
            components={
                "com.A": TestSubAgentPromptPropagation._make_fake_component("A"),
                "com.B": TestSubAgentPromptPropagation._make_fake_component("B"),
            },
            path_to_current_module=[],
            current_module_name="root",
            module_tree={},
            max_depth=2,
            current_depth=0,
            config=config,
            custom_instructions="focus on APIs",
            code_context="<CODE_CONTEXT>Java 8 codebase</CODE_CONTEXT>",
            framework_context="<FRAMEWORK_CONTEXT>EJB 2.1</FRAMEWORK_CONTEXT>",
            objectives_override="Help business stakeholders",
            glossary_block="<GLOSSARY>terms here</GLOSSARY>",
        )

    @pytest.mark.asyncio
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.create_fallback_models")
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.Agent")
    async def test_complex_sub_agent_receives_projection_blocks(self, MockAgent, mock_models):
        """A complex sub-module's system prompt must include all projection blocks."""
        from codewiki.src.be.agent_tools.generate_sub_module_documentations import (
            generate_sub_module_documentation,
        )

        mock_models.return_value = MagicMock()

        # Make the agent.run() return a mock result
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run = AsyncMock(return_value=MagicMock())
        MockAgent.return_value = mock_agent_instance

        deps = self._make_deps_with_projection()
        # Make it look complex: multiple files + under max_depth
        # is_complex_module returns True when > 1 file
        ctx = MagicMock()
        ctx.deps = deps

        with patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.is_complex_module",
            return_value=True,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.count_tokens",
            return_value=100000,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.format_user_prompt",
            return_value="user prompt",
        ):
            await generate_sub_module_documentation(
                ctx,
                sub_module_specs={"sub_mod": ["com.A", "com.B"]},
            )

        # Agent was called once
        MockAgent.assert_called_once()
        call_kwargs = MockAgent.call_args
        system_prompt = call_kwargs.kwargs.get("system_prompt") or call_kwargs[1].get("system_prompt")

        assert "<CODE_CONTEXT>" in system_prompt
        assert "Java 8 codebase" in system_prompt
        assert "<FRAMEWORK_CONTEXT>" in system_prompt
        assert "EJB 2.1" in system_prompt
        assert "business stakeholders" in system_prompt
        assert "<GLOSSARY>" in system_prompt
        assert "terms here" in system_prompt

    @pytest.mark.asyncio
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.create_fallback_models")
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.Agent")
    async def test_leaf_sub_agent_receives_projection_blocks(self, MockAgent, mock_models):
        """A leaf sub-module's system prompt must include all projection blocks."""
        from codewiki.src.be.agent_tools.generate_sub_module_documentations import (
            generate_sub_module_documentation,
        )

        mock_models.return_value = MagicMock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run = AsyncMock(return_value=MagicMock())
        MockAgent.return_value = mock_agent_instance

        deps = self._make_deps_with_projection()
        ctx = MagicMock()
        ctx.deps = deps

        with patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.is_complex_module",
            return_value=False,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.count_tokens",
            return_value=100,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.format_user_prompt",
            return_value="user prompt",
        ):
            await generate_sub_module_documentation(
                ctx,
                sub_module_specs={"leaf_mod": ["com.A"]},
            )

        MockAgent.assert_called_once()
        call_kwargs = MockAgent.call_args
        system_prompt = call_kwargs.kwargs.get("system_prompt") or call_kwargs[1].get("system_prompt")

        assert "<CODE_CONTEXT>" in system_prompt
        assert "<FRAMEWORK_CONTEXT>" in system_prompt
        assert "business stakeholders" in system_prompt
        assert "<GLOSSARY>" in system_prompt

    @pytest.mark.asyncio
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.create_fallback_models")
    @patch("codewiki.src.be.agent_tools.generate_sub_module_documentations.Agent")
    async def test_none_deps_produces_default_behavior(self, MockAgent, mock_models):
        """With all projection fields None, sub-agent prompts behave as before."""
        from codewiki.src.be.agent_tools.generate_sub_module_documentations import (
            generate_sub_module_documentation,
        )

        mock_models.return_value = MagicMock()

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run = AsyncMock(return_value=MagicMock())
        MockAgent.return_value = mock_agent_instance

        config = MagicMock()
        config.max_token_per_leaf_module = 16000
        config.max_depth = 2

        deps = CodeWikiDeps(
            absolute_docs_path="/tmp/docs",
            absolute_repo_path="/tmp/repo",
            registry={},
            components={
                "com.A": self._make_fake_component("A"),
            },
            path_to_current_module=[],
            current_module_name="root",
            module_tree={},
            max_depth=2,
            current_depth=0,
            config=config,
            # All projection fields left at defaults (None)
        )
        ctx = MagicMock()
        ctx.deps = deps

        with patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.is_complex_module",
            return_value=False,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.count_tokens",
            return_value=100,
        ), patch(
            "codewiki.src.be.agent_tools.generate_sub_module_documentations.format_user_prompt",
            return_value="user prompt",
        ):
            await generate_sub_module_documentation(
                ctx,
                sub_module_specs={"simple": ["com.A"]},
            )

        MockAgent.assert_called_once()
        call_kwargs = MockAgent.call_args
        system_prompt = call_kwargs.kwargs.get("system_prompt") or call_kwargs[1].get("system_prompt")

        # No projection blocks should appear
        assert "<CODE_CONTEXT>" not in system_prompt
        assert "<FRAMEWORK_CONTEXT>" not in system_prompt
        assert "<GLOSSARY>" not in system_prompt
        # Default objectives should be present
        assert DEFAULT_OBJECTIVES in system_prompt
