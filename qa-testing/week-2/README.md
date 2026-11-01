# Software QA Tester — Week 2: Web & Cross-Platform Testing

The application under test is the **Week 3 MERN app** in this repository (`../../mern/week-3`): a task manager with sign-in and image upload. Testing it found four real defects, all fixed (see `findings.md`).

| Brief item | What was done |
| --- | --- |
| **Web test matrix**: one app, two browsers, two viewport sizes | `matrix.js`: 11 checks in **Chrome 156 and Edge 156**, each at **1280 × 800 desktop and 390 × 844 mobile**. Results in `results/matrix.md`, screenshots in `results/`. The *before-fix* run (`results/matrix-BEFORE-fix.md`) showed real failures, and the final run is 11 of 11 in all four combinations. |
| **API practice**: GET, POST, PUT/PATCH, DELETE with expected vs actual | `api-practice.js`: 22 requests, 16 against the app's API and 6 against the public JSONPlaceholder practice API. The first run had 2 failures (DEF-1), and after the fix it is 22 of 22. `results/api-results-BEFORE-fix.md` has the first run. |
| **Test design**: partitions and boundaries for age, password length and purchase quantity | `test-design.md` and `bva.test.js` (12 tests). Password length is tested on the live API, which exposed DEF-3. Age and quantity use reference rules, as the app has no such fields. |
| **Mini project: web + API regression pack** | `regression.test.js`: 20 tests tagged P1 (sign-in and data protection), P2 (features) and P3 (polish), covering 9 API endpoints with positive and negative cases, plus real-browser tests. All pass. |

## Run it
1. Start MongoDB, then the app: in `../../mern/week-3/server` run `npm install` and `JWT_SECRET=<long random string> CORS_ORIGIN=http://127.0.0.1:5173 npm start`, then in `../../mern/week-3/client` run `npm install && npm run build && npx vite preview --host 127.0.0.1`.
2. Here: `npm install`, then `npm run matrix`, `npm run api`, `npm test`.

Needs Google Chrome and Microsoft Edge installed (Playwright drives them, so no browsers are downloaded).

## Limits
Both browsers are Chromium-based, so this is not Firefox or Safari coverage. No real phones, screen readers or load testing. The public API is only a practice target, since it fakes writes.
