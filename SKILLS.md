# SKILLS.md — notes for the next agent working on this repo

Context for picking this project back up. Read this before making changes.

## What this is

A terminal client for minutecryptic.com's daily cryptic clue game. `scripts/minute_cryptic.py`
fetches the puzzle from the site's undocumented JSON API and runs an interactive REPL to
solve it, with a `rich`-based UI (bordered panels, centered text, colors).

## The API (reverse-engineered, not documented anywhere)

Found by downloading the site's Next.js JS chunks and grepping for `/api/`. Base:
`https://www.minutecryptic.com/api/daily_puzzle`. No auth needed.

- `GET /today?tz=<IANA timezone>` — returns the puzzle object directly (NOT wrapped in
  `{"puzzle": ...}` — that wrapping only exists in the site's client-side localStorage
  cache logic, not the actual HTTP response). Fields: `puzzleId`, `date`, `clue` (list of
  `{text, type}`), `answer` (the full plaintext solution — no spoiler protection
  server-side), `puzzlePieces` (dict of index → `{answer, isRevealed, input}`, also leaks
  every letter), `config` (list of word lengths), `letterRevealOrder` (site's suggested
  letter-reveal sequence), `par`, `parDetails` (`averagePar`, `solveCount`), `hints` (list
  of `{text, type, colour, highlighting}` — `highlighting` is a list of `[start, end]`
  character offsets into the joined clue text, always ordered indicators → fodder →
  definition), `setterName`, `explainerVideo`, `thumbnail`.
- `GET /id/<puzzleId>` — same shape, for a specific puzzle.
- `GET /par/<date>` — just `parDetails`, with two extra fields (`averageHintsUsed`,
  `averageLettersRevealed`) not present in the `today`/`id` response.
- No date-indexed archive endpoint exists. Past puzzles are only reachable if you already
  have their id.

Local timezone is detected via `os.path.realpath("/etc/localtime")` (works on macOS/Linux),
falling back to `"UTC"` — no third-party tz library needed for that.

## Architecture

- `PuzzleSession` — holds one puzzle plus solve-in-progress state (`revealed` letter
  indices, `revealed_hints` indices, `wrong_guesses`, `letters_revealed_at_solve`).
- `run_session()` — REPL loop. **Bare input is always a guess; `/`-prefixed input is a
  command** (`/hint`, `/clue`, `/letter`, `/answer`, `/quit`, `/help`). This was a
  deliberate change from an earlier `guess <word>` / `g <word>` syntax — don't reintroduce
  the bare `guess`/`g` command.
- Rendering uses `rich` (`Console`, `Panel`, `Text`) — not hand-rolled ANSI. `Panel`
  defaults to `expand=True`, which is what makes boxes fill the terminal width; don't
  pass `width=` unless intentionally overriding that. Panel bodies use
  `Text(justify="center")` to center their content.
- Hint selection is **shorthand-only**: `i`/`f`/`d` (first letter of the hint's `type`).
  Numeric hint selection (`/hint 1`) was explicitly removed per user request — don't add
  it back without being asked.

## History feature

`record_and_save()` fires on **both** a successful guess and a confirmed `/answer`
give-up (via `handle_guess()` and the `/answer` branch of `handle_command()`
respectively). It prompts for a difficulty score and a puzzle rating (both 1-5, via
`prompt_rating()`, re-prompting on invalid input; `Ctrl-D`/`Ctrl-C` during the prompt
returns `None` rather than crashing) and then calls `save_history()`, which writes the
full puzzle dict plus a `stats` block to `isaac_history/<puzzle-date>.json` at the repo root:
`outcome` (`"solved"` or `"gaveUp"`), `wrongGuesses`, `hintsUsed`, `lettersRevealed`,
`difficulty`, `rating`, `recordedAt`.

`lettersRevealed` uses `PuzzleSession.letters_revealed_count`, a property that returns
`letters_revealed_at_solve` when solved (see the bug note below for why) or plain
`len(self.revealed)` when given up (safe in that case — give-up never overwrites
`self.revealed`).

`HISTORY_DIR` is computed as `Path(__file__).resolve().parent.parent / "isaac_history"` — this
assumes the script stays exactly one directory below the repo root (currently `scripts/`).
If you move the script again, update that path.

## A bug worth knowing about (already fixed, don't reintroduce)

`PuzzleSession.guess()` sets `self.revealed = set(range(piece_count))` on a correct guess
so the letter grid displays the full solved word. Because of that, `len(session.revealed)`
is useless as a "letters revealed" stat after solving — it's always the full word length.
The fix: snapshot the real count into `letters_revealed_at_solve` *before* overwriting
`self.revealed`. Use `letters_revealed_at_solve` for any post-solve stats, never
`len(session.revealed)`.

## Testing approach used throughout this project (no test suite exists)

- `python3 -c "import py_compile; py_compile.compile('scripts/minute_cryptic.py', doraise=True)"`
  as a fast syntax check after every edit.
- Simulate the REPL with piped stdin: `printf '/hint i\nguess\n/quit\n' | python3 scripts/minute_cryptic.py`.
  Note `rich` disables color when stdout isn't a tty, so this only verifies logic/text, not styling.
- To verify ANSI colors and terminal-width behavior (e.g. that panels actually expand),
  run under a pty: `COLUMNS=120 script -q /dev/null python3 scripts/minute_cryptic.py`,
  then inspect with `cat -v` or strip ANSI codes with a regex to check exact line widths.
- To test the live `mc` zsh alias end-to-end, write `source ~/.zshrc` and the command as
  **separate lines in a temp script file**, then `zsh /tmp/that_file.zsh`. A single
  `zsh -c 'source ~/.zshrc && mc'` does NOT reliably expand the alias — that's a zsh
  one-liner parsing quirk, not a real bug in the setup. Don't waste time debugging it.

## Dotfiles note

`~/.zshrc` is a symlink to `~/Github/dotfiles/zshrc` (a separate repo). The `Edit` tool
refuses to write through symlinks — edit `~/Github/dotfiles/zshrc` directly, not `~/.zshrc`.
The `mc` alias lives there.

## Known constraints / non-goals

- No pip package structure (no `setup.py`/`pyproject.toml`) — it's a single script plus
  a `requirements.txt`, installed via a shell alias. Don't add packaging machinery unless
  asked.
- `rich` is the one required third-party dependency; the script exits with a clear
  install message if it's missing rather than silently degrading.
