/**
 * Google Sheets workflow for form submissions (Google Apps Script, free with any Google account).
 * A Google Form ("Course sign-up") writes rows to the sheet "Form responses 1". On every submission this script:
 *   1. validates and normalises the row (trims, lower-cases email, checks the email format and required fields)
 *   2. de-duplicates: an email already in "Students" updates that student instead of adding a second one
 *   3. enriches: assigns a cohort (the Monday of the sign-up week) and a track from the experience answer
 *   4. writes the student to "Students" and a status back on the response row (OK / DUPLICATE-UPDATED / INVALID: reason)
 *   5. emails a personalised welcome (MailApp, within the free daily quota) and logs it in "Log"
 * Setup: Extensions -> Apps Script, paste this file, run setup() once (it creates the installable onFormSubmit trigger).
 */
var CFG = { responses: 'Form responses 1', students: 'Students', log: 'Log', sendEmail: true,
            headers: ['Email', 'Name', 'Track', 'Cohort', 'Signed up', 'Updated', 'Submissions'] };

function setup() {
  var ss = SpreadsheetApp.getActive();
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'onFormSubmit') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('onFormSubmit').forSpreadsheet(ss).onFormSubmit().create();
  sheet_(CFG.students, CFG.headers); sheet_(CFG.log, ['Time', 'Email', 'Event', 'Detail']);
}

function onFormSubmit(e) {
  var lock = LockService.getScriptLock(); lock.waitLock(30000);       // two submissions at once must not race
  try { return processRow_(e.range.getSheet(), e.range.getRow()); } finally { lock.releaseLock(); }
}

/** Re-process every response row that has no status yet (for back-filling, or after fixing a bug). */
function processPending() {
  var sh = SpreadsheetApp.getActive().getSheetByName(CFG.responses), n = sh.getLastRow(), out = [];
  for (var r = 2; r <= n; r++) if (!sh.getRange(r, statusCol_(sh)).getValue()) out.push(processRow_(sh, r));
  return out;
}

function processRow_(sh, row) {
  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var v = sh.getRange(row, 1, 1, head.length).getValues()[0], rec = {};
  head.forEach(function (h, i) { rec[String(h).trim().toLowerCase()] = v[i]; });
  var email = String(rec['email address'] || rec['email'] || '').trim().toLowerCase();
  var name = String(rec['full name'] || rec['name'] || '').trim().replace(/\s+/g, ' ');
  var exp = String(rec['coding experience'] || '').toLowerCase(), ts = rec['timestamp'] instanceof Date ? rec['timestamp'] : new Date();
  var problem = !name ? 'name missing' : !/^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(email) ? 'invalid email "' + email + '"' : null;
  if (problem) { status_(sh, row, 'INVALID: ' + problem); log_(email, 'invalid', problem); return { row: row, status: 'INVALID', reason: problem }; }

  name = name.split(' ').map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase(); }).join(' ');
  var track = /never|none|no experience|complete beginner/.test(exp) ? 'Python from zero' : /some|little|school/.test(exp) ? 'Python from zero (fast)' : 'Debugging basics';
  var monday = new Date(ts); monday.setHours(0, 0, 0, 0); monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  var cohort = Utilities.formatDate(monday, 'Asia/Kolkata', 'yyyy-MM-dd');

  var st = sheet_(CFG.students, CFG.headers), data = st.getDataRange().getValues(), found = -1;
  for (var i = 1; i < data.length; i++) if (data[i][0] === email) { found = i + 1; break; }
  var status;
  if (found > 0) {
    var subs = Number(st.getRange(found, 7).getValue() || 1) + 1;
    st.getRange(found, 2, 1, 6).setValues([[name, track, st.getRange(found, 4).getValue(), st.getRange(found, 5).getValue(), ts, subs]]);
    status = 'DUPLICATE-UPDATED';
  } else {
    st.appendRow([email, name, track, cohort, ts, ts, 1]); status = 'OK';
    if (CFG.sendEmail) {
      MailApp.sendEmail({ to: email, name: 'Code in Small Steps',
        subject: 'Welcome, ' + name.split(' ')[0] + '! Your first small step',
        body: 'Hi ' + name.split(' ')[0] + ',\n\nYou\'re in the ' + track + ' track (cohort of ' + cohort + ').\n' +
              'Start with lesson 1, "Variables: labelled boxes for values"; it takes about 5 minutes.\n\nMina, Code in Small Steps' });
      log_(email, 'email', 'welcome sent');
    }
  }
  status_(sh, row, status); log_(email, 'processed', status + ' / ' + track);
  return { row: row, status: status, email: email, name: name, track: track, cohort: cohort };
}

function sheet_(name, headers) {
  var ss = SpreadsheetApp.getActive(), sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.appendRow(headers); sh.setFrozenRows(1); }
  return sh;
}
function statusCol_(sh) {
  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0], c = head.indexOf('Status');
  if (c < 0) { c = head.length; sh.getRange(1, c + 1).setValue('Status'); }
  return c + 1;
}
function status_(sh, row, s) { sh.getRange(row, statusCol_(sh)).setValue(s); }
function log_(email, ev, detail) { sheet_(CFG.log, ['Time', 'Email', 'Event', 'Detail']).appendRow([new Date(), email, ev, detail]); }

if (typeof module !== 'undefined') module.exports = { onFormSubmit: onFormSubmit, processPending: processPending, setup: setup, CFG: CFG };
