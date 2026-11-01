// Run with: node --test analytics.test.js
const assert = require('node:assert/strict');
const { test } = require('node:test');
const A = require('./analytics');

const mem = () => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, raw: m }; };
let clock = 1000;
const make = (s = mem()) => ({ s, a: A.create(s, () => (clock += 500)) });

test('the catalogue has exactly 15 events', () => {
  assert.equal(Object.keys(A.EVENTS).length, 15);
});

test('valid events are recorded with their parameters', () => {
  const { a } = make();
  assert.equal(a.log('level_start', { level: 2 }), true);
  assert.equal(a.log('player_hit', { level: 2, reason: 'spike' }), true);
  assert.equal(a.log('level_complete', { level: 2, score: 312, seconds: 41.23456, health_left: 2 }), true);
  assert.equal(a.count('level_start'), 1);
  assert.deepEqual(a.all()[2].params, { level: 2, score: 312, seconds: 41.235, health_left: 2 });
});

test('unknown events and bad values are rejected, and nothing is recorded', () => {
  const { a } = make();
  assert.equal(a.log('purchase', { amount: 5 }), false, 'event not in the catalogue');
  assert.equal(a.log('player_hit', { level: 1, reason: 'lava' }), false, 'reason not allowed');
  assert.equal(a.log('level_start', { level: 'two' }), false, 'wrong type');
  assert.equal(a.log('level_complete', { level: 1, score: NaN }), false, 'NaN is not a number here');
  assert.equal(a.all().length, 0);
});

test('parameters outside the catalogue are dropped, so personal data cannot be recorded by accident', () => {
  const { a } = make();
  assert.equal(a.log('level_start', { level: 1, email: 'a@b.co', name: 'Asha', deviceId: 'abc' }), true);
  assert.deepEqual(a.all()[0].params, { level: 1 });
  assert.ok(!a.exportJson().includes('a@b.co'));
});

test('only the most recent 200 events are kept', () => {
  const { a } = make();
  for (let i = 0; i < A.MAX_EVENTS + 25; i++) a.log('pause', { level: 1 });
  assert.equal(a.all().length, A.MAX_EVENTS);
});

test('events survive a restart through storage, and corrupt or tampered storage is ignored', () => {
  const s = mem();
  const first = A.create(s, () => 1);
  first.log('session_start', { returning: false });
  first.log('level_start', { level: 1 });
  const second = A.create(s, () => 2);
  assert.equal(second.all().length, 2);
  s.setItem(A.STORAGE_KEY, '{broken');
  assert.deepEqual(A.create(s).all(), []);
  s.setItem(A.STORAGE_KEY, JSON.stringify([{ name: 'level_start' }, { name: 'made_up_event' }, null, 7]));
  assert.deepEqual(A.create(s).all().map(e => e.name), ['level_start'], 'entries not in the catalogue are discarded');
  assert.equal(A.create({ getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } }).log('pause', { level: 1 }), true, 'blocked storage does not crash');
});

test('session length is measured from session_start', () => {
  let t = 0;
  const a = A.create(mem(), () => t);
  assert.equal(a.sessionSeconds(), 0);
  t = 10000; a.log('session_start', { returning: true });
  t = 70000;
  assert.equal(a.sessionSeconds(), 60);
});

test('clear removes everything, including the stored copy', () => {
  const { a, s } = make();
  a.log('pause', { level: 1 });
  a.clear();
  assert.equal(a.all().length, 0);
  assert.equal(s.raw[A.STORAGE_KEY], '[]');
});
