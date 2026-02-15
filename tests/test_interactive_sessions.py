"""Tests for interactive grouping and glossary review sessions (Phase 10)."""

import json
import os
import tempfile

import pytest

from codewiki.cli.interactive_grouping import InteractiveGroupingSession
from codewiki.cli.interactive_glossary import InteractiveGlossarySession
from codewiki.src.be.glossary_generator import Glossary, GlossaryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_tree():
    """Return a sample module tree for grouping tests."""
    return {
        "Auth": {"components": ["auth_service.py", "login.py"], "children": {}},
        "Data": {"components": ["db.py"], "children": {"sub": {}}},
    }


def _sample_glossary():
    """Return a Glossary with a couple of entries for glossary tests."""
    return Glossary(
        entries={
            "UserAccount": GlossaryEntry(
                identifier="UserAccount",
                business_name="User Account",
                definition="Represents a customer account.",
                category="entity",
                confidence=0.9,
            ),
            "process_order": GlossaryEntry(
                identifier="process_order",
                business_name="Process Order",
                definition="Handles an incoming purchase order.",
                category="operation",
                confidence=0.6,
            ),
        }
    )


# ---------------------------------------------------------------------------
# InteractiveGroupingSession tests
# ---------------------------------------------------------------------------


def test_rename_group():
    """rename_group should update the tree key."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.rename_group("Auth", "Authentication")
    assert result is True
    assert "Authentication" in session.module_tree
    assert "Auth" not in session.module_tree
    # Components should be preserved under the new name
    assert "auth_service.py" in session.module_tree["Authentication"]["components"]


def test_rename_group_missing_source():
    """rename_group returns False when old_name doesn't exist."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.rename_group("NoSuchGroup", "NewName")
    assert result is False


def test_rename_group_name_collision():
    """rename_group returns False when new_name already exists."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.rename_group("Auth", "Data")
    assert result is False


def test_move_component():
    """move_component should transfer a component between groups."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.move_component("login.py", "Auth", "Data")
    assert result is True
    assert "login.py" not in session.module_tree["Auth"]["components"]
    assert "login.py" in session.module_tree["Data"]["components"]


def test_move_component_missing_source_group():
    """move_component returns False when source group doesn't exist."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.move_component("login.py", "NoGroup", "Data")
    assert result is False


def test_move_component_missing_target_group():
    """move_component returns False when target group doesn't exist."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.move_component("login.py", "Auth", "NoGroup")
    assert result is False


def test_move_component_not_in_source():
    """move_component returns False when component isn't in source group."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.move_component("nonexistent.py", "Auth", "Data")
    assert result is False


def test_merge_groups():
    """merge_groups should combine two groups into one."""
    session = InteractiveGroupingSession(_sample_tree())
    result = session.merge_groups("Auth", "Data", "Combined")
    assert result is True
    assert "Combined" in session.module_tree
    assert "Auth" not in session.module_tree
    assert "Data" not in session.module_tree
    # All components from both groups should be present
    combined_components = session.module_tree["Combined"]["components"]
    assert "auth_service.py" in combined_components
    assert "login.py" in combined_components
    assert "db.py" in combined_components
    # Children should be merged
    assert "sub" in session.module_tree["Combined"]["children"]


def test_merge_groups_missing_group():
    """merge_groups returns False when one of the groups doesn't exist."""
    session = InteractiveGroupingSession(_sample_tree())
    assert session.merge_groups("Auth", "NoGroup", "Merged") is False
    assert session.merge_groups("NoGroup", "Data", "Merged") is False


def test_save_json_format():
    """save() writes JSON with projection_name, saved_at, and module_tree."""
    session = InteractiveGroupingSession(_sample_tree(), projection_name="business")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir="/tmp/claude"
    ) as tmp:
        tmp_path = tmp.name

    try:
        session.save(tmp_path)
        with open(tmp_path, "r") as f:
            data = json.load(f)
        assert data["projection_name"] == "business"
        assert "saved_at" in data
        assert "module_tree" in data
        assert "Auth" in data["module_tree"]
    finally:
        os.unlink(tmp_path)


def test_accept_returns_tree():
    """accept() returns the (possibly modified) module tree."""
    tree = _sample_tree()
    session = InteractiveGroupingSession(tree)
    session.rename_group("Auth", "Authentication")
    result = session.accept()
    assert "Authentication" in result
    assert "Data" in result


# ---------------------------------------------------------------------------
# InteractiveGlossarySession tests
# ---------------------------------------------------------------------------


def test_edit_entry_business_name():
    """edit_entry should update the business_name field."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.edit_entry("UserAccount", "business_name", "Customer Account")
    assert result is True
    assert session.glossary.entries["UserAccount"].business_name == "Customer Account"


def test_edit_entry_definition():
    """edit_entry should update the definition field."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.edit_entry("process_order", "definition", "Fulfills a customer order.")
    assert result is True
    assert session.glossary.entries["process_order"].definition == "Fulfills a customer order."


def test_edit_entry_unknown_field():
    """edit_entry returns False for an unknown field name."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.edit_entry("UserAccount", "unknown_field", "value")
    assert result is False


def test_edit_entry_missing_identifier():
    """edit_entry returns False when the identifier doesn't exist."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.edit_entry("NoSuchEntry", "business_name", "value")
    assert result is False


def test_remove_entry():
    """remove_entry should delete the entry from the glossary."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.remove_entry("UserAccount")
    assert result is True
    assert "UserAccount" not in session.glossary.entries
    assert len(session.glossary.entries) == 1


def test_remove_entry_missing():
    """remove_entry returns False when identifier doesn't exist."""
    session = InteractiveGlossarySession(_sample_glossary())
    result = session.remove_entry("NoSuchEntry")
    assert result is False


def test_accept_returns_glossary():
    """accept() returns the (possibly modified) glossary."""
    session = InteractiveGlossarySession(_sample_glossary())
    session.edit_entry("UserAccount", "business_name", "Account")
    session.remove_entry("process_order")
    result = session.accept()
    assert isinstance(result, Glossary)
    assert "UserAccount" in result.entries
    assert result.entries["UserAccount"].business_name == "Account"
    assert "process_order" not in result.entries
