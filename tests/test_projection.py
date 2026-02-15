"""Tests for codewiki.src.be.projection module."""

import json
import os
import tempfile

import pytest

from codewiki.src.be.projection import (
    CodeProvenance,
    CompiledProjectionPrompts,
    ProjectionConfig,
    compile_projection_instructions,
    get_business_projection,
    get_developer_projection,
    get_ejb_migration_projection,
    get_natural_transpiled_projection,
    resolve_projection,
)


# ---------------------------------------------------------------------------
# CodeProvenance tests
# ---------------------------------------------------------------------------


class TestCodeProvenance:
    def test_defaults(self):
        prov = CodeProvenance()
        assert prov.source_language is None
        assert prov.transpilation_tool is None
        assert prov.naming_conventions == {}
        assert prov.runtime_library_packages == []
        assert prov.known_boilerplate_patterns == []

    def test_all_fields(self):
        prov = CodeProvenance(
            source_language="COBOL",
            transpilation_tool="CobolToJava",
            naming_conventions={"WS_*": "Working Storage"},
            runtime_library_packages=["com.example.runtime"],
            known_boilerplate_patterns=["init()", "cleanup()"],
        )
        assert prov.source_language == "COBOL"
        assert prov.transpilation_tool == "CobolToJava"
        assert prov.naming_conventions == {"WS_*": "Working Storage"}
        assert prov.runtime_library_packages == ["com.example.runtime"]
        assert prov.known_boilerplate_patterns == ["init()", "cleanup()"]

    def test_to_dict(self):
        prov = CodeProvenance(
            source_language="NATURAL",
            transpilation_tool="NatToJava",
            naming_conventions={"PRFM_*": "PERFORM"},
            runtime_library_packages=["com.sag.runtime"],
            known_boilerplate_patterns=["NaturalProgram.initialize()"],
        )
        d = prov.to_dict()
        assert d == {
            "source_language": "NATURAL",
            "transpilation_tool": "NatToJava",
            "naming_conventions": {"PRFM_*": "PERFORM"},
            "runtime_library_packages": ["com.sag.runtime"],
            "known_boilerplate_patterns": ["NaturalProgram.initialize()"],
        }

    def test_from_dict_round_trip(self):
        original = CodeProvenance(
            source_language="COBOL",
            transpilation_tool="CobolToJava",
            naming_conventions={"WS_*": "Working Storage", "PIC_*": "Picture clause"},
            runtime_library_packages=["com.example.runtime", "com.example.io"],
            known_boilerplate_patterns=["init()", "cleanup()"],
        )
        d = original.to_dict()
        restored = CodeProvenance.from_dict(d)
        assert restored.source_language == original.source_language
        assert restored.transpilation_tool == original.transpilation_tool
        assert restored.naming_conventions == original.naming_conventions
        assert restored.runtime_library_packages == original.runtime_library_packages
        assert restored.known_boilerplate_patterns == original.known_boilerplate_patterns

    def test_from_dict_with_missing_keys(self):
        prov = CodeProvenance.from_dict({"source_language": "RPG"})
        assert prov.source_language == "RPG"
        assert prov.transpilation_tool is None
        assert prov.naming_conventions == {}
        assert prov.runtime_library_packages == []
        assert prov.known_boilerplate_patterns == []


# ---------------------------------------------------------------------------
# ProjectionConfig tests
# ---------------------------------------------------------------------------


