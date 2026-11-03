### Load: 25 users, 60 s

| Request | Samples | Error % | Avg ms | p90 | p95 | p99 | Max | Req/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 01 GET login page | 408 | 0.0 | 1.1 | 2 | 2 | 3 | 29 | 6.9 |
| 02 POST /api/login | 400 | 0.0 | 1.2 | 2 | 2 | 3 | 4 | 6.9 |
| 03 GET /api/products | 400 | 0.0 | 1.1 | 2 | 2 | 3 | 5 | 6.9 |
| 04 GET /api/products?q=lamp | 392 | 0.0 | 1.0 | 2 | 2 | 3 | 4 | 6.9 |
| 05 POST /api/cart | 392 | 0.0 | 1.2 | 2 | 2 | 5 | 5 | 6.9 |
| 06 GET /api/cart | 383 | 0.0 | 1.1 | 2 | 2 | 3 | 4 | 6.8 |
| **All requests** | 2375 | 0.0 | 1.1 | 2 | 2 | 3 | 29 | 40.1 |

- Error rate 0.0% (limit 1.0%): PASS
- p95 2 ms (limit 500 ms): PASS
