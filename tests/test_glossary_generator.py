"""Tests for codewiki.src.be.glossary_generator module."""

from unittest.mock import MagicMock, patch

import pytest

from codewiki.src.be.glossary_generator import (
    Glossary,
    GlossaryEntry,
    _parse_glossary_response,
    extract_identifiers,
    generate_glossary,
    render_glossary_md,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_node(name, parameters=None, source_code=None, relative_path="src/test.java"):
    node = MagicMock()
    node.name = name
    node.parameters = parameters
    node.source_code = source_code
    node.relative_path = relative_path
    return node


VALID_LLM_RESPONSE = """\
<GLOSSARY_ENTRIES>
[
  {"identifier": "CustomerService", "business_name": "Customer Service", "definition": "Manages customer operations", "category": "entity", "confidence": 0.9}
]
</GLOSSARY_ENTRIES>
"""

VALID_LLM_RESPONSE_MULTI = """\
<GLOSSARY_ENTRIES>
[
  {"identifier": "CustomerService", "business_name": "Customer Service", "definition": "Manages customer operations", "category": "entity", "confidence": 0.9},
  {"identifier": "OrderProcessor", "business_name": "Order Processor", "definition": "Processes orders", "category": "operation", "confidence": 0.85}
]
</GLOSSARY_ENTRIES>
"""


# ---------------------------------------------------------------------------
# GlossaryEntry tests
# ---------------------------------------------------------------------------


class TestGlossaryEntry:
    def test_glossary_entry_creation(self):
        entry = GlossaryEntry(
            identifier="CustomerService",
            business_name="Customer Service",
            definition="Manages customer operations",
            category="entity",
            confidence=0.9,
            source_files=["src/CustomerService.java"],
            component_ids=["comp1", "comp2"],
        )
        assert entry.identifier == "CustomerService"
        assert entry.business_name == "Customer Service"
        assert entry.definition == "Manages customer operations"
        assert entry.category == "entity"
        assert entry.confidence == 0.9
        assert entry.source_files == ["src/CustomerService.java"]
        assert entry.component_ids == ["comp1", "comp2"]

    def test_glossary_entry_defaults(self):
        entry = GlossaryEntry(
            identifier="OrderProcessor",
            business_name="Order Processor",
            definition="Processes orders",
            category="operation",
            confidence=0.8,
        )
        assert entry.source_files == []
        assert entry.component_ids == []


# ---------------------------------------------------------------------------
# Glossary serialization tests
# ---------------------------------------------------------------------------


class TestGlossarySerialization:
    def test_glossary_to_dict(self):
        glossary = Glossary(
            entries={
                "CustomerService": GlossaryEntry(
                    identifier="CustomerService",
                    business_name="Customer Service",
                    definition="Manages customers",
                    category="entity",
                    confidence=0.9,
                    source_files=["src/cs.java"],
                    component_ids=["c1"],
                ),
                "OrderProcessor": GlossaryEntry(
                    identifier="OrderProcessor",
                    business_name="Order Processor",
                    definition="Processes orders",
                    category="operation",
                    confidence=0.8,
                ),
            }
        )
        d = glossary.to_dict()
        assert "entries" in d
        assert len(d["entries"]) == 2
        assert d["entries"]["CustomerService"]["identifier"] == "CustomerService"
        assert d["entries"]["CustomerService"]["business_name"] == "Customer Service"
        assert d["entries"]["CustomerService"]["source_files"] == ["src/cs.java"]
        assert d["entries"]["OrderProcessor"]["confidence"] == 0.8
        assert d["entries"]["OrderProcessor"]["component_ids"] == []

    def test_glossary_from_dict(self):
        data = {
            "entries": {
                "CustomerService": {
                    "identifier": "CustomerService",
                    "business_name": "Customer Service",
                    "definition": "Manages customers",
                    "category": "entity",
                    "confidence": 0.9,
                    "source_files": ["src/cs.java"],
                    "component_ids": ["c1"],
                },
                "OrderProcessor": {
                    "identifier": "OrderProcessor",
                    "business_name": "Order Processor",
                    "definition": "Processes orders",
                    "category": "operation",
                    "confidence": 0.8,
                    "source_files": [],
                    "component_ids": [],
                },
            }
        }
        glossary = Glossary.from_dict(data)
        assert len(glossary.entries) == 2
        assert glossary.entries["CustomerService"].business_name == "Customer Service"
        assert glossary.entries["CustomerService"].source_files == ["src/cs.java"]
        assert glossary.entries["OrderProcessor"].confidence == 0.8

    def test_glossary_roundtrip(self):
        original = Glossary(
            entries={
                "Foo": GlossaryEntry(
                    identifier="Foo",
                    business_name="Foo Bar",
                    definition="Does foo",
                    category="entity",
                    confidence=0.75,
                    source_files=["a.java", "b.java"],
                    component_ids=["c1", "c2"],
                ),
                "Baz": GlossaryEntry(
                    identifier="Baz",
                    business_name="Baz Qux",
                    definition="Does baz",
                    category="operation",
                    confidence=0.6,
                ),
            }
        )
        restored = Glossary.from_dict(original.to_dict())
        for key in original.entries:
            orig = original.entries[key]
            rest = restored.entries[key]
            assert orig.identifier == rest.identifier
            assert orig.business_name == rest.business_name
            assert orig.definition == rest.definition
            assert orig.category == rest.category
            assert orig.confidence == rest.confidence
            assert orig.source_files == rest.source_files
            assert orig.component_ids == rest.component_ids

    def test_glossary_from_dict_missing_optional(self):
        data = {
            "entries": {
                "X": {
                    "identifier": "X",
                    "business_name": "X Name",
                    "definition": "X def",
                    "category": "field",
                    "confidence": 0.5,
                    # source_files and component_ids missing
                }
            }
        }
        glossary = Glossary.from_dict(data)
        assert glossary.entries["X"].source_files == []
        assert glossary.entries["X"].component_ids == []


# ---------------------------------------------------------------------------
# Prompt block tests
# ---------------------------------------------------------------------------


class TestPromptBlock:
    def test_to_prompt_block_empty(self):
        glossary = Glossary()
        assert glossary.to_prompt_block() == ""

    def test_to_prompt_block_basic(self):
        glossary = Glossary(
            entries={
                "Alpha": GlossaryEntry(
                    identifier="Alpha",
                    business_name="A",
                    definition="def a",
                    category="entity",
                    confidence=0.9,
                ),
                "Beta": GlossaryEntry(
                    identifier="Beta",
                    business_name="B",
                    definition="def b",
                    category="operation",
                    confidence=0.8,
                ),
                "Gamma": GlossaryEntry(
                    identifier="Gamma",
                    business_name="G",
                    definition="def g",
                    category="field",
                    confidence=0.7,
                ),
            }
        )
        block = glossary.to_prompt_block()
        assert "<GLOSSARY>" in block
        assert "</GLOSSARY>" in block
        assert "Alpha" in block
        assert "Beta" in block
        assert "Gamma" in block

    def test_to_prompt_block_sorted_by_confidence(self):
        glossary = Glossary(
            entries={
                "Low": GlossaryEntry(
                    identifier="Low",
                    business_name="L",
                    definition="low",
                    category="field",
                    confidence=0.3,
                ),
                "High": GlossaryEntry(
                    identifier="High",
                    business_name="H",
                    definition="high",
                    category="entity",
                    confidence=0.9,
                ),
                "Mid": GlossaryEntry(
                    identifier="Mid",
                    business_name="M",
                    definition="mid",
                    category="operation",
                    confidence=0.6,
                ),
            }
        )
        block = glossary.to_prompt_block()
        high_pos = block.index("High")
        mid_pos = block.index("Mid")
        low_pos = block.index("Low")
        assert high_pos < mid_pos < low_pos

    def test_to_prompt_block_max_entries(self):
        entries = {}
        for i in range(5):
            name = f"Entry{i}"
            entries[name] = GlossaryEntry(
                identifier=name,
                business_name=f"Name {i}",
                definition=f"Def {i}",
                category="field",
                confidence=i * 0.2,  # 0.0, 0.2, 0.4, 0.6, 0.8
            )
        glossary = Glossary(entries=entries)
        block = glossary.to_prompt_block(max_entries=2)
        # Only the 2 highest-confidence entries should appear: Entry4 (0.8) and Entry3 (0.6)
        assert "Entry4" in block
        assert "Entry3" in block
        assert "Entry0" not in block
        assert "Entry1" not in block
        assert "Entry2" not in block


# ---------------------------------------------------------------------------
# extract_identifiers tests
# ---------------------------------------------------------------------------


class TestExtractIdentifiers:
    def test_extract_node_names(self):
        components = {
            "n1": make_node("CustomerService"),
            "n2": make_node("OrderProcessor"),
        }
        result = extract_identifiers(components, ["n1", "n2"])
        assert "CustomerService" in result
        assert "OrderProcessor" in result

    def test_extract_parameters(self):
        node = make_node(
            "process",  # "process" is not in GENERIC_NAMES and len > 2
            parameters=["customer_id: str", "order_total: float"],
        )
        components = {"n1": node}
        result = extract_identifiers(components, ["n1"])
        assert "customer_id" in result
        assert "order_total" in result

    def test_extract_java_fields(self):
        source = (
            "private String customerName;\n"
            "public int accountBalance = 0;\n"
        )
        node = make_node("MyClass", source_code=source)
        components = {"n1": node}
        result = extract_identifiers(components, ["n1"])
        assert "customerName" in result
        assert "accountBalance" in result

    def test_extract_natural_ws_variables(self):
        source = "MOVE WS_CUST_NM TO OUTPUT.\nMOVE WS_ACCT_BAL TO DISPLAY."
        node = make_node("MyProc", source_code=source)
        components = {"n1": node}
        result = extract_identifiers(components, ["n1"])
        assert "WS_CUST_NM" in result
        assert "WS_ACCT_BAL" in result

    def test_filter_generic_names(self):
        node = make_node("get", parameters=["self", "i"])
        components = {"n1": node}
        result = extract_identifiers(components, ["n1"])
        assert "get" not in result
        assert "self" not in result
        assert "i" not in result

    def test_filter_short_names(self):
        node = make_node("ab")  # 2 chars -> filtered
        components = {"n1": node}
        result = extract_identifiers(components, ["n1"])
        assert "ab" not in result

    def test_extract_empty_components(self):
        result = extract_identifiers({}, [])
        assert result == {}


# ---------------------------------------------------------------------------
# generate_glossary tests (mock call_llm)
# ---------------------------------------------------------------------------


class TestGenerateGlossary:
    @patch("codewiki.src.be.llm_services.call_llm")
    def test_generate_glossary_basic(self, mock_llm):
        mock_llm.return_value = VALID_LLM_RESPONSE
        config = MagicMock()
        components = {
            "n1": make_node("CustomerService"),
        }
        glossary = generate_glossary(components, ["n1"], config)
        assert "CustomerService" in glossary.entries
        entry = glossary.entries["CustomerService"]
        assert entry.business_name == "Customer Service"
        assert "n1" in entry.component_ids

    @patch("codewiki.src.be.llm_services.call_llm")
    def test_generate_glossary_empty(self, mock_llm):
        config = MagicMock()
        glossary = generate_glossary({}, [], config)
        assert len(glossary.entries) == 0
        mock_llm.assert_not_called()

    @patch("codewiki.src.be.llm_services.call_llm")
    def test_generate_glossary_bad_response(self, mock_llm):
        mock_llm.return_value = "totally garbage output with no structure"
        config = MagicMock()
        components = {
            "n1": make_node("CustomerService"),
        }
        glossary = generate_glossary(components, ["n1"], config)
        assert len(glossary.entries) == 0

    @patch("codewiki.src.be.llm_services.call_llm")
    def test_generate_glossary_batching(self, mock_llm):
        mock_llm.return_value = VALID_LLM_RESPONSE
        config = MagicMock()
        # Create 100 unique identifiers across nodes
        components = {}
        leaf_nodes = []
        for i in range(100):
            node_id = f"n{i}"
            components[node_id] = make_node(f"UniqueIdentifier{i:03d}")
            leaf_nodes.append(node_id)
        glossary = generate_glossary(components, leaf_nodes, config, batch_size=50)
        assert mock_llm.call_count == 2


# ---------------------------------------------------------------------------
# _parse_glossary_response tests
# ---------------------------------------------------------------------------


class TestParseGlossaryResponse:
    def test_parse_valid_response(self):
        entries = _parse_glossary_response(VALID_LLM_RESPONSE)
        assert len(entries) == 1
        assert entries[0].identifier == "CustomerService"
        assert entries[0].business_name == "Customer Service"
        assert entries[0].category == "entity"
        assert entries[0].confidence == 0.9

    def test_parse_no_tags(self):
        entries = _parse_glossary_response("No tags here, just plain text.")
        assert entries == []

    def test_parse_invalid_json(self):
        response = "<GLOSSARY_ENTRIES>\nnot valid json\n</GLOSSARY_ENTRIES>"
        entries = _parse_glossary_response(response)
        assert entries == []


# ---------------------------------------------------------------------------
# render_glossary_md tests
# ---------------------------------------------------------------------------


class TestRenderGlossaryMd:
    def test_render_glossary_md(self):
        glossary = Glossary(
            entries={
                "CustomerService": GlossaryEntry(
                    identifier="CustomerService",
                    business_name="Customer Service",
                    definition="Manages customers",
                    category="entity",
                    confidence=0.9,
                ),
                "OrderProcessor": GlossaryEntry(
                    identifier="OrderProcessor",
                    business_name="Order Processor",
                    definition="Processes orders",
                    category="operation",
                    confidence=0.85,
                ),
            }
        )
        md = render_glossary_md(glossary)
        assert "# Glossary / Data Dictionary" in md
        assert "| Identifier |" in md
        assert "`CustomerService`" in md
        assert "`OrderProcessor`" in md

    def test_render_glossary_md_sorted(self):
        glossary = Glossary(
            entries={
                "OrderProcessor": GlossaryEntry(
                    identifier="OrderProcessor",
                    business_name="Order Processor",
                    definition="Processes orders",
                    category="operation",
                    confidence=0.85,
                ),
                "CustomerService": GlossaryEntry(
                    identifier="CustomerService",
                    business_name="Customer Service",
                    definition="Manages customers",
                    category="entity",
                    confidence=0.9,
                ),
            }
        )
        md = render_glossary_md(glossary)
        entity_pos = md.index("entity")
        operation_pos = md.index("operation")
        assert entity_pos < operation_pos
