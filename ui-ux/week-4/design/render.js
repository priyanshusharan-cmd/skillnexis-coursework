const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
const ex = path.join(__dirname, '..', 'exports'); const errs = [];
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ deviceScaleFactor: 2, viewport: { width: 1800, height: 1000 } });
  p.on('pageerror', e => errs.push(e.message));
  for (const name of ['screens', 'wireframes', 'spec']) {
    const out = path.join(ex, name); fs.mkdirSync(out, { recursive: true });
    await p.goto('file://' + path.join(__dirname, name + '.html')); await p.evaluate(() => document.fonts.ready);
    for (const f of await p.$$('.frame')) { const l = await f.getAttribute('data-name');
      await f.screenshot({ path: path.join(out, l.replace(/[^\w]+/g, '-').replace(/^-|-$/g, '').toLowerCase() + '.png') }); }
    await p.screenshot({ path: path.join(ex, name + '-overview.png'), fullPage: true });
  }
  const ctx = await b.newContext({ viewport: { width: 520, height: 920 }, recordVideo: { dir: ex, size: { width: 520, height: 920 } } });
  const v = await ctx.newPage(); v.on('pageerror', e => errs.push('proto: ' + e.message));
  await v.goto('file://' + path.join(__dirname, 'prototype.html')); await v.evaluate(() => document.fonts.ready); await v.waitForTimeout(1200);
  const tap = async (frameId, sel) => { await v.click(`#w-${frameId} ${sel}`); await v.waitForTimeout(1100); };
  await tap('ob1', '.btn'); await tap('ob2', '.btn'); await tap('ob3', '.btn'); await tap('signin', '.btn');
  await tap('home', '.list-row'); await tap('group', '[aria-label="Add expense"]'); await tap('add', '[data-goto="split"]'); await tap('split', '.btn');
  await tap('add', '.btn'); await tap('saved', '[aria-label="Back"]'); await tap('home', '[data-goto="settle"]'); await tap('settle', '.btn'); await v.waitForTimeout(800);
  await tap('paid', '.btn'); await v.waitForTimeout(600);
  const vp = await v.video().path(); await ctx.close(); fs.renameSync(vp, path.join(ex, 'prototype-walkthrough.webm'));
  await b.close(); console.log(errs.length ? errs.join('\n') : 'no errors');
})();
