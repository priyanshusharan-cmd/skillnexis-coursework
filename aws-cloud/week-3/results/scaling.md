One simulated day (1,440 minutes); peak demand 338 req/s during the 18:00 results rush (one t3.micro handles 120 req/s).

| Setup | Instance-hours | Cost/day (after free tier) | Minutes over 80 % CPU | Requests dropped |
|---|---:|---:|---:|---:|
| Auto Scaling 1-3 | 26.3 | $0.295 | 8 | 0 (0.00%) |
| Auto Scaling 1-4 | 27.1 | $0.304 | 2 | 0 (0.00%) |
| Auto Scaling 1-4 + scheduled 3 at 17:45 | 28.6 | $0.321 | 0 | 0 (0.00%) |
| Fixed 1 instance | 24.0 | $0.269 | 17 | 118,811 (6.59%) |
| Fixed 3 instances | 72.0 | $0.806 | 6 | 0 (0.00%) |

- Auto Scaling 1-3 used **26 instance-hours instead of 72** for a fixed fleet of 3 (63% less) and dropped nothing.
- Its 8 minutes above 80 % CPU (slow pages) were all in the 18:00 rush (8 of them): new instances need 3 minutes to boot and pass health checks.
- Raising the cap to 4: 2 hot minutes. Adding a scheduled action (minimum 3 from 17:45) before a known event: **0** hot minutes for +2.3 instance-hours (about $0.026).
- Even a fixed fleet of 3 had 6 hot minutes at the peak, at 2.7x the cost. Recommendation: min 1 / max 4, CPU target 50 %, scheduled scaling before known events.
