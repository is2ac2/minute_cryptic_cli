# Minute Cryptic CLI

Play [minutecryptic.com](https://www.minutecryptic.com/)'s daily cryptic clue in your terminal.

Uses the site's public JSON API (`/api/daily_puzzle/today`, `/api/daily_puzzle/id/<id>`,
`/api/daily_puzzle/par/<date>`) — no API key or login needed.

## Setup

Requires the [`rich`](https://github.com/Textualize/rich) package for the terminal UI:

```
pip3 install -r requirements.txt
```

A `mc` alias was added to `~/.zshrc`, pointing at `minute_cryptic.py` in this directory.
Open a new terminal (or `source ~/.zshrc`) and run:

```
mc
```

## Usage

Once running, you get today's clue and a blank-letter grid in a box that fills your
terminal width. Type a word directly to guess it — everything else needs a leading `/`:

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
