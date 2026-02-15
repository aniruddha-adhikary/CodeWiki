"""Tests for supplementary file collection, filtering, and prompt integration."""

import os
import tempfile

import pytest
from unittest.mock import MagicMock, patch

from codewiki.src.be.documentation_generator import collect_supplementary_files
from codewiki.src.be.utils import filter_supplementary_for_module
from codewiki.src.be.prompt_template import format_user_prompt


def make_mock_components():
    node = MagicMock()
    node.source_code = "class Foo {}"
    node.relative_path = "src/Foo.java"
    node.file_path = "/fake/src/Foo.java"
    node.display_name = "Foo"
    node.name = "Foo"
    return {"comp1": node}


# ---------------------------------------------------------------------------
# collect_supplementary_files tests
# ---------------------------------------------------------------------------


class TestCollectSupplementaryFiles:
    def test_collect_supplementary_basic(self, tmp_path):
        """Matching a single XML pattern returns that file."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "ejb-jar.xml").write_text("<ejb-jar/>")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.java").write_text("class Main {}")
        (tmp_path / "README.md").write_text("# readme")

        result = collect_supplementary_files(str(tmp_path), ["**/*.xml"])
        assert len(result) == 1
        key = os.path.join("config", "ejb-jar.xml")
        assert key in result
        assert result[key]  # non-empty content

    def test_collect_supplementary_multiple_patterns(self, tmp_path):
        """Multiple glob patterns collect all matching files."""
        (tmp_path / "ejb-jar.xml").write_text("<ejb-jar/>")
        (tmp_path / "web.xml").write_text("<web/>")
        (tmp_path / "app.properties").write_text("key=value")

        result = collect_supplementary_files(
            str(tmp_path), ["**/*.xml", "**/*.properties"]
        )
        assert len(result) == 3

    def test_collect_supplementary_50kb_cap(self, tmp_path):
        """Files larger than 50KB are truncated with a marker."""
        big_file = tmp_path / "big.xml"
        big_file.write_text("x" * (60 * 1024))

        result = collect_supplementary_files(str(tmp_path), ["**/*.xml"])
        assert len(result) == 1
        content = result["big.xml"]
        assert content.endswith("\n... [truncated]")
        # 50KB of content + truncation marker
        assert len(content) > 50 * 1024

    def test_collect_supplementary_skips_binary(self, tmp_path):
        """Binary files are skipped (UnicodeDecodeError)."""
        binary_file = tmp_path / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x80\x81\x82")

        result = collect_supplementary_files(str(tmp_path), ["**/*.bin"])
        assert result == {}

    def test_collect_supplementary_no_matches(self, tmp_path):
        """Patterns that match nothing return an empty dict."""
        (tmp_path / "readme.md").write_text("# hello")

        result = collect_supplementary_files(str(tmp_path), ["**/*.xml"])
        assert result == {}


# ---------------------------------------------------------------------------
# filter_supplementary_for_module tests
# ---------------------------------------------------------------------------


class TestFilterSupplementaryForModule:
    def test_filter_supplementary_root_files(self):
        """Root-level files are always included; unrelated subtrees are excluded."""
        all_files = {
            "ejb-jar.xml": "content",
            "src/deep/file.xml": "content2",
        }
        result = filter_supplementary_for_module(all_files, ["src/other/Main.java"])
        assert "ejb-jar.xml" in result
        assert "src/deep/file.xml" not in result

    def test_filter_supplementary_same_subtree(self):
        """Files in the same subtree are included; different subtrees are not."""
        all_files = {"src/main/resources/persistence.xml": "xml content"}

        # Different subtree under src/main
        result = filter_supplementary_for_module(
            all_files, ["src/main/java/App.java"]
        )
        assert "src/main/resources/persistence.xml" not in result

        # Same subtree
        result = filter_supplementary_for_module(
            all_files, ["src/main/resources/Config.java"]
        )
        assert "src/main/resources/persistence.xml" in result

    def test_filter_supplementary_empty(self):
        """Empty all_files returns empty dict."""
        result = filter_supplementary_for_module({}, ["src/Main.java"])
        assert result == {}


# ---------------------------------------------------------------------------
# format_user_prompt supplementary integration tests
# ---------------------------------------------------------------------------


class TestFormatUserPromptSupplementary:
    def _make_module_tree(self):
        return {
            "test_module": {
                "components": ["comp1"],
                "children": {},
            }
        }

    @patch("codewiki.src.be.prompt_template.file_manager")
    def test_format_user_prompt_with_supplementary(self, mock_fm):
        """Supplementary files produce a SUPPLEMENTARY_CONFIGURATION block."""
        mock_fm.load_text.return_value = "class Foo {}"
        components = make_mock_components()
        module_tree = self._make_module_tree()
        supplementary = {"ejb-jar.xml": "<ejb-jar>content</ejb-jar>"}

        result = format_user_prompt(
            module_name="test_module",
            core_component_ids=["comp1"],
            components=components,
            module_tree=module_tree,
            supplementary_files=supplementary,
            supplementary_file_role="EJB deployment descriptors",
        )
        assert "<SUPPLEMENTARY_CONFIGURATION>" in result
        assert "ejb-jar.xml" in result
        assert "EJB deployment descriptors" in result

    @patch("codewiki.src.be.prompt_template.file_manager")
    def test_format_user_prompt_without_supplementary(self, mock_fm):
        """No supplementary files means no SUPPLEMENTARY_CONFIGURATION block."""
        mock_fm.load_text.return_value = "class Foo {}"
        components = make_mock_components()
        module_tree = self._make_module_tree()

        result = format_user_prompt(
            module_name="test_module",
            core_component_ids=["comp1"],
            components=components,
            module_tree=module_tree,
        )
        assert "<SUPPLEMENTARY_CONFIGURATION>" not in result
