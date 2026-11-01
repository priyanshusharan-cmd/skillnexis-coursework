// Run with: node test.js
const assert = require('assert');
const { createStore } = require('./store');
const mem = () => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, raw: m }; };

const s1 = mem();
const a = createStore(s1);
const t1 = a.add('  buy milk  ');
const t2 = a.add('write report');
assert.strictEqual(a.add('   '), null, 'blank tasks are rejected');
assert.strictEqual(t1.text, 'buy milk');
assert.notStrictEqual(t1.id, t2.id);
assert.strictEqual(a.remaining(), 2);
a.toggle(t1.id);
assert.deepStrictEqual(a.filter('done').map(t => t.text), ['buy milk']);
assert.deepStrictEqual(a.filter('active').map(t => t.text), ['write report']);
assert.strictEqual(a.all().length, 2);

const b = createStore(s1);
assert.strictEqual(b.all().length, 2, 'tasks persist through storage');
assert.strictEqual(b.all()[0].done, true);
b.clearDone();
assert.deepStrictEqual(b.all().map(t => t.text), ['write report']);
assert.strictEqual(b.remove('nope'), false);
assert.strictEqual(b.remove(t2.id), true);

const bad = mem();
bad.setItem('todo-tasks', '{not json');
assert.deepStrictEqual(createStore(bad).all(), [], 'corrupt storage is ignored');
const odd = mem();
odd.setItem('todo-tasks', JSON.stringify([{ id: 'x', text: 'ok' }, { nope: 1 }, null]));
assert.strictEqual(createStore(odd).all().length, 1, 'malformed entries are dropped');
console.log('all store tests passed');
