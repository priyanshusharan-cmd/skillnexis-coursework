const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2400, height: 2000 } });
  const out = path.join(__dirname, '..', 'exports', 'posts'); fs.mkdirSync(out, { recursive: true });
  await p.goto('file://' + path.join(__dirname, 'posts.html')); await p.evaluate(() => document.fonts.ready);
  const els = await p.$$('.a'); for (const e of els) { await e.screenshot({ path: path.join(out, (await e.getAttribute('id')) + '.png') }); }
  // contact sheet
  const files = fs.readdirSync(out).filter(f => f.endsWith('.png')).sort();
  await p.setContent(`<body style="margin:0;background:#efe7dc;display:flex;flex-wrap:wrap;gap:16px;padding:16px;width:2000px">${files.map(f => `<img src="file://${out}/${f}" style="height:${f.match(/^(09|1[0-5])/) ? 560 : 400}px">`).join('')}</body>`);
  await p.waitForTimeout(800); await p.screenshot({ path: path.join(__dirname, '..', 'exports', 'campaign-overview.png'), fullPage: true });
  console.log(els.length, 'assets'); await b.close(); })();
