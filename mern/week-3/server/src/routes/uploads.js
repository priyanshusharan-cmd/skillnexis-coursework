const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const express = require('express');
const multer = require('multer');
const Upload = require('../models/Upload');

const MAX_BYTES = 2 * 1024 * 1024;
const TYPES = { 'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/webp': '.webp' };

/** Checks the first bytes of the file so a renamed non-image is not accepted. */
function looksLikeImage(buf, mime) {
  if (mime === 'image/png') return buf.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
  if (mime === 'image/jpeg') return buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff;
  if (mime === 'image/gif') return buf.subarray(0, 4).toString('latin1') === 'GIF8';
  if (mime === 'image/webp') return buf.subarray(0, 4).toString('latin1') === 'RIFF' && buf.subarray(8, 12).toString('latin1') === 'WEBP';
  return false;
}

module.exports = function uploadRoutes(dir) {
  fs.mkdirSync(dir, { recursive: true });
  const router = express.Router();
  const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: MAX_BYTES, files: 1 },
    fileFilter: (req, file, cb) => {
      if (TYPES[file.mimetype]) return cb(null, true);
      cb(Object.assign(new Error('Only PNG, JPEG, GIF or WebP images are allowed'), { code: 'BAD_TYPE' }));
    },
  });

  router.post('/', (req, res, next) => {
    upload.single('image')(req, res, async err => {
      try {
        if (err && err.code === 'LIMIT_FILE_SIZE') return res.status(400).json({ error: 'Image must be 2 MB or smaller' });
        if (err && err.code === 'BAD_TYPE') return res.status(400).json({ error: err.message });
        if (err instanceof multer.MulterError) return res.status(400).json({ error: 'Upload rejected' });
        if (err) return next(err);
        if (!req.file) return res.status(400).json({ error: 'Attach an image in the "image" field' });
        if (!looksLikeImage(req.file.buffer, req.file.mimetype)) return res.status(400).json({ error: 'File content is not a valid image' });
        const filename = crypto.randomBytes(16).toString('hex') + TYPES[req.file.mimetype];
        await fs.promises.writeFile(path.join(dir, filename), req.file.buffer);
        const doc = await Upload.create({ owner: req.userId, filename, originalName: path.basename(req.file.originalname), mimeType: req.file.mimetype, size: req.file.size });
        res.status(201).json({ id: doc.id, url: `/uploads/${filename}`, originalName: doc.originalName, size: doc.size });
      } catch (e) {
        next(e);
      }
    });
  });

  router.get('/', async (req, res, next) => {
    try {
      const docs = await Upload.find({ owner: req.userId }).sort({ createdAt: -1 });
      res.json(docs.map(d => ({ id: d.id, url: `/uploads/${d.filename}`, originalName: d.originalName, size: d.size })));
    } catch (e) {
      next(e);
    }
  });

  return router;
};
