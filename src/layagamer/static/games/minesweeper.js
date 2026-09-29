import {requestJson} from '../api.js';

export function mount(root,{config,inspector}) {
  root.dataset.game='minesweeper';
  root.innerHTML=`<div class="section-head"><h2>The minefield</h2><span id="mine-count" class="tag"></span></div>
    <div class="controls"><button id="mine-step">Step</button><button id="mine-auto">Auto play</button><button id="mine-new">New game</button></div>
    <p id="mine-status" role="status" aria-live="polite"></p><div id="mine-board" class="mine-board" aria-label="Minesweeper board"></div>
    <p class="footnote">Laya sees the same numbered grid as a player. Mine locations are held by the game engine and omitted from its observation.</p>`;
  const $=id=>root.querySelector(`#${id}`),width=8,height=8,mineTotal=10;
  let mines,revealed,flagged,exploded,busy,auto,timer,pending,records,selected,generation=0,seed=7;
  const key=([x,y])=>`${x},${y}`,point=s=>s.split(',').map(Number);
  function random(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}
  function neighbors([x,y]){const out=[];for(let ny=Math.max(0,y-1);ny<=Math.min(height-1,y+1);ny++)for(let nx=Math.max(0,x-1);nx<=Math.min(width-1,x+1);nx++)if(nx!==x||ny!==y)out.push([nx,ny]);return out;}
  function number(p){return neighbors(p).filter(n=>mines.has(key(n))).length;}
  function won(){return !exploded&&revealed.size===width*height-mines.size;}
  function finished(){return !!exploded||won();}
  function reveal(start){const stack=[start];while(stack.length){const p=stack.pop(),k=key(p);if(revealed.has(k)||flagged.has(k))continue;if(mines.has(k)){exploded=k;return;}revealed.add(k);if(number(p)===0)stack.push(...neighbors(p));}}
  function apply(action){const [kind,raw]=action.split(':'),p=point(raw),k=key(p);if(kind==='flag'){if(flagged.has(k))flagged.delete(k);else flagged.add(k);}else reveal(p);}
  function render(){const board=$('mine-board');board.style.setProperty('--columns',width);board.replaceChildren();for(let y=0;y<height;y++)for(let x=0;x<width;x++){
    const k=`${x},${y}`,cell=document.createElement('span');cell.className='mine-cell';
    if(exploded&&mines.has(k)){cell.classList.add('mine');cell.textContent='✦';}else if(flagged.has(k)){cell.classList.add('flag');cell.textContent='⚑';}else if(revealed.has(k)){const n=number([x,y]);cell.classList.add('revealed',`n${n}`);cell.textContent=n||'';}else cell.classList.add('hidden');board.append(cell);}
    $('mine-count').textContent=`${flagged.size}/${mineTotal} FLAGS`;$('mine-step').disabled=busy||finished();$('mine-auto').disabled=finished();$('mine-auto').textContent=auto?'Pause':'Auto play';
    $('mine-status').textContent=exploded?'Mine revealed. Game over.':won()?'Minefield cleared.':busy?'Laya is choosing…':auto?'Auto play is running.':"Ready for Laya's next action.";}
  async function step(){if(busy||finished())return;const current=generation;busy=true;pending=new AbortController();render();try{
    const {response,data:decision}=await requestJson(`api/games/${config.id}/decision`,{method:'POST',signal:pending.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({agent:'tactical',width,height,mines:[...mines].map(point),revealed:[...revealed].map(point),flagged:[...flagged].map(point)})});
    if(current!==generation)return;if(!response.ok)throw new Error(decision.error||'Decision failed');records.push(decision);selected=records.length-1;apply(decision.move);busy=false;if(finished())auto=false;render();renderAnalysis();if(auto)timer=setTimeout(step,500);
  }catch(error){if(current!==generation)return;busy=false;auto=false;render();$('mine-status').textContent=error.message;}}
  function present(record,index){const offered=record.questions.move.criteria,probs=record.selection?.probabilities||record.result.answers.move.probabilities;
    return{label:`Action ${index+1}`,latencyMs:record.latency_ms,snapshot:record.state.board.map(row=>row.join(' ')).join('\n'),note:`Minesweeper harness · ${record.state.action_constraint.replaceAll('_',' ')}.`,choices:record.legal_moves.map(move=>({label:move.replace(':',' '),offered:true,selected:move===record.move,probability:probs[move],description:offered[move]})),raw:record};}
  function renderAnalysis(){inspector.render(records.map(present),selected,index=>{selected=index;renderAnalysis();});}
  function newGame(){generation++;pending?.abort();clearTimeout(timer);seed++;mines=new Set();while(mines.size<mineTotal)mines.add(`${Math.floor(random()*width)},${Math.floor(random()*height)}`);revealed=new Set();flagged=new Set();exploded=null;busy=false;auto=false;records=[];selected=-1;render();renderAnalysis();}
  $('mine-step').onclick=step;$('mine-auto').onclick=()=>{auto=!auto;render();if(auto)step();};$('mine-new').onclick=newGame;newGame();
  return()=>{generation++;pending?.abort();clearTimeout(timer);root.replaceChildren();delete root.dataset.game;};
}
