# Web Development — Week 4: Capstone (Option 3, To-Do App)

Add, delete and mark tasks complete, filter by All, Active or Done, and clear completed tasks. Tasks are saved in `localStorage` and survive a refresh. If storage is blocked the app falls back to memory for the session. Task text is inserted with `textContent`, so it cannot inject HTML.

Open `index.html`. `node test.js` runs the store logic tests, which cover persistence, filters and corrupt stored data.
