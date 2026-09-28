import {createInspector} from './inspector.js';
import {mount as mountTicTacToe} from './games/tictactoe.js';
import {mount as mountSnake} from './games/snake.js';
import {mount as mountMinesweeper} from './games/minesweeper.js';
import {mount as mountChess} from './games/chess.js';

// Add implemented games here; no plugin framework or placeholder modes.
const gameViews = {tictactoe: mountTicTacToe, snake: mountSnake,
  minesweeper: mountMinesweeper, chess: mountChess};
const selector = document.getElementById('game-select');
const root = document.getElementById('game-root');
const inspector = createInspector(document.getElementById('analysis'));
let dispose = () => {};

async function initialize() {
  try {
    const response = await fetch('/api/games');
    if (!response.ok) throw new Error('Could not load games. Restart the server and refresh.');
    const {games} = await response.json();
    const available = games.filter(game => gameViews[game.id]);
    if (!available.length) throw new Error('No playable games are configured.');
    available.forEach(game => {
      const option = document.createElement('option'); option.value = game.id; option.textContent = game.label;
      selector.append(option);
    });
    function selectGame() {
      dispose(); inspector.render();
      const config = available.find(game => game.id === selector.value);
      document.title = `Laya • ${config.label}`;
      document.getElementById('game-label').textContent = `GAME LAB / ${config.label.toUpperCase()}`;
      dispose = gameViews[config.id](root, {config, inspector});
    }
    selector.disabled = false; selector.onchange = selectGame; selectGame();
  } catch (error) { root.textContent = error.message; }
}
initialize();
