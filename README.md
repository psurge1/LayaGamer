# LayaGamer

## Games

The web dashboard includes four games:

- **Tic-tac-toe:** human versus the original tactical or fine-tuned agent.
- **Snake:** step or auto play; the harness supplies collision, relative food
  bearing, shortest visible food routes, and reachable-space context, and
  filters immediate deaths when possible.
- **Minesweeper:** step or auto play; the harness derives safe cells, certain
  mines, and risk estimates from the visible numbered board. Laya never receives
  the hidden mine coordinates.
- **Chess:** human versus tactical Laya as White or Black. The `chess` package
  (python-chess 1.11.2) owns legal moves, transitions, checks, castling,
  promotions, checkmate, stalemate, and draw outcomes. The harness supplies SAN,
  captures, checks, attacked destinations, and reply counts.

Snake and Minesweeper are intentionally step-based so every inference appears
in the shared decision inspector. Their **Auto play** controls repeatedly request
the same observable decisions. The web server lazily shares one base Laya Router
across all tactical agents; the fine-tuned tic-tac-toe checkpoint remains separate.

## Adding another game to the dashboard

The Game selector lists implemented games.
The dashboard remains vanilla JavaScript with native ES modules.

1. Add a `static/games/<game>.js` module exporting
   `mount(root, {config, inspector})`. It owns its controls, observation/action
   format, and timing (turns, keyboard input, or a timer). Return a cleanup
   function that cancels requests/timers, removes listeners, and ignores late
   responses. Scope game CSS beneath `[data-game="<game>"]`.
2. Use `inspector.render(records, selectedIndex, onSelect)` to show decisions.
   Each display record has `label`, `latencyMs`, `snapshot` (text), `note`, `raw`,
   and `choices`. Choices have `label`, `offered`, `selected`, `probability`, and
   optional `description`. This is presentation data, not a universal game state.
3. Add a server adapter in `games/<game>/web.py` with `describe()`,
   `prepare(payload)` (validation), and `decide(prepared)` (inference).
   Register it in the small `games` mapping in `web.py`, import its browser
   module in `static/app.js`, and allowlist its asset route in `web.py`.
   `/api/games` supplies game/agent labels; decisions use
   `/api/games/<game>/decision`. The old tic-tac-toe endpoints remain compatible.

Game-specific controls and the board live in the game view; history, histograms,
and request details are shared. Agents and checkpoints retain their existing
behavior. Run frontend checks with `node --test tests/frontend.test.mjs`.

The dashboard retains its dark lab palette with compact typography, a subdued
board surface, and an open analysis column. Styles live in
`src/layagamer/static/style.css`; refresh the browser to see visual updates.

Runtime agents sample moves from model probabilities with a moderate temperature by default.
This favors stronger-scoring choices while allowing variation. Tactical sampling
stays within the win/block constraints; a forced move remains deterministic.
Agent constructors accept `temperature=0` for the previous argmax behavior and
`seed` for reproducible sampling. Dashboard bars show the sampling distribution;
logs retain original model probabilities and the model's top choice separately.
Sampling adds variety, not learned competence, and can reduce playing strength.

Laya's probability output is deterministic for the same checkpoint and request;
it does not learn during a game. Snake uses temperature `1.0`, preserving rather
than sharpening that distribution when sampling. On CPU, model inference remains
the dominant per-step cost; the web auto-player adds only a short scheduling
pause between decisions and reports inference latency separately.

Gameplay observation (2026-09-28): the user reports that the tactical agent
substantially outperforms the current fine-tuned checkpoint, which plays poorly.
This is qualitative feedback, not a measured benchmark. Fine-tuned playing
strength remains an open issue; randomness does not resolve it.

## Separate fine-tuning agent

The new `games/tictactoe/agents/finetuned.py` agent uses
`decide(observation) -> Decision` and always offers every legal move. Its inputs
contain the board, mark, numbering, and rules; no tactical facts or forced
win/block choices. The existing tactical agent and dashboard retain their behavior.
Both agents reuse the existing immutable board engine.

