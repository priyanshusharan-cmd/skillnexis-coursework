// Prioritized web + API regression pack. Run with: node --test regression.test.js (app must be running; see README.md)
//   P1 = must pass before any release (sign-in, data protection, core task flow)
//   P2 = important features
//   P3 = polish and known minor issues
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { after, before, describe, it } = require('node:test');
const { chromium } = require('playwright-core');

const BASE = process.env.BASE || 'http://127.0.0.1:5173';
const API = process.env.API || 'http://127.0.0.1:4000';
const RUN = Date.now().toString(36);
const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(32)]);

const http = async (method, p, { token, body, form } = {}) => {
  const res = await fetch(API + p, { method, headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: form || (body ? JSON.stringify(body) : undefined) });
  const text = await res.text();
  return { status: res.status, body: text ? JSON.parse(text) : null, headers: res.headers };
};

let token, taskId, browser;
const email = `reg-${RUN}@example.com`;

before(async () => {
  const r = await http('POST', '/api/auth/register', { body: { name: 'Regression', email, password: 'regression-pass-1' } });
  token = r.body.token;
  browser = await chromium.launch({ channel: 'chrome', headless: true });
});
after(async () => { await browser.close(); });

describe('P1: sign-in and data protection', () => {
  it('P1-API-01 register returns a token and never exposes the password hash', async () => {
    const r = await http('POST', '/api/auth/register', { body: { name: 'R2', email: `reg2-${RUN}@example.com`, password: 'regression-pass-2' } });
    assert.equal(r.status, 201); assert.ok(r.body.token); assert.equal(r.body.user.passwordHash, undefined);
  });
  it('P1-API-02 duplicate email is refused (409)', async () => assert.equal((await http('POST', '/api/auth/register', { body: { name: 'D', email, password: 'regression-pass-1' } })).status, 409));
  it('P1-API-03 login: right password 200, wrong password 401 with the same message as an unknown user', async () => {
    assert.equal((await http('POST', '/api/auth/login', { body: { email, password: 'regression-pass-1' } })).status, 200);
    const wrong = await http('POST', '/api/auth/login', { body: { email, password: 'not-the-password' } });
    const unknown = await http('POST', '/api/auth/login', { body: { email: `nobody-${RUN}@example.com`, password: 'not-the-password' } });
    assert.equal(wrong.status, 401); assert.deepEqual(wrong.body, unknown.body);
  });
  it('P1-API-04 every protected endpoint refuses a missing or forged token (401)', async () => {
    for (const p of ['/api/tasks', '/api/notes', '/api/uploads']) {
      assert.equal((await http('GET', p)).status, 401, p + ' without token');
      assert.equal((await http('GET', p, { token: 'a.b.c' })).status, 401, p + ' with forged token');
    }
  });
  it("P1-API-05 one user cannot read another user's task (404)", async () => {
    const t = await http('POST', '/api/tasks', { token, body: { title: 'private' } });
    const other = (await http('POST', '/api/auth/register', { body: { name: 'O', email: `other-${RUN}@example.com`, password: 'regression-pass-3' } })).body.token;
    assert.equal((await http('GET', `/api/tasks/${t.body._id}`, { token: other })).status, 404);
    assert.equal((await http('DELETE', `/api/tasks/${t.body._id}`, { token: other })).status, 404);
  });
  it('P1-UI-01 an unauthenticated visitor is sent to the login page', async () => {
    const page = await browser.newPage();
    await page.goto(BASE + '/');
    await page.waitForURL('**/login');
    await page.close();
  });
  it('P1-UI-02 register, add a task, reload and the task is still there', async () => {
    const page = await browser.newPage();
    await page.goto(BASE + '/register');
    await page.getByLabel('Name').fill('UI User');
    await page.getByLabel('Email').fill(`ui-${RUN}@example.com`);
    await page.getByLabel('Password').fill('ui-regression-pass');
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.getByRole('heading', { name: 'My tasks' }).waitFor();
    await page.getByLabel('New task').fill('Survives a reload');
    await page.getByRole('button', { name: 'Add', exact: true }).click();
    await page.getByText('Survives a reload').waitFor();
    await page.reload();
    await page.getByText('Survives a reload').waitFor({ timeout: 5000 });
    await page.close();
  });
});