class TestProjectionConfig:
    def test_defaults(self):
        cfg = ProjectionConfig()
        assert cfg.name == ""
        assert cfg.description == ""
        assert cfg.clustering_goal == ""
        assert cfg.clustering_examples == ""
        assert cfg.audience == ""
        assert cfg.perspective == ""
        assert cfg.doc_objectives == []
        assert cfg.doc_anti_objectives == []
        assert cfg.detail_level == "standard"
        assert cfg.max_depth_override is None
        assert cfg.saved_grouping is None
        assert cfg.objectives_override is None
        assert cfg.code_provenance is None
        assert cfg.framework_context is None
        assert cfg.supplementary_file_patterns is None
        assert cfg.supplementary_file_role is None
        assert cfg.output_artifacts == ["documentation"]
        assert cfg.glossary_path is None

    def test_all_fields(self):
        prov = CodeProvenance(source_language="NATURAL")
        cfg = ProjectionConfig(
            name="test",
            description="Test projection",
            clustering_goal="group by domain",
            clustering_examples="example clusters",
            audience="engineers",
            perspective="migration",
            doc_objectives=["obj1", "obj2"],
            doc_anti_objectives=["anti1"],
            detail_level="detailed",
            max_depth_override=3,
            saved_grouping={"a": "b"},
            objectives_override="custom objectives",
            code_provenance=prov,
            framework_context="Spring Boot",
            supplementary_file_patterns=["*.xml"],
            supplementary_file_role="config files",
            output_artifacts=["documentation", "data_dictionary"],
            glossary_path="/tmp/glossary.json",
        )
        assert cfg.name == "test"
        assert cfg.description == "Test projection"
        assert cfg.clustering_goal == "group by domain"
        assert cfg.audience == "engineers"
        assert cfg.code_provenance is prov
        assert cfg.max_depth_override == 3
        assert cfg.output_artifacts == ["documentation", "data_dictionary"]

    def test_to_dict_with_provenance(self):
        prov = CodeProvenance(source_language="COBOL")
        cfg = ProjectionConfig(name="test", code_provenance=prov)
        d = cfg.to_dict()
        assert d["name"] == "test"
        assert d["code_provenance"] is not None
        assert d["code_provenance"]["source_language"] == "COBOL"

    def test_to_dict_without_provenance(self):
        cfg = ProjectionConfig(name="simple")
        d = cfg.to_dict()
        assert d["code_provenance"] is None

    def test_from_dict_round_trip_with_provenance(self):
        prov = CodeProvenance(
            source_language="NATURAL",
            transpilation_tool="NatToJava",
        )
        original = ProjectionConfig(
            name="round-trip",
            description="Round-trip test",
            audience="testers",
            perspective="testing",
            doc_objectives=["verify round-trip"],
            detail_level="detailed",
            code_provenance=prov,
            output_artifacts=["documentation", "data_dictionary"],
        )
        d = original.to_dict()
        restored = ProjectionConfig.from_dict(d)
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.audience == original.audience
        assert restored.perspective == original.perspective
        assert restored.doc_objectives == original.doc_objectives
        assert restored.detail_level == original.detail_level
        assert restored.code_provenance is not None
        assert restored.code_provenance.source_language == "NATURAL"
        assert restored.code_provenance.transpilation_tool == "NatToJava"
        assert restored.output_artifacts == original.output_artifacts

    def test_from_dict_with_missing_keys(self):
        cfg = ProjectionConfig.from_dict({"name": "minimal"})
        assert cfg.name == "minimal"
        assert cfg.description == ""
        assert cfg.audience == ""
        assert cfg.doc_objectives == []
        assert cfg.detail_level == "standard"
        assert cfg.code_provenance is None
        assert cfg.output_artifacts == ["documentation"]

    def test_from_dict_empty_dict(self):
        cfg = ProjectionConfig.from_dict({})
        assert cfg.name == ""
        assert cfg.detail_level == "standard"
        assert cfg.output_artifacts == ["documentation"]


# ---------------------------------------------------------------------------
# CompiledProjectionPrompts tests
# ---------------------------------------------------------------------------


class TestCompiledProjectionPrompts:
    def test_defaults(self):
        prompts = CompiledProjectionPrompts()
        assert prompts.code_context_block == ""
        assert prompts.framework_context_block == ""
        assert prompts.objectives_override is None
        assert prompts.custom_instructions == ""
        assert prompts.glossary_block == ""


# ---------------------------------------------------------------------------
# compile_projection_instructions() tests
# ---------------------------------------------------------------------------


class TestCompileProjectionInstructions:
    def test_business_projection(self):
        proj = get_business_projection()
        result = compile_projection_instructions(proj)
        assert result.objectives_override is not None
        assert len(result.objectives_override) > 0
        assert "product managers" in result.custom_instructions

    def test_developer_projection(self):
        proj = get_developer_projection()
        result = compile_projection_instructions(proj)
        assert result.code_context_block == ""
        assert result.objectives_override is None

    def test_natural_projection(self):
        proj = get_natural_transpiled_projection()
        result = compile_projection_instructions(proj)
        assert "NATURAL" in result.code_context_block
        assert "Working Storage" in result.code_context_block

    def test_ejb_projection(self):
        proj = get_ejb_migration_projection()
        result = compile_projection_instructions(proj)
        assert len(result.framework_context_block) > 0
        assert "EJB" in result.framework_context_block

    def test_no_provenance_no_framework(self):
        proj = ProjectionConfig(name="bare")
        result = compile_projection_instructions(proj)
        assert result.code_context_block == ""
        assert result.framework_context_block == ""
        assert result.objectives_override is None
        assert result.custom_instructions == ""

    def test_custom_instructions_includes_audience_and_perspective(self):
        proj = ProjectionConfig(
            audience="QA engineers",
            perspective="test coverage",
            detail_level="verbose",
            doc_objectives=["Cover edge cases"],
            doc_anti_objectives=["Skip internals"],
        )
        result = compile_projection_instructions(proj)
        assert "QA engineers" in result.custom_instructions
        assert "test coverage" in result.custom_instructions
        assert "verbose" in result.custom_instructions
        assert "Cover edge cases" in result.custom_instructions
        assert "Skip internals" in result.custom_instructions

    def test_standard_detail_level_omitted(self):
        proj = ProjectionConfig(audience="devs", detail_level="standard")
        result = compile_projection_instructions(proj)
        assert "Detail level" not in result.custom_instructions

    def test_provenance_runtime_and_boilerplate(self):
        prov = CodeProvenance(
            source_language="COBOL",
            runtime_library_packages=["com.example.rt"],
            known_boilerplate_patterns=["init()"],
        )
        proj = ProjectionConfig(code_provenance=prov)
        result = compile_projection_instructions(proj)
        assert "com.example.rt" in result.code_context_block
        assert "init()" in result.code_context_block
        assert "<CODE_CONTEXT>" in result.code_context_block
        assert "</CODE_CONTEXT>" in result.code_context_block


