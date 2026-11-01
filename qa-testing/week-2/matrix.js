// Web test matrix: the same checks run in 2 browsers x 2 viewports against the app under test.
// Start the app first (see README.md). Usage: node matrix.js   (BASE=http://127.0.0.1:5173 to change the address)
const fs = require('node:fs');
const path = require('node:path');
const { chromium, devices } = require('playwright-core');

const BASE = process.env.BASE || 'http://127.0.0.1:5173';
const RUN = Date.now().toString(36);
const out = path.join(__dirname, 'results');
fs.mkdirSync(out, { recursive: true });

const BROWSERS = [{ name: 'Google Chrome', channel: 'chrome' }, { name: 'Microsoft Edge', channel: 'msedge' }];
const VIEWPORTS = [
  { name: 'Desktop 1280x800', options: { viewport: { width: 1280, height: 800 } } },
  { name: 'Mobile 390x844', options: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 } },
];

async function runChecks(page, tag) {
  const results = [];
  const check = async (name, fn) => {
    try { const note = await fn(); results.push({ check: name, status: 'PASS', note: note || '' }); }
    catch (e) { results.push({ check: name, status: 'FAIL', note: e.message.split('\n')[0] }); }
  };
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => { if (r.status() >= 400) errors.push(`HTTP ${r.status()} for ${new URL(r.url()).pathname}`); });
  const need = (cond, msg) => { if (!cond) throw new Error(msg); };

  await check('1. Unauthenticated visit to / redirects to the login page', async () => {
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    need(page.url().endsWith('/login'), 'landed on ' + page.url());
  });
  await check('2. Registration form rejects an empty submit with a message', async () => {
    await page.goto(BASE + '/register');
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.getByRole('alert').waitFor({ timeout: 3000 });
    return await page.getByRole('alert').innerText();
  });
  await check('3. Short password is rejected before submitting', async () => {
    await page.getByLabel('Name').fill('QA Tester');
    await page.getByLabel('Email').fill(`qa-${RUN}-${tag}@example.com`);
    await page.getByLabel('Password').fill('short');
    await page.getByRole('button', { name: 'Sign up' }).click();
    const t = await page.getByRole('alert').innerText();
    need(/8 characters/.test(t), 'message was: ' + t);
    return t;
  });
  await check('4. Valid registration signs the user in and shows the task page', async () => {
    await page.getByLabel('Password').fill('a-long-enough-pass');
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.getByRole('heading', { name: 'My tasks' }).waitFor({ timeout: 5000 });
  });
  await check('5. A task can be added and appears in the list', async () => {
    await page.getByLabel('New task').fill('Check the matrix');
    await page.getByRole('button', { name: 'Add', exact: true }).click();
    await page.getByText('Check the matrix').waitFor({ timeout: 3000 });
  });
  await check('6. A task can be ticked and the remaining count updates', async () => {
    // click() rather than check(): the app updates the box after the server replies, not instantly.
    await page.getByLabel('Mark Check the matrix done').click();
    await page.getByText('0 left').waitFor({ timeout: 3000 });
  });
  await check('7. No horizontal scrolling at this width', async () => {
    const o = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth }));
    need(o.sw <= o.iw, `page is ${o.sw}px wide in a ${o.iw}px viewport`);
    return `${o.sw}px content in ${o.iw}px viewport`;
  });
  await check('8. Interactive controls are at least 24 px (WCAG 2.2 minimum target size)', async () => {
    const small = await page.evaluate(() => [...document.querySelectorAll('button, a, input:not([type=hidden])')].filter(e => e.offsetParent !== null)
      .map(e => ({ label: e.getAttribute('aria-label') || e.innerText || e.type, w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }))
      .filter(e => Math.min(e.w, e.h) < 24));
    need(small.length === 0, `${small.length} control(s) under 24 px: ` + small.map(s => `"${s.label}" ${s.w}x${s.h}`).join('; '));
  });
  await check('9. Controls reach the 44 px touch-friendly size (best practice; 24 px checkboxes are an accepted risk)', async () => {
    const all = await page.evaluate(() => [...document.querySelectorAll('button, a, input:not([type=hidden])')].filter(e => e.offsetParent !== null)
      .map(e => ({ label: (e.getAttribute('aria-label') || e.innerText || e.type).slice(0, 18), type: e.type, h: Math.round(Math.min(e.getBoundingClientRect().width, e.getBoundingClientRect().height)) })).filter(e => e.h < 44));
    const boxes = all.filter(e => e.type === 'checkbox' && e.h >= 24);   // meets WCAG 2.2 AA (24 px), below the 44 px AAA guideline
    const bad = all.filter(e => !boxes.includes(e));
    need(bad.length === 0, `${bad.length} control(s) under 44 px: ` + bad.map(s => `"${s.label}" ${s.h}px`).join(', '));
    return boxes.length ? `accepted risk: ${boxes.length} checkbox(es) at ${boxes[0].h} px (meets the 24 px minimum)` : '';
  });
  await page.screenshot({ path: path.join(out, `${tag}-tasks.png`), fullPage: true });
  await check('10. Log out returns to the login page and protects the task page', async () => {
    await page.getByRole('button', { name: 'Log out' }).click();
    await page.waitForURL('**/login');
    await page.goto(BASE + '/');
    await page.waitForURL('**/login');
  });
  await check('11. No console errors or uncaught exceptions during the session', async () => {
    need(errors.length === 0, [...new Set(errors)].slice(0, 3).join(' | '));
  });
  return results;
}

(async () => {
  const matrix = [];
  for (const b of BROWSERS) {
    const browser = await chromium.launch({ channel: b.channel, headless: true });
    for (const v of VIEWPORTS) {
      const ctx = await browser.newContext(v.options);
      const page = await ctx.newPage();
      const tag = `${b.channel}-${v.name.split(' ')[0].toLowerCase()}`;
      const results = await runChecks(page, tag);
      matrix.push({ browser: b.name, version: browser.version(), viewport: v.name, results });
      await ctx.close();
    }
    await browser.close();
  }
  fs.writeFileSync(path.join(out, 'matrix.json'), JSON.stringify(matrix, null, 2));
  const names = matrix[0].results.map(r => r.check);
  let md = '| Check | ' + matrix.map(m => `${m.browser.replace('Google ', '').replace('Microsoft ', '')} ${m.viewport.split(' ')[0]}`).join(' | ') + ' |\n|---|' + matrix.map(() => '---|').join('') + '\n';
  names.forEach((n, i) => { md += `| ${n} | ` + matrix.map(m => m.results[i].status).join(' | ') + ' |\n'; });
  fs.writeFileSync(path.join(out, 'matrix.md'), md);
  console.log(md);
  for (const m of matrix) for (const r of m.results) if (r.status === 'FAIL') console.log(`FAIL [${m.browser} / ${m.viewport}] ${r.check}\n     ${r.note}`);
  console.log('\nBrowser versions:', matrix.filter((m, i) => i % 2 === 0).map(m => `${m.browser} ${m.version}`).join(', '));
})();
