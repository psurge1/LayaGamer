"""Play against an explicitly selected fine-tuning checkpoint."""
import argparse

from layagamer.games.tictactoe.agents.finetuned import FinetunedAgent
from .engine import Board


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device")
    parser.add_argument("--human-mark", choices=("X", "O"), default="X")
    args = parser.parse_args()
    agent = FinetunedAgent(args.checkpoint, device=args.device)
    board = Board()
    try:
        while not board.finished:
            print(board.render())
            if board.turn == args.human_mark:
                move = input("Your square: ").strip()
                if move not in board.legal_moves:
                    print("Choose an empty square.")
                    continue
            else:
                decision = agent.decide(board)
                move = decision.action
                print(f"Laya chooses {move}")
            board = board.play(move)
        print(board.render())
        print(f"{board.winner} wins" if board.winner else "Draw")
    except (EOFError, KeyboardInterrupt):
        print("\nStopped.")


if __name__ == "__main__":
    main()
