"""Tests for prompt template parameterization (Phase 2).

Validates that format_system_prompt, format_leaf_system_prompt, and
format_user_prompt correctly handle the new optional context slots
(code_context, framework_context, objectives, glossary) while
maintaining backwards compatibility with the original API.
"""

import pytest

from codewiki.src.be.prompt_template import (
    DEFAULT_OBJECTIVES,
    EXTENSION_TO_LANGUAGE,
    format_leaf_system_prompt,
    format_system_prompt,
    format_user_prompt,
)


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------


class TestBackwardsCompatibility:
    """Calling with only the original parameters must behave identically."""

    def test_format_system_prompt_legacy_call(self):
        result = format_system_prompt(module_name="test", custom_instructions="focus on APIs")
        assert DEFAULT_OBJECTIVES in result
        assert "<CUSTOM_INSTRUCTIONS>" in result
        assert "focus on APIs" in result
        # New optional blocks must NOT appear
        assert "<CODE_CONTEXT>" not in result
        assert "<FRAMEWORK_CONTEXT>" not in result
        assert "<GLOSSARY>" not in result

    def test_format_leaf_system_prompt_legacy_call(self):
        result = format_leaf_system_prompt(module_name="test", custom_instructions="focus on APIs")
        assert DEFAULT_OBJECTIVES in result
        assert "<CUSTOM_INSTRUCTIONS>" in result
        assert "focus on APIs" in result
        assert "<CODE_CONTEXT>" not in result
        assert "<FRAMEWORK_CONTEXT>" not in result
        assert "<GLOSSARY>" not in result


# ---------------------------------------------------------------------------
# DEFAULT_OBJECTIVES constant
# ---------------------------------------------------------------------------


class TestDefaultObjectives:
    def test_contains_target_audience(self):
        assert "developers and maintainers" in DEFAULT_OBJECTIVES

    def test_contains_module_purpose(self):
        assert "module's purpose" in DEFAULT_OBJECTIVES


# ---------------------------------------------------------------------------
# Custom objectives override
# ---------------------------------------------------------------------------


class TestCustomObjectives:
    def test_custom_objectives_replaces_default(self):
        result = format_system_prompt(module_name="m", objectives="Help business stakeholders")
        assert "business stakeholders" in result
        assert "developers and maintainers" not in result

    def test_leaf_custom_objectives_replaces_default(self):
        result = format_leaf_system_prompt(module_name="m", objectives="Help business stakeholders")
        assert "business stakeholders" in result
        assert "developers and maintainers" not in result


# ---------------------------------------------------------------------------
# Block ordering
# ---------------------------------------------------------------------------


class TestBlockOrdering:
    """When all optional blocks are provided, they must appear in the
    correct order: CODE_CONTEXT < FRAMEWORK_CONTEXT < OBJECTIVES < GLOSSARY < DOCUMENTATION_STRUCTURE."""

    @pytest.fixture()
    def full_prompt(self):
        return format_system_prompt(
            module_name="m",
            code_context="<CODE_CONTEXT>test</CODE_CONTEXT>",
            framework_context="<FRAMEWORK_CONTEXT>ejb</FRAMEWORK_CONTEXT>",
            objectives="custom obj",
            glossary="<GLOSSARY>terms</GLOSSARY>",
        )

    def test_code_before_framework(self, full_prompt):
        assert full_prompt.index("<CODE_CONTEXT>") < full_prompt.index("<FRAMEWORK_CONTEXT>")

    def test_framework_before_objectives(self, full_prompt):
        assert full_prompt.index("<FRAMEWORK_CONTEXT>") < full_prompt.index("<OBJECTIVES>")

    def test_objectives_before_glossary(self, full_prompt):
        assert full_prompt.index("<OBJECTIVES>") < full_prompt.index("<GLOSSARY>")

    def test_glossary_before_doc_structure(self, full_prompt):
        assert full_prompt.index("<GLOSSARY>") < full_prompt.index("<DOCUMENTATION_STRUCTURE>")


