# Software QA Tester — Week 4: Performance, CI/CD & Major Project

Application under test: **Demo Shop** (`../week-3/demo-shop/server.js`), a store with login, search, cart, checkout and a 9-endpoint REST API.

| Brief item | What was done |
| --- | --- |
| **JMeter test plan for load testing a web page** | `jmeter/demo-shop-load.jmx`: one user journey (login page → API login with token extraction → product list → search → add to cart → view cart) with response, JSON-path and status assertions. Users, ramp-up, duration and think time are `-J` parameters. |
| **Stress test with 100 virtual users, analyse results** | Run on GitHub Actions with JMeter 5.6.3: **100 users for 90 s, 16,931 requests, 0% errors, p95 2 ms**. Analysis below. `jmeter/summarize.py` turns the `.jtl` file into per-request percentiles and fails the build above 1% errors or a p95 over 500 ms. |
| **CI pipeline that runs automated tests on push** | `.github/workflows/qa-tests.yml` (at the repository root). Every push touching QA weeks 3–4 runs Selenium, the Node regression tests, the scripted checks and Newman. If those pass, it runs the JMeter load and stress tests. Results are uploaded as build artifacts, and the JMeter tables go into the run summary. |
| **QA portfolio of all test artefacts** | `PORTFOLIO.md` covers weeks 1–4, the defects, metrics and links. |
| **Major project: test plan, strategy, 50+ cases, 15 Selenium scenarios, 5 APIs, JMeter at 100 users, portfolio** | `test-plan.md`, `test-strategy.md`, `test-cases.csv` (**60 cases**, every one executed). 15 critical Selenium scenarios: C01–C10 in `../week-3/selenium/test_scenarios.py`, C11–C15 in `selenium/test_critical.py`. 5 API groups / 15 requests in `../week-3/postman/`. JMeter as above. |

## Defects found and fixed this week

| ID | Severity | Found by | Problem | Fix | Regression test |
| --- | --- | --- | --- | --- | --- |
| DEF-1 | Minor | Scripted layout check (TC-057) | The nav links and the Checkout link were **20 px tall**, under the 24 px minimum target size (WCAG 2.2, 2.5.8), so they were easy to mis-tap on a phone. | Links get `display:inline-block; padding:10px 4px`, making them 40 px tall. | `selenium/test_regression_def1.py` checks every link and button on 4 pages |
| DEF-2 | Major | Reviewing the stress run (each JMeter iteration logs in) | **Sessions never expired.** 50,000 logins grew the live heap from 4.5 MB to 21.4 MB, which never came back down, so a long-running server would eventually run out of memory. | Sessions now expire after 30 min idle (`SESSION_TTL_MS`), a sweeper removes them, and the store is capped at 10,000 (`MAX_SESSIONS`, oldest evicted first). After the fix the same 50,000 logins left the heap at 9.8 MB and the store at 10,000. | `regression/sessions.test.js`: idle token expires, active token survives, store capped, sweeper empties it |

The heap numbers were measured with `node --expose-gc`, forcing a garbage collection before each reading, on the code before and after the fix.

## Performance analysis

Both runs were on a GitHub `ubuntu-latest` runner, with JMeter and the shop on the same 2-vCPU machine and 500 ms think time per step.

| Run | Users | Requests | Errors | Avg | p95 | p99 | Max | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Load | 25 (ramp 25 s, 60 s) | 2,375 | 0% | 1.1 ms | 2 ms | 3 ms | 29 ms | 40 req/s |
| Stress | 100 (ramp 10 s, 90 s) | 16,931 | 0% | 0.9 ms | 2 ms | 3 ms | 28 ms | 189 req/s |

Per-request tables are in `results/jmeter-load.md` and `results/jmeter-stress.md`.

**Reading the results**
- Throughput rose 4.7× from 25 to 100 users (40 → 189 req/s), roughly linear with user count, and response times did not rise. So at 100 users the shop is **not yet saturated**. The limit is the think time, not the server.
- The 28–29 ms maximums are single first requests (connection set-up and JIT warm-up); p99 stays at 3 ms.
- No request failed, including the token-dependent cart calls, so the auth chain holds under concurrency.
- What the numbers do not show: the cost of sessions piling up. The stress run created about 2,850 sessions in 90 s and never freed them, which led to DEF-2. A short run with a good p95 can still hide a slow leak, which is why a soak test belongs in the plan.
- **Next steps:** a soak run of 30 min or more watching heap size, and a step test at 0 ms think time to find the throughput ceiling.

## Run it locally

```sh
cd ../week-3 && npm install && cd ../week-4
python -m pytest -v ../week-3/selenium selenium                # 27 UI tests (+2 optional saucedemo)
node --test regression/sessions.test.js                         # DEF-2 regression
node ../week-3/demo-shop/server.js & python scripted-checks.py # scripted test cases
jmeter -n -t jmeter/demo-shop-load.jmx -Jusers=100 -Jrampup=10 -Jduration=90 -l stress.jtl -e -o report-stress
python jmeter/summarize.py stress.jtl --title "Stress: 100 users"
```

## Limits
- JMeter ran on the same machine as the shop, so these are best-case numbers with no network latency.
- The JMeter HTML dashboards are CI artifacts (kept 90 days) and are not committed. The summary tables in `results/` come from the same run.
- Firefox headless has a 500 px minimum window, so the layout checks ran at 500 px, not 390 px.
