const jwt = require('jsonwebtoken');

/** Requires "Authorization: Bearer <token>" and sets req.userId. */
function requireAuth(secret) {
  return (req, res, next) => {
    const header = req.get('Authorization') || '';
    const [scheme, token] = header.split(' ');
    if (scheme !== 'Bearer' || !token) return res.status(401).json({ error: 'Missing bearer token' });
    try {
      req.userId = jwt.verify(token, secret).sub;
      next();
    } catch {
      res.status(401).json({ error: 'Invalid or expired token' });
    }
  };
}

module.exports = { requireAuth };
