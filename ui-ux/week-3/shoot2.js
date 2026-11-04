const { chromium } = require('playwright'); const path = require('path');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1340, height: 900 } });
  for (const t of ['', 'dark']) { await p.goto('file://' + path.join(__dirname, 'pulse', 'components.html')); await p.evaluate(t => document.documentElement.dataset.theme = t, t); await p.waitForTimeout(500);
    await p.screenshot({ path: path.join(__dirname, 'exports', `components${t ? '-dark' : ''}.png`), fullPage: true }); }
  await b.close(); })();