Prepare a solver-labeled dataset, then explicitly train a new checkpoint:

```sh
uv run python -m layagamer.games.tictactoe.dataset --output artifacts/tictactoe/data.jsonl
uv run python -m layagamer.games.tictactoe.train --data artifacts/tictactoe/data.jsonl --output artifacts/tictactoe/checkpoint --device cpu
uv run python -m layagamer.games.tictactoe.play_finetuned --checkpoint ./artifacts/tictactoe/checkpoint
```

No trained weights ship with this scaffold. Training can take substantial time;
choose `--device mps` or `--device cuda` on compatible hardware. This initial
trainer freezes the encoder and trains the decision head using supervised
cross-entropy against a uniform distribution over optimal minimax actions.
It prints held-out validation accuracy after each epoch. Test examples are
reserved; rotations/reflections remain in the same split. Targets prefer win
over draw over loss, with no preference for how quickly equal outcomes occur.
Training and inference share the same versioned request builder. Checkpoint
probabilities are uncalibrated. Existing output files/directories are refused.

The training tensor format follows Laya's
[official notebook](https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb);
this repository uses supervised distillation rather than its RL training loop.

Local Laya game experiments, starting with terminal tic-tac-toe.

## Browser dashboard

```sh
uv run layagamer-web
# Or without reinstalling the entry point:
uv run python -m layagamer.web
```

Open http://127.0.0.1:8000 and select a game. Each game exposes its applicable
controls and agent choices. The dashboard automatically enables
Fine-tuned Laya when `artifacts/tictactoe/checkpoint/model.safetensors` exists;
use `--checkpoint PATH` for a different local checkpoint. Changing agents starts
a fresh game. Restart the server after training to load new weights.

Inspect
each Laya turn's probability histogram, pre-move board, tactical descriptions,
and full request/response. Decisions remain available for the current game's
history. Use `--device cpu` or `--port 8001` if desired.

Bars show sampling probabilities over offered actions, not internal reasoning. Legal
actions excluded by win/block constraints are marked filtered, not 0%.
The server reuses one local model and serializes inference across browser tabs.

```sh
uv run layagamer
uv run layagamer --opponent random --games 10 --seed 42
uv run layagamer --laya-mark O --show-state --log runs/decisions.jsonl
uv run layagamer --device cpu --opponent random
```

X goes first. Enter an empty square number (1–9, left to right, top to bottom)
to play. Default: one human game, Laya as X.

Each Laya turn sends the board, rules, marks, numbering, and legal moves as state.
One `choice` question offers only empty squares. Laya chooses directly; no
tactical solver selects its moves. A deterministic context supplier annotates
every legal action with immediate wins/draws, blocked threats, remaining enemy
winning squares, your next winning squares, forks, and opponent replies that
create unanswered forks. These facts appear in state and in each option's text.
The analysis looks ahead through one opponent reply. An explicit action policy
gives immediate wins priority: when any exist, only winning moves are offered
to Laya. With multiple wins, Laya chooses among them. Otherwise, if the opponent
threatens an immediate win, only complete blocks are offered. If several threats
make a complete block impossible, partial blocks are offered and the remaining
danger stays explicit. Without wins or threats, all legal moves remain available.
Full consequences remain in state
and logs even for actions excluded by this policy. This is a bounded tactical
guard, not a full-game solver or learning system.
Repeated states can still produce repeated choices. Game understanding and optimal play are not
guaranteed. The engine validates actions and detects wins and draws.

`games/tictactoe/engine.py` owns state and rules,
`games/tictactoe/agents/tactical.py` translates observations and legal actions
into predictions, and `main.py` runs terminal matches. Compatibility modules
preserve the original import paths. No diep.io automation is implemented yet.

The English checkpoint loads on the first prediction, using the default Laya
device unless `--device` is supplied. First use may download weights; later runs
reuse the cache. First-decision latency includes cold checkpoint loading.
JSONL records include full states, questions, responses with probabilities, and
latency. Random opponents are seeded; model results may vary between runs.

Test without loading weights:

```sh
uv run python -m unittest discover -s tests -v
```
