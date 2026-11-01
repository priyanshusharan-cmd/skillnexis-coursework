// Rendering, input, menus and the game loop. All rules live in core.js.
(function () {
  const C = window.GameCore;
  const A = window.GameAudio;
  const T = C.TILE;
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;

  let storage;
  try { storage = window.localStorage; storage.getItem('x'); } catch (e) { const m = {}; storage = { getItem: k => m[k] || null, setItem: (k, v) => { m[k] = v; } }; }
  let save = C.loadSave(storage);
  A.setVolume(save.volume);
  A.setMuted(save.muted);

  const $ = id => document.getElementById(id);
  const panels = ['menu', 'pause', 'between', 'gameover', 'victory'];
  let mode = 'menu'; // menu | playing | paused | between | gameover | victory
  let game = null;
  let camX = 0;
  const keys = { left: false, right: false, jump: false };
  const fx = { particles: [], shake: 0, squash: 0, wasOnGround: true, floaters: [] };
  // Analytics stay on this device (see analytics.js). logEvent returns false for an event that fails validation.
  const analytics = window.GameAnalytics.create(storage);
  const logEvent = (name, params) => analytics.log(name, params);
  let sessionFirstControl = false;
  const noteControl = scheme => { if (!sessionFirstControl) { sessionFirstControl = true; logEvent('control_scheme', { scheme }); } };

  // ---------- profiling and optimisation switches ----------
  // ?opt=0 turns every optimisation below off (the "before" build), ?opt=1 or nothing leaves them on.
  const params = new URLSearchParams(location.search);
  // Each optimisation has its own switch: ?opt=0 turns all off, ?only=tiles (or cull, hud, or a comma list) turns on just those.
  const ON = { tiles: true, cull: true, hud: true };
  if (params.get('opt') === '0') Object.keys(ON).forEach(k => { ON[k] = false; });
  if (params.has('only')) { const only = params.get('only').split(','); Object.keys(ON).forEach(k => { ON[k] = only.includes(k); }); }
  const OPT = ON.tiles;
  const prof = { on: params.has('profile'), t: {}, n: 0 };
  const timed = (name, fn) => {
    if (!prof.on) return fn();
    const t0 = performance.now();
    const r = fn();
    prof.t[name] = (prof.t[name] || 0) + performance.now() - t0;
    return r;
  };

  function show(name) {
    panels.forEach(p => { $(p).hidden = p !== name; });
    mode = { pause: 'paused' }[name] || name;
  }
  const showNone = () => { panels.forEach(p => { $(p).hidden = true; }); mode = 'playing'; };

  function persist() { C.writeSave(storage, save); }

  // ---------- menu ----------
  function buildLevelButtons() {
    const box = $('levels');
    box.innerHTML = '';
    C.LEVELS.forEach((lvl, i) => {
      const b = document.createElement('button');
      b.textContent = i + 1;
      b.title = `${lvl.name}${save.best[i] ? ' (best ' + save.best[i] + ')' : ''}`;
      b.setAttribute('aria-label', `Level ${i + 1}: ${lvl.name}${i > save.unlocked ? ' (locked)' : ''}`);
      b.disabled = i > save.unlocked;
      b.addEventListener('click', () => start(i, 0));
      box.appendChild(b);
    });
  }

  function openMenu() {
    A.stopMusic();
    buildLevelButtons();
    $('volume').value = Math.round(save.volume * 100);
    $('btn-mute').textContent = 'Sound: ' + (save.muted ? 'off' : 'on');
    $('btn-mute').setAttribute('aria-pressed', String(save.muted));
    $('btn-play').textContent = save.unlocked > 0 ? 'Continue (level ' + (save.unlocked + 1) + ')' : 'Play';
    show('menu');
    $('btn-play').focus();
  }

  function start(levelIndex, score) {
    A.unlock();
    A.startMusic();
    game = C.createGame(levelIndex, { score });
    camX = 0;
    fx.particles = [];
    fx.floaters = [];
    logEvent('level_start', { level: levelIndex + 1 });
    showNone();
  }

  // ---------- input ----------
  const map = { ArrowLeft: 'left', a: 'left', A: 'left', ArrowRight: 'right', d: 'right', D: 'right', ArrowUp: 'jump', w: 'jump', W: 'jump', ' ': 'jump' };
  window.addEventListener('keydown', e => {
    if (map[e.key]) { keys[map[e.key]] = true; noteControl('keyboard'); if (mode === 'playing') e.preventDefault(); }
    if ((e.key === 'p' || e.key === 'P' || e.key === 'Escape') && !e.repeat) togglePause();
    if ((e.key === 'm' || e.key === 'M') && !e.repeat) setMuted(!save.muted);
  });
  window.addEventListener('keyup', e => { if (map[e.key]) keys[map[e.key]] = false; });
  window.addEventListener('blur', () => { keys.left = keys.right = keys.jump = false; if (mode === 'playing') togglePause(); });

  function togglePause() {
    if (mode === 'playing') { logEvent('pause', { level: game.levelIndex + 1 }); show('pause'); $('btn-resume').focus(); }
    else if (mode === 'paused') showNone();
  }
  function setMuted(m) {
    save.muted = m; A.setMuted(m); persist(); logEvent('setting_changed', { setting: 'mute', value: m });
    $('btn-mute').textContent = 'Sound: ' + (m ? 'off' : 'on');
    $('btn-mute').setAttribute('aria-pressed', String(m));
  }

  $('btn-play').addEventListener('click', () => start(save.unlocked, 0));
  $('btn-resume').addEventListener('click', showNone);
  $('btn-restart').addEventListener('click', () => { logEvent('level_retry', { level: game.levelIndex + 1, after: 'pause_menu' }); start(game.levelIndex, game.levelStartScore); });
  ['btn-quit', 'btn-quit2', 'btn-quit3'].forEach(id => $(id).addEventListener('click', openMenu));
  $('btn-retry').addEventListener('click', () => { logEvent('level_retry', { level: game.levelIndex + 1, after: 'game_over' }); start(game.levelIndex, game.levelStartScore); });
  $('btn-again').addEventListener('click', () => start(0, 0));
  $('btn-next').addEventListener('click', () => start(game.levelIndex + 1, game.score));
  $('btn-mute').addEventListener('click', () => setMuted(!save.muted));
  $('volume').addEventListener('input', e => { save.volume = e.target.value / 100; A.setVolume(save.volume); A.unlock(); A.play('coin'); persist(); logEvent('setting_changed', { setting: 'volume', value: save.volume }); });

  // ---------- touch controls ----------
  // Shown on touch screens (or with ?touch). Each button sets the same key flags the keyboard uses, and pointer
  // capture plus pointercancel handling stop a finger sliding off a button from leaving a direction stuck on.
  const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
  if (coarse || params.has('touch')) $('touch').hidden = false;
  [['t-left', 'left'], ['t-right', 'right'], ['t-jump', 'jump']].forEach(([id, flag]) => {
    const b = $(id);
    const set = on => { keys[flag] = on; b.classList.toggle('active', on); };
    b.addEventListener('pointerdown', e => { e.preventDefault(); noteControl('touch'); A.unlock(); try { b.setPointerCapture(e.pointerId); } catch (err) { /* old browsers */ } set(true); });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(ev => b.addEventListener(ev, () => set(false)));
    b.addEventListener('contextmenu', e => e.preventDefault());
  });
  $('t-pause').addEventListener('click', togglePause);
  const rotateHint = () => { $('rotate').hidden = !(($('touch').hidden === false) && window.innerHeight > window.innerWidth); };
  window.addEventListener('resize', rotateHint);
  window.addEventListener('orientationchange', rotateHint);
  rotateHint();

  // ---------- reacting to game events ----------
  function burst(x, y, color, n) {
    for (let i = 0; i < n; i++) fx.particles.push({ x, y, vx: (Math.random() - 0.5) * 220, vy: -Math.random() * 220, life: 0.5 + Math.random() * 0.3, color });
  }

  function handleEvents() {
    const p = game.player;
    for (const ev of game.events) {
      A.play(ev.type === 'win' ? 'win' : ev.type);
      if (ev.type === 'coin') { burst(p.x + 11, p.y + 8, '#ffd23f', 8); fx.floaters.push({ x: p.x, y: p.y - 6, text: '+10', life: 0.7 }); }
      if (ev.type === 'hurt') { fx.shake = 0.3; burst(p.x + 11, p.y + 14, '#ff5a5f', 14); logEvent('player_hit', { level: game.levelIndex + 1, reason: ev.reason }); }
      if (ev.type === 'stomp') { burst(p.x + 11, p.y + 28, '#ffffff', 10); logEvent('enemy_stomped', { level: game.levelIndex + 1 }); }
      if (ev.type === 'checkpoint') logEvent('checkpoint', { level: game.levelIndex + 1 });
      if (ev.type === 'jump') fx.squash = -0.25;
    }
    game.events.length = 0;
    if (game.status === 'levelComplete') finishLevel();
    else if (game.status === 'dead') {
      A.stopMusic();
      logEvent('game_over', { level: game.levelIndex + 1, score: game.score });
      $('gameover-text').textContent = `Score ${game.score}. You reached ${Math.round(game.player.x / T)} tiles into ${game.level.name}.`;
      show('gameover');
      $('btn-retry').focus();
    }
  }

  function finishLevel() {
    const i = game.levelIndex;
    save.best[i] = Math.max(save.best[i], game.score);
    save.unlocked = Math.max(save.unlocked, Math.min(i + 1, C.LEVELS.length - 1));
    persist();
    logEvent('coins_collected', { level: i + 1, coins: game.stats.coins });
    logEvent('level_complete', { level: i + 1, score: game.score, seconds: Math.round(game.time), health_left: game.health });
    if (i + 1 >= C.LEVELS.length) {
      A.stopMusic();
      $('victory-text').textContent = `Final score ${game.score}. Coins: ${game.stats.coins}, enemies stomped: ${game.stats.stomps}.`;
      show('victory');
      $('btn-again').focus();
    } else {
      $('between-title').textContent = `${game.level.name} complete`;
      $('between-text').textContent = `Score ${game.score} in ${game.time.toFixed(1)} s. Next: ${C.LEVELS[i + 1].name}.`;
      show('between');
      $('btn-next').focus();
    }
  }

  // ---------- drawing ----------
  let tileCache = null; // { levelIndex, canvas }: all solid tiles of the current level, drawn once
  function tilesCanvas(g) {
    if (tileCache && tileCache.levelIndex === g.levelIndex) return tileCache.canvas;
    const lvl = g.level, c = document.createElement('canvas');
    c.width = lvl.cols * T; c.height = lvl.rows * T;
    const x2 = c.getContext('2d');
    for (let ty = 0; ty < lvl.rows; ty++) for (let tx = 0; tx < lvl.cols; tx++) if (lvl.solid[ty][tx]) drawTile(x2, lvl, g.levelIndex, tx, ty, tx * T);
    tileCache = { levelIndex: g.levelIndex, canvas: c };
    return c;
  }
  function drawTile(c2, lvl, levelIndex, tx, ty, x) {
    const y = ty * T, topExposed = ty === 0 || !lvl.solid[ty - 1][tx];
    c2.fillStyle = '#5b4636'; c2.fillRect(x, y, T, T);
    c2.fillStyle = '#4a3a2d'; c2.fillRect(x + 2, y + T - 4, T - 4, 4);
    if (topExposed) { c2.fillStyle = ['#59b34a', '#6d7b8d', '#e8eef2'][levelIndex % 3]; c2.fillRect(x, y, T, 7); }
  }
  // Optimisation B: the sky gradient only depends on the level, so build it once per level.
  let skyCache = null;
  function skyFor(index) {
    if (skyCache && skyCache.index === index) return skyCache.g;
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, ['#6ec6ff', '#2b2d4a', '#f4a261'][index % 3]);
    sky.addColorStop(1, ['#d6f0ff', '#4a4e79', '#ffe8c2'][index % 3]);
    skyCache = { index, g: sky };
    return sky;
  }

  function drawLevel(g, t) {
    timed('level background', () => drawBackground(g));
    timed('level objects', () => drawObjects(g, t));
  }

  function drawBackground(g) {
    const lvl = g.level;
    if (OPT) {
      ctx.fillStyle = skyFor(g.levelIndex);
      ctx.fillRect(0, 0, W, H);
      const sx = Math.round(camX);
      ctx.drawImage(tilesCanvas(g), sx, 0, W, lvl.rows * T, 0, 0, W, lvl.rows * T);
    } else {
      const sky = ctx.createLinearGradient(0, 0, 0, H);
      sky.addColorStop(0, ['#6ec6ff', '#2b2d4a', '#f4a261'][g.levelIndex % 3]);
      sky.addColorStop(1, ['#d6f0ff', '#4a4e79', '#ffe8c2'][g.levelIndex % 3]);
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, W, H);
      const first = Math.max(0, Math.floor(camX / T)), last = Math.min(lvl.cols - 1, Math.ceil((camX + W) / T));
      for (let ty = 0; ty < lvl.rows; ty++) for (let tx = first; tx <= last; tx++) if (lvl.solid[ty][tx]) drawTile(ctx, lvl, g.levelIndex, tx, ty, tx * T - camX);
    }
  }

  const visible = (x, w) => !ON.cull || (x + w >= camX && x <= camX + W); // Optimisation C: skip objects that are off screen
  function drawObjects(g, t) {
    const lvl = g.level;
    for (const s of lvl.spikes) {
      if (!visible(s.x, s.w)) continue;
      ctx.fillStyle = '#d9d9e3';
      for (let k = 0; k < 2; k++) {
        const bx = s.x - 4 + k * 16 - camX + 4, by = s.y + s.h;
        ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + 8, by - s.h); ctx.lineTo(bx + 16, by); ctx.closePath(); ctx.fill();
      }
    }
    for (const cp of lvl.checkpoints) {
      if (!visible(cp.x, cp.w + 24)) continue;
      const x = cp.x - camX;
      ctx.fillStyle = '#8a8a8a'; ctx.fillRect(x + 6, cp.y, 3, cp.h);
      ctx.fillStyle = cp.active ? '#3ddc84' : '#c0c0c0';
      const wave = cp.active ? Math.sin(t * 8) * 2 : 0;
      ctx.beginPath(); ctx.moveTo(x + 9, cp.y + 2); ctx.lineTo(x + 26 + wave, cp.y + 8); ctx.lineTo(x + 9, cp.y + 14); ctx.fill();
    }
    for (const c of lvl.coins) {
      if (c.taken || !visible(c.x, c.w)) continue;
      const squeeze = Math.abs(Math.cos(t * 4 + c.x)); // spinning coin: animation 1
      ctx.fillStyle = '#ffd23f'; ctx.beginPath(); ctx.ellipse(c.x + 8 - camX, c.y + 8, 7 * Math.max(squeeze, 0.15), 8, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = '#b8860b'; ctx.lineWidth = 1.5; ctx.stroke();
    }
    for (const e of lvl.enemies) {
      if (!e.alive || !visible(e.x, e.w)) continue;
      const x = e.x - camX, waddle = Math.sin(t * 10 + e.startX) * 2;
      ctx.fillStyle = '#9b4dca'; ctx.fillRect(x, e.y + 4 + Math.abs(waddle) * 0.5, e.w, e.h - 4);
      ctx.fillStyle = '#fff'; ctx.fillRect(x + 4, e.y + 10, 6, 6); ctx.fillRect(x + 14, e.y + 10, 6, 6);
      ctx.fillStyle = '#111'; ctx.fillRect(x + (e.vx > 0 ? 7 : 5), e.y + 12, 3, 3); ctx.fillRect(x + (e.vx > 0 ? 17 : 15), e.y + 12, 3, 3);
    }
    if (lvl.goal && visible(lvl.goal.x, 48)) {
      const x = lvl.goal.x - camX;
      ctx.fillStyle = '#fff'; ctx.fillRect(x + 14, lvl.goal.y, 4, lvl.goal.h);
      ctx.fillStyle = '#ff4d6d'; ctx.beginPath(); ctx.moveTo(x + 18, lvl.goal.y + 2); ctx.lineTo(x + 40 + Math.sin(t * 6) * 3, lvl.goal.y + 12); ctx.lineTo(x + 18, lvl.goal.y + 22); ctx.fill();
    }
  }

  function drawPlayer(g, t) {
    const p = g.player;
    if (p.invuln > 0 && Math.floor(t * 14) % 2 === 0) return; // blink while protected
    const run = p.onGround && (keys.left || keys.right) ? Math.sin(t * 22) : 0; // running bob: animation 2
    const sq = fx.squash;
    const w = p.w * (1 - sq * 0.5), h = p.h * (1 + sq) - Math.abs(run) * 2;
    const x = p.x - camX + (p.w - w) / 2, y = p.y + p.h - h;
    ctx.fillStyle = '#ff9f1c'; ctx.fillRect(x, y, w, h);
    ctx.fillStyle = '#2a9d8f'; ctx.fillRect(x, y, w, 8);
    ctx.fillStyle = '#fff'; ctx.fillRect(x + (p.facing > 0 ? w - 9 : 3), y + 10, 6, 6);
    ctx.fillStyle = '#111'; ctx.fillRect(x + (p.facing > 0 ? w - 6 : 3), y + 12, 3, 3);
  }

  function paintHud(c2, g) {
    c2.font = '700 16px system-ui, sans-serif';
    c2.textBaseline = 'top';
    for (let i = 0; i < C.MAX_HEALTH; i++) { c2.fillStyle = i < g.health ? '#ff5a5f' : '#ffffff44'; c2.fillText('\u2665', 10 + i * 20, 8); }
    c2.fillStyle = '#fff'; c2.textAlign = 'center'; c2.fillText(`${g.level.name}  (level ${g.levelIndex + 1} of ${C.LEVELS.length})`, W / 2, 8);
    c2.textAlign = 'right'; c2.fillText(`Score ${g.score}`, W - 10, 8); c2.fillText(`${g.time.toFixed(0)} s`, W - 10, 28);
    c2.textAlign = 'left';
  }
  // Optimisation: the HUD text only changes when health, score, level or whole seconds change, so keep it on its own
  // canvas and redraw that canvas only then, instead of re-laying-out five strings every frame.
  let hudCache = null;
  function drawHud(g) {
    if (!ON.hud) { paintHud(ctx, g); return; }
    const key = `${g.health}|${g.score}|${g.levelIndex}|${g.time.toFixed(0)}`;
    if (!hudCache) { const c = document.createElement('canvas'); c.width = W; c.height = 48; hudCache = { c, ctx: c.getContext('2d'), key: '' }; }
    if (hudCache.key !== key) { hudCache.ctx.clearRect(0, 0, W, 48); paintHud(hudCache.ctx, g); hudCache.key = key; }
    ctx.drawImage(hudCache.c, 0, 0);
  }

  function render(t, dt) {
    ctx.save();
    if (fx.shake > 0) { ctx.translate((Math.random() - 0.5) * 8 * fx.shake * 3, (Math.random() - 0.5) * 8 * fx.shake * 3); fx.shake -= dt; }
    if (game) {
      timed('draw level', () => drawLevel(game, t));
      timed('draw sprites', () => {
        drawPlayer(game, t);
        for (const q of fx.particles) { ctx.fillStyle = q.color; ctx.globalAlpha = Math.max(q.life, 0); ctx.fillRect(q.x - camX, q.y, 4, 4); }
        ctx.globalAlpha = 1;
        for (const f of fx.floaters) { ctx.fillStyle = '#fff'; ctx.globalAlpha = Math.max(f.life, 0); ctx.fillText(f.text, f.x - camX, f.y); }
        ctx.globalAlpha = 1;
      });
      timed('draw HUD', () => drawHud(game));
    } else { ctx.fillStyle = '#1b2236'; ctx.fillRect(0, 0, W, H); }
    ctx.restore();
  }

  // ---------- loop ----------
  let last = 0, clock = 0;
  let perfMs = 0, perfFrames = 0;
  function update(dt) {
    const t0 = performance.now();
    clock += dt;
    if (game && mode === 'playing') {
      const wasOnGround = game.player.onGround;
      timed('physics', () => C.step(game, keys, dt));
      if (!wasOnGround && game.player.onGround) fx.squash = 0.3; // landing squash
      handleEvents();
      const target = Math.min(Math.max(game.player.x - W / 2 + 11, 0), game.level.cols * T - W);
      camX += (target - camX) * Math.min(1, dt * 8);
    }
    fx.squash *= Math.pow(0.001, dt);
    for (const q of fx.particles) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 700 * dt; q.life -= dt; }
    fx.particles = fx.particles.filter(q => q.life > 0);
    for (const f of fx.floaters) { f.y -= 30 * dt; f.life -= dt; }
    fx.floaters = fx.floaters.filter(f => f.life > 0);
    render(clock, dt);
    if (prof.on) prof.n++;
    if (mode === 'playing') {
      perfMs += performance.now() - t0; perfFrames++;
      if (perfFrames === 600) { logEvent('perf_sample', { avg_frame_ms: perfMs / perfFrames }); perfMs = 0; perfFrames = 0; }
    }
  }
  function frame(now) {
    const dt = Math.min((now - last) / 1000 || 0, 1 / 30);
    last = now;
    update(dt);
    requestAnimationFrame(frame);
  }

  // Exposed so tests and the browser console can inspect state.
  window.__profile = {
    reset() { prof.t = {}; prof.n = 0; },
    report() { const per = {}; let total = 0; for (const k in prof.t) { per[k] = +(prof.t[k] / prof.n).toFixed(4); total += prof.t[k] / prof.n; } return { frames: prof.n, msPerFrame: per, totalMs: +total.toFixed(4), on: { ...ON } }; },
  };
  window.__game = { get state() { return game; }, get mode() { return mode; }, get save() { return save; }, keys, start, tick: update };
  logEvent('session_start', { returning: analytics.count('session_start') > 0 });
  window.addEventListener('pagehide', () => logEvent('session_end', { seconds: analytics.sessionSeconds(), levels_completed: analytics.count('level_complete') }));
  window.addEventListener('beforeinstallprompt', () => logEvent('pwa_install', { outcome: 'prompted' }));
  window.addEventListener('appinstalled', () => logEvent('pwa_install', { outcome: 'installed' }));
  $('btn-clear').addEventListener('click', () => {
    if (!window.confirm('Delete saved progress, settings and stored analytics on this device?')) return;
    analytics.clear();
    save = C.defaultSave(); A.setVolume(save.volume); A.setMuted(save.muted); persist();
    openMenu();
  });
  window.__analytics = analytics;
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(() => {});
  openMenu();
  requestAnimationFrame(frame);
})();
