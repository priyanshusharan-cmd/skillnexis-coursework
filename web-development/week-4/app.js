let storage;
try { storage = window.localStorage; storage.getItem('x'); } catch (e) {
  const mem = {};
  storage = { getItem: k => mem[k] || null, setItem: (k, v) => { mem[k] = v; } };
}
const store = createStore(storage);
let mode = 'all';

const list = document.getElementById('list');
const count = document.getElementById('count');

function render() {
  list.innerHTML = '';
  for (const t of store.filter(mode)) {
    const li = document.createElement('li');
    if (t.done) li.className = 'done';
    const box = document.createElement('input');
    box.type = 'checkbox';
    box.checked = t.done;
    box.setAttribute('aria-label', 'Mark "' + t.text + '" complete');
    box.addEventListener('change', () => { store.toggle(t.id); render(); });
    const label = document.createElement('span');
    label.textContent = t.text;
    const del = document.createElement('button');
    del.textContent = '×';
    del.setAttribute('aria-label', 'Delete "' + t.text + '"');
    del.addEventListener('click', () => { store.remove(t.id); render(); });
    li.append(box, label, del);
    list.appendChild(li);
  }
  const n = store.remaining();
  count.textContent = n + (n === 1 ? ' task left' : ' tasks left');
  document.querySelectorAll('.filters button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.filter === mode)));
}

document.getElementById('add').addEventListener('submit', e => {
  e.preventDefault();
  const input = document.getElementById('text');
  if (store.add(input.value)) { input.value = ''; render(); }
});
document.querySelector('.filters').addEventListener('click', e => {
  if (e.target.dataset.filter) { mode = e.target.dataset.filter; render(); }
});
document.getElementById('clear').addEventListener('click', () => { store.clearDone(); render(); });
render();
