const cors = require('cors');
const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { requireAuth } = require('./middleware/auth');
const Note = require('./models/Note');
const Task = require('./models/Task');
const authRoutes = require('./routes/auth');
const crudRouter = require('./routes/crud');

function createApp({ jwtSecret, corsOrigin = 'http://localhost:5173' }) {
  if (!jwtSecret || jwtSecret.length < 16) throw new Error('JWT_SECRET must be set to at least 16 characters');
  const app = express();
  app.use(helmet());
  app.use(cors({ origin: corsOrigin }));
  app.use(express.json({ limit: '100kb' }));

  app.get('/api/health', (req, res) => res.json({ ok: true }));
  app.use('/api/auth', rateLimit({ windowMs: 15 * 60 * 1000, limit: 100, standardHeaders: true, legacyHeaders: false }), authRoutes(jwtSecret));

  const auth = requireAuth(jwtSecret);
  app.use('/api/tasks', auth, crudRouter(Task, ['title', 'done']));
  app.use('/api/notes', auth, crudRouter(Note, ['title', 'body']));

  app.use((req, res) => res.status(404).json({ error: 'Not found' }));
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err.name === 'ValidationError') return res.status(400).json({ error: err.message });
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  });
  return app;
}

module.exports = { createApp };
