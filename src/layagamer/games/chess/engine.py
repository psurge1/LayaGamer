"""Immutable wrapper around python-chess's authoritative rules engine."""
from dataclasses import dataclass
import chess

PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}


@dataclass(frozen=True)
class ChessState:
    fen: str = chess.STARTING_FEN

    def __post_init__(self) -> None:
        board = chess.Board(self.fen)
        if not board.is_valid(): raise ValueError("Invalid chess position")

    def board(self) -> chess.Board:
        return chess.Board(self.fen)

    @property
    def finished(self) -> bool:
        return self.board().is_game_over(claim_draw=True)

    @property
    def legal_actions(self) -> tuple[str, ...]:
        return tuple(move.uci() for move in self.board().legal_moves)

    def apply(self, action: str) -> "ChessState":
        board = self.board(); move = chess.Move.from_uci(action)
        if move not in board.legal_moves: raise ValueError("Illegal chess move")
        board.push(move)
        return ChessState(board.fen())

    def serialize(self) -> dict:
        board = self.board(); outcome = board.outcome(claim_draw=True)
        pieces = [{"square": chess.square_name(square), "symbol": piece.symbol(),
                   "color": "white" if piece.color else "black"}
                  for square, piece in board.piece_map().items()]
        return {"fen": self.fen, "turn": "white" if board.turn else "black",
                "pieces": pieces, "legal_moves": list(self.legal_actions),
                "check": board.is_check(), "finished": outcome is not None,
                "outcome": None if outcome is None else {
                    "winner": None if outcome.winner is None else "white" if outcome.winner else "black",
                    "termination": outcome.termination.name.lower().replace("_", " ")}}

    def consequences(self) -> dict[str, dict]:
        board = self.board(); facts = {}
        for move in board.legal_moves:
            san = board.san(move)
            captured = board.piece_at(move.to_square)
            if board.is_en_passant(move): captured = chess.Piece(chess.PAWN, not board.turn)
            mover = board.piece_at(move.from_square)
            after = board.copy(); after.push(move)
            attacked = after.is_attacked_by(after.turn, move.to_square)
            defended = after.is_attacked_by(not after.turn, move.to_square)
            facts[move.uci()] = {"san": san, "capture": None if captured is None else captured.symbol().lower(),
                "capture_value": 0 if captured is None else PIECE_VALUES[captured.piece_type],
                "piece": mover.symbol().upper(), "check": after.is_check(), "checkmate": after.is_checkmate(),
                "promotion": None if move.promotion is None else chess.piece_name(move.promotion),
                "destination_attacked": attacked, "destination_defended": defended,
                "opponent_legal_replies": after.legal_moves.count()}
        return facts
