# Data Analyst — Week 3: Python & Data Wrangling

Assignment: clean a messy dataset in pandas by handling missing values, filtering rows and creating new columns.

`messy_workouts.csv` is the brief's dataset (32 workout rows with a missing date, two missing calorie values, a duplicate row, a bad duration, mixed date formats and an impossible pulse pair). `clean.py` fixes each problem and writes `cleaning_log.txt` saying what was changed and why:

| Problem | Fix |
| --- | --- |
| Dates as `'2020/12/01'`, `20201226` and one blank | Parsed both formats. The blank is the day between its two neighbours, which are two days apart. |
| 1 exact duplicate row | Dropped. |
| `Duration` 450 | Every other session is 30, 45 or 60 minutes and this row burns 253 kcal, like a 45-minute session, so it is treated as a typo for 45. This is an assumption. |
| `Maxpulse` below `Pulse` | The two values are swapped, since maximum pulse cannot be under the average. This is an assumption. |
| 2 missing `Calories` | Estimated from the median calories per minute (5.49) times the duration; flagged in `calories_estimated`. |

New columns: `calories_per_min`, `pulse_reserve`, `weekday` and `intensity` (low, medium, high by terciles). The script also filters to sessions of 45 minutes or more, prints summary statistics, writes `clean_workouts.csv` and draws `workouts.png` with Matplotlib and Seaborn.

Run with `pip install pandas matplotlib seaborn` and then `python3 clean.py`.
