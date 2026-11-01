| # | API | Test | Request | Expected | Actual | Result |
|---|---|---|---|---|---|---|
| 1 | local | Register a new user | `POST /api/auth/register` | 201 | 201 | PASS |
| 2 | local | Register the same email again (negative) | `POST /api/auth/register` | 409 | 409 | PASS |
| 3 | local | Register with a 7-character password (negative) | `POST /api/auth/register` | 400 | 400 | PASS |
| 4 | local | Log in with the right password | `POST /api/auth/login` | 200 | 200 | PASS |
| 5 | local | Log in with the wrong password (negative) | `POST /api/auth/login` | 401 | 401 | PASS |
| 6 | local | List tasks with no token (negative) | `GET /api/tasks` | 401 | 401 | PASS |
| 7 | local | Create a task | `POST /api/tasks` | 201 | 201 | PASS |
| 8 | local | List tasks | `GET /api/tasks` | 200 | 200 | PASS |
| 9 | local | Update the task (PUT) | `PUT /api/tasks/6ae6e6c3bf0ff60ca74b4271` | 200 | 200 | PASS |
| 10 | local | Create a task with an empty title (negative) | `POST /api/tasks` | 400 | 400 | PASS |
| 11 | local | Get a task with a malformed id (negative) | `GET /api/tasks/not-an-id` | 400 | 400 | PASS |
| 12 | local | Send malformed JSON (negative) | `POST /api/tasks` | 400 | 500 | FAIL |
| 13 | local | Send an oversized body of about 200 KB (negative) | `POST /api/tasks` | 413 | 500 | FAIL |
| 14 | local | Delete the task | `DELETE /api/tasks/6ae6e6c3bf0ff60ca74b4271` | 204 | 204 | PASS |
| 15 | local | Delete the same task again (negative) | `DELETE /api/tasks/6ae6e6c3bf0ff60ca74b4271` | 404 | 404 | PASS |
| 16 | local | Security headers are present (helmet) | `GET /api/health` | x-content-type-options: nosniff | nosniff | PASS |
| 17 | public | GET a post | `GET /posts/1` | 200 | 200 | PASS |
| 18 | public | GET a post that does not exist (negative) | `GET /posts/99999` | 404 | 404 | PASS |
| 19 | public | POST a new post | `POST /posts` | 201 | 201 | PASS |
| 20 | public | PUT replaces a post | `PUT /posts/1` | 200 | 200 | PASS |
| 21 | public | PATCH changes one field | `PATCH /posts/1` | 200 | 200 | PASS |
| 22 | public | DELETE a post | `DELETE /posts/1` | 200 | 200 | PASS |
