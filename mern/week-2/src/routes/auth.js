const bcrypt = require('bcryptjs');
const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

module.exports = function authRoutes(secret) {
  const router = express.Router();
  const sign = user => jwt.sign({ sub: user.id }, secret, { expiresIn: '2h' });

  router.post('/register', async (req, res, next) => {
    try {
      const { name, email, password } = req.body || {};
      if (typeof name !== 'string' || !name.trim()) return res.status(400).json({ error: 'Name is required' });
      if (typeof email !== 'string' || !EMAIL.test(email)) return res.status(400).json({ error: 'A valid email is required' });
      if (typeof password !== 'string' || password.length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters' });
      if (await User.exists({ email: email.toLowerCase() })) return res.status(409).json({ error: 'Email already registered' });
      const user = await User.create({ name, email, passwordHash: await bcrypt.hash(password, 10) });
      res.status(201).json({ token: sign(user), user: { id: user.id, name: user.name, email: user.email } });
    } catch (err) {
      next(err);
    }
  });

  router.post('/login', async (req, res, next) => {
    try {
      const { email, password } = req.body || {};
      const user = typeof email === 'string' ? await User.findOne({ email: email.toLowerCase() }) : null;
      // The same message for an unknown email and a wrong password avoids revealing which accounts exist.
      if (!user || typeof password !== 'string' || !(await bcrypt.compare(password, user.passwordHash))) {
        return res.status(401).json({ error: 'Invalid email or password' });
      }
      res.json({ token: sign(user), user: { id: user.id, name: user.name, email: user.email } });
    } catch (err) {
      next(err);
    }
  });

  return router;
};
