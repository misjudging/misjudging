from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("judgements.json")


@dataclass
class Entry:
    id: int
    statement: str
    created_at: str
    closed: bool = False
    outcome: str = ""


def load_entries() -> list[Entry]:
    if not DATA_FILE.exists():
        return []
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [Entry(**item) for item in raw]


def save_entries(entries: list[Entry]) -> None:
    DATA_FILE.write_text(
        json.dumps([asdict(e) for e in entries], indent=2),
        encoding="utf-8",
    )


def add_entry(statement: str) -> None:
    entries = load_entries()
    next_id = 1 if not entries else max(e.id for e in entries) + 1
    entries.append(Entry(id=next_id, statement=statement, created_at=datetime.utcnow().isoformat()))
    save_entries(entries)
    print(f"Added entry #{next_id}")


def list_entries() -> None:
    entries = load_entries()
    if not entries:
        print("No entries yet.")
        return
    for e in entries:
        status = "closed" if e.closed else "open"
        suffix = f" | outcome: {e.outcome}" if e.outcome else ""
        print(f"#{e.id} [{status}] {e.statement}{suffix}")


def close_entry(entry_id: int, outcome: str) -> None:
    entries = load_entries()
    for e in entries:
        if e.id == entry_id:
            e.closed = True
            e.outcome = outcome
            save_entries(entries)
            print(f"Closed entry #{entry_id}")
            return
    print(f"Entry #{entry_id} not found.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    add_cmd = sub.add_parser("add")
    add_cmd.add_argument("statement")

    sub.add_parser("list")

    close_cmd = sub.add_parser("close")
    close_cmd.add_argument("id", type=int)
    close_cmd.add_argument("--outcome", required=True)

    args = parser.parse_args()

    if args.command == "add":
        add_entry(args.statement)
    elif args.command == "list":
        list_entries()
    elif args.command == "close":
        close_entry(args.id, args.outcome)


if __name__ == "__main__":
    main()
