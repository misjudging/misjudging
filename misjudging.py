from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

DATA_FILE = Path("judgements.json")


@dataclass
class Entry:
    id: int
    statement: str
    created_at: str
    closed: bool = False
    outcome: str = ""
    closed_at: str = ""


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
    entries.append(
        Entry(
            id=next_id,
            statement=statement,
            created_at=datetime.now(UTC).isoformat(),
        )
    )
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


def parse_iso_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def classify_outcome(outcome: str) -> str:
    text = outcome.lower()
    positive = {"right", "won", "up", "profit", "good", "success", "correct", "worked"}
    negative = {"wrong", "lost", "down", "loss", "bad", "fail", "failed", "incorrect"}
    pos = sum(1 for word in positive if word in text)
    neg = sum(1 for word in negative if word in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def print_stats(days: int | None = None) -> None:
    entries = load_entries()
    if not entries:
        print("No entries yet.")
        return

    if days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        scoped_entries = [
            e for e in entries if parse_iso_timestamp(e.created_at).astimezone(UTC) >= cutoff
        ]
        label = f"last {days} day(s)"
    else:
        scoped_entries = entries
        label = "all time"

    if not scoped_entries:
        print(f"No entries found for {label}.")
        return

    total = len(scoped_entries)
    closed = [e for e in scoped_entries if e.closed]
    open_entries = [e for e in scoped_entries if not e.closed]
    closed_count = len(closed)
    open_count = len(open_entries)
    close_rate = (closed_count / total) * 100

    moods = Counter(classify_outcome(e.outcome) for e in closed if e.outcome)
    top_outcomes = Counter(e.outcome.strip().lower() for e in closed if e.outcome.strip())
    longest_open = None
    if open_entries:
        oldest_open = min(open_entries, key=lambda e: parse_iso_timestamp(e.created_at))
        longest_open = (datetime.now(UTC) - parse_iso_timestamp(oldest_open.created_at).astimezone(UTC)).days

    streak = 0
    for e in sorted(scoped_entries, key=lambda item: item.id, reverse=True):
        if e.closed:
            streak += 1
        else:
            break

    print(f"Stats ({label})")
    print(f"- Total: {total}")
    print(f"- Open: {open_count}")
    print(f"- Closed: {closed_count}")
    print(f"- Closure rate: {close_rate:.1f}%")
    print(f"- Current close streak: {streak}")

    if longest_open is not None:
        print(f"- Oldest open age: {longest_open} day(s)")

    if moods:
        print(
            f"- Outcome mood: +{moods.get('positive', 0)} / "
            f"-{moods.get('negative', 0)} / ={moods.get('neutral', 0)}"
        )

    if top_outcomes:
        print("- Top outcomes:")
        for text, count in top_outcomes.most_common(3):
            print(f"  {count}x {text}")


def search_entries(query: str) -> None:
    entries = load_entries()
    q = query.lower()
    matches = [e for e in entries if q in e.statement.lower() or q in e.outcome.lower()]
    if not matches:
        print(f"No matches for '{query}'.")
        return

    for e in matches:
        status = "closed" if e.closed else "open"
        suffix = f" | outcome: {e.outcome}" if e.outcome else ""
        print(f"#{e.id} [{status}] {e.statement}{suffix}")


def random_open_entry() -> None:
    entries = [e for e in load_entries() if not e.closed]
    if not entries:
        print("No open entries to pick from.")
        return
    pick = random.choice(entries)
    print(f"Random open pick -> #{pick.id}: {pick.statement}")


def close_entry(entry_id: int, outcome: str) -> None:
    entries = load_entries()
    for e in entries:
        if e.id == entry_id:
            if e.closed:
                print(f"Entry #{entry_id} is already closed.")
                return
            e.closed = True
            e.outcome = outcome
            e.closed_at = datetime.now(UTC).isoformat()
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
    stats_cmd = sub.add_parser("stats")
    stats_cmd.add_argument("--days", type=int)
    search_cmd = sub.add_parser("search")
    search_cmd.add_argument("query")
    sub.add_parser("random")

    close_cmd = sub.add_parser("close")
    close_cmd.add_argument("id", type=int)
    close_cmd.add_argument("--outcome", required=True)

    args = parser.parse_args()

    if args.command == "add":
        add_entry(args.statement)
    elif args.command == "list":
        list_entries()
    elif args.command == "stats":
        print_stats(args.days)
    elif args.command == "search":
        search_entries(args.query)
    elif args.command == "random":
        random_open_entry()
    elif args.command == "close":
        close_entry(args.id, args.outcome)


if __name__ == "__main__":
    main()
