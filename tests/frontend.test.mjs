import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createInspector} from '../src/layagamer/static/inspector.js';
import {requestJson} from '../src/layagamer/static/api.js';
import {mount, presentDecision} from '../src/layagamer/static/games/tictactoe.js';

class Element {
  constructor() { this.children = []; this.style = {}; this.dataset = {}; this.value = ''; }
  append(...children) { this.children.push(...children); if (!this.value) this.value = children[0]?.value || ''; }
  replaceChildren(...children) { this.children = children; }
  setAttribute() {}
}
function rootFor(ids) {
  const entries = Object.fromEntries(ids.map(id => [id, new Element()]));
  const root = new Element(); root.querySelector = selector => entries[selector.slice(1)];
  return {root, entries};
}
globalThis.document = {createElement: () => new Element()};

test('inspector accepts named actions without board or square assumptions', () => {
  const {root, entries} = rootFor(['history','chart','context','request-details','request','latency','snapshot','chart-note']);
  const inspector = createInspector(root);
  inspector.render([{label:'Step 12 · turn left', latencyMs:12, snapshot:'Snake heading north', note:'Directional actions',
    choices:[{label:'Turn left',offered:true,selected:true,probability:.75}, {label:'Reverse',offered:false,probability:1}], raw:{direction:'left'}}], 0);
  assert.equal(entries.chart.children.length, 2);
  assert.equal(entries.chart.children[0].children[0].textContent, 'Turn left');
  assert.equal(entries.chart.children[1].children[2].textContent, 'filtered');
  assert.equal(entries.chart.children[1].children[1].children[0].style.width, '0%');
  inspector.render();
  assert.equal(entries.chart.children.length, 0);
  assert.equal(entries.request.textContent, '');
});

test('tic-tac-toe preserves snapshots, probabilities and labels', () => {
  const view = presentDecision({move:'5',latency_ms:20,agent:'tactical',legal_moves:['2','5'],
    state:{you:'X',board:[['.','.','.'],['.','.','.'],['.','.','.']],action_constraint:'immediate_win'},
    questions:{move:{criteria:{'5':'Win now'}}},result:{answers:{move:{probabilities:{'5':1}}}}}, 0);
  assert.equal(view.choices[0].offered, false);
  assert.equal(view.choices[1].selected, true);
  assert.equal(view.choices[1].probability, 1);
  assert.match(view.snapshot, /X move/);
});

test('disposing a game aborts requests and ignores late decisions', async () => {
  const {root, entries} = rootFor(['agent','board','turn-badge','status','retry','agent-description','human-mark','new-game']);
  entries['human-mark'].value = 'X';
  let resolve, signal, renders = 0;
  globalThis.fetch = (url, options) => {
    assert.equal(url, '/api/games/tictactoe/decision');
    signal = options.signal;
    return new Promise(done => {resolve = done;});
  };
  const dispose = mount(root, {config:{id:'tictactoe',agents:[{id:'tactical',label:'Tactical'}]}, inspector:{render:() => renders++}});
  entries.board.children[0].onclick();
  dispose();
  assert.equal(signal.aborted, true);
  const before = renders;
  resolve({ok:true,json:async () => ({move:'5'})});
  await new Promise(done => setImmediate(done));
  assert.equal(renders, before);
  assert.equal(root.children.length, 0);
});

test('API paths respect a GitHub Pages project directory', async () => {
  const previousFetch = globalThis.fetch;
  document.baseURI = 'https://psurge1.github.io/LayaGamer/';
  let requested;
  globalThis.fetch = async url => {
    requested = url;
    return {ok:true, json:async () => ({games:[]})};
  };
  try {
    await requestJson('api/games');
    assert.equal(requested, '/LayaGamer/api/games');
  } finally {
    delete document.baseURI;
    globalThis.fetch = previousFetch;
  }
});
