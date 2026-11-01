// Run with: node core.test.js
const assert = require('node:assert/strict');
const { test } = require('node:test');
const G = require('./core');

const DT = 1 / 60;
const mem = () => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); } }; };
const run = (g, input, seconds) => { for (let i = 0; i < Math.round(seconds / DT); i++) G.step(g, input, DT); return g; };

test('every level parses with a start, a goal and some coins', () => {
  G.LEVELS.forEach((_, i) => {
    const lvl = G.parseLevel(i);
    assert.ok(lvl.goal, `level ${i} has a goal`);
    assert.ok(lvl.coins.length >= 5, `level ${i} has coins`);
    assert.ok(lvl.checkpoints.length >= 1, `level ${i} has a checkpoint`);
    assert.ok(lvl.start.x >= 0);
  });
});

test('gravity pulls the player onto the floor and they stay there', () => {
  const g = G.createGame(0);
  run(g, {}, 1);
  assert.equal(g.player.onGround, true);
  const y = g.player.y;
  run(g, {}, 1);
  assert.equal(g.player.y, y);
});

test('jumping needs the ground, and cannot be repeated in mid-air', () => {
  const g = G.createGame(0);
  run(g, {}, 0.5);
  G.step(g, { jump: true }, DT);
  assert.ok(g.player.vy < 0);
  const jumpsAfterFirst = g.stats.jumps;
  G.step(g, { jump: true }, DT);
  assert.equal(g.stats.jumps, jumpsAfterFirst, 'no double jump');
});

test('walls stop horizontal movement', () => {
  const g = G.createGame(0);
  run(g, {}, 0.3);
  run(g, { left: true }, 2);
  assert.equal(g.player.x, 0, 'cannot walk off the left edge of the level');
});

test('coins add score once', () => {
  const g = G.createGame(0);
  const c = g.level.coins[0];
  g.player.x = c.x; g.player.y = c.y;
  G.step(g, {}, DT);
  assert.equal(g.score, 10);
  G.step(g, {}, DT);
  assert.equal(g.score, 10);
  assert.equal(g.stats.coins, 1);
});

test('a spike costs one health, then protects the player briefly, and respawns them', () => {
  const g = G.createGame(1);
  const s = g.level.spikes[0];
  g.player.x = s.x; g.player.y = s.y - 10;
  G.step(g, {}, DT);
  assert.equal(g.health, G.MAX_HEALTH - 1);
  assert.deepEqual([g.player.x, g.player.y], [g.respawn.x, g.respawn.y]);
  assert.ok(g.player.invuln > 1);
  g.player.x = s.x; g.player.y = s.y - 10;
  G.step(g, {}, DT);
  assert.equal(g.health, G.MAX_HEALTH - 1, 'no second hit while protected');
});

test('losing all health ends the game', () => {
  const g = G.createGame(1);
  const s = g.level.spikes[0];
  for (let i = 0; i < G.MAX_HEALTH; i++) {
    g.player.invuln = 0;
    g.player.x = s.x; g.player.y = s.y - 10;
    G.step(g, {}, DT);
  }
  assert.equal(g.status, 'dead');
  assert.ok(g.events.some(e => e.type === 'gameover'));
});

test('a checkpoint becomes the respawn point', () => {
  const g = G.createGame(0);
  const cp = g.level.checkpoints[0];
  g.player.x = cp.x; g.player.y = cp.y;
  G.step(g, {}, DT);
  assert.equal(cp.active, true);
  assert.ok(Math.abs(g.respawn.x - cp.x) <= 3);
  g.player.invuln = 0;
  g.player.y = 99999;
  G.step(g, {}, DT);
  assert.equal(g.health, G.MAX_HEALTH - 1, 'falling out of the level costs health');
  assert.ok(Math.abs(g.player.x - g.respawn.x) < 1, 'respawns at the checkpoint');
});

