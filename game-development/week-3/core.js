// Pure game logic: no DOM, no audio, no drawing. This is what the tests run in Node.
(function (root) {
  const TILE = 32;
  const GRAVITY = 1800;
  const MOVE = 190;
  const JUMP = 640;
  const PW = 22; // player box
  const PH = 28;
  const MAX_HEALTH = 3;
  const INVULN = 1.2; // seconds of protection after a hit

  // '#' solid  '.' air  'c' coin  '^' spike  'F' checkpoint  'G' goal  'e' enemy  'P' start
  const LEVELS = [
    {
      name: 'Meadow',
      map: [
        '..........................................................',
        '..........................................................',
        '..........................................................',
        '..........................................................',
        '...............c.c.c..........................c.c.........',
        '...............#####.......................#######........',
        '..........................c..............................G',
        '.....c.c...........###...................................##',
        '.P.................................e...F..................#',
        '###########..#######################..#######..###########',
        '###########..#######################..#######..###########',
      ],
    },
    {
      name: 'Caverns',
      map: [
        '..........................................................',
        '..........................................................',
        '..........................................................',
        '.........c.c.c.........................c.c.c..............',
        '........#######.....................########..............',
        '...............................c.........................G',
        '...c.c...................####........................######',
        '.........e...F.........e........^^.......e................#',
        '.P......#######.....#######..#########.....######..####....#',
        '#########.....####.......####.........#####......##..###^^^##',
        '#########.....####.......####.........#####......##..#########',
      ],
    },
    {
      name: 'Summit',
      map: [
        '..........................................................',
        '..........................................................',
        '......c.c.......................c.c.c.....................',
        '.....#####............................................c.c..',
        '................c......................c..............####G',
        '...........e..#####....e..............#####...............##',
        '...c.c........................^^......................e..#.',
        '..........F.........^^....#######...........F...............',
        '.P....#########..#########......##....######.......#########.',
        '#######.......####.......####....##..##....###..^^..###.....#',
        '#######.......####.......####....##..##....###########.....#',
      ],
    },
  ];

  function parseLevel(index) {
    const def = LEVELS[index];
    const rows = def.map;
    const width = Math.max(...rows.map(r => r.length));
    const solid = rows.map(r => Array.from({ length: width }, (_, x) => r[x] === '#'));
    const level = { name: def.name, cols: width, rows: rows.length, solid, coins: [], spikes: [], checkpoints: [], enemies: [], goal: null, start: { x: 0, y: 0 } };
    rows.forEach((r, ty) => {
      for (let tx = 0; tx < r.length; tx++) {
        const ch = r[tx];
        const x = tx * TILE, y = ty * TILE;
        if (ch === 'c') level.coins.push({ x: x + 8, y: y + 8, w: 16, h: 16, taken: false });
        else if (ch === '^') level.spikes.push({ x: x + 4, y: y + 12, w: 24, h: 20 });
        else if (ch === 'F') level.checkpoints.push({ x: x + 8, y, w: 16, h: 32, active: false });
        else if (ch === 'G') level.goal = { x, y: y - 32, w: 32, h: 64 };
        else if (ch === 'e') level.enemies.push({ x: x + 4, y: y + 6, w: 24, h: 26, vx: 55, alive: true, startX: x + 4 });
        else if (ch === 'P') level.start = { x: x + 5, y: y + 4 };
      }
    });
    return level;
  }

  const overlap = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
  const isSolid = (lvl, tx, ty) => (tx < 0 || tx >= lvl.cols ? true : ty < 0 ? false : ty >= lvl.rows ? false : lvl.solid[ty][tx]);

  function createGame(levelIndex = 0, carry = {}) {
    const level = parseLevel(levelIndex);
    return {
      levelIndex,
      level,
      player: { x: level.start.x, y: level.start.y, w: PW, h: PH, vx: 0, vy: 0, onGround: false, facing: 1, invuln: 0 },
      respawn: { x: level.start.x, y: level.start.y },
      health: MAX_HEALTH,
      score: carry.score || 0,
      levelStartScore: carry.score || 0,
      time: 0,
      status: 'playing', // playing | dead | levelComplete
      events: [], // consumed by the audio and animation layers each frame
      stats: { jumps: 0, hits: 0, coins: 0, checkpoints: 0, stomps: 0 },
    };
  }

  function moveAxis(lvl, p, dx, dy) {
    if (dx) {
      p.x += dx;
      const top = Math.floor(p.y / TILE), bottom = Math.floor((p.y + p.h - 0.01) / TILE);
      const tx = dx > 0 ? Math.floor((p.x + p.w - 0.01) / TILE) : Math.floor(p.x / TILE);
      for (let ty = top; ty <= bottom; ty++) {
        if (isSolid(lvl, tx, ty)) {
          p.x = dx > 0 ? tx * TILE - p.w : (tx + 1) * TILE;
          p.vx = 0;
          break;
        }
      }
    }
    if (dy) {
      p.y += dy;
      p.onGround = false;
      const left = Math.floor(p.x / TILE), right = Math.floor((p.x + p.w - 0.01) / TILE);
      const ty = dy > 0 ? Math.floor((p.y + p.h - 0.01) / TILE) : Math.floor(p.y / TILE);
      for (let tx = left; tx <= right; tx++) {
        if (isSolid(lvl, tx, ty)) {
          if (dy > 0) {
            p.y = ty * TILE - p.h;
            p.onGround = true;
          } else p.y = (ty + 1) * TILE;
          p.vy = 0;
          break;
        }
      }
    }
  }

  function hurt(g, reason) {
    if (g.player.invuln > 0 || g.status !== 'playing') return;
    g.health -= 1;
    g.stats.hits += 1;
    g.events.push({ type: 'hurt', reason });
    if (g.health <= 0) {
      g.status = 'dead';
      g.events.push({ type: 'gameover' });
      return;
    }
    g.player.invuln = INVULN;
    g.player.x = g.respawn.x;
    g.player.y = g.respawn.y;
    g.player.vx = g.player.vy = 0;
  }

  // input: { left, right, jump }. dt in seconds (callers pass at most 1/30).
  function step(g, input, dt) {
    if (g.status !== 'playing') return g;
    const p = g.player, lvl = g.level;
    g.time += dt;
    p.invuln = Math.max(0, p.invuln - dt);

    const dir = (input.right ? 1 : 0) - (input.left ? 1 : 0);
    p.vx = dir * MOVE;
    if (dir) p.facing = dir;
    if (input.jump && p.onGround) {
      p.vy = -JUMP;
      p.onGround = false;
      g.stats.jumps += 1;
      g.events.push({ type: 'jump' });
    }
    p.vy = Math.min(p.vy + GRAVITY * dt, 900);
    moveAxis(lvl, p, p.vx * dt, 0);
    moveAxis(lvl, p, 0, p.vy * dt);
    if (p.x < 0) p.x = 0;

    for (const c of lvl.coins) {
      if (!c.taken && overlap(p, c)) {
        c.taken = true;
        g.score += 10;
        g.stats.coins += 1;
        g.events.push({ type: 'coin' });
      }
    }
    for (const cp of lvl.checkpoints) {
      if (!cp.active && overlap(p, cp)) {
        cp.active = true;
        g.respawn = { x: cp.x - 3, y: cp.y };
        g.stats.checkpoints += 1;
        g.events.push({ type: 'checkpoint' });
      }
    }
    for (const s of lvl.spikes) if (overlap(p, s)) hurt(g, 'spike');
    for (const e of lvl.enemies) {
      if (!e.alive) continue;
      const nextX = e.x + e.vx * dt;
      const aheadX = e.vx > 0 ? nextX + e.w : nextX;
      const footTy = Math.floor((e.y + e.h + 2) / TILE), tx = Math.floor(aheadX / TILE), ty = Math.floor((e.y + e.h / 2) / TILE);
      if (isSolid(lvl, tx, ty) || !isSolid(lvl, tx, footTy)) e.vx = -e.vx;
      else e.x = nextX;
      if (overlap(p, e)) {
        if (p.vy > 150 && p.y + p.h - e.y < 16) {
          e.alive = false; // stomped from above
          p.vy = -JUMP * 0.55;
          g.score += 25;
          g.stats.stomps += 1;
          g.events.push({ type: 'stomp' });
        } else hurt(g, 'enemy');
      }
    }
    if (p.y > (lvl.rows + 2) * TILE) hurt(g, 'fall');
    if (lvl.goal && overlap(p, lvl.goal) && g.status === 'playing') {
      g.status = 'levelComplete';
      g.score += Math.max(0, Math.round(100 - g.time)) + g.health * 20;
      g.events.push({ type: 'win' });
    }
    return g;
  }

  // ----- Saving: a small JSON blob. storage is any object with getItem/setItem (localStorage or a fake). -----
  const SAVE_KEY = 'sn-platformer-save-v1';
  const defaultSave = () => ({ unlocked: 0, best: [0, 0, 0], volume: 0.6, muted: false });

  function loadSave(storage) {
    try {
      const raw = JSON.parse(storage.getItem(SAVE_KEY) || 'null');
      if (!raw || typeof raw !== 'object') return defaultSave();
      const d = defaultSave();
      return {
        unlocked: Number.isInteger(raw.unlocked) ? Math.min(Math.max(raw.unlocked, 0), LEVELS.length - 1) : d.unlocked,
        best: Array.isArray(raw.best) && raw.best.length === LEVELS.length ? raw.best.map(n => (Number.isFinite(n) && n >= 0 ? n : 0)) : d.best,
        volume: Number.isFinite(raw.volume) ? Math.min(Math.max(raw.volume, 0), 1) : d.volume,
        muted: raw.muted === true,
      };
    } catch (e) {
      return defaultSave();
    }
  }

  function writeSave(storage, save) {
    try { storage.setItem(SAVE_KEY, JSON.stringify(save)); return true; } catch (e) { return false; }
  }

  const api = { TILE, MAX_HEALTH, INVULN, LEVELS, parseLevel, createGame, step, loadSave, writeSave, defaultSave, overlap };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.GameCore = api;
})(typeof window !== 'undefined' ? window : globalThis);
