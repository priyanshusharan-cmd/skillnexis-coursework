# MERN — Week 4: Capstone (Option 2, Social Media Feed)

A social feed with a Node/Express/MongoDB API (`server/`) and a React app (`client/`).

- **Accounts:** register and log in (bcrypt-hashed passwords, JWT, from Weeks 2 and 3).
- **Posts:** write a post (up to 500 characters), newest first, with cursor paging (`?before=<id>&limit=`).
- **Likes:** one like per user per post, toggled on and off.
- **Comments:** add comments (up to 300 characters) under any post.
- **Delete:** only a post's author can delete it; others get a 403.
- Post and comment text is rendered as text, so HTML typed into a post cannot run.

Not included: WebSockets for real-time updates (marked optional in the brief), and the deployment items in the week's topics (Vercel, Netlify, Render, MongoDB Atlas), which need your own cloud accounts. The app runs locally only.

## Run

```
cd server && npm install && cp .env.example .env   # set JWT_SECRET
npm start                                           # API on :4000, needs MongoDB
cd ../client && npm install && npm run dev          # app on :5173
```

## What was checked

- `npm test` in `server/`: 11 tests (auth, validation, ordering and paging, like toggling, comments, and author-only delete). All passed against a local MongoDB.
- `npm run build` in `client/` succeeds.
- Ran the API and built client together and used the real UI in a browser with two accounts: posted, liked, unliked, commented, and confirmed the other user has no Delete button on someone else's post.
