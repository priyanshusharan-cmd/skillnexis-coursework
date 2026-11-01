// Sound effects and music, synthesized with the Web Audio API, so the game ships no audio files.
// Every sound goes through one master gain, so one slider and one mute switch control everything,
// and each effect has its own fixed level so loudness stays consistent between them.
(function () {
  let ctx = null;
  let master = null;
  let musicTimer = null;
  let volume = 0.6;
  let muted = false;

  const LEVELS = { jump: 0.22, coin: 0.2, hurt: 0.3, checkpoint: 0.22, stomp: 0.3, win: 0.25, gameover: 0.28, music: 0.07 };

  function ensure() {
    if (ctx) return true;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    ctx = new AC();
    master = ctx.createGain();
    master.connect(ctx.destination);
    apply();
    return true;
  }

  function apply() {
    if (master) master.gain.value = muted ? 0 : volume;
  }

  function tone(freq, start, dur, type, level, slideTo) {
    const t = ctx.currentTime + start;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(level, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g);
    g.connect(master);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  function noise(start, dur, level) {
    const t = ctx.currentTime + start;
    const buf = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * dur), ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const s = ctx.createBufferSource();
    const g = ctx.createGain();
    s.buffer = buf;
    g.gain.value = level;
    s.connect(g);
    g.connect(master);
    s.start(t);
  }

  const effects = {
    jump: () => tone(300, 0, 0.16, 'square', LEVELS.jump, 700),
    coin: () => { tone(988, 0, 0.07, 'square', LEVELS.coin); tone(1319, 0.07, 0.14, 'square', LEVELS.coin); },
    hurt: () => tone(380, 0, 0.3, 'sawtooth', LEVELS.hurt, 90),
    checkpoint: () => [523, 659, 784].forEach((f, i) => tone(f, i * 0.09, 0.14, 'triangle', LEVELS.checkpoint)),
    stomp: () => { noise(0, 0.12, LEVELS.stomp); tone(180, 0, 0.12, 'square', LEVELS.stomp * 0.7, 70); },
    win: () => [523, 659, 784, 1047].forEach((f, i) => tone(f, i * 0.12, 0.25, 'triangle', LEVELS.win)),
    gameover: () => [392, 330, 262, 196].forEach((f, i) => tone(f, i * 0.2, 0.3, 'sawtooth', LEVELS.gameover)),
  };

  const NOTES = [110, 138.6, 164.8, 138.6, 98, 123.5, 146.8, 123.5]; // a simple looping bass line
  function startMusic() {
    if (!ensure() || musicTimer) return;
    let i = 0;
    musicTimer = setInterval(() => {
      if (ctx.state === 'running') tone(NOTES[i++ % NOTES.length], 0, 0.28, 'triangle', LEVELS.music);
    }, 300);
  }

  window.GameAudio = {
    unlock() { if (ensure() && ctx.state === 'suspended') ctx.resume(); },
    play(name) { if (muted || !ensure() || !effects[name]) return; effects[name](); },
    startMusic,
    stopMusic() { clearInterval(musicTimer); musicTimer = null; },
    setVolume(v) { volume = Math.min(Math.max(v, 0), 1); apply(); },
    setMuted(m) { muted = !!m; apply(); },
    get muted() { return muted; },
    get volume() { return volume; },
    get supported() { return !!(window.AudioContext || window.webkitAudioContext); },
  };
})();
