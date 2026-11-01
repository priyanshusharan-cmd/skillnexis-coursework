// Pure task logic, kept separate from the DOM so it can be tested in Node.
function createStore(storage, key = 'todo-tasks') {
  let tasks = [];
  try {
    const parsed = JSON.parse(storage.getItem(key) || '[]');
    if (Array.isArray(parsed)) tasks = parsed.filter(t => t && typeof t.id === 'string' && typeof t.text === 'string');
  } catch (e) { tasks = []; }

  const save = () => { try { storage.setItem(key, JSON.stringify(tasks)); } catch (e) { /* storage full or blocked */ } };
  let seq = Date.now();

  return {
    all: () => tasks.slice(),
    add(text) {
      const clean = String(text).trim();
      if (!clean) return null;
      const task = { id: 't' + (seq++).toString(36), text: clean, done: false };
      tasks.push(task);
      save();
      return task;
    },
    toggle(id) {
      const t = tasks.find(x => x.id === id);
      if (t) { t.done = !t.done; save(); }
      return !!t;
    },
    remove(id) {
      const before = tasks.length;
      tasks = tasks.filter(x => x.id !== id);
      save();
      return tasks.length !== before;
    },
    clearDone() { tasks = tasks.filter(t => !t.done); save(); },
    filter(mode) { return tasks.filter(t => mode === 'active' ? !t.done : mode === 'done' ? t.done : true); },
    remaining: () => tasks.filter(t => !t.done).length,
  };
}
if (typeof module !== 'undefined') module.exports = { createStore };
