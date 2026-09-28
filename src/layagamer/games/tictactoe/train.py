"""Supervised decision-head fine-tuning; encoder remains frozen."""
import argparse
import json
from pathlib import Path
import random

from layagamer.games.tictactoe.agents.finetuned import ENCODING_VERSION


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base", default="convaiinnovations/laya")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output must be a new directory; existing checkpoints are never overwritten")
    if args.epochs < 1 or args.learning_rate <= 0:
        parser.error("epochs and learning-rate must be positive")
    rows = [json.loads(line) for line in args.data.read_text().splitlines() if line.strip()]
    if not rows or any(row["encoding_version"] != ENCODING_VERSION for row in rows):
        parser.error("Dataset encoding does not match this agent")
    train = [row for row in rows if row["split"] == "train"]
    validation = [row for row in rows if row["split"] == "validation"]
    if not train or not validation:
        parser.error("Dataset needs train and validation examples")
    if {r["group"] for r in train} & {r["group"] for r in validation}:
        parser.error("Train and validation symmetry groups overlap")
    import torch
    from laya import Agent
    from laya.common import build_sequence, QTYPES
    from safetensors.torch import save_file

    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    backend = Agent(args.base, device=args.device)
    model = backend.model
    for parameter in model.encoder.parameters():
        parameter.requires_grad_(False)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.learning_rate)

    def forward(row: dict):
        question = row["questions"]["move"]
        seq, markers = build_sequence(backend.tok, row["state"],
            {"t": "choice", "ins": question["instructions"], "crit": question["criteria"]},
            backend.cfg["max_len"], backend.cfg["head_max_len"])
        if len(markers) != len(question["criteria"]):
            raise ValueError("Tokenization dropped action markers")
        tensor = lambda data: torch.tensor(data, device=backend.device)
        logits, _ = model(input_ids=tensor([seq]), attention_mask=tensor([[1] * len(seq)]),
            marker_pos=tensor([markers]), marker_mask=tensor([[True] * len(markers)]),
            qtype=tensor([QTYPES["choice"]]))
        target = tensor([[row["target"][m] for m in question["criteria"]]])
        return logits, target

    for epoch in range(args.epochs):
        rng.shuffle(train)
        model.train()
        model.encoder.eval()
        total = 0.0
        for row in train:
            optimizer.zero_grad(set_to_none=True)
            logits, target = forward(row)
            loss = -(target * torch.log_softmax(logits, -1)).sum()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total += loss.item()
        model.eval()
        correct = 0
        with torch.no_grad():
            for row in validation:
                logits, _ = forward(row)
                move = list(row["questions"]["move"]["criteria"])[logits.argmax().item()]
                correct += move in row["optimal_moves"]
        print(f"Epoch {epoch + 1}: loss={total / len(train):.4f}, validation optimal={correct / len(validation):.3f}", flush=True)

    args.output.mkdir(parents=True, exist_ok=False)
    model.encoder.config.save_pretrained(args.output / "encoder")
    backend.tok.save_pretrained(args.output / "tokenizer")
    cfg = dict(backend.cfg)
    cfg.pop("temperature_by_options", None)
    cfg["temperature"] = [1.0, 1.0, 1.0]
    (args.output / "rl_agent_config.json").write_text(json.dumps(cfg, indent=2))
    save_file({name: tensor.detach().cpu().contiguous() for name, tensor in model.state_dict().items()}, str(args.output / "model.safetensors"))
    (args.output / "training.json").write_text(json.dumps({"encoding_version": ENCODING_VERSION,
        "base": args.base, "epochs": args.epochs, "seed": args.seed,
        "method": "supervised decision-head training; frozen encoder", "calibrated": False}, indent=2))
    print(f"Saved {args.output}. Probabilities have not been calibrated.")


if __name__ == "__main__":
    main()
