# MERN — Week 2: Backend (Node.js, Express, MongoDB)

A REST API covering all three parts of the brief:

- **To-Do List REST API:** `GET/POST /api/tasks`, `GET/PUT/DELETE /api/tasks/:id`, stored in MongoDB with Mongoose.
- **User Authentication API:** `POST /api/auth/register` and `/api/auth/login`. Passwords are hashed with bcrypt, and login returns a JWT that expires after 2 hours. Wrong email and wrong password give the same error.
- **Notes App Backend** (mini project): the same CRUD at `/api/notes`, protected by the JWT.

Tasks and notes belong to the signed-in user: one user cannot read, change or delete another user's items, and clients cannot set the `owner` field. Other protections: `helmet`, a request size limit, rate limiting on the auth routes, CORS limited to one origin, and a `JWT_SECRET` that must be set (the server refuses to start without one).

## Run

```
npm install
cp .env.example .env     # set JWT_SECRET to a long random string
npm start                # needs MongoDB at MONGO_URI
```

## Tests

`npm test` runs 9 tests against a real MongoDB (set `MONGO_URI`, or it uses a throwaway database on localhost:27017). They cover validation, duplicate and login errors, hashed storage, rejected tokens, the full task lifecycle, and privacy between users. All 6 passed against a local MongoDB.

Testing was done with Node's built-in test runner and `fetch` instead of Postman; the endpoints are plain JSON and work from Postman too.