describe('P2: task and upload features', () => {
  it('P2-API-01 create a task (201) with done=false, then list it', async () => {
    const r = await http('POST', '/api/tasks', { token, body: { title: 'Regression task' } });
    assert.equal(r.status, 201); assert.equal(r.body.done, false); taskId = r.body._id;
    assert.ok((await http('GET', '/api/tasks', { token })).body.some(t => t._id === taskId));
  });
  it('P2-API-02 update (PUT) changes only the sent field', async () => {
    const r = await http('PUT', `/api/tasks/${taskId}`, { token, body: { done: true } });
    assert.equal(r.status, 200); assert.equal(r.body.done, true); assert.equal(r.body.title, 'Regression task');
  });
  it('P2-API-03 an empty title (400) and a malformed id (400) are rejected', async () => {
    assert.equal((await http('POST', '/api/tasks', { token, body: { title: '  ' } })).status, 400);
    assert.equal((await http('GET', '/api/tasks/not-an-id', { token })).status, 400);
  });
  it('P2-API-04 a client cannot set the owner of a task', async () => {
    const r = await http('POST', '/api/tasks', { token, body: { title: 'owner test', owner: '000000000000000000000000' } });
    assert.equal(r.status, 201);
    assert.ok((await http('GET', '/api/tasks', { token })).body.some(t => t._id === r.body._id), 'the task still belongs to the caller');
  });
  it('P2-API-05 delete returns 204, and deleting again returns 404', async () => {
    assert.equal((await http('DELETE', `/api/tasks/${taskId}`, { token })).status, 204);
    assert.equal((await http('DELETE', `/api/tasks/${taskId}`, { token })).status, 404);
  });
  it('P2-API-06 malformed JSON gets 400 and an oversized body gets 413 (these were 500 before the fix, DEF-1)', async () => {
    const raw = await fetch(API + '/api/tasks', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: '{"title": ' });
    assert.equal(raw.status, 400);
    assert.equal((await http('POST', '/api/tasks', { token, body: { title: 'x'.repeat(200000) } })).status, 413);
  });
  it('P2-API-07 upload accepts a PNG and rejects a fake image', async () => {
    const send = (data, type, name) => { const f = new FormData(); f.append('image', new Blob([data], { type }), name); return http('POST', '/api/uploads', { token, form: f }); };
    assert.equal((await send(PNG, 'image/png', 'ok.png')).status, 201);
    assert.equal((await send(Buffer.from('not a png'), 'image/png', 'fake.png')).status, 400);
    assert.equal((await send('<svg/>', 'image/svg+xml', 'x.svg')).status, 400);
  });
  it('P2-API-08 passwords of 72 bytes are accepted, 73 bytes are refused (DEF-3)', async () => {
    assert.equal((await http('POST', '/api/auth/register', { body: { name: 'L', email: `l72-${RUN}@example.com`, password: 'a'.repeat(72) } })).status, 201);
    assert.equal((await http('POST', '/api/auth/register', { body: { name: 'L', email: `l73-${RUN}@example.com`, password: 'a'.repeat(73) } })).status, 400);
  });
  it('P2-UI-01 filters show the right tasks', async () => {
    const page = await browser.newPage();
    await page.goto(BASE + '/register');
    await page.getByLabel('Name').fill('Filter User');
    await page.getByLabel('Email').fill(`flt-${RUN}@example.com`);
    await page.getByLabel('Password').fill('filter-regression-pass');
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.getByRole('heading', { name: 'My tasks' }).waitFor();
    for (const t of ['one', 'two']) { await page.getByLabel('New task').fill(t); await page.getByRole('button', { name: 'Add', exact: true }).click(); await page.getByText(t, { exact: true }).waitFor(); }
    await page.getByLabel('Mark one done').click();
    await page.getByText('1 left').waitFor();
    await page.getByRole('button', { name: 'done', exact: true }).click();
    assert.equal(await page.locator('li').count(), 1);
    await page.getByRole('button', { name: 'active', exact: true }).click();
    assert.equal(await page.locator('li').count(), 1);
    await page.close();
  });
});

describe('P3: polish and known issues', () => {
  it('P3-API-01 security headers are set', async () => {
    const h = (await http('GET', '/api/health')).headers;
    assert.equal(h.get('x-content-type-options'), 'nosniff');
    assert.ok(h.get('content-security-policy') || h.get('strict-transport-security'), 'at least one of CSP or HSTS is present');
  });
  it('P3-UI-01 no horizontal scrolling on a phone-sized screen', async () => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    await page.goto(BASE + '/login');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await ctx.close();
  });
  it('P3-UI-02 the page declares an icon, so browsers do not request a missing /favicon.ico (DEF-2)', async () => {
    const html = await (await fetch(BASE + '/')).text();
    assert.match(html, /<link[^>]+rel="icon"/);
  });
  it('P3-UI-03 interactive controls are at least 24 px (WCAG 2.2 target size, DEF-4)', async () => {
    const page = await browser.newPage();
    await page.goto(BASE + '/register');
    await page.getByLabel('Name').fill('A11y');
    await page.getByLabel('Email').fill(`a11y-${RUN}@example.com`);
    await page.getByLabel('Password').fill('a11y-regression-pass');
    await page.getByRole('button', { name: 'Sign up' }).click();
    await page.getByRole('heading', { name: 'My tasks' }).waitFor();
    const small = await page.evaluate(() => [...document.querySelectorAll('button, a, input')].filter(e => e.offsetParent && Math.min(e.getBoundingClientRect().width, e.getBoundingClientRect().height) < 24).length);
    await page.close();
    assert.equal(small, 0);
  });
});
