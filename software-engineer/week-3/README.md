# Software Engineer — Week 3: System Design & APIs

| Brief item | Where | Notes |
| --- | --- | --- |
| **Design a URL shortener: architecture diagram and API endpoints** | `docs/url-shortener-design.md` | Requirements, capacity estimate (4k reads/s average, 3 TB over 5 years, 350 MB cache), Mermaid architecture diagram (CDN, load balancer, Redis, sharded KV store, Kafka analytics), API table, code generation (counter ranges + base62 + Feistel shuffle, compared with hashing and random codes), 301 vs 302, scaling and failure modes. |
| **RESTful API with CRUD, authentication and input validation** | `blog_api/` | The blog API below. |
| **Normalised database schema for a social media app** | `docs/social-media-schema.sql`, `.md` | 13 tables in 3NF (users, follows, posts, media, comments with replies, likes, hashtags, DMs, notifications), ER diagram, normal-form reasoning, index-to-query map. `docs/schema_check.py` loads the schema, confirms 5 constraints reject bad rows and runs the feed/hashtag/follower queries (`schema_check_output.txt`). |
| **API documentation with Swagger** | `/docs` on the running API, `docs/openapi.json` | Generated from the code, so it can't drift. Every request and response model has field limits and examples, and there is an Authorize button for the JWT. |
| **Mini project: blog platform API** | `blog_api/` + `tests/` | JWT auth, post CRUD, comments, likes, pagination, search, rate limiting, validation, Swagger. **33 tests, 100% line and branch coverage.** Deploy config in `/render.yaml`. |

## Blog API

| Method | Path | Auth | What it does |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Create a user (username 3–30 of `A-Z a-z 0-9 _`, password 8–72 bytes). `409` if taken (case-insensitive). |
| POST | `/auth/login` | – | Returns a JWT (HS256, 1 h). Same error for an unknown user and a wrong password. |
| GET | `/users/me` | ✔ | Current user |
| GET | `/posts?page=&page_size=&q=&author=` | – | Newest first, paginated (max 50 per page), search in title and body, filter by author. `%` and `_` in the search are matched literally. |
| POST | `/posts` | ✔ | Create (title 1–200, body 1–10,000; blank or whitespace-only rejected) |
| GET / PATCH / DELETE | `/posts/{id}` | PATCH and DELETE: owner only (`403` otherwise) | Read includes like and comment counts |
| GET / POST | `/posts/{id}/comments` | POST ✔ | Paginated, oldest first |
| DELETE | `/comments/{id}` | comment author **or** post author | Post authors can moderate their threads |
| PUT / DELETE | `/posts/{id}/like` | ✔ | Idempotent: liking twice is one like |

**Security and robustness**
- Passwords hashed with **scrypt** (standard library, salted); the 72-byte cap and constant-time compare are tested.
- JWTs accept only HS256 and require `sub`, `iat` and `exp`. Expired, tampered, wrong-algorithm and deleted-user tokens are all rejected (6 tests). The app refuses to start without a `JWT_SECRET` of 32+ characters.
- **Rate limiting** with token buckets: login and register at 5/min per IP (brute-force protection), everything else at 60/min per user (or per IP when anonymous). Responses carry `X-RateLimit-Limit` and `X-RateLimit-Remaining`, and a `429` carries `Retry-After`.
- All SQL is parameterised. Foreign keys cascade, so deleting a post removes its comments and likes.

## Run it

```sh
cd software-engineer/week-3
pip install -r requirements-dev.txt
export JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
uvicorn blog_api.app:app --reload          # Swagger UI at http://127.0.0.1:8000/docs
python -m pytest --cov=blog_api --cov-branch
python docs/schema_check.py
```

## Deploy (free)
`/render.yaml` at the repository root deploys this folder on **Render's free plan**: Dashboard → New → Blueprint → pick the repository. Render generates `JWT_SECRET` itself. The free plan has no persistent disk, so the SQLite data resets when the service restarts; a real deployment would point `BLOG_DB` at a managed database. The service sleeps after 15 minutes idle, so the first request after that takes about 30 s.

**Live URL:** to be added after the Render deploy.