test('stomping an enemy from above kills it and scores, touching from the side hurts', () => {
  const g = G.createGame(0);
  const e = g.level.enemies[0];
  g.player.x = e.x; g.player.y = e.y - g.player.h + 6; g.player.vy = 300;
  G.step(g, {}, DT);
  assert.equal(e.alive, false);
  assert.equal(g.stats.stomps, 1);

  const h = G.createGame(0);
  const e2 = h.level.enemies[0];
  h.player.x = e2.x; h.player.y = e2.y; h.player.vy = 0;
  G.step(h, {}, DT);
  assert.equal(h.health, G.MAX_HEALTH - 1);
});

test('reaching the goal completes the level with a score bonus', () => {
  const g = G.createGame(0);
  g.player.x = g.level.goal.x; g.player.y = g.level.goal.y;
  G.step(g, {}, DT);
  assert.equal(g.status, 'levelComplete');
  assert.ok(g.score >= G.MAX_HEALTH * 20);
});

// Searches every sequence of left/right/jump choices (held for 0.1 s at a time) through the real physics code and
// reports whether the goal can be reached without touching a spike or falling out of the level.
function findRoute(levelIndex) {
  const g = G.createGame(levelIndex);
  g.level.enemies = [];   // enemies can be stomped or walked around, so they do not make a level impossible
  g.level.coins = [];
  g.level.checkpoints = [];
  const start = { x: g.player.x, y: g.player.y, vx: 0, vy: 0, onGround: false, facing: 1 };
  const key = n => `${Math.round(n.x / 4)},${Math.round(n.y / 4)},${Math.round(n.vy / 80)},${n.onGround ? 1 : 0}`;
  const seen = new Set([key(start)]);
  let frontier = [{ ...start, path: [] }];
  const actions = [];
  for (const dir of [-1, 0, 1]) for (const jump of [false, true]) actions.push({ left: dir < 0, right: dir > 0, jump });
  for (let depth = 0; depth < 400 && frontier.length; depth++) {
    const next = [];
    for (const n of frontier) {
      for (const a of actions) {
        Object.assign(g.player, { x: n.x, y: n.y, vx: n.vx, vy: n.vy, onGround: n.onGround, facing: n.facing, invuln: 0 });
        g.health = G.MAX_HEALTH; g.status = 'playing'; g.events.length = 0;
        let ok = true;
        for (let f = 0; f < 6 && ok; f++) {
          G.step(g, a, DT);
          if (g.health < G.MAX_HEALTH) ok = false;
          if (g.status === 'levelComplete') return { reached: true, seconds: (depth + 1) * 0.1 };
        }
        if (!ok) continue;
        const m = { x: g.player.x, y: g.player.y, vx: g.player.vx, vy: g.player.vy, onGround: g.player.onGround, facing: g.player.facing };
        const k = key(m);
        if (!seen.has(k)) { seen.add(k); next.push(m); }
      }
    }
    frontier = next;
  }
  return { reached: false, states: seen.size };
}

test('every level can be completed without taking damage (exhaustive search of the real physics)', () => {
  G.LEVELS.forEach((def, i) => {
    const r = findRoute(i);
    assert.equal(r.reached, true, `${def.name}: no hazard-free route to the goal was found (${r.states} states explored)`);
    console.log(`  ${def.name}: goal reachable in about ${r.seconds.toFixed(1)} s of play`);
  });
});

test('saving: round trip, defaults, and corrupt or tampered data', () => {
  const s = mem();
  assert.deepEqual(G.loadSave(s), G.defaultSave());
  const save = { unlocked: 2, best: [120, 90, 0], volume: 0.3, muted: true };
  assert.equal(G.writeSave(s, save), true);
  assert.deepEqual(G.loadSave(s), save);
  s.setItem('sn-platformer-save-v1', '{nope');
  assert.deepEqual(G.loadSave(s), G.defaultSave());
  s.setItem('sn-platformer-save-v1', JSON.stringify({ unlocked: 99, best: [1, 2], volume: 5, muted: 'yes' }));
  const bad = G.loadSave(s);
  assert.equal(bad.unlocked, G.LEVELS.length - 1);
  assert.deepEqual(bad.best, [0, 0, 0]);
  assert.equal(bad.volume, 1);
  assert.equal(bad.muted, false);
  assert.equal(G.writeSave({ setItem() { throw new Error('quota'); } }, save), false, 'a full or blocked storage does not crash');
});
