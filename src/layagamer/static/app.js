const $ = id => document.getElementById(id);
const lines = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
let cells, turn, human, busy, records, selected, generation = 0;
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
  busy = true; $('retry').hidden = true; renderBoard();
  try {
    const response = await fetch('/api/decision', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({cells,turn,agent:$('agent').value})});
    const decision = await response.json();
    if (current !== generation) return;
    if (!response.ok) throw new Error(decision.error || 'Request failed');
    const index = Number(decision.move)-1;
    if (!Number.isInteger(index) || index < 0 || index > 8 || cells[index] !== '.') throw new Error('Server returned an invalid action.');
    records.push(decision); selected = records.length-1;
    cells[index] = turn; turn = turn === 'X' ? 'O' : 'X';
    busy = false; renderBoard(); renderAnalysis();
  } catch (error) {
    if (current !== generation) return;
    busy = false; renderBoard(); $('status').textContent = error.message; $('retry').hidden = false;
  }
}
function renderAnalysis() {
  $('history').replaceChildren(); $('chart').replaceChildren(); $('context').replaceChildren();
  records.forEach((record,i) => {
    const button = document.createElement('button'); button.textContent = `Turn ${i+1} · square ${record.move}`;
    button.className = selected === i ? 'active' : ''; button.onclick = () => {selected = i; renderAnalysis();};
    $('history').append(button);
  });
  const record = records[selected];
  $('request-details').hidden = !record;
  if (!record) { $('latency').textContent = 'AWAITING MOVE'; $('snapshot').textContent = ''; $('chart-note').textContent = "Laya's first decision will appear here."; return; }
  $('latency').textContent = `${record.latency_ms.toFixed(0)} MS`;
  $('snapshot').textContent = `Board before Laya's ${record.state.you} move\n` + record.state.board.map(row => row.join('  ')).join('\n');
  const probabilities = record.selection?.probabilities || record.result.answers.move.probabilities || {};
  const offered = record.questions.move.criteria;
  const legalMoves = record.legal_moves || record.state.legal_moves || Object.keys(offered);
  const filtered = legalMoves.filter(move => !(move in offered));
  const constraint = record.state.action_constraint || (filtered.length ? 'immediate_win' : 'none');
  const notes = {immediate_win:'Immediate-win constraint: only winning actions were offered.', block_opponent_win:'Blocking constraint: only actions preventing an immediate opponent win were offered.', partial_block:'Multiple winning threats: no complete block exists. Only partial blocks were offered.', none:'All legal actions were offered. Highlight = selected move.'};
  $('chart-note').textContent = (record.agent === 'tictactoe-finetuned' ? 'Fine-tuned Laya · probabilities are uncalibrated. ' : 'Tactical Laya · ') + notes[constraint];
  if (record.selection?.method === 'sample') {
    $('chart-note').textContent += ` Sampling at temperature ${record.selection.temperature}. Bars show sampling probabilities; model's top choice: ${record.selection.model_choice}. Original probabilities are in the full response.`;
  }
  legalMoves.forEach(move => {
    const isOffered = move in offered, probability = probabilities[move];
    const row = document.createElement('div'); row.className = 'bar-row' + (move === record.move ? ' selected' : '') + (!isOffered ? ' excluded' : '');
    const label = document.createElement('span'); label.textContent = `Square ${move}`;
    const track = document.createElement('div'); track.className = 'track';
    const bar = document.createElement('div'); bar.className = 'bar'; bar.style.width = `${Number.isFinite(probability) ? Math.max(0,Math.min(1,probability))*100 : 0}%`; track.append(bar);
    const value = document.createElement('span'); value.className = 'percentage'; value.textContent = !isOffered ? 'filtered' : Number.isFinite(probability) ? `${(probability*100).toFixed(1)}%` : 'n/a';
    row.append(label,track,value); $('chart').append(row);
    const detail = document.createElement('div'); detail.className = 'context-item';
    const title = document.createElement('strong'); title.textContent = `Square ${move}${move === record.move ? ' · selected' : ''}${!isOffered ? ' · filtered by harness' : ''}`;
    const text = document.createElement('p'); text.textContent = offered[move] || (constraint === 'immediate_win' ? 'Immediate win available elsewhere; this legal action was excluded.' : 'Excluded by blocking priority: this action does not block the required opponent threat.');
    detail.append(title,text); $('context').append(detail);
  });
  $('request').textContent = JSON.stringify(record,null,2);
}
function newGame() {
  $('agent-description').textContent = $('agent').value === 'finetuned' ? 'Fine-tuned checkpoint · all legal moves offered. No tactical constraints.' : 'Tactical agent · English checkpoint. Priority: win → block → other moves.';
  generation++; cells = Array(9).fill('.'); turn = 'X'; human = $('human-mark').value;
  busy = false; records = []; selected = -1; $('retry').hidden = true;
  renderBoard(); renderAnalysis(); if (human === 'O') layaTurn();
}
$('new-game').onclick = newGame; $('human-mark').onchange = newGame; $('agent').onchange = newGame; $('retry').onclick = layaTurn;
async function initialize() {
  try {
    const response = await fetch('/api/agents');
    if (!response.ok) throw new Error('Could not load agent configuration.');
    const config = await response.json();
    if (!config.finetuned_available) {
      $('agent').querySelector('option[value="finetuned"]').disabled = true;
      $('agent').value = 'tactical';
    }
    newGame();
  } catch (error) { $('status').textContent = error.message + ' Restart the server and refresh.'; }
}
initialize();
