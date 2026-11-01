# MERN — Week 3: Full Stack Integration

`server/` is the Week 2 API plus image upload. `client/` is a React (Vite) app that uses it.

- **Full-stack To-Do app / Task Manager** (assignment 1 and mini project): register and log in, add, tick and delete tasks, filter by all, active or done. The token and user are kept in `sessionStorage`, routes use React Router with a protected-route wrapper, and auth state is shared with the Context API. An expired token logs the user out.
- **Image upload** (assignment 2): `POST /api/uploads` with Multer. It accepts PNG, JPEG, GIF and WebP up to 2 MB, checks the file's first bytes and not just its declared type, saves under a random name (the original filename is never used as a path), and rejects everything else, including SVG. The React page previews the chosen image before upload and lists the user's uploads.

## Run

```
cd server && npm install && cp .env.example .env   # set JWT_SECRET
npm start                                           # API on :4000, needs MongoDB
cd ../client && npm install && npm run dev          # app on :5173, proxies /api and /uploads to :4000
```

## What was checked

- Server: `npm test` has 10 tests, including upload cases (path-traversal filename, SVG, a fake PNG, an oversized file, and privacy between users). All passed against a local MongoDB.
- Client: `npm run build` succeeds. I also ran the API and the built client together and used the real UI in a browser: registered (including validation messages), added, ticked, filtered and deleted tasks, reloaded to confirm they persisted, uploaded a PNG and saw it listed and loaded, saw a fake image rejected, and confirmed a logged-out visitor is redirected to the login page.
