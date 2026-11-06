# Library brief: HTTP client for an async web scraper

**Recommendation: `aiohttp`** (score 0.94 of 1), chosen for the most recent release (3.14.5, 2026-10-11), native async support, which the need requires.

| Package | Score | Latest | Released | First release | GitHub stars | Meets requirements |
|---|---|---|---|---|---|---|
| [aiohttp](https://pypi.org/project/aiohttp/) | 0.94 | 3.14.5 | 2026-10-11 | 2013-10-25 | 16,605 | yes |
| [httpx](https://pypi.org/project/httpx/) | 0.59 | 0.28.1 | 2024-12-06 | 2019-07-19 | 15,738 | yes |
| [requests](https://pypi.org/project/requests/) | 0.43 | 2.34.2 | 2026-05-14 | 2011-02-14 | 54,643 | partial |

**Runner-up:** `httpx` (0.59).

*Async is a hard requirement here, so packages without native async support get a 40 % penalty.*  
*Scoring:* maintenance 35% (days since last release), popularity 25% (log GitHub stars), maturity 20% (years since first release), fit 20%. Data from PyPI and GitHub on 2026-11-06.

---
## Agent log

1. **Planner**: candidates ['httpx', 'aiohttp', 'requests'] via rules; criteria {'maintenance': 0.35, 'maturity': 0.2, 'popularity': 0.25, 'fit': 0.2, 'async_required': True}
2. **Researcher**: PyPI + GitHub facts for httpx, aiohttp, requests; failed: []
3. **Analyst**: ranking aiohttp 0.94, httpx 0.59, requests 0.43
4. **Writer**: draft 963 chars via template
5. **Reviewer**: approved: 16 numbers verified

Review: {'ok': True, 'notes': [], 'numbers_checked': 16}
