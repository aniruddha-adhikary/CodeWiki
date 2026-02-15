"""Tests for projection-aware clustering (Phase 4).

Covers:
- format_cluster_prompt() with/without grouping_directive
- cluster_modules() with saved_grouping bypass
- cluster_modules() with business projection (clustering_goal passed)
- cluster_modules() without projection (backwards compatible)
"""

from unittest.mock import MagicMock, patch

import pytest

from codewiki.src.be.projection import ProjectionConfig, get_business_projection
from codewiki.src.be.prompt_template import format_cluster_prompt


# ---------------------------------------------------------------------------
# format_cluster_prompt() tests
# ---------------------------------------------------------------------------


class TestFormatClusterPromptGroupingDirective:
    """Test grouping_directive parameter in format_cluster_prompt()."""

    def test_no_directive_repo_prompt(self):
        """Repo prompt without directive has no GROUPING_STRATEGY block."""
        result = format_cluster_prompt("comp_a\ncomp_b")
        assert "<GROUPING_STRATEGY>" not in result
        assert "</GROUPING_STRATEGY>" not in result
        assert "<POTENTIAL_CORE_COMPONENTS>" in result

    def test_no_directive_module_prompt(self):
        """Module prompt without directive has no GROUPING_STRATEGY block."""
        tree = {"mod": {"components": ["c1"], "children": {}}}
        result = format_cluster_prompt("comp_a", module_tree=tree, module_name="mod")
        assert "<GROUPING_STRATEGY>" not in result
        assert "<MODULE_TREE>" in result

    def test_empty_string_directive(self):
        """Empty string directive produces no GROUPING_STRATEGY block."""
        result = format_cluster_prompt("comp_a", grouping_directive="")
        assert "<GROUPING_STRATEGY>" not in result

    def test_none_directive(self):
        """None directive produces no GROUPING_STRATEGY block."""
        result = format_cluster_prompt("comp_a", grouping_directive=None)
        assert "<GROUPING_STRATEGY>" not in result

    def test_directive_present_repo_prompt(self):
        """Repo prompt with directive includes GROUPING_STRATEGY block."""
        directive = "Group by business capabilities"
        result = format_cluster_prompt("comp_a\ncomp_b", grouping_directive=directive)
        assert "<GROUPING_STRATEGY>" in result
        assert "</GROUPING_STRATEGY>" in result
        assert directive in result

    def test_directive_present_module_prompt(self):
        """Module prompt with directive includes GROUPING_STRATEGY block."""
        tree = {"mod": {"components": ["c1"], "children": {}}}
        directive = "Group by domain context"
        result = format_cluster_prompt(
            "comp_a", module_tree=tree, module_name="mod", grouping_directive=directive
        )
        assert "<GROUPING_STRATEGY>" in result
        assert directive in result
        assert "<MODULE_TREE>" in result

    def test_directive_before_components_repo(self):
        """GROUPING_STRATEGY appears before POTENTIAL_CORE_COMPONENTS in repo prompt."""
        directive = "Group by business capabilities"
        result = format_cluster_prompt("comp_a", grouping_directive=directive)
        gs_pos = result.index("<GROUPING_STRATEGY>")
        pc_pos = result.index("<POTENTIAL_CORE_COMPONENTS>")
        assert gs_pos < pc_pos

    def test_directive_before_components_module(self):
        """GROUPING_STRATEGY appears before POTENTIAL_CORE_COMPONENTS in module prompt."""
        tree = {"mod": {"components": ["c1"], "children": {}}}
        directive = "Group by domain"
        result = format_cluster_prompt(
            "comp_a", module_tree=tree, module_name="mod", grouping_directive=directive
        )
        gs_pos = result.index("<GROUPING_STRATEGY>")
        pc_pos = result.index("<POTENTIAL_CORE_COMPONENTS>")
        assert gs_pos < pc_pos

    def test_backwards_compatible_output(self):
        """Output without directive matches expected format exactly."""
        result_no_dir = format_cluster_prompt("comp_a\ncomp_b")
        result_none = format_cluster_prompt("comp_a\ncomp_b", grouping_directive=None)
        assert result_no_dir == result_none


# ---------------------------------------------------------------------------
# cluster_modules() tests
# ---------------------------------------------------------------------------


def _make_node(name: str, relative_path: str = "src/file.py", source_code: str = "pass"):
    """Create a mock Node for testing."""
    node = MagicMock()
    node.relative_path = relative_path
    node.source_code = source_code
    return node


def _make_components(names):
    """Create a dict of mock components."""
    return {name: _make_node(name) for name in names}


def _first_high_then_low(threshold=100000, low=500):
    """Return a count_tokens side_effect: first call returns high, rest return low.

    Note: cluster_modules calls count_tokens twice when below threshold
    (once in the condition, once in the logger.debug format string).
    """
    calls = {"n": 0}

    def _counter(*args):
        calls["n"] += 1
        return threshold if calls["n"] == 1 else low

    return _counter


