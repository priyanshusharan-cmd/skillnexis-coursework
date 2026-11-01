// Equivalence partitioning and boundary value tests for three fields. Run with: node --test bva.test.js
//   * Password length: tested against the REAL registration API (needs the app running; API=http://127.0.0.1:4000).
//   * Age and purchase quantity: the app has no such fields, so these test small reference validators written from the
//     specification below. They demonstrate the technique; they are not tests of the app.
const assert = require('node:assert/strict');
const { test } = require('node:test');

const API = process.env.API || 'http://127.0.0.1:4000';
const RUN = Date.now().toString(36);
let n = 0;
const register = (password) => fetch(`${API}/api/auth/register`, {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'BVA', email: `bva-${RUN}-${n++}@example.com`, password }),
});

// ---------------- Password length (real API). Specification: 8 or more characters. ----------------
// Partitions: too short (0..7) invalid, long enough (8..) valid. Boundaries: 0, 1, 7, 8, 9. Plus extreme length.
test('password length: partitions and boundaries against the real API', async (t) => {
  const cases = [[0, 400], [1, 400], [7, 400], [8, 201], [9, 201], [64, 201]];
  for (const [len, expected] of cases) {
    await t.test(`length ${len} -> ${expected}`, async () => {
      assert.equal((await register('a'.repeat(len))).status, expected);
    });
  }
  await t.test('a non-string password is rejected', async () => {
    const res = await fetch(`${API}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'B', email: `bva-${RUN}-x@example.com`, password: 12345678 }) });
    assert.equal(res.status, 400);
  });
});

test('password length: very long passwords are handled safely (bcrypt only reads 72 bytes)', async (t) => {
  const email = `bva-long-${RUN}@example.com`;
  const long = 'A'.repeat(72) + 'LAST-PART-IS-DIFFERENT';
  const reg = await fetch(`${API}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'L', email, password: long }) });
  const login = pw => fetch(`${API}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password: pw }) });
  await t.test('a 94-character password is either rejected or fully respected', async () => {
    if (reg.status !== 201) return assert.equal(reg.status, 400);            // rejecting over-long passwords is acceptable
    assert.equal((await login(long)).status, 200, 'the full password logs in');
    const truncated = await login('A'.repeat(72));
    assert.equal(truncated.status, 401, 'the first 72 characters alone must NOT log in, or the extra characters are silently ignored');
  });
});

// ---------------- Age. Specification used for this exercise: a whole number from 18 to 65 inclusive. ----------------
const validateAge = v => typeof v === 'number' && Number.isInteger(v) && v >= 18 && v <= 65;
test('age: equivalence partitions and boundary values', () => {
  // [value, expected, why]
  const table = [
    [17, false, 'just below the lower boundary'], [18, true, 'lower boundary'], [19, true, 'just above the lower boundary'],
    [40, true, 'typical valid value (valid partition)'],
    [64, true, 'just below the upper boundary'], [65, true, 'upper boundary'], [66, false, 'just above the upper boundary'],
    [0, false, 'zero'], [-1, false, 'negative'], [1000, false, 'far above (invalid partition)'],
    [18.5, false, 'not a whole number'], ['30', false, 'string, not a number'], [NaN, false, 'NaN'], [null, false, 'missing'], [undefined, false, 'missing'],
  ];
  for (const [value, expected, why] of table) assert.equal(validateAge(value), expected, `${String(value)}: ${why}`);
});

// ---------------- Purchase quantity. Specification: a whole number from 1 to 10 per order. ----------------
const validateQuantity = v => typeof v === 'number' && Number.isInteger(v) && v >= 1 && v <= 10;
test('purchase quantity: equivalence partitions and boundary values', () => {
  const table = [
    [0, false, 'just below the lower boundary'], [1, true, 'lower boundary'], [2, true, 'just above the lower boundary'],
    [5, true, 'typical valid value'],
    [9, true, 'just below the upper boundary'], [10, true, 'upper boundary'], [11, false, 'just above the upper boundary'],
    [-1, false, 'negative'], [1e9, false, 'huge'], [1.5, false, 'fraction'], ['5', false, 'string'], [Infinity, false, 'infinity'], [null, false, 'missing'],
  ];
  for (const [value, expected, why] of table) assert.equal(validateQuantity(value), expected, `${String(value)}: ${why}`);
});
