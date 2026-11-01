// API practice: sends GET, POST, PUT/PATCH and DELETE requests to (1) the local app's API and (2) a public practice API,
// and records expected versus actual. Usage: node api-practice.js   (API=http://127.0.0.1:4000 to change the local address)
const fs = require('node:fs');
const path = require('node:path');

const API = process.env.API || 'http://127.0.0.1:4000';
const PUBLIC = 'https://jsonplaceholder.typicode.com';
const RUN = Date.now().toString(36);
const rows = [];

async function call(group, label, method, url, { token, body, raw, expect, expectBody }) {
  const headers = { ...(body !== undefined && !raw ? { 'Content-Type': 'application/json' } : {}), ...(raw ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  let status, text = '', res;
  try {
    res = await fetch(url, { method, headers, body: raw !== undefined ? raw : body !== undefined ? JSON.stringify(body) : undefined });
    status = res.status;
    text = await res.text();
  } catch (e) { status = 'NETWORK ERROR'; text = e.message; }
  let json = null; try { json = JSON.parse(text); } catch { /* not JSON */ }
  let ok = status === expect;
  let note = '';
  if (ok && expectBody) { try { ok = expectBody(json); if (!ok) note = 'body check failed'; } catch { ok = false; note = 'body check threw'; } }
  rows.push({ group, label, request: `${method} ${url.replace(API, '').replace(PUBLIC, '')}`, expected: expect, actual: status, result: ok ? 'PASS' : 'FAIL', note: note || (ok ? '' : text.slice(0, 100)) });
  return { status, json, res };
}

(async () => {
  // ---------- Local app API ----------
  const email = `api-${RUN}@example.com`;
  const reg = await call('local', 'Register a new user', 'POST', `${API}/api/auth/register`, { body: { name: 'API Tester', email, password: 'a-long-enough-pass' }, expect: 201, expectBody: j => !!j.token && !j.user.passwordHash });
  const token = reg.json && reg.json.token;
  await call('local', 'Register the same email again (negative)', 'POST', `${API}/api/auth/register`, { body: { name: 'Dup', email, password: 'a-long-enough-pass' }, expect: 409 });
  await call('local', 'Register with a 7-character password (negative)', 'POST', `${API}/api/auth/register`, { body: { name: 'X', email: `s-${RUN}@example.com`, password: '1234567' }, expect: 400 });
  await call('local', 'Log in with the right password', 'POST', `${API}/api/auth/login`, { body: { email, password: 'a-long-enough-pass' }, expect: 200, expectBody: j => !!j.token });
  await call('local', 'Log in with the wrong password (negative)', 'POST', `${API}/api/auth/login`, { body: { email, password: 'wrong-password-here' }, expect: 401 });
  await call('local', 'List tasks with no token (negative)', 'GET', `${API}/api/tasks`, { expect: 401 });
  const created = await call('local', 'Create a task', 'POST', `${API}/api/tasks`, { token, body: { title: 'Practice' }, expect: 201, expectBody: j => j.done === false && j.title === 'Practice' });
  const id = created.json && created.json._id;
  await call('local', 'List tasks', 'GET', `${API}/api/tasks`, { token, expect: 200, expectBody: j => Array.isArray(j) && j.length === 1 });
  await call('local', 'Update the task (PUT)', 'PUT', `${API}/api/tasks/${id}`, { token, body: { done: true }, expect: 200, expectBody: j => j.done === true && j.title === 'Practice' });
  await call('local', 'Create a task with an empty title (negative)', 'POST', `${API}/api/tasks`, { token, body: { title: '   ' }, expect: 400 });
  await call('local', 'Get a task with a malformed id (negative)', 'GET', `${API}/api/tasks/not-an-id`, { token, expect: 400 });
  await call('local', 'Send malformed JSON (negative)', 'POST', `${API}/api/tasks`, { token, raw: '{"title": ', expect: 400 });
  await call('local', 'Send an oversized body of about 200 KB (negative)', 'POST', `${API}/api/tasks`, { token, body: { title: 'x'.repeat(200000) }, expect: 413 });
  await call('local', 'Delete the task', 'DELETE', `${API}/api/tasks/${id}`, { token, expect: 204 });
  await call('local', 'Delete the same task again (negative)', 'DELETE', `${API}/api/tasks/${id}`, { token, expect: 404 });
  const hdr = await fetch(`${API}/api/health`);
  rows.push({ group: 'local', label: 'Security headers are present (helmet)', request: 'GET /api/health', expected: 'x-content-type-options: nosniff', actual: hdr.headers.get('x-content-type-options') || 'missing', result: hdr.headers.get('x-content-type-options') === 'nosniff' ? 'PASS' : 'FAIL', note: '' });

  // ---------- Public practice API (JSONPlaceholder fakes writes: it replies as if saved but stores nothing) ----------
  await call('public', 'GET a post', 'GET', `${PUBLIC}/posts/1`, { expect: 200, expectBody: j => j.id === 1 && typeof j.title === 'string' });
  await call('public', 'GET a post that does not exist (negative)', 'GET', `${PUBLIC}/posts/99999`, { expect: 404 });
  await call('public', 'POST a new post', 'POST', `${PUBLIC}/posts`, { body: { title: 'qa', body: 'practice', userId: 1 }, expect: 201, expectBody: j => j.id === 101 && j.title === 'qa' });
  await call('public', 'PUT replaces a post', 'PUT', `${PUBLIC}/posts/1`, { body: { id: 1, title: 'replaced', body: 'b', userId: 1 }, expect: 200, expectBody: j => j.title === 'replaced' });
  await call('public', 'PATCH changes one field', 'PATCH', `${PUBLIC}/posts/1`, { body: { title: 'patched' }, expect: 200, expectBody: j => j.title === 'patched' && j.userId === 1 });
  await call('public', 'DELETE a post', 'DELETE', `${PUBLIC}/posts/1`, { expect: 200 });

  const out = path.join(__dirname, 'results');
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'api-results.json'), JSON.stringify(rows, null, 2));
  let md = '| # | API | Test | Request | Expected | Actual | Result |\n|---|---|---|---|---|---|---|\n';
  rows.forEach((r, i) => { md += `| ${i + 1} | ${r.group} | ${r.label} | \`${r.request}\` | ${r.expected} | ${r.actual} | ${r.result} |\n`; });
  fs.writeFileSync(path.join(out, 'api-results.md'), md);
  console.log(md);
  const bad = rows.filter(r => r.result === 'FAIL');
  console.log(`${rows.length - bad.length} of ${rows.length} passed.`);
  bad.forEach(r => console.log(`FAIL: ${r.label}: expected ${r.expected}, got ${r.actual}. ${r.note}`));
})();
