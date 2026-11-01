// Analytics: a fixed catalogue of 15 events, validated before they are recorded.
// Events are kept ON THE DEVICE ONLY (an in-memory list plus a small copy in localStorage). Nothing is sent anywhere.
// Sending data to a server would need a privacy policy and, in many places, the player's consent, so that is left out on purpose.
// The catalogue says which parameters each event may carry; anything else is dropped, so personal data cannot slip in by accident.
(function (root) {
  const MAX_EVENTS = 200;
  const STORAGE_KEY = 'sn-gemrun-analytics-v1';
  const num = v => typeof v === 'number' && Number.isFinite(v);
  const oneOf = (...vals) => v => vals.includes(v);
  const level = v => Number.isInteger(v) && v >= 1 && v <= 99;

  // name -> { parameter: validator }. Every parameter is optional unless the validator rejects undefined.
  const EVENTS = {
    session_start: { returning: v => typeof v === 'boolean' },
    control_scheme: { scheme: oneOf('keyboard', 'touch') },
    level_start: { level },
    level_complete: { level, score: num, seconds: num, health_left: v => Number.isInteger(v) && v >= 0 && v <= 3 },
    game_over: { level, score: num },
    player_hit: { level, reason: oneOf('spike', 'enemy', 'fall') },
    checkpoint: { level },
    coins_collected: { level, coins: v => Number.isInteger(v) && v >= 0 },
    enemy_stomped: { level },
    pause: { level },
    level_retry: { level, after: oneOf('game_over', 'pause_menu') },
    setting_changed: { setting: oneOf('volume', 'mute'), value: v => num(v) || typeof v === 'boolean' },
    session_end: { seconds: num, levels_completed: v => Number.isInteger(v) && v >= 0 },
    pwa_install: { outcome: oneOf('prompted', 'installed') },
    perf_sample: { avg_frame_ms: num },
  };

  function create(storage, now = () => Date.now()) {
    let events = [];
    let session = null;
    try {
      const saved = JSON.parse(storage.getItem(STORAGE_KEY) || '[]');
      if (Array.isArray(saved)) events = saved.filter(e => e && EVENTS[e.name]).slice(-MAX_EVENTS);
    } catch (e) { events = []; }

    const persist = () => { try { storage.setItem(STORAGE_KEY, JSON.stringify(events)); } catch (e) { /* storage full or blocked */ } };

    return {
      names: () => Object.keys(EVENTS),
      /** Returns true if the event was recorded, false if it was rejected. */
      log(name, params = {}) {
        const spec = EVENTS[name];
        if (!spec) return false;
        const clean = {};
        for (const [k, v] of Object.entries(params)) {
          if (!spec[k]) continue;           // unknown parameter: dropped
          if (!spec[k](v)) return false;    // known parameter with a bad value: the whole event is rejected
          clean[k] = typeof v === 'number' ? Math.round(v * 1000) / 1000 : v;
        }
        if (name === 'session_start') session = now();
        events.push({ name, t: now(), ...(Object.keys(clean).length ? { params: clean } : {}) });
        if (events.length > MAX_EVENTS) events = events.slice(-MAX_EVENTS);
        persist();
        return true;
      },
      all: () => events.slice(),
      count: name => events.filter(e => e.name === name).length,
      sessionSeconds: () => (session === null ? 0 : (now() - session) / 1000),
      exportJson: () => JSON.stringify(events, null, 2),
      clear() { events = []; persist(); },
    };
  }

  const api = { EVENTS, create, MAX_EVENTS, STORAGE_KEY };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.GameAnalytics = api;
})(typeof window !== 'undefined' ? window : globalThis);
