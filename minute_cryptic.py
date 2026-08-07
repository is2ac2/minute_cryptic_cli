#!/usr/bin/env python3
"""Interactive terminal client for minutecryptic.com's daily puzzle."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    sys.exit(
        "minute cryptic: this tool needs the 'rich' package.\n"
        "Install it with: pip3 install rich"
    )

API_BASE = "https://www.minutecryptic.com/api/daily_puzzle"
USER_AGENT = "Mozilla/5.0 (minute-cryptic-cli)"
HINT_STYLES = {"indicators": "magenta", "fodder": "yellow", "definition": "blue"}

console = Console()


def hint_shorthand(label):
    return label[0] if label else "?"


def local_timezone():
    try:
        real_path = os.path.realpath("/etc/localtime")
        if "zoneinfo/" in real_path:
            return real_path.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    return "UTC"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"minute cryptic: request failed ({e.code} {e.reason}) for {url}")
    except urllib.error.URLError as e:
        sys.exit(f"minute cryptic: could not reach minutecryptic.com ({e.reason})")


def fetch_today():
    return fetch_json(f"{API_BASE}/today?tz={local_timezone()}")


def fetch_by_id(puzzle_id):
    return fetch_json(f"{API_BASE}/id/{puzzle_id}")


class PuzzleSession:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.clue_words = [w["text"] for w in puzzle["clue"]]
        self.clue_text = " ".join(self.clue_words)
        self.answer = puzzle["answer"].upper()
        self.reveal_order = puzzle["letterRevealOrder"]
        self.piece_count = len(puzzle["puzzlePieces"])
        self.groups = self._letter_groups(puzzle["config"])
        self.hints = puzzle["hints"]
        self.revealed = set()
        self.revealed_hints = set()
        self.wrong_guesses = 0
        self.solved = False
        self.gave_up = False
        self.letters_revealed_at_solve = 0

    @staticmethod
    def _letter_groups(config):
        groups, idx = [], 0
        for word_len in config:
            groups.append(list(range(idx, idx + word_len)))
            idx += word_len
        return groups

    def blanks_text(self):
        text = Text()
        for gi, group in enumerate(self.groups):
            if gi:
                text.append("   ")
            for i, idx in enumerate(group):
                if i:
                    text.append(" ")
                if idx in self.revealed:
                    text.append(self.answer[idx], style="bold green")
                else:
                    text.append("_", style="dim")
        return text

    def reveal_next_letter(self):
        remaining = [i for i in self.reveal_order if i not in self.revealed]
        if not remaining:
            return None
        idx = remaining[0]
        self.revealed.add(idx)
        return idx

    def resolve_hint_query(self, query):
        query = query.strip().lower()
        if not query:
            return None
        for i, hint in enumerate(self.hints):
            label = (hint["type"] or "").lower()
            if query == hint_shorthand(label):
                return i
        return None

    def reveal_hint(self, idx):
        self.revealed_hints.add(idx)
        return self.hints[idx]

    def guess(self, word):
        if word.strip().upper() == self.answer:
            self.solved = True
            self.letters_revealed_at_solve = len(self.revealed)
            self.revealed = set(range(self.piece_count))
            return True
        self.wrong_guesses += 1
        return False


def par_text(puzzle):
    details = puzzle.get("parDetails") or {}
    text = Text()
    text.append("Par: ", style="dim")
    text.append(str(puzzle["par"]), style="bold yellow")
    text.append(" avg ", style="dim")
    text.append(str(details.get("averagePar", "?")), style="bold blue")
    text.append(" solves ", style="dim")
    text.append(str(details.get("solveCount", "?")), style="bold cyan")
    return text


def print_header(session):
    puzzle = session.puzzle
    body = Text(justify="center")
    body.append(f"Minute Cryptic — {puzzle['date']}", style="bold cyan")
    body.append("  ")
    body.append(f"(par {puzzle['par']})", style="bold yellow")
    body.append("\n")
    if puzzle.get("setterName"):
        body.append(f"Set by {puzzle['setterName']}", style="magenta")
        body.append("\n")
    body.append_text(par_text(puzzle))
    body.append("\n\n")
    body.append(session.clue_text, style="bold")
    body.append("\n\n")
    body.append_text(session.blanks_text())
    console.print()
    console.print(Panel(body, border_style="cyan"))
    console.print()


def print_hint(session, idx):
    hint = session.hints[idx]
    label = hint["type"] or "hint"
    style = HINT_STYLES.get(label)
    body = Text(justify="center")

    if hint.get("highlighting"):
        clue = Text(session.clue_text)
        for start, end in hint["highlighting"]:
            clue.stylize(f"bold underline {style}" if style else "bold", start, end)
        body.append_text(clue)
        body.append("\n\n")

    body.append(f"[{label}] ", style=f"bold {style}" if style else "dim")
    body.append(hint["text"])
    console.print(Panel(body, border_style=style or "cyan"))
    console.print()


def print_hint_menu(session):
    body = Text(justify="center")
    body.append("Hints\n\n", style="bold")
    for i, hint in enumerate(session.hints):
        label = hint["type"] or "hint"
        style = HINT_STYLES.get(label)
        seen = i in session.revealed_hints
        body.append("● ", style=style or "white")
        body.append(f"{label:<11} ", style=None)
        body.append(f"({hint_shorthand(label)})  ", style=f"bold {style}" if style else None)
        body.append("[", style="dim")
        body.append("seen" if seen else "new", style="dim" if seen else "green")
        body.append("]\n", style="dim")
    body.append("\n")
    body.append("Use: /hint <shorthand>", style="dim")
    console.print(Panel(body, border_style="cyan"))
    console.print()


def print_help():
    text = Text()
    text.append("Type your guess directly. ", style="dim")
    text.append("Commands: ")
    for i, token in enumerate(["/hint [i|f|d]", "/clue", "/letter", "/answer", "/quit", "/help"]):
        if i:
            text.append("   ")
        text.append(token, style="cyan")
    console.print(text)


def handle_command(session, cmd, arg):
    if cmd in ("q", "quit", "exit"):
        console.print("See you tomorrow.")
        return True
    elif cmd in ("?", "help"):
        print_help()
    elif cmd in ("c", "clue"):
        print_header(session)
    elif cmd in ("h", "hint"):
        if not arg:
            print_hint_menu(session)
            return False
        idx = session.resolve_hint_query(arg)
        if idx is None:
            console.print(Text(f"No hint matches '{arg}'.", style="red"))
        else:
            session.reveal_hint(idx)
            print_hint(session, idx)
    elif cmd in ("l", "letter"):
        idx = session.reveal_next_letter()
        if idx is None:
            console.print(Text("All letters already revealed.", style="dim"))
        else:
            console.print(session.blanks_text())
        console.print()
    elif cmd in ("a", "answer"):
        confirm = input("Give up and reveal the answer? [y/N] ").strip().lower()
        if confirm == "y":
            session.gave_up = True
            console.print(Text.from_markup(f"The answer was [bold green]{session.answer}[/]."))
    else:
        console.print(Text(f"Unknown command '/{cmd}'.", style="red"))
        print_help()
    return False


def handle_guess(session, word):
    if session.guess(word):
        console.print()
        body = Text(justify="center")
        body.append(f"Correct! {session.answer}", style="bold green")
        body.append("\n\n")
        body.append("Wrong guesses: ", style="dim")
        body.append(str(session.wrong_guesses), style="bold yellow")
        body.append("   Hints used: ", style="dim")
        body.append(str(len(session.revealed_hints)), style="bold blue")
        body.append("   Letters revealed: ", style="dim")
        body.append(str(session.letters_revealed_at_solve), style="bold cyan")
        body.append("\n")
        body.append_text(par_text(session.puzzle))
        console.print(Panel(body, border_style="green"))
        console.print()
    else:
        console.print(Text("Not quite — try again.", style="red"))


def run_session(session):
    print_header(session)
    print_help()
    console.print()

    while not session.solved and not session.gave_up:
        try:
            raw = console.input("[bold cyan]mc> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return

        if not raw:
            continue

        if raw.startswith("/"):
            cmd, _, arg = raw[1:].partition(" ")
            if handle_command(session, cmd.lower(), arg.strip()):
                return
        else:
            handle_guess(session, raw)


def main():
    parser = argparse.ArgumentParser(description="Play today's Minute Cryptic puzzle in your terminal.")
    parser.add_argument("--id", metavar="PUZZLE_ID", help="load a specific puzzle by id instead of today's")
    args = parser.parse_args()

    puzzle = fetch_by_id(args.id) if args.id else fetch_today()
    session = PuzzleSession(puzzle)
    run_session(session)


if __name__ == "__main__":
    main()
