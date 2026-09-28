# Repository terminology

These definitions describe LayaGamer's vocabulary, not required classes or modules.

| Term | Meaning in this repository |
| --- | --- |
| Game engine | Owns game rules, authoritative state, legal actions, transitions, and terminal outcomes. |
| Observation | Game-specific information available to an agent at a decision point. It need not expose the engine's complete state. |
| Action | A game-specific command that can be applied to the engine or game environment. |
| Legal action | An action allowed by the game's rules in the current state. |
| Offered action | An action made available to Laya by an agent's harness. The harness may offer only a subset of legal actions. |
| Agent | A configured decision-maker combining a checkpoint and its harness. It turns a game-specific observation into a decision through `decide(observation)`. Agents may differ in checkpoint, harness, or both. |
| Decision | The common result envelope: a game-specific `action` plus diagnostic `metadata`. |
| Sampling | Selecting an offered action randomly according to a probability distribution. Sampling temperature controls how strongly the highest model probabilities are favored; zero selects the model's top choice deterministically. Model probabilities and sampling probabilities are recorded separately. |
| Harness | Runtime code surrounding the model: input preparation, context suppliers, question construction, action constraints, validation, and any explicit fallback or override. Game execution, training, and evaluation are separate responsibilities. |
| Context supplier | Computes additional facts from an observation, such as action consequences. Supplying facts does not itself select or restrict actions. |
| Action consequences | Predicted effects or tactical facts for a candidate action, with the analysis horizon made explicit. |
| Action constraint | A harness rule restricting offered actions, such as offering only immediate wins when they exist. Distinct from game legality. |
| Override | A harness rule replacing the model's selected action. Distinct from constraining choices before inference. |
| Checkpoint | Saved model weights and associated configuration/tokenizer artifacts used for inference. |
| Backend | The inference implementation that loads a checkpoint and executes predictions. |
| Runner | Drives turns or game steps, obtains agent decisions, applies actions, and records outcomes. |
| Game view | A browser module that owns a game's workspace, controls, and run loop. Mounting returns a cleanup function for switching games. |
| Decision inspector | Shared browser presentation of history, snapshots, action probabilities, and diagnostics. Games translate their records into display data; the inspector does not interpret game rules. |
| Evaluation | Measures a specified agent's performance, identifying the checkpoint and enabled harness aids. |
| Model-only evaluation | Tests learned decisions with tactical suppliers, constraints, overrides, and solver fallbacks disabled; basic observation encoding and legality validation remain. |
| Fine-tuning | Updating model weights using task-specific training data/objectives. Ordinary inference calls do not perform fine-tuning. |
| Teacher / oracle | A solver or other trusted source used to label training examples or evaluation targets. Its runtime use must be identified as a harness aid. |

Laya's wire payload calls encoded input `state` and decision queries `questions`.
Use **observation** for the agent input, **game state** for the engine's state,
and **request state** for the encoded Laya payload when the distinction matters.

Use **agent** rather than **policy**, **policy variant**, or **Laya instance**
for repository concepts. Name agents descriptively by their setup, such as
`tactical` or `finetuned`; **raw variant** is not an agreed repository term.

The current scaffold's `LayaPlayer.choose(board)` and dictionary result predate
the planned `decide(observation) -> Decision` boundary. These definitions guide
future changes; they do not imply that the interface migration is complete.
