// Regression tests for DEF-2: sessions never expired, so every login grew server memory.
// Run: node --test regression/
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const path = require('node:path');

const PORT = 4390;
const BASE = `http://127.0.0.1:${PORT}`;
let server;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const login = () => fetch(`${BASE}/api/login`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ username: 'standard_user', password: 'demo-pass-123' }) }).then(r => r.json());
const health = () => fetch(`${BASE}/api/health`).then(r => r.json());

before(async () => {
  server = spawn(process.execPath, [path.join(__dirname, '../../week-3/demo-shop/server.js')], {
    env: { ...process.env, PORT: String(PORT), SESSION_TTL_MS: '400', MAX_SESSIONS: '50' }, stdio: 'ignore',
  });
  for (let i = 0; i < 50; i++) { try { await health(); return; } catch { await sleep(100); } }
  throw new Error('server did not start');
});
after(() => server.kill());

test('an idle session expires and its token stops working', async () => {
  const { token } = await login();
  const ok = await fetch(`${BASE}/api/cart`, { headers: { authorization: `Bearer ${token}` } });
  assert.equal(ok.status, 200);
  await sleep(600);
  const expired = await fetch(`${BASE}/api/cart`, { headers: { authorization: `Bearer ${token}` } });
  assert.equal(expired.status, 401);
});

test('an active session is kept alive by use', async () => {
  const { token } = await login();
  for (let i = 0; i < 4; i++) {
    await sleep(200); // total 800 ms, longer than the 400 ms TTL, but never idle for 400 ms
    const r = await fetch(`${BASE}/api/cart`, { headers: { authorization: `Bearer ${token}` } });
    assert.equal(r.status, 200, `request ${i + 1}`);
  }
});

test('the session store never grows past MAX_SESSIONS', async () => {
  await Promise.all(Array.from({ length: 300 }, login));
  assert.ok((await health()).sessions <= 50);
});

test('the sweeper empties the store after everyone goes idle', async () => {
  await Promise.all(Array.from({ length: 30 }, login));
  await sleep(1000);
  assert.equal((await health()).sessions, 0);
});
