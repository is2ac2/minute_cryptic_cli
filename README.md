# Minute Cryptic CLI

Play [minutecryptic.com](https://www.minutecryptic.com/)'s daily cryptic clue in your terminal.

Uses the site's public JSON API (`/api/daily_puzzle/today`, `/api/daily_puzzle/id/<id>`,
`/api/daily_puzzle/par/<date>`) — no API key or login needed.

## Install

Clone the repo and install the one dependency ([`rich`](https://github.com/Textualize/rich),
used for the terminal UI):

```
git clone <this-repo-url>
cd minute_cryptic_cli
pip3 install -r requirements.txt
```

Make the script executable and put it on your `PATH`, or add an alias. For zsh, add this
line to your `~/.zshrc` (adjust the path to wherever you cloned the repo):

```
alias mc="/path/to/minute_cryptic_cli/scripts/minute_cryptic.py"
```

Then reload your shell config and run it:

```
source ~/.zshrc
mc
```

## Usage

Running `mc` fetches today's puzzle and shows the clue and a blank-letter grid in a box
that fills your terminal width. Type a word directly to guess it — everything else needs
a leading `/`:

```
mc> great apes         # guesses are typed directly, no command needed
mc> /hint              # list the three hint types (indicators, fodder, definition)
mc> /hint i            # reveal a specific hint by shorthand: i, f, or d
mc> /letter            # reveal the next letter, in the site's suggested order
mc> /clue              # re-show the puzzle box (title, par, clue, letter grid)
mc> /answer            # give up and reveal the answer (asks to confirm)
mc> /quit              # exit without spoiling anything left unrevealed
```

To load a specific past puzzle instead of today's, if you know its id:

```
mc --id <puzzle-id>
```

There's no date-indexed archive endpoint in the API — only `today` and `id/<id>` lookups.

## Replay

```
mc 2026-08-06
```

Replays a puzzle you've already played, loaded from your own `isaac_history/<date>.json`
— no network call needed. A `[replay]` tag shows in the header, and solving or giving up
does **not** prompt for a rating or touch that day's saved stats; it's just a replay. You
can only replay dates that already have a history entry.

## History

After you solve a puzzle (or give up with `/answer`), you're asked to rate it (skipped
entirely in replay mode, see above) — a
difficulty score and a puzzle rating, both 1-5. The result is saved as JSON to
`isaac_history/<date>.json` in this repo: the full puzzle (clue, answer, hints, par) plus your
stats for that attempt — outcome (solved/gave up), wrong guesses, which hint types you
used, how many letters you revealed, your difficulty/rating scores, and a timestamp.

## Project layout

```
scripts/minute_cryptic.py   the CLI itself
isaac_history/              one JSON file per puzzle attempt, named by date
requirements.txt            Python dependencies (rich)
```
