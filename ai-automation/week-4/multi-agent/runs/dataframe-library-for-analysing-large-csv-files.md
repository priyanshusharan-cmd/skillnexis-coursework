# Library brief: dataframe library for analysing large CSV files

**Recommendation: `pandas`** (score 0.98 of 1), chosen for the most recent release (3.1.1, 2026-11-04), the largest community (50,439 GitHub stars).

| Package | Score | Latest | Released | First release | GitHub stars | Meets requirements |
|---|---|---|---|---|---|---|
| [pandas](https://pypi.org/project/pandas/) | 0.98 | 3.1.1 | 2026-11-04 | 2009-12-25 | 50,439 | yes |
| [polars](https://pypi.org/project/polars/) | 0.91 | 2.1.0 | 2026-10-25 | 2021-03-15 | 40,274 | yes |
| [duckdb](https://pypi.org/project/duckdb/) | 0.84 | 2.0.0 | 2026-10-21 | 2019-05-08 | 204 | yes |

**Runner-up:** `polars` (0.91).

*Scoring:* maintenance 35% (days since last release), popularity 25% (log GitHub stars), maturity 20% (years since first release), fit 20%. Data from PyPI and GitHub on 2026-11-06.

---
## Agent log

1. **Planner**: candidates ['pandas', 'polars', 'duckdb'] via rules; criteria {'maintenance': 0.35, 'maturity': 0.2, 'popularity': 0.25, 'fit': 0.2, 'async_required': False}
2. **Researcher**: PyPI + GitHub facts for pandas, polars, duckdb; failed: []
3. **Analyst**: ranking pandas 0.98, polars 0.91, duckdb 0.84
4. **Writer**: draft 858 chars via template
5. **Reviewer**: approved: 15 numbers verified

Review: {'ok': True, 'notes': [], 'numbers_checked': 15}
