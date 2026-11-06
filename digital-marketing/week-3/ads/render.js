const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2600, height: 2400 } });
  const out = path.join(__dirname, '..', 'exports', 'creatives'); fs.mkdirSync(out, { recursive: true });
  await p.goto('file://' + path.join(__dirname, 'creatives.html')); await p.evaluate(() => document.fonts.ready);
  for (const e of await p.$$('.b')) await e.screenshot({ path: path.join(out, (await e.getAttribute('id')) + '.png') });
  await p.screenshot({ path: path.join(__dirname, '..', 'exports', 'creatives-overview.png'), fullPage: true }); await b.close(); })();
