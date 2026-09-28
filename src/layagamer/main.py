import argparse
import json
import random
from pathlib import Path

from layagamer.games.tictactoe.agents.tactical import LayaPlayer
from layagamer.games.tictactoe.engine import Board


def main() -> None:
    parser = argparse.ArgumentParser(description="Play tic-tac-toe with local Laya")
    parser.add_argument("--opponent", choices=("human", "random"), default="human")
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--laya-mark", choices=("X", "O"), default="X")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", help="cpu, mps, or cuda")
    parser.add_argument("--show-state", action="store_true")
    parser.add_argument("--log", type=Path, help="Append inference records to JSONL")
    args = parser.parse_args()
    if args.games < 1:
        parser.error("--games must be positive")
    player = LayaPlayer(device=args.device)
    rng = random.Random(args.seed)
    totals = dict(wins=0, losses=0, draws=0)
    try:
        for game in range(1, args.games + 1):
            board = Board()
            print(f"\nGame {game}: Laya is {args.laya_mark}. X goes first.")
            print(board.render())
            while not board.finished:
                if board.turn == args.laya_mark:
                    if args.show_state:
                        state, questions = player.request(board)
                        print(json.dumps(dict(state=state, questions=questions), indent=2))
                    decision = player.choose(board)
                    move = decision["move"]
                    print(f"Laya chooses {move} ({decision['latency_ms']:.1f} ms)")
                    if args.log:
                        args.log.parent.mkdir(parents=True, exist_ok=True)
                        with args.log.open("a") as stream:
                            stream.write(json.dumps({"game": game, **decision}) + "\n")
                elif args.opponent == "random":
                    move = rng.choice(board.legal_moves)
                    print(f"Random opponent chooses {move}")
                else:
                    while True:
                        move = input(f"Your move ({', '.join(board.legal_moves)}): ").strip()
                        if move in board.legal_moves:
                            break
                        print("Choose an empty square numbered 1–9.")
                board = board.play(move)
                print(board.render())
            outcome = "draws" if board.winner is None else (
                "wins" if board.winner == args.laya_mark else "losses")
            totals[outcome] += 1
            print("Draw." if board.winner is None else f"{board.winner} wins.")
    except (EOFError, KeyboardInterrupt):
        print("\nStopped.")
    print(f"Laya results: {totals}")


if __name__ == "__main__":
    main()
