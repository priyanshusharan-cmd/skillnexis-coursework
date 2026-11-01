const assert = require('node:assert/strict');
const { after, before, describe, it } = require('node:test');
const mongoose = require('mongoose');
const { createApp } = require('../src/app');

let server, base;
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
  server = createApp({ jwtSecret: 'test-secret-test-secret' }).listen(0);
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

describe('social feed', () => {
  let a, b, postId;
  before(async () => {
    a = (await call('POST', '/api/auth/login', { body: { email: 'asha@x.io', password: 'correct horse' } })).body.token;
    b = (await call('POST', '/api/auth/register', { body: { name: 'Ravi', email: 'ravi@x.io', password: 'another pass' } })).body.token;
  });

  it('requires a token', async () => {
    assert.equal((await call('GET', '/api/posts')).status, 401);
  });
  it('creates posts and rejects empty or oversized text', async () => {
    assert.equal((await call('POST', '/api/posts', { token: a, body: { text: '   ' } })).status, 400);
    assert.equal((await call('POST', '/api/posts', { token: a, body: { text: 'x'.repeat(501) } })).status, 400);
    const res = await call('POST', '/api/posts', { token: a, body: { text: 'Hello feed', author: 'someone-else', likeCount: 99 } });
    assert.equal(res.status, 201);
    assert.equal(res.body.author.name, 'Asha');
    assert.equal(res.body.likeCount, 0);
    postId = res.body.id;
  });
  it('lists newest first with the author name', async () => {
    await call('POST', '/api/posts', { token: b, body: { text: 'Second post' } });
    const feed = (await call('GET', '/api/posts', { token: a })).body;
    assert.deepEqual(feed.map(p => p.text), ['Second post', 'Hello feed']);
    assert.equal(feed[0].author.name, 'Ravi');
    assert.equal((await call('GET', '/api/posts?limit=1', { token: a })).body.length, 1);
    const older = (await call('GET', `/api/posts?before=${feed[0].id}`, { token: a })).body;
    assert.deepEqual(older.map(p => p.text), ['Hello feed']);
  });
  it('likes once per user and toggles off', async () => {
    let r = await call('POST', `/api/posts/${postId}/like`, { token: b });
    assert.equal(r.body.likeCount, 1);
    assert.equal(r.body.likedByMe, true);
    r = await call('POST', `/api/posts/${postId}/like`, { token: a });
    assert.equal(r.body.likeCount, 2);
    r = await call('POST', `/api/posts/${postId}/like`, { token: b });
    assert.equal(r.body.likeCount, 1);
    assert.equal(r.body.likedByMe, false);
    assert.equal((await call('POST', '/api/posts/not-an-id/like', { token: a })).status, 400);
    assert.equal((await call('POST', '/api/posts/64b64b64b64b64b64b64b64b/like', { token: a })).status, 404);
  });
  it('adds comments with validation', async () => {
    assert.equal((await call('POST', `/api/posts/${postId}/comments`, { token: b, body: { text: ' ' } })).status, 400);
    const r = await call('POST', `/api/posts/${postId}/comments`, { token: b, body: { text: 'Nice one' } });
    assert.equal(r.status, 201);
    assert.equal(r.body.comments.length, 1);
    assert.equal(r.body.comments[0].author.name, 'Ravi');
  });
  it('lets only the author delete a post', async () => {
    assert.equal((await call('DELETE', `/api/posts/${postId}`, { token: b })).status, 403);
    assert.equal((await call('DELETE', `/api/posts/${postId}`, { token: a })).status, 204);
    assert.equal((await call('DELETE', `/api/posts/${postId}`, { token: a })).status, 404);
  });
});
