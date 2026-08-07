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

## History

Every puzzle you solve is saved as JSON to `history/<date>.json` in this repo — the full
puzzle (clue, answer, hints, par) plus your stats for that solve (wrong guesses, which
hint types you used, how many letters you revealed, and the solve timestamp).

## Project layout

```
scripts/minute_cryptic.py   the CLI itself
history/                    one JSON file per solved puzzle, named by date
requirements.txt            Python dependencies (rich)
```
