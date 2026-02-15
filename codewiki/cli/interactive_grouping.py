"""Interactive grouping session for reviewing and modifying module clustering."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

import click


class InteractiveGroupingSession:
    """Interactive session for reviewing and modifying module grouping.

    Allows users to rename, move components between, and merge groups before
    accepting the final module tree for documentation generation.
    """

    def __init__(self, module_tree: Dict[str, Any], projection_name: str = ""):
        self.module_tree = module_tree
        self.projection_name = projection_name

    # -- display --------------------------------------------------------

    def display_tree(self) -> None:
        """Pretty-print the proposed groups with component counts."""
        click.echo("\nProposed module grouping:")
        click.echo("=" * 60)
        for group_name, group_info in sorted(self.module_tree.items()):
            components = group_info.get("components", [])
            children = group_info.get("children", {})
            click.echo(f"  {group_name}  ({len(components)} components, {len(children)} children)")
            for comp in components[:5]:
                click.echo(f"    - {comp}")
            if len(components) > 5:
                click.echo(f"    ... and {len(components) - 5} more")
        click.echo("=" * 60)

    # -- mutations -------------------------------------------------------

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """Rename a group in the module tree."""
        if old_name not in self.module_tree:
            click.echo(f"Group '{old_name}' not found.")
            return False
        if new_name in self.module_tree:
            click.echo(f"Group '{new_name}' already exists.")
            return False
        self.module_tree[new_name] = self.module_tree.pop(old_name)
        click.echo(f"Renamed '{old_name}' -> '{new_name}'")
        return True

    def move_component(self, component_id: str, from_group: str, to_group: str) -> bool:
        """Move a component from one group to another."""
        if from_group not in self.module_tree:
            click.echo(f"Source group '{from_group}' not found.")
            return False
        if to_group not in self.module_tree:
            click.echo(f"Target group '{to_group}' not found.")
            return False

        source_components = self.module_tree[from_group].get("components", [])
        if component_id not in source_components:
            click.echo(f"Component '{component_id}' not found in '{from_group}'.")
            return False

        source_components.remove(component_id)
        self.module_tree[to_group].setdefault("components", []).append(component_id)
        click.echo(f"Moved '{component_id}' from '{from_group}' to '{to_group}'")
        return True

    def merge_groups(self, group_a: str, group_b: str, new_name: str) -> bool:
        """Merge two groups into one with the given name."""
        if group_a not in self.module_tree:
            click.echo(f"Group '{group_a}' not found.")
            return False
        if group_b not in self.module_tree:
            click.echo(f"Group '{group_b}' not found.")
            return False

        merged_components = (
            self.module_tree[group_a].get("components", [])
            + self.module_tree[group_b].get("components", [])
        )
        merged_children = {
            **self.module_tree[group_a].get("children", {}),
            **self.module_tree[group_b].get("children", {}),
        }

        del self.module_tree[group_a]
        del self.module_tree[group_b]
        self.module_tree[new_name] = {
            "components": merged_components,
            "children": merged_children,
        }
        click.echo(f"Merged '{group_a}' + '{group_b}' -> '{new_name}'")
        return True

    # -- accept / save ---------------------------------------------------

    def accept(self) -> Dict[str, Any]:
        """Finalize and return the modified module tree."""
        return self.module_tree

    def save(self, path: str) -> None:
        """Persist the grouping as JSON with metadata."""
        data = {
            "projection_name": self.projection_name,
            "saved_at": datetime.now().isoformat(),
            "module_tree": self.module_tree,
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        click.echo(f"Grouping saved to {path}")

    # -- interactive loop ------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """Interactive loop reading user commands.

        Commands:
            show                          -- display the current tree
            rename "<old>" "<new>"        -- rename a group
            move "<comp>" "<from>" "<to>" -- move component between groups
            merge "<a>" "<b>" "<new>"     -- merge two groups
            accept                        -- finalize
            quit / exit                   -- abort
        """
        self.display_tree()
        click.echo(
            "\nCommands: show, rename, move, merge, accept, quit"
        )

        while True:
            try:
                line = click.prompt("grouping", type=str).strip()
            except (EOFError, click.Abort):
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()

            if cmd == "show":
                self.display_tree()
            elif cmd == "rename" and len(parts) == 3:
                self.rename_group(parts[1], parts[2])
            elif cmd == "move" and len(parts) == 4:
                self.move_component(parts[1], parts[2], parts[3])
            elif cmd == "merge" and len(parts) == 4:
                self.merge_groups(parts[1], parts[2], parts[3])
            elif cmd == "accept":
                save_path = os.path.join(
                    ".codewiki", "projections", f"{self.projection_name}-grouping.json"
                )
                self.save(save_path)
                return self.accept()
            elif cmd in ("quit", "exit"):
                click.echo("Aborted.")
                return self.module_tree
            else:
                click.echo(f"Unknown command or wrong arguments: {line}")
                click.echo("Commands: show, rename <old> <new>, move <comp> <from> <to>, merge <a> <b> <new>, accept, quit")

        return self.module_tree
