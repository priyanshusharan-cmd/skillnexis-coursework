// Renders every phone frame to exports/<page>/<NN-name>.png at 2x, plus one overview sheet per page and the style guide.
//   node design/render.js
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 2, viewport: { width: 1800, height: 1000 } });
  for (const name of ['wireframes', 'circle-hifi', 'haat']) {
    const out = path.join(__dirname, '..', 'exports', name); fs.mkdirSync(out, { recursive: true });
    await p.goto('file://' + path.join(__dirname, name + '.html')); await p.evaluate(() => document.fonts.ready);
    const frames = await p.$$('.frame');
    for (const f of frames) {
      const label = await f.getAttribute('data-name');
      await f.screenshot({ path: path.join(out, label.replace(/[^\w]+/g, '-').replace(/^-|-$/g, '').toLowerCase() + '.png') });
    }
    await p.screenshot({ path: path.join(__dirname, '..', 'exports', name + '-overview.png'), fullPage: true });
    console.log(name, frames.length, 'frames');
  }
  await p.setViewportSize({ width: 1200, height: 900 });
  await p.goto('file://' + path.join(__dirname, 'style-guide.html')); await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(__dirname, '..', 'exports', 'style-guide.png'), fullPage: true });
  await b.close();
})();
