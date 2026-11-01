// Run with: node --test sw.test.js
// Checks the service worker without a browser: every pre-cached file exists, and the handlers use the cache correctly.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, 'sw.js'), 'utf8');

function load() {
  const handlers = {};
  const store = new Map();            // cache name -> Map(url -> response)
  const added = [];
  const self = { addEventListener: (t, fn) => { handlers[t] = fn; }, skipWaiting: () => Promise.resolve(), clients: { claim: () => Promise.resolve() } };
  const caches = {
    open: async name => { if (!store.has(name)) store.set(name, new Map()); const m = store.get(name); return { addAll: async urls => urls.forEach(u => { added.push(u); m.set(u, 'cached:' + u); }) }; },
    keys: async () => [...store.keys()],
    delete: async name => store.delete(name),
    match: async req => { for (const m of store.values()) if (m.has(req.url)) return m.get(req.url); return undefined; },
  };
  vm.runInNewContext(source, { self, caches, fetch: async () => { throw new Error('offline'); }, Promise });
  return { handlers, store, added, caches };
}

test('every pre-cached file exists next to sw.js', () => {
  const files = vm.runInNewContext(source.match(/const FILES = (\[.*?\]);/s)[1]);
  for (const f of files) {
    if (f === './') continue;
    assert.ok(fs.existsSync(path.join(__dirname, f)), `${f} is listed in the service worker but missing, which would make installation fail`);
  }
});

test('install caches the app shell, activate removes old caches', async () => {
  const sw = load();
  let waited; sw.handlers.install({ waitUntil: p => { waited = p; } });
  await waited;
  assert.ok(sw.added.includes('game.js') && sw.added.includes('index.html'));
  sw.store.set('gem-run-v0', new Map());
  sw.handlers.activate({ waitUntil: p => { waited = p; } });
  await waited;
  assert.deepEqual([...sw.store.keys()], ['gem-run-v1'], 'the old cache version is deleted');
});

test('fetch is served from the cache, and only GET requests are handled', async () => {
  const sw = load();
  let waited; sw.handlers.install({ waitUntil: p => { waited = p; } });
  await waited;
  const respond = req => new Promise(res => sw.handlers.fetch({ request: req, respondWith: p => res(p) }));
  assert.equal(await (await respond({ method: 'GET', url: 'game.js' })), 'cached:game.js');
  let handled = false; sw.handlers.fetch({ request: { method: 'POST', url: 'x' }, respondWith: () => { handled = true; } });
  assert.equal(handled, false, 'non-GET requests are not intercepted');
});