# ---------------------------------------------------------------------------
# Factory function tests
# ---------------------------------------------------------------------------


class TestFactoryFunctions:
    def test_get_developer_projection(self):
        proj = get_developer_projection()
        assert proj.name == "developer"
        assert "developers" in proj.audience

    def test_get_business_projection(self):
        proj = get_business_projection()
        assert len(proj.clustering_goal) > 0
        assert proj.objectives_override is not None

    def test_get_ejb_migration_projection(self):
        proj = get_ejb_migration_projection()
        assert proj.supplementary_file_patterns is not None
        assert any(
            "ejb-jar.xml" in p for p in proj.supplementary_file_patterns
        )

    def test_get_natural_transpiled_projection(self):
        proj = get_natural_transpiled_projection()
        assert "data_dictionary" in proj.output_artifacts
        assert proj.code_provenance is not None
        assert proj.code_provenance.source_language == "NATURAL"


# ---------------------------------------------------------------------------
# resolve_projection() tests
# ---------------------------------------------------------------------------


class TestResolveProjection:
    def test_resolve_business(self):
        proj = resolve_projection("business")
        assert proj.name == "business"

    def test_resolve_developer(self):
        proj = resolve_projection("developer")
        assert proj.name == "developer"

    def test_resolve_json_file(self):
        config = ProjectionConfig(
            name="from-file",
            audience="testers",
            doc_objectives=["test obj"],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config.to_dict(), f)
            tmp_path = f.name
        try:
            proj = resolve_projection(tmp_path)
            assert proj.name == "from-file"
            assert proj.audience == "testers"
            assert proj.doc_objectives == ["test obj"]
        finally:
            os.unlink(tmp_path)

    def test_resolve_nonexistent_name_raises(self):
        with pytest.raises(ValueError, match="Unknown projection 'nonexistent'"):
            resolve_projection("nonexistent")
        with pytest.raises(ValueError, match="Available built-in projections"):
            resolve_projection("nonexistent")

    def test_resolve_nonexistent_json_raises(self):
        with pytest.raises(ValueError, match="Projection file not found"):
            resolve_projection("/tmp/does_not_exist_abc123.json")


# ---------------------------------------------------------------------------
# JSON serialization round-trip
# ---------------------------------------------------------------------------


class TestSerializationRoundTrip:
    def test_full_round_trip_via_json_string(self):
        prov = CodeProvenance(
            source_language="NATURAL",
            transpilation_tool="NatToJava",
            naming_conventions={"WS_*": "Working Storage"},
            runtime_library_packages=["com.sag.runtime"],
            known_boilerplate_patterns=["NaturalProgram.initialize()"],
        )
        original = ProjectionConfig(
            name="round-trip-json",
            description="Full JSON round-trip test",
            clustering_goal="group by domain",
            clustering_examples="example",
            audience="engineers",
            perspective="migration",
            doc_objectives=["obj1", "obj2"],
            doc_anti_objectives=["anti1"],
            detail_level="detailed",
            max_depth_override=5,
            saved_grouping={"cluster1": ["a", "b"]},
            objectives_override="custom override",
            code_provenance=prov,
            framework_context="Spring Boot context",
            supplementary_file_patterns=["*.xml", "*.properties"],
            supplementary_file_role="config files",
            output_artifacts=["documentation", "data_dictionary"],
            glossary_path="/path/to/glossary.json",
        )

        # Serialize to JSON string
        json_str = json.dumps(original.to_dict())

        # Deserialize back
        data = json.loads(json_str)
        restored = ProjectionConfig.from_dict(data)

        # Verify all fields
        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.clustering_goal == original.clustering_goal
        assert restored.clustering_examples == original.clustering_examples
        assert restored.audience == original.audience
        assert restored.perspective == original.perspective
        assert restored.doc_objectives == original.doc_objectives
        assert restored.doc_anti_objectives == original.doc_anti_objectives
        assert restored.detail_level == original.detail_level
        assert restored.max_depth_override == original.max_depth_override
        assert restored.saved_grouping == original.saved_grouping
        assert restored.objectives_override == original.objectives_override
        assert restored.framework_context == original.framework_context
        assert restored.supplementary_file_patterns == original.supplementary_file_patterns
        assert restored.supplementary_file_role == original.supplementary_file_role
        assert restored.output_artifacts == original.output_artifacts
        assert restored.glossary_path == original.glossary_path

        # Verify nested CodeProvenance
        assert restored.code_provenance is not None
        assert restored.code_provenance.source_language == prov.source_language
        assert restored.code_provenance.transpilation_tool == prov.transpilation_tool
        assert restored.code_provenance.naming_conventions == prov.naming_conventions
        assert (
            restored.code_provenance.runtime_library_packages
            == prov.runtime_library_packages
        )
        assert (
            restored.code_provenance.known_boilerplate_patterns
            == prov.known_boilerplate_patterns
        )
