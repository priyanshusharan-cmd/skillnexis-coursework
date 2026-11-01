// Benchmark: plays a fixed number of frames of scripted movement and reports the average cost per frame.
// Open index.html?profile&bench with ?opt=0 (every optimisation off), ?only=tiles, ?only=cull, ?only=hud, or nothing (all on).
// It runs 5 times and reports the median, because one run is noisy. Loaded only when "bench" is in the URL.
(function () {
  if (!new URLSearchParams(location.search).has('bench')) return;
  const FRAMES = 6000, WARMUP = 300, DT = 1 / 60, RUNS = 5;
  function once() {
    let seed = 12345;
    const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296; // fixed seed: same script every run
    const g = window.__game;
    g.start(1, 0);
    for (let i = 0; i < WARMUP; i++) g.tick(DT);
    window.__profile.reset();
    const t0 = performance.now();
    for (let i = 0; i < FRAMES; i++) {
      if (g.mode !== 'playing') g.start(1, 0);
      g.keys.right = rnd() < 0.8; g.keys.left = !g.keys.right && rnd() < 0.3; g.keys.jump = rnd() < 0.08;
      if (i % 40 === 0) { const p = g.state.player; g.state.level.coins.forEach(c => { if (Math.abs(c.x - p.x) < 200) c.taken = false; }); }
      g.tick(DT);
    }
    const wall = performance.now() - t0;
    const r = window.__profile.report();
    r.wallMsPerFrame = wall / FRAMES;
    return r;
  }
  window.addEventListener('load', () => setTimeout(() => {
    const runs = Array.from({ length: RUNS }, once);
    const med = a => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
    window.__benchResult = {
      on: runs[0].on, frames: FRAMES, runs: RUNS,
      medianWallMsPerFrame: +med(runs.map(r => r.wallMsPerFrame)).toFixed(4),
      allWallMsPerFrame: runs.map(r => +r.wallMsPerFrame.toFixed(4)),
    };
    document.title = 'bench done';
  }, 400));
})();
