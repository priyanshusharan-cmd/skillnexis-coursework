// Screen-records the Hisaab prototype for each tutorial scene, timing taps to the voiceover sentences.
// Output: build/rec_<scene>.webm + build/rec_offsets.json (seconds to trim from the start of each recording)
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const B = path.join(__dirname, '..', 'build'); const T = JSON.parse(fs.readFileSync(path.join(B, 'timing.json')));
const PROTO = 'file://' + path.resolve(__dirname, '../../../ui-ux/week-4/design/prototype.html');
const S = (id, i) => T[id].subs[Math.min(i, T[id].subs.length - 1)][0];
// [time (s) or [sentenceIndex, delay], action]  actions: 'go:<screen>' instant jump, 'tap:<screen>|<selector>' ripple + click
const PLAN = {
  onboard: { start: 'ob1', steps: [[[1, 0.2], 'tap:ob1|.btn'], [[1, 3.2], 'tap:ob2|.btn'], [[3, 0.2], 'tap:ob3|.btn']] },
  home: { start: 'home', steps: [] },
  add: { start: 'home', steps: [[[0, 1.2], 'tap:home|.list-row'], [[0, 3.6], 'tap:group|[aria-label="Add expense"]'], [[3, 0.6], 'tap:add|[data-goto="split"]'], [[5, 3.2], 'tap:split|.btn'], [[5, 5.5], 'tap:add|.btn']] },
  saved: { start: 'saved', steps: [[[1, 0.3], 'go:group'], [[1, 1.4], 'tap:group|.card'], ] },
  settle: { start: 'home', steps: [[[1, 0.2], 'tap:home|[data-goto="settle"]'], [[2, 2.6], 'tap:settle|.btn']] },
  extras: { start: 'home', steps: [[[1, 0.2], 'tap:home|[data-goto="remind"]'], [[2, 0.2], 'go:insights'], [[3, 0.3], 'go:home']] },
};
const CSS = `body{background:radial-gradient(circle at 30% 40%,#14524C 0%,#0B3B37 55%,#072927 100%)!important}.hint{display:none!important}
.stage{transform:scale(1.13);transform-origin:center;margin-left:-560px}
.ripple{position:fixed;width:70px;height:70px;margin:-35px 0 0 -35px;border-radius:50%;background:rgba(255,255,255,.55);border:3px solid #fff;pointer-events:none;z-index:99;animation:rp .6s ease-out forwards}
@keyframes rp{from{transform:scale(.4);opacity:1}to{transform:scale(1.4);opacity:0}}`;
(async () => {
  const b = await chromium.launch(); const offsets = {};
  for (const [id, plan] of Object.entries(PLAN)) {
    const dur = T[id].dur; const t0 = Date.now();
    const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: B, size: { width: 1920, height: 1080 } } });
    const p = await ctx.newPage(); await p.goto(PROTO + '#' + plan.start); await p.addStyleTag({ content: CSS }); await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(700); const ready = (Date.now() - t0) / 1000; offsets[id] = ready;
    const start = Date.now(); const at = s => p.waitForTimeout(Math.max(0, s * 1000 - (Date.now() - start)));
    for (const [when, act] of plan.steps) {
      const s = Array.isArray(when) ? S(id, when[0]) + when[1] : when; await at(s);
      if (act.startsWith('go:')) await p.evaluate(x => show(x, 'fwd'), act.slice(3));
      else { const [scr, sel] = act.slice(4).split('|');
        await p.evaluate(([scr, sel]) => { const el = document.querySelector('#w-' + scr + ' ' + sel); const r = el.getBoundingClientRect();
          const d = document.createElement('div'); d.className = 'ripple'; d.style.left = (r.left + r.width / 2) + 'px'; d.style.top = (r.top + r.height / 2) + 'px'; document.body.appendChild(d);
          setTimeout(() => { el.click(); d.remove(); }, 380); }, [scr, sel]); }
    }
    await at(dur + 0.3); const v = await p.video().path(); await ctx.close(); fs.renameSync(v, path.join(B, `rec_${id}.webm`)); console.log(id, dur.toFixed(1), 'offset', ready.toFixed(2));
  }
  fs.writeFileSync(path.join(B, 'rec_offsets.json'), JSON.stringify(offsets)); await b.close();
})();
