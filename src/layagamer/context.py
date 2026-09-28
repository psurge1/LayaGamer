"""Supply bounded tactical facts without selecting or filtering actions."""

from layagamer.tictactoe import Board, LINES


def winning_squares(cells: tuple[str, ...], mark: str) -> list[str]:
    """Empty squares that complete at least one line for this mark."""
    return sorted({str(i + 1) for line in LINES
                   if sum(cells[j] == mark for j in line) == 2
                   for i in line if cells[i] == "."}, key=int)


def consequences(board: Board) -> dict[str, dict]:
    """Inspect each action and one opponent reply; no minimax or ranking."""
    if board.finished:
        raise ValueError("No consequences on a finished board")
    you = board.turn
    opponent = "O" if you == "X" else "X"
    threats = winning_squares(board.cells, opponent)
    facts = {}
    for move in board.legal_moves:
        after = board.play(move)
        wins = after.winner == you
        draws = after.finished and not wins
        own_threats = [] if after.finished else winning_squares(after.cells, you)
        opponent_wins = [] if after.finished else winning_squares(after.cells, opponent)
        forks = []
        for reply in after.legal_moves:
            response = after.play(reply)
            # A fork matters only when the reply does not end the game and
            # you cannot win immediately before the opponent uses its threats.
            if (not response.finished and not winning_squares(response.cells, you)
                    and len(winning_squares(response.cells, opponent)) >= 2):
                forks.append(reply)
        facts[move] = {
            "wins_now": wins,
            "draws_now": draws,
            "blocks_threat_at": move if move in threats else None,
            "opponent_can_win_next_at": opponent_wins,
            "your_next_winning_squares": own_threats,
            "creates_fork": len(own_threats) >= 2,
            "opponent_fork_replies": forks,
            "position": "center" if move == "5" else "corner" if move in ("1", "3", "7", "9") else "edge",
        }
    return facts


def describe(fact: dict) -> str:
    """Put consequences alongside the option so they survive state truncation."""
    if fact["wins_now"]:
        return "Wins the game immediately."
    if fact["draws_now"]:
        return "Ends the game in a draw."
    parts = []
    if fact["blocks_threat_at"]:
        parts.append(f"Blocks the opponent's winning square {fact['blocks_threat_at']}.")
    if fact["opponent_can_win_next_at"]:
        parts.append("Allows the opponent to win immediately at square(s) "
                     + ", ".join(fact["opponent_can_win_next_at"]) + ".")
    else:
        parts.append("Opponent has no immediate winning move.")
    if fact["creates_fork"]:
        parts.append("Creates a fork: two or more winning threats.")
    if fact["your_next_winning_squares"]:
        parts.append("Your next winning square(s): " + ", ".join(fact["your_next_winning_squares"]) + ".")
    if fact["opponent_fork_replies"]:
        parts.append("Opponent can create an unanswered fork by playing "
                     + ", ".join(fact["opponent_fork_replies"]) + ".")
    parts.append(f"Occupies a {fact['position']}.")
    return " ".join(parts)
