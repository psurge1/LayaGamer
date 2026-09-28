export function mount(root, {config, inspector}) {
root.innerHTML = `
<div class="section-head"><h2>The board</h2><span id="turn-badge" class="tag">X FIRST</span></div>
<div class="controls"><label>You play <select id="human-mark"><option value="X">X — first</option><option value="O">O — second</option></select></label><button id="new-game">New game</button></div>
<div class="controls"><label>Opponent <select id="agent"></select></label></div>
<p id="status" role="status" aria-live="polite"></p>
<div id="board" class="board" aria-label="Tic-tac-toe board"></div>
<button id="retry" hidden>Retry Laya's turn</button>
<div class="legend"><span><i class="human-dot"></i>You</span><span><i class="laya-dot"></i>Laya</span></div>
<p id="agent-description" class="footnote"></p>`;
root.dataset.game = 'tictactoe';
const $ = id => root.querySelector(`#${id}`);
config.agents.forEach(agent => {
  const option = document.createElement('option'); option.value = agent.id; option.textContent = agent.label;
  $('agent').append(option);
});
const lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
let cells, turn, human, busy, records, selected, generation = 0;
let disposed = false, pending = null;
function outcome() {
  const line = lines.find(([a,b,c]) => cells[a] !== '.' && cells[a] === cells[b] && cells[a] === cells[c]);
  return {line, winner: line ? cells[line[0]] : null, done: !!line || !cells.includes('.')};
}
function renderBoard() {
  const result = outcome();
  $('board').replaceChildren();
  cells.forEach((mark,i) => {
    const button = document.createElement('button');
    button.className = 'cell ' + (mark === '.' ? 'empty' : mark === human ? 'human' : 'laya') + (result.line?.includes(i) ? ' winner' : '');
    button.textContent = mark === '.' ? i + 1 : mark;
    button.setAttribute('aria-label', `Square ${i+1}, ${mark === '.' ? 'empty' : mark}`);
    button.disabled = busy || result.done || turn !== human || mark !== '.';
    button.onclick = () => { cells[i] = human; turn = human === 'X' ? 'O' : 'X'; renderBoard(); if (!outcome().done) layaTurn(); };
    $('board').append(button);
  });
  $('turn-badge').textContent = result.done ? 'GAME OVER' : busy ? 'INFERENCE' : `${turn} TO MOVE`;
  $('status').textContent = result.done ? (result.winner ? `${result.winner === human ? 'You win' : 'Laya wins'}!` : 'Draw. Start another game?') : busy ? 'Laya is deciding… First use may take longer to load the model.' : turn === human ? 'Your turn. Choose an empty square.' : "Laya's turn.";
}
async function layaTurn() {
  const current = generation;
  pending = new AbortController();
  busy = true; $('retry').hidden = true; renderBoard();
  try {
    const response = await fetch(`/api/games/${config.id}/decision`, {method:'POST', signal:pending.signal, headers:{'Content-Type':'application/json'}, body:JSON.stringify({cells,turn,agent:$('agent').value})});
    const decision = await response.json();
    if (disposed || current !== generation) return;
    if (!response.ok) throw new Error(decision.error || 'Request failed');
    const index = Number(decision.move)-1;
    if (!Number.isInteger(index) || index < 0 || index > 8 || cells[index] !== '.') throw new Error('Server returned an invalid action.');
    records.push(decision); selected = records.length-1;
    cells[index] = turn; turn = turn === 'X' ? 'O' : 'X';
    busy = false; renderBoard(); renderAnalysis();
  } catch (error) {
    if (disposed || current !== generation) return;
    busy = false; renderBoard(); $('status').textContent = error.message; $('retry').hidden = false;
  }
}
function renderAnalysis() {
  inspector.render(records.map(presentDecision), selected, index => {selected = index; renderAnalysis();});
}
function newGame() {
  $('agent-description').textContent = $('agent').value === 'finetuned' ? 'Fine-tuned checkpoint · all legal moves offered. No tactical constraints.' : 'Tactical agent · English checkpoint. Priority: win → block → other moves.';
  generation++; cells = Array(9).fill('.'); turn = 'X'; human = $('human-mark').value;
  pending?.abort();
  busy = false; records = []; selected = -1; $('retry').hidden = true;
  renderBoard(); renderAnalysis(); if (human === 'O') layaTurn();
}
$('new-game').onclick = newGame; $('human-mark').onchange = newGame; $('agent').onchange = newGame; $('retry').onclick = layaTurn;
newGame();
return () => { disposed = true; generation++; pending?.abort(); root.replaceChildren(); delete root.dataset.game; };
}

export function presentDecision(record, index) {
  const offered = record.questions.move.criteria;
  const probabilities = record.selection?.probabilities || record.result.answers.move.probabilities || {};
  const legalMoves = record.legal_moves || record.state.legal_moves || Object.keys(offered);
  const constraint = record.state.action_constraint || 'none';
  const notes = {immediate_win:'Immediate-win constraint: only winning actions were offered.', block_opponent_win:'Blocking constraint: only actions preventing an immediate opponent win were offered.', partial_block:'Multiple winning threats: no complete block exists. Only partial blocks were offered.', none:'All legal actions were offered. Highlight = selected move.'};
  let note = (record.agent === 'tictactoe-finetuned' ? 'Fine-tuned Laya · probabilities are uncalibrated. ' : 'Tactical Laya · ') + notes[constraint];
  if (record.selection?.method === 'sample') note += ` Sampling at temperature ${record.selection.temperature}. Bars show sampling probabilities; model's top choice: ${record.selection.model_choice}. Original probabilities are in the full response.`;
  return {
    label: `Turn ${index + 1} · square ${record.move}`,
    latencyMs: record.latency_ms,
    snapshot: `Board before Laya's ${record.state.you} move\n` + record.state.board.map(row => row.join('  ')).join('\n'),
    note,
    choices: legalMoves.map(move => ({label: `Square ${move}`, selected: move === record.move,
      offered: move in offered, probability: probabilities[move],
      description: offered[move] || (constraint === 'immediate_win' ? 'Immediate win available elsewhere; this legal action was excluded.' : 'Excluded by blocking priority: this action does not block the required opponent threat.')})),
    raw: record,
  };
}
