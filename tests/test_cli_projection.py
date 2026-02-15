"""Tests for CLI integration with the projection framework."""

import json
import os
import tempfile

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from codewiki.src.be.projection import (
    resolve_projection,
    get_business_projection,
    ProjectionConfig,
)
from codewiki.cli.adapters.doc_generator import CLIDocumentationGenerator


# ---------------------------------------------------------------------------
# resolve_projection tests
# ---------------------------------------------------------------------------


def test_resolve_projection_business():
    """Built-in 'business' projection resolves correctly."""
    result = resolve_projection("business")
    assert result.name == "business"


def test_resolve_projection_invalid():
    """Unknown projection name raises ValueError with 'available' hint."""
    with pytest.raises(ValueError, match="(?i)available"):
        resolve_projection("nonexistent")


def test_resolve_projection_json_file():
    """resolve_projection loads a custom projection from a JSON file."""
    data = {"name": "custom", "audience": "testers"}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name

    try:
        result = resolve_projection(tmp_path)
        assert result.name == "custom"
        assert result.audience == "testers"
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# CLIDocumentationGenerator projection acceptance tests
# ---------------------------------------------------------------------------


@patch("codewiki.cli.adapters.doc_generator.ProgressTracker")
@patch("codewiki.cli.adapters.doc_generator.DocumentationJob")
def test_cli_adapter_accepts_projection(mock_job_cls, mock_tracker_cls):
    """CLIDocumentationGenerator stores a projection when provided."""
    mock_job_cls.return_value = MagicMock()
    generator = CLIDocumentationGenerator(
        repo_path=Path("/tmp/repo"),
        output_dir=Path("/tmp/out"),
        config={"main_model": "m", "cluster_model": "c", "base_url": "u"},
        projection=get_business_projection(),
    )
    assert generator.projection is not None
    assert generator.projection.name == "business"


@patch("codewiki.cli.adapters.doc_generator.ProgressTracker")
@patch("codewiki.cli.adapters.doc_generator.DocumentationJob")
def test_cli_adapter_no_projection(mock_job_cls, mock_tracker_cls):
    """CLIDocumentationGenerator defaults projection to None."""
    mock_job_cls.return_value = MagicMock()
    generator = CLIDocumentationGenerator(
        repo_path=Path("/tmp/repo"),
        output_dir=Path("/tmp/out"),
        config={"main_model": "m", "cluster_model": "c", "base_url": "u"},
    )
    assert generator.projection is None


@patch("codewiki.cli.adapters.doc_generator.ProgressTracker")
@patch("codewiki.cli.adapters.doc_generator.DocumentationJob")
def test_cli_adapter_output_dir_unchanged(mock_job_cls, mock_tracker_cls):
    """Without a projection the output_dir is unchanged."""
    mock_job_cls.return_value = MagicMock()
    original = Path("/tmp/out")
    generator = CLIDocumentationGenerator(
        repo_path=Path("/tmp/repo"),
        output_dir=original,
        config={"main_model": "m", "cluster_model": "c", "base_url": "u"},
    )
    assert generator.output_dir == original


# ---------------------------------------------------------------------------
# Projection configuration mutation tests
# ---------------------------------------------------------------------------


def test_generate_glossary_flag_adds_data_dictionary():
    """Appending 'data_dictionary' to output_artifacts works correctly."""
    proj = get_business_projection()
    assert "data_dictionary" not in proj.output_artifacts
    proj.output_artifacts.append("data_dictionary")
    assert "data_dictionary" in proj.output_artifacts


def test_load_grouping_sets_saved_grouping():
    """saved_grouping can be populated from a JSON file."""
    grouping_data = {"Module A": {"components": ["c1"], "children": {}}}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp:
        json.dump(grouping_data, tmp)
        tmp_path = tmp.name

    try:
        proj = get_business_projection()
        with open(tmp_path, "r") as f:
            proj.saved_grouping = json.load(f)
        assert proj.saved_grouping == {
            "Module A": {"components": ["c1"], "children": {}}
        }
    finally:
        os.unlink(tmp_path)


def test_load_glossary_sets_path():
    """glossary_path can be set on a projection."""
    proj = get_business_projection()
    proj.glossary_path = "/path/to/glossary.json"
    assert proj.glossary_path == "/path/to/glossary.json"


# ---------------------------------------------------------------------------
# Output subdirectory test
# ---------------------------------------------------------------------------


def test_projection_output_subdirectory():
    """When a projection is active, output goes to docs/{projection_name}/."""
    output_dir = Path("docs").resolve()
    proj = get_business_projection()
    adjusted = output_dir / proj.name
    assert adjusted.name == "business"
    assert str(adjusted).endswith("docs/business")
