const assert = require('node:assert/strict');
const { after, before, describe, it } = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const mongoose = require('mongoose');
const { createApp } = require('../src/app');

let server, base, uploadDir;
const call = async (method, path, { token, body } = {}) => {
  const res = await fetch(base + path, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  return { status: res.status, body: text ? JSON.parse(text) : null };
};

before(async () => {
  const uri = process.env.MONGO_URI || `mongodb://127.0.0.1:27017/sn_test_${Date.now()}`;
  await mongoose.connect(uri);
  uploadDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sn-uploads-'));
  server = createApp({ jwtSecret: 'test-secret-test-secret', uploadDir }).listen(0);
  base = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  await mongoose.connection.dropDatabase();
  await mongoose.disconnect();
  server.close();
});

describe('authentication', () => {
  it('registers, rejects bad input and duplicates, and logs in', async () => {
    assert.equal((await call('POST', '/api/auth/register', { body: { name: 'A', email: 'bad', password: 'longenough' } })).status, 400);
    assert.equal((await call('POST', '/api/auth/register', { body: { name: 'A', email: 'a@x.io', password: 'short' } })).status, 400);
    const ok = await call('POST', '/api/auth/register', { body: { name: 'Asha', email: 'Asha@X.io', password: 'correct horse' } });
    assert.equal(ok.status, 201);
    assert.ok(ok.body.token);
    assert.equal(ok.body.passwordHash, undefined);
    assert.equal(ok.body.user.passwordHash, undefined);
    assert.equal((await call('POST', '/api/auth/register', { body: { name: 'Asha', email: 'asha@x.io', password: 'correct horse' } })).status, 409);
    assert.equal((await call('POST', '/api/auth/login', { body: { email: 'asha@x.io', password: 'correct horse' } })).status, 200);
    const wrong = await call('POST', '/api/auth/login', { body: { email: 'asha@x.io', password: 'nope nope nope' } });
    const unknown = await call('POST', '/api/auth/login', { body: { email: 'ghost@x.io', password: 'nope nope nope' } });
    assert.equal(wrong.status, 401);
    assert.deepEqual(wrong.body, unknown.body);
  });

  it('stores a bcrypt hash, never the password', async () => {
    const User = mongoose.model('User');
    const u = await User.findOne({ email: 'asha@x.io' });
    assert.match(u.passwordHash, /^\$2[aby]\$/);
    assert.ok(!JSON.stringify(u).includes('correct horse'));
  });
});

describe('protected CRUD for tasks and notes', () => {
  let a, b;
  before(async () => {
    a = (await call('POST', '/api/auth/login', { body: { email: 'asha@x.io', password: 'correct horse' } })).body.token;
    b = (await call('POST', '/api/auth/register', { body: { name: 'Ravi', email: 'ravi@x.io', password: 'another pass' } })).body.token;
  });

  it('rejects missing or forged tokens', async () => {
    assert.equal((await call('GET', '/api/tasks')).status, 401);
    assert.equal((await call('GET', '/api/tasks', { token: 'abc.def.ghi' })).status, 401);
    assert.equal((await call('GET', '/api/notes')).status, 401);
  });

  it('runs the task lifecycle: add, update, list, delete', async () => {
    assert.equal((await call('POST', '/api/tasks', { token: a, body: { title: '   ' } })).status, 400);
    const created = await call('POST', '/api/tasks', { token: a, body: { title: 'Write tests', owner: 'hacker' } });
    assert.equal(created.status, 201);
    assert.equal(created.body.done, false);
    const id = created.body._id;
    const upd = await call('PUT', `/api/tasks/${id}`, { token: a, body: { done: true } });
    assert.equal(upd.body.done, true);
    assert.equal(upd.body.title, 'Write tests');
    assert.equal((await call('GET', '/api/tasks', { token: a })).body.length, 1);
    assert.equal((await call('GET', '/api/tasks/not-an-id', { token: a })).status, 400);
    assert.equal((await call('DELETE', `/api/tasks/${id}`, { token: a })).status, 204);
    assert.equal((await call('DELETE', `/api/tasks/${id}`, { token: a })).status, 404);
  });

  it("keeps one user's data private from another user", async () => {
    const note = (await call('POST', '/api/notes', { token: a, body: { title: 'Private', body: 'secret' } })).body;
    assert.equal((await call('GET', '/api/notes', { token: b })).body.length, 0);
    assert.equal((await call('GET', `/api/notes/${note._id}`, { token: b })).status, 404);
    assert.equal((await call('PUT', `/api/notes/${note._id}`, { token: b, body: { title: 'pwned' } })).status, 404);
    assert.equal((await call('DELETE', `/api/notes/${note._id}`, { token: b })).status, 404);
    assert.equal((await call('GET', `/api/notes/${note._id}`, { token: a })).body.title, 'Private');
  });

  it('runs notes CRUD', async () => {
    const n = (await call('POST', '/api/notes', { token: a, body: { title: 'Idea', body: 'ship it' } })).body;
    assert.equal((await call('PUT', `/api/notes/${n._id}`, { token: a, body: { body: 'ship it today' } })).body.body, 'ship it today');
    assert.equal((await call('POST', '/api/notes', { token: a, body: { body: 'no title' } })).status, 400);
  });
});

describe('image upload', () => {
  const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(32)]);
  let token;
  const send = (name, type, data, tok = token) => {
    const form = new FormData();
    form.append('image', new Blob([data], { type }), name);
    return fetch(base + '/api/uploads', { method: 'POST', headers: tok ? { Authorization: `Bearer ${tok}` } : {}, body: form });
  };
  before(async () => {
    token = (await call('POST', '/api/auth/register', { body: { name: 'Meera', email: 'meera@x.io', password: 'upload pass 1' } })).body.token;
  });

  it('requires authentication', async () => {
    assert.equal((await send('a.png', 'image/png', PNG, null)).status, 401);
  });
  it('accepts a PNG, stores it under a random name and serves it back', async () => {
    const res = await send('../../evil name.png', 'image/png', PNG);
    assert.equal(res.status, 201);
    const body = await res.json();
    assert.match(body.url, /^\/uploads\/[0-9a-f]{32}\.png$/);
    assert.equal(body.originalName, 'evil name.png');
    const got = await fetch(base + body.url);
    assert.equal(got.status, 200);
    assert.equal(got.headers.get('content-type'), 'image/png');
    assert.equal(Buffer.from(await got.arrayBuffer()).length, PNG.length);
    assert.equal(fs.readdirSync(uploadDir).length, 1);
    assert.equal((await call('GET', '/api/uploads', { token })).body.length, 1);
  });
  it('rejects non-image types, fake images and oversized files', async () => {
    assert.equal((await send('x.svg', 'image/svg+xml', '<svg onload=alert(1)/>')).status, 400);
    assert.equal((await send('x.png', 'image/png', Buffer.from('not really a png'))).status, 400);
    assert.equal((await send('big.png', 'image/png', Buffer.concat([PNG, Buffer.alloc(3 * 1024 * 1024)]))).status, 400);
    assert.equal(fs.readdirSync(uploadDir).length, 1, 'rejected files are not written to disk');
  });
  it('does not expose other users uploads in the listing', async () => {
    const other = (await call('POST', '/api/auth/register', { body: { name: 'Kabir', email: 'kabir@x.io', password: 'upload pass 2' } })).body.token;
    assert.equal((await call('GET', '/api/uploads', { token: other })).body.length, 0);
  });
});
