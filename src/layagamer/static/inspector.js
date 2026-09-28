// Receives presentation data; game state and action encoding stay in each game.
export function createInspector(root) {
  const $ = id => root.querySelector(`#${id}`);
  function render(records = [], selected = -1, onSelect = () => {}) {
    $('history').replaceChildren(); $('chart').replaceChildren(); $('context').replaceChildren();
    records.forEach((record, index) => {
      const button = document.createElement('button'); button.textContent = record.label;
      button.className = selected === index ? 'active' : ''; button.onclick = () => onSelect(index);
      $('history').append(button);
    });
    const record = records[selected];
    $('request-details').hidden = !record;
    $('request').textContent = record ? JSON.stringify(record.raw, null, 2) : '';
    $('latency').textContent = record ? `${record.latencyMs.toFixed(0)} MS` : 'AWAITING MOVE';
    $('snapshot').textContent = record?.snapshot || '';
    $('chart-note').textContent = record?.note || "Laya's first decision will appear here.";
    if (!record) return;
    record.choices.forEach(choice => {
      const row = document.createElement('div'); row.className = 'bar-row' + (choice.selected ? ' selected' : '') + (!choice.offered ? ' excluded' : '');
      const label = document.createElement('span'); label.textContent = choice.label;
      const track = document.createElement('div'); track.className = 'track';
      const bar = document.createElement('div'); bar.className = 'bar';
      bar.style.width = `${choice.offered && Number.isFinite(choice.probability) ? Math.max(0, Math.min(1, choice.probability)) * 100 : 0}%`; track.append(bar);
      const value = document.createElement('span'); value.className = 'percentage';
      value.textContent = !choice.offered ? 'filtered' : Number.isFinite(choice.probability) ? `${(choice.probability * 100).toFixed(1)}%` : 'n/a';
      row.append(label, track, value); $('chart').append(row);
      const detail = document.createElement('div'); detail.className = 'context-item';
      const title = document.createElement('strong'); title.textContent = choice.label + (choice.selected ? ' · selected' : '') + (!choice.offered ? ' · filtered by harness' : '');
      const text = document.createElement('p'); text.textContent = choice.description || '';
      detail.append(title, text); $('context').append(detail);
    });
  }
  return {render};
}
