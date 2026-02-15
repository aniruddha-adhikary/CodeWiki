"""Interactive glossary review session for editing generated glossary entries."""

import click

from codewiki.src.be.glossary_generator import Glossary, GlossaryEntry


class InteractiveGlossarySession:
    """Interactive session for reviewing and editing a generated glossary.

    Entries are displayed grouped by confidence level. Users can edit
    business names/definitions, remove entries, and accept the final result.
    """

    def __init__(self, glossary: Glossary):
        self.glossary = glossary

    # -- display --------------------------------------------------------

    def display(self) -> None:
        """Show entries grouped by confidence (high / medium / low)."""
        high = []
        medium = []
        low = []
        for entry in self.glossary.entries.values():
            if entry.confidence >= 0.8:
                high.append(entry)
            elif entry.confidence >= 0.5:
                medium.append(entry)
            else:
                low.append(entry)

        click.echo("\n=== Glossary Review ===")

        for label, group in [("High confidence", high), ("Medium confidence", medium), ("Low confidence", low)]:
            if not group:
                continue
            click.echo(f"\n--- {label} ({len(group)} entries) ---")
            for e in sorted(group, key=lambda x: x.identifier):
                click.echo(
                    f"  {e.identifier} -> {e.business_name}: {e.definition} "
                    f"[{e.category}, {e.confidence:.1f}]"
                )

        click.echo(f"\nTotal: {len(self.glossary.entries)} entries")

    # -- mutations -------------------------------------------------------

    def edit_entry(self, identifier: str, field: str, value: str) -> bool:
        """Modify an entry's business_name or definition."""
        if identifier not in self.glossary.entries:
            click.echo(f"Entry '{identifier}' not found.")
            return False
        entry = self.glossary.entries[identifier]
        if field == "business_name":
            entry.business_name = value
        elif field == "definition":
            entry.definition = value
        else:
            click.echo(f"Unknown field '{field}'. Use 'business_name' or 'definition'.")
            return False
        click.echo(f"Updated {identifier}.{field} = {value}")
        return True

    def remove_entry(self, identifier: str) -> bool:
        """Remove an entry from the glossary."""
        if identifier not in self.glossary.entries:
            click.echo(f"Entry '{identifier}' not found.")
            return False
        del self.glossary.entries[identifier]
        click.echo(f"Removed '{identifier}'")
        return True

    # -- accept ----------------------------------------------------------

    def accept(self) -> Glossary:
        """Finalize and return the modified glossary."""
        return self.glossary

    # -- interactive loop ------------------------------------------------

    def run(self) -> Glossary:
        """Interactive loop reading user commands.

        Commands:
            show                                 -- display entries
            edit <identifier> <field> <value>     -- edit a field
            remove <identifier>                   -- remove entry
            accept                                -- finalize
            quit / exit                           -- abort
        """
        self.display()
        click.echo(
            "\nCommands: show, edit <id> <field> <value>, remove <id>, accept, quit"
        )

        while True:
            try:
                line = click.prompt("glossary", type=str).strip()
            except (EOFError, click.Abort):
                break

            if not line:
                continue

            parts = line.split(maxsplit=3)
            cmd = parts[0].lower()

            if cmd == "show":
                self.display()
            elif cmd == "edit" and len(parts) >= 4:
                self.edit_entry(parts[1], parts[2], parts[3])
            elif cmd == "remove" and len(parts) >= 2:
                self.remove_entry(parts[1])
            elif cmd == "accept":
                return self.accept()
            elif cmd in ("quit", "exit"):
                click.echo("Aborted.")
                return self.glossary
            else:
                click.echo(f"Unknown command: {line}")
                click.echo("Commands: show, edit <id> <field> <value>, remove <id>, accept, quit")

        return self.glossary
