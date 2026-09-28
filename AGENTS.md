# LayaGamer conventions

This repository experiments with local Laya agents across games.
Support different harnesses, checkpoints, and training approaches through a
small shared decision boundary; each agent may use different observations,
questions, context, and action representations.

Read [TERMINOLOGY.md](TERMINOLOGY.md) for repository-specific vocabulary. Use
its terms consistently in code, documentation, and discussion. Update the
glossary when introducing or changing a repository concept; definitions describe
responsibilities and do not require a separate abstraction for every term.

## Decision boundary

- Use `decide(observation) -> Decision` for new agents. Observations and
  actions are game-specific typed values, not a universal board/schema.
- Keep the shared `Decision` envelope small: `action` and `metadata`. Metadata
  records agent identity, checkpoint identity, inference latency, and optional
  request/response diagnostics. Preserve game-specific actions inside `action`.
- An agent's harness owns observation encoding, context, question construction, model
  invocation, and response decoding. Runners consume decisions without knowing
  the agent's prompt format or training method.
- Game engines own rules, legal actions, transitions, and terminal outcomes.
  Validate decoded actions at the agent boundary and legality at the engine.
- Make tactical filtering, overrides, fallbacks, and context suppliers explicit
  agent configuration choices. Record their use in diagnostics. Evaluation of model-only
  behavior must allow these aids to be disabled.

## Organization

- As additional agents/games arrive, group rules, runners, and evaluations
  under `games/<game>/`, and game-specific agents under that game's
  `agents/`. Name agents descriptively, e.g. `tactical`, `finetuned`.
- Share only the decision envelope and genuinely reused inference utilities
  under `agents/` at package level. Keep training and dataset generation
  separate from runtime inference; store weights and run artifacts outside code.
- Tic-tac-toe, Snake, Minesweeper, and Chess follow the game-package layout.
  Compatibility imports preserve the original tic-tac-toe CLI paths. Do not build empty packages,
  plugin registries, abstract base classes, or a universal game framework ahead
  of demonstrated needs. Use a small `Protocol` only when interchangeability
  needs a typed contract.

## Implementation and verification

- Python 3.12+, uv, snake_case functions/modules, PascalCase classes. Use
  annotations at public boundaries, small dataclasses for structured values,
  explicit dependencies, and ordinary composition. Keep dictionaries for Laya
  wire payloads and flexible diagnostics; avoid pervasive `Any`.
- Load models lazily and reuse them. Imports, help commands, and engine tests
  must not load weights or require network access. Checkpoint/device selection
  belongs in agent configuration, not game rules.
- Keep inference independent of training: predictions do not imply learning.
  Preserve input encoding with trained artifacts so training and serving agree.
- Test rules and tactical facts independently of model quality. Use injected
  fake backends for decision-contract tests. Measure actual model quality with
  separate evaluations, including wins, blocks, and forks; label results by
  agent, checkpoint, and enabled aids. Keep equivalent board symmetries in
  the same split for training/evaluation.
- Run `uv run python -m unittest discover -s tests -v` for relevant changes.
  Document behavior changes and runnable commands in README.md.
