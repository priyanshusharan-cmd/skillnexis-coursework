// Screens at desktop/tablet/mobile, interaction states, and a video of the prototype flow (converted to GIF/MP4 after).
const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
const url = 'file://' + path.join(__dirname, 'pulse', 'index.html'); const out = path.join(__dirname, 'exports'); fs.mkdirSync(out, { recursive: true });
const errors = [];
(async () => {
  const b = await chromium.launch();
  const sizes = { desktop: [1440, 900], tablet: [834, 1112], mobile: [390, 844] };
  for (const [dev, [w, h]] of Object.entries(sizes)) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dev === 'desktop' ? 1 : 2 });
    p.on('pageerror', e => errors.push(dev + ': ' + e.message));
    for (const s of ['overview', 'customers', 'reports', 'settings']) {
      await p.goto(url + '#' + s); await p.waitForTimeout(1400);
      await p.screenshot({ path: path.join(out, `${dev}-${s}.png`), fullPage: dev !== 'desktop' ? false : true });
    }
    await p.goto(url + '#customers'); await p.waitForTimeout(600); await p.click('tbody tr.clickable'); await p.waitForTimeout(700);
    await p.screenshot({ path: path.join(out, `${dev}-customer-drawer.png`) });
    if (dev === 'desktop') {
      await p.keyboard.press('Escape'); await p.goto(url + '#settings'); await p.waitForTimeout(800); await p.click('#open-modal'); await p.waitForTimeout(600);
      await p.screenshot({ path: path.join(out, 'desktop-modal.png') });
      await p.keyboard.press('Escape'); await p.evaluate(() => document.documentElement.dataset.theme = 'dark'); await p.goto(url + '#overview');
      await p.evaluate(() => document.documentElement.dataset.theme = 'dark'); await p.waitForTimeout(1400);
      await p.screenshot({ path: path.join(out, 'desktop-overview-dark.png'), fullPage: true });
      await p.evaluate(() => document.documentElement.dataset.theme = '');
      await p.goto(url + '#customers'); await p.waitForTimeout(500); await p.fill('#filter', 'zzz'); await p.waitForTimeout(400);
      await p.screenshot({ path: path.join(out, 'desktop-empty-state.png') });
    }
    await p.close();
  }
  // recorded walkthrough
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 }, recordVideo: { dir: out, size: { width: 1280, height: 800 } } });
  const p = await ctx.newPage(); p.on('pageerror', e => errors.push('video: ' + e.message));
  await p.goto(url + '#overview'); await p.waitForTimeout(1800);
  await p.click('.seg button[data-range="7d"]'); await p.waitForTimeout(600);
  await p.click('.side [data-go="customers"]'); await p.waitForTimeout(900);
  await p.click('th button[data-sort="orders"]'); await p.waitForTimeout(700);
  await p.click('.tabs button[data-status="At risk"]'); await p.waitForTimeout(700);
  await p.click('tbody tr.clickable'); await p.waitForTimeout(1300);
  await p.click('.drawer .btn-primary'); await p.waitForTimeout(1500);
  await p.click('.side [data-go="reports"]'); await p.waitForTimeout(1800);
  await p.click('.side [data-go="settings"]'); await p.waitForTimeout(900);
  await p.click('.switch >> nth=2'); await p.waitForTimeout(900);
  await p.click('#open-modal'); await p.waitForTimeout(1000); await p.click('#confirm-delete'); await p.waitForTimeout(2200);
  await p.click('#theme'); await p.click('.side [data-go="overview"]'); await p.waitForTimeout(2000);
  const v = await p.video().path(); await ctx.close(); fs.renameSync(v, path.join(out, 'prototype-walkthrough.webm'));
  await b.close();
  console.log(errors.length ? 'ERRORS:\n' + errors.join('\n') : 'no page errors');
})();