# ---------------------------------------------------------------------------
# Conditional emptiness
# ---------------------------------------------------------------------------


class TestConditionalEmptiness:
    """Each optional param as None must produce no corresponding XML block."""

    def test_no_code_context_when_none(self):
        result = format_system_prompt(module_name="m", code_context=None)
        assert "<CODE_CONTEXT>" not in result

    def test_no_framework_context_when_none(self):
        result = format_system_prompt(module_name="m", framework_context=None)
        assert "<FRAMEWORK_CONTEXT>" not in result

    def test_no_glossary_when_none(self):
        result = format_system_prompt(module_name="m", glossary=None)
        assert "<GLOSSARY>" not in result

    def test_default_objectives_when_none(self):
        result = format_system_prompt(module_name="m", objectives=None)
        assert DEFAULT_OBJECTIVES in result

    def test_leaf_no_code_context_when_none(self):
        result = format_leaf_system_prompt(module_name="m", code_context=None)
        assert "<CODE_CONTEXT>" not in result

    def test_leaf_no_framework_context_when_none(self):
        result = format_leaf_system_prompt(module_name="m", framework_context=None)
        assert "<FRAMEWORK_CONTEXT>" not in result

    def test_leaf_no_glossary_when_none(self):
        result = format_leaf_system_prompt(module_name="m", glossary=None)
        assert "<GLOSSARY>" not in result

    def test_leaf_default_objectives_when_none(self):
        result = format_leaf_system_prompt(module_name="m", objectives=None)
        assert DEFAULT_OBJECTIVES in result


# ---------------------------------------------------------------------------
# EXTENSION_TO_LANGUAGE mapping
# ---------------------------------------------------------------------------


class TestExtensionToLanguage:
    """New config-file extensions plus existing ones."""

    @pytest.mark.parametrize(
        "ext, lang",
        [
            (".xml", "xml"),
            (".yaml", "yaml"),
            (".yml", "yaml"),
            (".properties", "properties"),
            (".py", "python"),
            (".java", "java"),
            (".js", "javascript"),
            (".ts", "typescript"),
        ],
    )
    def test_extension_mapping(self, ext, lang):
        assert EXTENSION_TO_LANGUAGE[ext] == lang


# ---------------------------------------------------------------------------
# format_user_prompt – supplementary files
# ---------------------------------------------------------------------------


class TestFormatUserPromptSupplementary:
    """format_user_prompt must embed supplementary file content when provided."""

    @staticmethod
    def _make_minimal_components():
        """Create a minimal components dict that format_user_prompt can consume."""

        class FakeComponent:
            def __init__(self, rel_path, file_path):
                self.relative_path = rel_path
                self.file_path = file_path

        return {
            "com.example.Main": FakeComponent("Main.java", "/dev/null"),
        }

    @staticmethod
    def _simple_module_tree():
        return {
            "example": {
                "components": ["com.example.Main"],
                "children": {},
            }
        }

    def test_supplementary_files_present(self):
        result = format_user_prompt(
            module_name="example",
            core_component_ids=["com.example.Main"],
            components=self._make_minimal_components(),
            module_tree=self._simple_module_tree(),
            supplementary_files={"ejb-jar.xml": "<ejb-jar>content</ejb-jar>"},
            supplementary_file_role="EJB descriptors",
        )
        assert "<SUPPLEMENTARY_CONFIGURATION>" in result
        assert "ejb-jar.xml" in result
        assert "EJB descriptors" in result
        assert "<ejb-jar>content</ejb-jar>" in result

    def test_no_supplementary_files(self):
        result = format_user_prompt(
            module_name="example",
            core_component_ids=["com.example.Main"],
            components=self._make_minimal_components(),
            module_tree=self._simple_module_tree(),
        )
        assert "<SUPPLEMENTARY_CONFIGURATION>" not in result
