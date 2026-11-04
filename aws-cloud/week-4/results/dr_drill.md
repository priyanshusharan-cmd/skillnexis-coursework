Drill PASSED: 1,000 items before the incident, 1,000 after restore, identical (owner, id and url compared item by item).

| Step | Time (emulator) |
|---|---:|
| seed data | 565 ms |
| take backup | 11 ms |
| incident: table deleted | 6 ms |
| restore from backup | 16 ms |
| verify | 321 ms |

Emulator timings show the procedure works, not real durations: on AWS a restore of a small table takes minutes, so the documented RTO is 30 minutes including switching the Lambda's TABLE_NAME to the restored table.
