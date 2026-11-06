// Runs Code.gs unchanged in Node against in-memory mocks of SpreadsheetApp, MailApp, LockService, Utilities and
// ScriptApp, replaying 8 form submissions (valid, duplicate, bad email, missing name, messy casing, concurrent).
//   node test_harness.js -> results/harness-output.json, results/sheets-after.md
const fs = require('fs');
class Range { constructor(sh, r, c, nr = 1, nc = 1) { Object.assign(this, { sh, r, c, nr, nc }); }
  getValues() { const o = []; for (let i = 0; i < this.nr; i++) { const row = []; for (let j = 0; j < this.nc; j++) row.push(((this.sh.d[this.r - 1 + i] || [])[this.c - 1 + j]) ?? ''); o.push(row); } return o; }
  getValue() { return this.getValues()[0][0]; }
  setValues(v) { v.forEach((row, i) => row.forEach((x, j) => { const R = this.r - 1 + i; this.sh.d[R] = this.sh.d[R] || []; this.sh.d[R][this.c - 1 + j] = x; })); return this; }
  setValue(x) { return this.setValues([[x]]); } getSheet() { return this.sh; } getRow() { return this.r; } }
class Sheet { constructor(name, d = []) { this.name = name; this.d = d; }
  getRange(r, c, nr, nc) { return new Range(this, r, c, nr, nc); } getLastRow() { return this.d.length; } getLastColumn() { return Math.max(0, ...this.d.map(r => r.length)); }
  appendRow(r) { this.d.push(r.slice()); } setFrozenRows() {} getDataRange() { return this.getRange(1, 1, this.getLastRow(), this.getLastColumn()); } }
const sheets = {}; const ss = { getSheetByName: n => sheets[n] || null, insertSheet: n => (sheets[n] = new Sheet(n)) };
const sent = [];
Object.assign(global, { SpreadsheetApp: { getActive: () => ss }, MailApp: { sendEmail: m => sent.push(m) }, LockService: { getScriptLock: () => ({ waitLock() {}, releaseLock() {} }) },
  ScriptApp: { getProjectTriggers: () => [], newTrigger: () => ({ forSpreadsheet: () => ({ onFormSubmit: () => ({ create() {} }) }) }) },
  Utilities: { formatDate: (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` } });
const vm = require('vm'); const mod = { exports: {} }; vm.runInThisContext('(function(module){' + fs.readFileSync(__dirname + '/Code.gs', 'utf8') + '\n})')(mod); const gs = mod.exports;
const resp = sheets['Form responses 1'] = new Sheet('Form responses 1', [['Timestamp', 'Full name', 'Email address', 'Coding experience']]);
const subs = [
  [new Date('2026-11-02T10:15:00'), 'aarav mehta', 'Aarav.Mehta@Example.com ', 'Never coded'],
  [new Date('2026-11-03T09:00:00'), 'Meera  Iyer', 'meera@example.org', 'Some school Python'],
  [new Date('2026-11-04T18:30:00'), 'Rohan Das', 'rohan@example', 'A little'],
  [new Date('2026-11-05T08:05:00'), '', 'nobody@example.com', 'none'],
  [new Date('2026-11-05T21:40:00'), 'AARAV MEHTA', 'aarav.mehta@example.com', 'some experience now'],
  [new Date('2026-11-06T07:20:00'), 'Ananya Pillai', 'ananya.pillai@example.net', 'I build websites'],
  [new Date('2026-11-06T07:20:00'), 'Vikram Rao', 'vikram@example.com', 'complete beginner'],
  [new Date('2026-11-09T12:00:00'), 'meera iyer', 'MEERA@example.org', 'some'] ];
gs.setup(); const results = [];
for (const s of subs) { resp.appendRow(s); results.push(gs.onFormSubmit({ range: resp.getRange(resp.getLastRow(), 1, 1, 4) })); }
const st = sheets['Students'].d;
const checks = { students: st.length - 1, emails_sent: sent.length, invalid: results.filter(r => r.status === 'INVALID').length, duplicates_updated: results.filter(r => r.status === 'DUPLICATE-UPDATED').length,
  unique_emails: new Set(st.slice(1).map(r => r[0])).size === st.length - 1, every_response_has_status: resp.d.slice(1).every(r => r[4]) };
fs.mkdirSync('results', { recursive: true });
fs.writeFileSync('results/harness-output.json', JSON.stringify({ checks, results, emails: sent.map(m => ({ to: m.to, subject: m.subject })) }, null, 1));
const md = t => '| ' + t[0].join(' | ') + ' |\n|' + t[0].map(() => '---').join('|') + '|\n' + t.slice(1).map(r => '| ' + r.map(x => x instanceof Date ? x.toISOString().slice(0, 16).replace('T', ' ') : x).join(' | ') + ' |').join('\n');
fs.writeFileSync('results/sheets-after.md', `# Sheets after 8 submissions\n\n## Form responses 1\n\n${md(resp.d)}\n\n## Students\n\n${md(st)}\n\n## Welcome emails sent\n\n${sent.map(m => `* ${m.to}: ${m.subject}`).join('\n')}\n`);
console.log(checks); if (!(checks.students === 4 && checks.invalid === 2 && checks.duplicates_updated === 2 && checks.unique_emails && checks.every_response_has_status)) { console.error('CHECK FAILED'); process.exit(1); }
