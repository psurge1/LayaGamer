export function mount(root, {config, inspector}) {
  root.dataset.game = 'snake';
  root.innerHTML = `<div class="section-head"><h2>The arena</h2><span id="snake-score" class="tag">SCORE 0</span></div>
    <div class="controls"><button id="snake-step">Step</button><button id="snake-auto">Auto play</button><button id="snake-new">New game</button></div>
    <p id="snake-status" role="status" aria-live="polite">Ready for Laya's first move.</p>
    <div id="snake-board" class="snake-board" aria-label="Snake board"></div>
    <p class="footnote">Laya chooses left, straight, or right from route, food-bearing, and escape-space context. Fatal moves are filtered when a safe move exists.</p>`;
  const $ = id => root.querySelector(`#${id}`);
  const width = 10, height = 10;
  let snake, direction, food, score, alive, busy, auto, timer, pending, records, selected, lastLatency, generation = 0, seed = 1;
  const vectors = {up:[0,-1],right:[1,0],down:[0,1],left:[-1,0]};
  const turns = {up:{left:'left',straight:'up',right:'right'},right:{left:'up',straight:'right',right:'down'},down:{left:'right',straight:'down',right:'left'},left:{left:'down',straight:'left',right:'up'}};
  const key = ([x,y]) => `${x},${y}`;
  function random() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
  function spawnFood() {
    const occupied = new Set(snake.map(key));
    const free = Array.from({length:width*height},(_,i)=>[i%width,Math.floor(i/width)]).filter(p=>!occupied.has(key(p)));
    return free[Math.floor(random()*free.length)];
  }
  function render() {
    const occupied = new Map(snake.map((p,i)=>[key(p),i]));
    $('snake-board').style.setProperty('--columns', width); $('snake-board').replaceChildren();
    for (let y=0;y<height;y++) for (let x=0;x<width;x++) {
      const cell=document.createElement('span'), index=occupied.get(`${x},${y}`);
      cell.className='snake-cell'+(index===0?' head':index!==undefined?' body':food[0]===x&&food[1]===y?' food':'');
      $('snake-board').append(cell);
    }
    $('snake-score').textContent=`SCORE ${score}`;
    $('snake-step').disabled=busy||!alive; $('snake-auto').disabled=!alive;
    $('snake-auto').textContent=auto?'Pause':'Auto play';
    const timing=lastLatency==null?'':` Last inference: ${Math.round(lastLatency)} ms.`;
    $('snake-status').textContent=!alive?`Game over. Final score: ${score}.`:busy?'Laya is choosing…':auto?`Auto play is running.${timing}`:`Ready for Laya's next move.${timing}`;
  }
  function apply(action) {
    direction=turns[direction][action]; const [dx,dy]=vectors[direction];
    const head=[snake[0][0]+dx,snake[0][1]+dy], grows=head[0]===food[0]&&head[1]===food[1];
    const occupied=new Set((grows?snake:snake.slice(0,-1)).map(key));
    if(head[0]<0||head[0]>=width||head[1]<0||head[1]>=height||occupied.has(key(head))){alive=false;auto=false;return;}
    snake=[head,...(grows?snake:snake.slice(0,-1))]; if(grows){score++;food=spawnFood();}
  }
  async function step() {
    if(busy||!alive)return; const current=generation; busy=true;pending=new AbortController();render();
    try {
      const response=await fetch(`/api/games/${config.id}/decision`,{method:'POST',signal:pending.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({agent:'tactical',width,height,snake,direction,food,score})});
      const decision=await response.json(); if(current!==generation)return;
      if(!response.ok)throw new Error(decision.error||'Decision failed');
      records.push(decision);selected=records.length-1;lastLatency=decision.latency_ms;apply(decision.move);busy=false;render();renderAnalysis();
      if(auto&&alive)timer=setTimeout(step,60);
    } catch(error){if(current!==generation)return;busy=false;auto=false;render();$('snake-status').textContent=error.message;}
  }
  function present(record,index){const offered=record.action_criteria,probs=record.selection.probabilities;
    return {label:`Step ${index+1} · ${record.move}`,latencyMs:record.latency_ms,
      snapshot:`Head ${record.state.snake[0].join(',')} · facing ${record.state.direction}\nFood ${record.state.food.join(',')} · score ${record.state.score}`,
      note:`Snake tactical harness · ${record.state.action_constraint.replaceAll('_',' ')}.`,
      choices:record.legal_moves.map(move=>({label:move,offered:move in offered,selected:move===record.move,probability:probs[move],description:offered[move]||'Filtered because this move dies immediately.'})),raw:record};}
  function renderAnalysis(){inspector.render(records.map(present),selected,index=>{selected=index;renderAnalysis();});}
  function newGame(){generation++;pending?.abort();clearTimeout(timer);seed++;snake=[[4,5],[3,5],[2,5]];direction='right';score=0;alive=true;busy=false;auto=false;food=[7,5];records=[];selected=-1;lastLatency=null;render();renderAnalysis();}
  $('snake-step').onclick=step;$('snake-auto').onclick=()=>{auto=!auto;render();if(auto)step();};$('snake-new').onclick=newGame;newGame();
  return()=>{generation++;pending?.abort();clearTimeout(timer);root.replaceChildren();delete root.dataset.game;};
}
