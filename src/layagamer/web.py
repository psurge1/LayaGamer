"""Local browser runner; no additional server dependencies."""

import argparse
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock

from layagamer.games.tictactoe.agents.tactical import LayaPlayer
from layagamer.games.tictactoe.web import TicTacToeWeb
from layagamer.games.tictactoe.agents.finetuned import FinetunedAgent
from layagamer.games.snake.agent import SnakeLayaAgent
from layagamer.games.snake.web import SnakeWeb
from layagamer.games.minesweeper.agent import MinesweeperLayaAgent
from layagamer.games.minesweeper.web import MinesweeperWeb
from layagamer.games.chess.agent import ChessLayaAgent
from layagamer.games.chess.web import ChessWeb
from layagamer.agents.runtime import SharedRouter

LOGGER = logging.getLogger(__name__)
ASSETS = Path(__file__).with_name("static")


def make_handler(player: LayaPlayer, finetuned: FinetunedAgent | None = None) -> type[BaseHTTPRequestHandler]:
    inference_lock = Lock()
    games = {
        "tictactoe": TicTacToeWeb(player, finetuned),
        "snake": SnakeWeb(SnakeLayaAgent(device=player.device, router=player.router)),
        "minesweeper": MinesweeperWeb(MinesweeperLayaAgent(device=player.device, router=player.router)),
        "chess": ChessWeb(ChessLayaAgent(device=player.device, router=player.router)),
    }

    class Handler(BaseHTTPRequestHandler):
        def send_payload(self, status: int, payload: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def send_json(self, status: int, payload: dict) -> None:
            self.send_payload(status, json.dumps(
                payload).encode(), "application/json")

        def do_GET(self) -> None:
            if self.path == "/api/games":
                self.send_json(200, {"games": [game.describe() for game in games.values()]})
                return
            if self.path == "/api/agents":
                self.send_json(200, {"finetuned_available": finetuned is not None})
                return
            assets = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/api.js": ("api.js", "text/javascript; charset=utf-8"),
                      "/inspector.js": ("inspector.js", "text/javascript; charset=utf-8"),
                      "/games/tictactoe.js": ("games/tictactoe.js", "text/javascript; charset=utf-8"),
                      "/games/snake.js": ("games/snake.js", "text/javascript; charset=utf-8"),
                      "/games/minesweeper.js": ("games/minesweeper.js", "text/javascript; charset=utf-8"),
                      "/games/chess.js": ("games/chess.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8")}
            asset = assets.get(self.path)
            if asset is None:
                self.send_json(404, {"error": "Not found"})
                return
            name, mime = asset
            self.send_payload(200, (ASSETS / name).read_bytes(), mime)

        def do_POST(self) -> None:
            parts = self.path.strip("/").split("/")
            legacy = self.path == "/api/decision"
            decision_route = len(parts) == 4 and parts[:2] == ["api", "games"] and parts[3] == "decision"
            state_route = len(parts) == 4 and parts[:2] == ["api", "games"] and parts[3] == "state"
            game_id = "tictactoe" if legacy else parts[2] if decision_route or state_route else None
            game = games.get(game_id)
            if game is None:
                self.send_json(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("Invalid request size")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Expected an object")
                if state_route:
                    if not hasattr(game, "state"): raise ValueError("Game has no state endpoint")
                    response = game.state(payload)
                else:
                    prepared = game.prepare(payload)
            except (ValueError, TypeError):
                self.send_json(400, {"error": "Invalid board or request"})
                return
            try:
                if state_route:
                    self.send_json(200, response)
                else:
                    with inference_lock:
                        decision = game.decide(prepared)
                    self.send_json(200, decision)
            except Exception:
                LOGGER.exception("Laya inference failed")
                self.send_json(
                    500, {"error": "Laya inference failed. See the server terminal for details."})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Laya game dashboard")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", help="cpu, mps, or cuda")
    parser.add_argument("--checkpoint", type=Path, default=Path("artifacts/tictactoe/checkpoint"),
                        help="Fine-tuned checkpoint directory (loaded on first use)")
    args = parser.parse_args()
    finetuned = None
    if (args.checkpoint / "model.safetensors").is_file():
        finetuned = FinetunedAgent(str(args.checkpoint.resolve()), device=args.device)
    shared_router = SharedRouter(args.device)
    server = ThreadingHTTPServer(("127.0.0.1", args.port),
                                 make_handler(LayaPlayer(device=args.device, router=shared_router), finetuned))
    print(
        f"Open http://127.0.0.1:{server.server_port} — Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
