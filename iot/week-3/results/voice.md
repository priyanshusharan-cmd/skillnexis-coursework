Train: 2406 clips from 6 voices. Test: 702 clips from **unseen voices** (en-029, en-gb-scotland).

Overall test accuracy **0.953**; distractor phrases or noise wrongly taken as a command: **4.9%**. Model: 7,062 parameters, **12.0 KB** int8, 105 µs per inference on this PC.

| Command | Recall on unseen voices |
|---|---:|
| light on | 0.91 |
| light off | 0.94 |
| fan on | 0.96 |
| fan off | 1.00 |
| status | 0.96 |
| _unknown | 0.95 |
