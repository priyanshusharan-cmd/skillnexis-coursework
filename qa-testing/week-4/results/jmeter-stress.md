### Stress: 100 users, 90 s

| Request | Samples | Error % | Avg ms | p90 | p95 | p99 | Max | Req/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 01 GET login page | 2862 | 0.0 | 0.9 | 2 | 2 | 3 | 28 | 32.0 |
| 02 POST /api/login | 2847 | 0.0 | 1.0 | 2 | 2 | 3 | 9 | 32.0 |
| 03 GET /api/products | 2832 | 0.0 | 0.9 | 2 | 2 | 3 | 11 | 32.0 |
| 04 GET /api/products?q=lamp | 2816 | 0.0 | 0.9 | 2 | 2 | 3 | 10 | 32.0 |
| 05 POST /api/cart | 2797 | 0.0 | 1.0 | 2 | 2 | 3 | 8 | 32.0 |
| 06 GET /api/cart | 2777 | 0.0 | 0.9 | 2 | 2 | 3 | 11 | 32.0 |
| **All requests** | 16931 | 0.0 | 0.9 | 2 | 2 | 3 | 28 | 189.1 |

- Error rate 0.0% (limit 1.0%): PASS
- p95 2 ms (limit 500 ms): PASS