class TestClusterModulesSavedGrouping:
    """Test saved_grouping bypass in cluster_modules()."""

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens", return_value=100000)
    def test_saved_grouping_returns_directly(self, mock_tokens, mock_llm):
        """When saved_grouping is set, return it without calling LLM."""
        from codewiki.src.be.cluster_modules import cluster_modules

        saved = {"module_a": {"components": ["c1"], "children": {}}}
        projection = ProjectionConfig(saved_grouping=saved)
        config = MagicMock()

        result = cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
            projection=projection,
        )

        assert result == saved
        mock_llm.assert_not_called()

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens")
    def test_none_saved_grouping_calls_llm(self, mock_tokens, mock_llm):
        """When saved_grouping is None, LLM is called normally."""
        from codewiki.src.be.cluster_modules import cluster_modules

        mock_tokens.side_effect = _first_high_then_low()
        mock_llm.return_value = (
            '<GROUPED_COMPONENTS>\n'
            '{"mod_a": {"path": "src/a", "components": ["c1"]}, '
            '"mod_b": {"path": "src/b", "components": ["c2"]}}\n'
            '</GROUPED_COMPONENTS>'
        )
        projection = ProjectionConfig(saved_grouping=None)
        config = MagicMock()
        config.max_token_per_module = 1000

        result = cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
            projection=projection,
        )

        mock_llm.assert_called_once()
        assert "mod_a" in result
        assert "mod_b" in result


class TestClusterModulesBusinessProjection:
    """Test that business projection's clustering_goal is passed to prompt."""

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens")
    def test_clustering_goal_in_prompt(self, mock_tokens, mock_llm):
        """Business projection's clustering_goal appears in the LLM prompt."""
        from codewiki.src.be.cluster_modules import cluster_modules

        mock_tokens.side_effect = _first_high_then_low()
        mock_llm.return_value = (
            '<GROUPED_COMPONENTS>\n'
            '{"mod_a": {"path": "src/a", "components": ["c1"]}, '
            '"mod_b": {"path": "src/b", "components": ["c2"]}}\n'
            '</GROUPED_COMPONENTS>'
        )

        projection = get_business_projection()
        config = MagicMock()
        config.max_token_per_module = 1000

        cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
            projection=projection,
        )

        # Verify the prompt passed to call_llm contains GROUPING_STRATEGY
        prompt_arg = mock_llm.call_args[0][0]
        assert "<GROUPING_STRATEGY>" in prompt_arg
        assert projection.clustering_goal in prompt_arg

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens")
    def test_projection_propagated_to_recursive_calls(self, mock_tokens, mock_llm):
        """Projection is passed through recursive cluster_modules() calls."""
        from codewiki.src.be.cluster_modules import cluster_modules

        mock_tokens.side_effect = _first_high_then_low()
        mock_llm.return_value = (
            '<GROUPED_COMPONENTS>\n'
            '{"mod_a": {"path": "src/a", "components": ["c1"]}, '
            '"mod_b": {"path": "src/b", "components": ["c2"]}}\n'
            '</GROUPED_COMPONENTS>'
        )

        projection = ProjectionConfig(clustering_goal="Group by domain")
        config = MagicMock()
        config.max_token_per_module = 1000

        cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
            projection=projection,
        )

        # LLM called once for top level; recursive calls skip due to low token count
        assert mock_llm.call_count == 1
        prompt_arg = mock_llm.call_args[0][0]
        assert "Group by domain" in prompt_arg


class TestClusterModulesWithoutProjection:
    """Test that cluster_modules without projection behaves identically."""

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens")
    def test_no_projection_no_grouping_strategy(self, mock_tokens, mock_llm):
        """Without projection, no GROUPING_STRATEGY block in prompt."""
        from codewiki.src.be.cluster_modules import cluster_modules

        mock_tokens.side_effect = _first_high_then_low()
        mock_llm.return_value = (
            '<GROUPED_COMPONENTS>\n'
            '{"mod_a": {"path": "src/a", "components": ["c1"]}, '
            '"mod_b": {"path": "src/b", "components": ["c2"]}}\n'
            '</GROUPED_COMPONENTS>'
        )
        config = MagicMock()
        config.max_token_per_module = 1000

        cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
        )

        prompt_arg = mock_llm.call_args[0][0]
        assert "<GROUPING_STRATEGY>" not in prompt_arg

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens")
    def test_none_projection_no_grouping_strategy(self, mock_tokens, mock_llm):
        """Explicitly passing projection=None produces no GROUPING_STRATEGY."""
        from codewiki.src.be.cluster_modules import cluster_modules

        mock_tokens.side_effect = _first_high_then_low()
        mock_llm.return_value = (
            '<GROUPED_COMPONENTS>\n'
            '{"mod_a": {"path": "src/a", "components": ["c1"]}, '
            '"mod_b": {"path": "src/b", "components": ["c2"]}}\n'
            '</GROUPED_COMPONENTS>'
        )
        config = MagicMock()
        config.max_token_per_module = 1000

        cluster_modules(
            leaf_nodes=["c1", "c2"],
            components=_make_components(["c1", "c2"]),
            config=config,
            projection=None,
        )

        prompt_arg = mock_llm.call_args[0][0]
        assert "<GROUPING_STRATEGY>" not in prompt_arg

    @patch("codewiki.src.be.cluster_modules.call_llm")
    @patch("codewiki.src.be.cluster_modules.count_tokens", return_value=500)
    def test_skip_clustering_when_tokens_below_threshold(self, mock_tokens, mock_llm):
        """When token count is below threshold, return empty dict (no LLM call)."""
        from codewiki.src.be.cluster_modules import cluster_modules

        config = MagicMock()
        config.max_token_per_module = 1000

        result = cluster_modules(
            leaf_nodes=["c1"],
            components=_make_components(["c1"]),
            config=config,
        )

        assert result == {}
        mock_llm.assert_not_called()
