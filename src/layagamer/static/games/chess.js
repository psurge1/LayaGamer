const svgNamespace='http://www.w3.org/2000/svg';
const pieceShapes={
  p:'<circle cx="22.5" cy="11.5" r="5.2"/><path d="M18 18h9c0 5 2 8 5 11l2 7H11l2-7c3-3 5-6 5-11z"/><path class="piece-detail" d="M14 29h17M12 36h21"/>',
  r:'<path d="M11 7h6v5h4V7h4v5h4V7h6v10l-4 4v11l4 5H10l4-5V21l-3-4z"/><path class="piece-detail" d="M14 18h17M14 31h17"/>',
  n:'<path d="M11 37h26c-1-6-4-11-9-14 3-5 3-10 0-16-8 1-13 5-16 12l-5 7 8-2c2 5 0 9-4 13z"/><circle class="piece-eye" cx="22" cy="14" r="1.5"/>',
  b:'<path d="M22.5 6c6 5 8 10 4 15 4 3 6 7 6 11l3 5h-26l3-5c0-4 2-8 6-11-4-5-2-10 4-15z"/><path class="piece-detail" d="M25.5 10 20 18M13 31h19"/>',
  q:'<circle cx="9" cy="10" r="2.4"/><circle cx="18" cy="7" r="2.4"/><circle cx="27" cy="7" r="2.4"/><circle cx="36" cy="10" r="2.4"/><path d="m10 14 6 12 2-15 5 14 4-14 2 15 6-12-3 18 3 5H10l3-5-3-18z"/><path class="piece-detail" d="M13 31h19"/>',
  k:'<path class="piece-detail cross" d="M22.5 4v10M18.5 8h8"/><path d="M22.5 13c4 0 7 3 7 7 0 2-1 4-3 6 4 1 6 4 6 7l3 4h-26l3-4c0-3 2-6 6-7-2-2-3-4-3-6 0-4 3-7 7-7z"/><path class="piece-detail" d="M13 32h19"/>'
};
function createPiece(piece){
  const svg=document.createElementNS(svgNamespace,'svg');
  svg.setAttribute('viewBox','0 0 45 45');svg.setAttribute('aria-hidden','true');
  svg.classList.add('chess-piece',piece.color);svg.innerHTML=pieceShapes[piece.symbol.toLowerCase()];
  return svg;
}
export function mount(root,{config,inspector}){
  root.dataset.game='chess';root.innerHTML=`<div class="section-head"><h2>The board</h2><span id="chess-turn" class="tag"></span></div>
    <div class="controls"><label>You play <select id="chess-color"><option value="white">White — first</option><option value="black">Black — second</option></select></label><button id="chess-new">New game</button></div>
    <p id="chess-status" role="status" aria-live="polite"></p><div id="chess-board" class="chess-board" aria-label="Chess board"></div>
    <p class="footnote">Rules, legal moves, checks, castling, promotion, and outcomes are provided by python-chess. Click a piece, then its destination.</p>`;
  const $=id=>root.querySelector(`#${id}`);let position,human='white',selectedSquare,busy,pending,records=[],selected=-1,generation=0;
  function orderedSquares(){const ranks=human==='white'?[8,7,6,5,4,3,2,1]:[1,2,3,4,5,6,7,8],files=human==='white'?'abcdefgh':'hgfedcba';return ranks.flatMap(r=>[...files].map(f=>`${f}${r}`));}
  function status(){if(!position)return 'Loading position…';if(position.finished)return position.outcome.winner?`${position.outcome.winner} wins by ${position.outcome.termination}.`:`Draw by ${position.outcome.termination}.`;return busy?'Laya is choosing…':position.turn===human?(position.check?'Your king is in check.':'Your move.'):`Laya to move${position.check?' in check':''}.`;}
  function render(){if(!position)return;const pieces=new Map(position.pieces.map(p=>[p.square,p]));$('chess-board').replaceChildren();for(const square of orderedSquares()){
    const button=document.createElement('button'),piece=pieces.get(square),legalFrom=position.legal_moves.some(move=>move.startsWith(square));
    button.className=`chess-square ${((square.charCodeAt(0)-97)+Number(square[1]))%2?'dark':'light'}`+(selectedSquare===square?' selected-square':'');
    if(piece)button.append(createPiece(piece));
    button.setAttribute('aria-label',`${square}${piece?' '+piece.color+' '+piece.symbol:''}`);
    button.disabled=busy||position.finished||position.turn!==human||(!selectedSquare&&!legalFrom);button.onclick=()=>clickSquare(square);$('chess-board').append(button);}
    $('chess-turn').textContent=position.finished?'GAME OVER':`${position.turn.toUpperCase()} TO MOVE`;$('chess-status').textContent=status();}
  async function getState(move){const current=generation;pending=new AbortController();const response=await fetch(`/api/games/${config.id}/state`,{method:'POST',signal:pending.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({fen:position?.fen,move})});const data=await response.json();if(current!==generation)return null;if(!response.ok)throw new Error(data.error||'Position update failed');return data;}
  async function clickSquare(square){if(!selectedSquare){selectedSquare=square;render();return;}const matches=position.legal_moves.filter(move=>move.startsWith(selectedSquare+square));if(!matches.length){selectedSquare=null;render();return;}const move=matches.find(m=>m.endsWith('q'))||matches[0];selectedSquare=null;try{position=await getState(move);render();if(position&&!position.finished)layaMove();}catch(error){$('chess-status').textContent=error.message;}}
  async function layaMove(){const current=generation;busy=true;pending=new AbortController();render();try{const before=position;const response=await fetch(`/api/games/${config.id}/decision`,{method:'POST',signal:pending.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({fen:position.fen,agent:'tactical'})});const decision=await response.json();if(current!==generation)return;if(!response.ok)throw new Error(decision.error||'Decision failed');records.push(decision);selected=records.length-1;position=decision.position;busy=false;render();renderAnalysis();}catch(error){if(current!==generation)return;busy=false;render();$('chess-status').textContent=error.message;}}
  function present(record,index){const offered=record.questions.move.criteria,probs=record.selection?.probabilities||record.result.answers.move.probabilities,facts=record.state.action_consequences;return{label:`Move ${index+1} · ${facts[record.move].san}`,latencyMs:record.latency_ms,snapshot:record.state.board.join('\n'),note:`Chess tactical harness · ${record.state.action_constraint.replaceAll('_',' ')}.`,choices:record.legal_moves.map(move=>({label:facts[move]?.san||move,offered:move in offered,selected:move===record.move,probability:probs[move],description:offered[move]||'Filtered because checkmate is available.'})),raw:record};}
  function renderAnalysis(){inspector.render(records.map(present),selected,index=>{selected=index;renderAnalysis();});}
  async function newGame(){generation++;pending?.abort();human=$('chess-color').value;selectedSquare=null;busy=false;records=[];selected=-1;position=null;root.querySelector('#chess-board').replaceChildren();$('chess-status').textContent='Loading position…';renderAnalysis();try{position=await getState();render();if(position.turn!==human)layaMove();}catch(error){$('chess-status').textContent=error.message;}}
  $('chess-new').onclick=newGame;$('chess-color').onchange=newGame;newGame();
  return()=>{generation++;pending?.abort();root.replaceChildren();delete root.dataset.game;};
}
